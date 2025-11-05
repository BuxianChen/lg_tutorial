# 主要用途:
# checkpoint
# 在 chatbot1.py 基础上加上 checkpoint

from typing import Annotated, Any

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver


from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
load_dotenv()

provider = "WILDCARD"
model = "gpt-5-mini"
base_url = os.environ[f"{provider}_BASE_URL"]
api_key = os.environ[f"{provider}_API_KEY"]
model = ChatOpenAI(model=model, base_url=base_url, api_key=api_key)


# 用户输入
def render_yellow(input: Any) -> str:
    return f"\033[33m{str(input)}\033[0m"

# 每次invoke或stream的最终结果
def render_red(input: Any) -> str:
    return f"\033[31m{str(input)}\033[0m"

# 流式过程
def render_green(input: Any) -> str:
    return f"\033[32m{str(input)}\033[0m"


class State(TypedDict):
    messages: Annotated[list, add_messages]


def chatbot(state: State):
    return {"messages": [model.invoke(state["messages"])]}

graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile(checkpointer=InMemorySaver())


# 使用checkpoint之后, 无需再手动维护 state 变量
def stream_graph_updates(user_input: str, config):
    """
    user_input: 本轮用户输入
    """
    for event in graph.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
        stream_mode="values"
    ):
        print(render_green(event["messages"][-1].content))
        # print(render_green(event))

    print(render_red(event))
    return event


if __name__ == "__main__":
    # 使用 langgraph 实现多轮对话, 一般是外面有个 while 表示多轮交互
    config = {"configurable": {"thread_id": "1"}}
    while True:
        user_input = input(render_yellow("User: "))
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        stream_graph_updates(user_input, config)

# Hello, I'm Bob
# What's my name