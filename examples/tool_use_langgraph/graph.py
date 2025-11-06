# 使用 checkpointer 手工实现 tool use agent

# by GPT-5:
"""手工实现一个 tool use agent, 用 langgraph 实现

工具如下：
- 汇率转化：只允许美元、欧元、人民币互转,
- 计算器: 支持加减乘除, 输入必须能用 numexpr.evaluate 来计算, 输出为结果
- 当前时间: 无输入, 输出格式为 YYYY-MM-DD HH:MM:SS
- 日期差距: 日期差距计算器, 输入为两个日期 YYYY-MM-DD
- 日期顺延或倒退计算: 输入为 YYYY-MM-DD 以及 day, day 为整数, 正数表示基准日期+day, 否则是基准日期 -day

请给出完整实现

注意:
- tool 带上完整的输入输出参数的 docstring
- 需要支持连续对话, 用户问题由命令行输入
- 命令行输出需包含用户message, AI message(区分 tool call 和普通回答), ToolMessage, 用不同的 icon 区分
- 需要一个 system prompt, 希望大模型只回答我的问题, 不要进行寒暄与引导式发问

还需要给一个连贯的对话例子：
(1) 某些轮的问题需要调多个工具解答
(2) 某些轮的问题会纠正之前的部分内容(但仍需要联系前文)
(3) 对话例子最好有实际常见
(4) 用户问话轮数大约为 3 轮

对话例子放在脚本最后, 用注释的形式给出, 只需要给出用户的多轮问题即可
"""


from datetime import datetime, timedelta
import numexpr as ne
import os
from typing import Annotated, Literal, TypedDict, Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, AnyMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from dotenv import load_dotenv
load_dotenv()

# --------------------------
# 🧰 定义工具
# --------------------------

@tool
def convert_currency(amount: float, from_currency: Literal["USD", "EUR", "CNY"], to_currency: Literal["USD", "EUR", "CNY"]) -> float:
    """
    Convert currency between USD, EUR, and CNY.

    Args:
        amount (float): The amount of money to convert.
        from_currency (Literal["USD", "EUR", "CNY"]): Source currency.
        to_currency (Literal["USD", "EUR", "CNY"]): Target currency.

    Returns:
        float: Converted amount based on hardcoded exchange rates.

    Notes:
        Exchange rates are static and for demo purposes only:
        - 1 USD = 7.2 CNY
        - 1 EUR = 7.8 CNY
        - 1 EUR = 1.08 USD
    """
    rates = {
        ("USD", "CNY"): 7.2,
        ("CNY", "USD"): 1/7.2,
        ("EUR", "CNY"): 7.8,
        ("CNY", "EUR"): 1/7.8,
        ("USD", "EUR"): 1/1.08,
        ("EUR", "USD"): 1.08,
    }
    if from_currency == to_currency:
        return amount
    return amount * rates[(from_currency, to_currency)]


@tool
def calculator(expression: str) -> float:
    """
    Evaluate a mathematical expression using numexpr.

    Args:
        expression (str): The expression to evaluate. Must be valid for `numexpr.evaluate()`.
            Example: "3 + 5 * (2 - 1)"

    Returns:
        float: The evaluated numerical result.
    """
    try:
        return float(ne.evaluate(expression))
    except Exception as e:
        raise ValueError(f"Invalid expression: {e}")


@tool
def current_datetime() -> str:
    """
    Get the current system datetime.

    Returns:
        str: Current date and time in format "YYYY-MM-DD HH:MM:SS".
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool
def date_difference(date1: str, date2: str) -> int:
    """
    Calculate the difference in days between two dates.

    Args:
        date1 (str): The first date (format: YYYY-MM-DD).
        date2 (str): The second date (format: YYYY-MM-DD).

    Returns:
        int: The absolute number of days between the two dates.
    """
    d1 = datetime.strptime(date1, "%Y-%m-%d")
    d2 = datetime.strptime(date2, "%Y-%m-%d")
    return abs((d2 - d1).days)


@tool
def shift_date(base_date: str, day: int) -> str:
    """
    Shift a given date by a number of days.

    Args:
        base_date (str): The base date in format YYYY-MM-DD.
        day (int): Number of days to shift. Positive to move forward, negative to move backward.

    Returns:
        str: The resulting date after applying the shift.
    """
    d = datetime.strptime(base_date, "%Y-%m-%d")
    return (d + timedelta(days=day)).strftime("%Y-%m-%d")


# --------------------------
# 🧩 定义 State
# --------------------------

class AgentState(TypedDict):
    """Agent 的状态，包括消息历史。"""
    messages: Annotated[list[AnyMessage], add_messages]


# --------------------------
# 🤖 构建 Graph
# --------------------------

SYSTEM_PROMPT = """
你是一个专业的智能助手，具备多种工具能力（汇率换算、计算器、日期计算等）。
你的核心职责是：
- 只回答用户提出的问题；
- 不主动解释推理过程；
- 不进行寒暄、感叹或超出问题范围的回答；
- 若需要使用工具，请在内部完成后，直接给出最终结论；

回答风格：
- 简洁、直接；
- 仅在需要时给出推理中的关键结果；
- 不重复用户的提问。
"""

# llm = ChatOpenAI(model="gpt-4o-mini")

provider = "WILDCARD"
modelPname = "gpt-5"
base_url = os.environ[f"{provider}_BASE_URL"]
api_key = os.environ[f"{provider}_API_KEY"]
llm = ChatOpenAI(model=modelPname, base_url=base_url, api_key=api_key)


tools = [convert_currency, calculator, current_datetime, date_difference, shift_date]
tool_node = ToolNode(tools)

# agent 节点
def agent_node(state: AgentState):
    """Agent节点，决定是否调用工具"""

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("input")
    ])
    
    # 绑定工具
    model_with_tools = (prompt | llm.bind_tools(tools))
    response = model_with_tools.invoke({"input": state["messages"]})
    return {"messages": [response]}


# --------------------------
# 构建图结构
# --------------------------

builder = StateGraph(AgentState)

builder.add_node("agent", agent_node)
builder.add_node("tools", tool_node)

# conditional edge: 根据 AIMessage 是否请求使用工具
def should_continue(state: AgentState):
    msg = state["messages"][-1]
    if isinstance(msg, AIMessage) and msg.tool_calls:
        return "tools"
    return END

builder.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
builder.add_edge("tools", "agent")

builder.set_entry_point("agent")
memory = InMemorySaver()
graph = builder.compile(checkpointer=memory)


def pretty_print_message(msg):
    """美化输出消息"""
    if isinstance(msg, HumanMessage):
        print(f"👤 用户: {msg.content}")
    elif isinstance(msg, AIMessage):
        if msg.tool_calls:
            print(f"🧠 AI（Tool Call）:")
            for call in msg.tool_calls:
                print(f"   🔧 调用工具: {call['name']}({call['args']}) [id={call['id']}]")
        else:
            print(f"🤖 AI: {msg.content}")
    elif isinstance(msg, ToolMessage):
        print(f"🛠️ 工具结果 [{msg.name}]: {msg.content}")
    else:
        print(f"❓ 未知消息: {msg}")


if __name__ == "__main__":
    # with open("graph.png", "wb") as fw: 
    #     fw.write(graph.get_graph().draw_mermaid_png())

    # --------------------------
    # 🚀 运行示例
    # --------------------------

    thread_config = {"configurable": {"thread_id": "chat-1"}}

    print("=== 🤖 Tool-Use Agent Ready ===")
    print("输入你的问题（输入 exit 结束）\n")

    while True:
        user_input = input("\n👤 你: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        events = graph.stream(
            {"messages": [HumanMessage(content=user_input)]},
            thread_config,
            stream_mode="values",
        )

        for event in events:
            msg = event["messages"][-1]
            pretty_print_message(msg)

    # 我计划3天后从北京早上出发去巴黎，中午到达，行程持续 7 天(包含首尾两天)，最后一天中午出发，晚上到达，能帮我算下返回日期吗？
    # 我大概需要 1500 欧元的住宿费和 800 美元的餐饮费，能告诉我折算成人民币总共大概多少吗？
    # 我决定提前2天出发，再告诉我新的出发和返回日期。


"""本例的一些发现:
(1) gpt-5-mini 尝试了几次都不能很好的利用工具解决问题, 但gpt-5可以
"""