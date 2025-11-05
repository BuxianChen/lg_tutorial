# 主要用途:
# (1) chatbot 实现
# 以下两部分简单体验下
# (2) langsmith
# (3) langgraph studio, langgraph-cli: 需要演示 template

# 代码修改自:
# https://langchain-ai.github.io/langgraph/tutorials/get-started/1-build-basic-chatbot/

from typing import Annotated, Any

from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


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
    # 注意: State 定义的字段除了可以标识字段类型外, 还可以标识 reducer
    # 就是节点运行返回 messages 这个字段时, 对这个字段做这种处理:
    # state["messages"] = add_message(state["messages"], node_output["messages"])
    # 之前的例子都没有做类似的标识, 所以默认是用节点返回的值覆盖相应的字段
    messages: Annotated[list, add_messages]


def chatbot(state: State):
    return {"messages": [model.invoke(state["messages"])]}

graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("chatbot", END)
graph = graph_builder.compile()


def stream_graph_updates(state, user_input: str):
    """
    state: 当前状态(上一轮 graph.stream 返回的结果)
    user_input: 本轮用户输入
    """
    # 每一轮分为两个步骤: 
    # (1) "前一轮的状态 + 当前的用户输入" 得到本轮的输入
    # (2) graph.invoke/stream 得到本轮的输出

    # STEP 1: 根据本轮输入更新状态
    if not state.get("messages"):
        state["messages"] = []
    state["messages"].append({"role": "user", "content": user_input})
    
    # STEP 2: graph.invoke/stream 得到本轮的输出
    for event in graph.stream(
        state,
        stream_mode="values"
    ):
        print(render_green(event["messages"][-1].content))
        # print(render_green(event))

    return event


if __name__ == "__main__":
    # 使用 langgraph 实现多轮对话, 一般是外面有个 while 表示多轮交互
    state = State()
    print(render_red(state))
    while True:
        user_input = input(render_yellow("User: "))
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break
        # old_state + user_input -> new_state
        state = stream_graph_updates(state, user_input)
        print(render_red(state))

# Hello, I'm Bob
# What's my name
