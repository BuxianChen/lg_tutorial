"""帮我使用 langgraph 实现下面的一个 demo

输入 a, b, upper_bound, min_increment, max_increment, 均为整数

- a, b 的默认值为 0
- min_increment 的默认值为 1
- max_increment 的默认值为 3
- upper_bound 的默认值为 10

做如下事情:

(1) 使用大模型判断循环次数最少和最多的预估
(2) 计算 a + b 的值, 假设 a + b 的值小于 upper_bound, 那么分别对 a 和 b 增加一个 [min_increment, max_increment] 的随机数, 注意两者增加的随机数不相同, 且需要并行处理各自的增加过程, 假设 a + b 的值大于等于 upper_bound 则循环结束. 注意: 要等 a 和 b 均进行了增加后再计算 a + b, 来判断是否已经超过了 upper_bound
(3) 循环结束后, 使用大模型节点描述整个过程, 并说明实际的循环次数

State:
- a: int, 输入
- b: int, 输入
- a_list: list[int], 实际执行时, 每一步的 a 的记录, 注意使用自定义的 reducer 来做字段注解
- a_list: list[int], 实际执行时, 每一步的 b 的记录, 注意使用自定义的 reducer 来做字段注解
- upper_bound: int, 输入, 两者求和需要达到的上限值
- min_increment: int, 输入, 每次增加的整数的下限
- max_increment: int, 输入, 每次增加的整数的上限
- theory_analyse: str, 大模型判断循环次数最少和最多的预估
- process_interpreter: str, 大模型解释整个过程

计算拓扑图涉及上, 由于我再 State 里没有明文存储当前 a + b 的值, 因此在 a 和 b 的自增结点前后, 可能需要增加 passthrough 节点 (不确定是否必要), 请自行考虑

具体的 Node 如下:

(1) START
(2) set_default: 根据输入情况设置默认值
(3) theory_analysis: 理论分析节点
(4) before_condition_passthrough: 条件判断前空节点
(5) after_condition_passthrough: 条件判断后空节点
(6) increment_a: 对 a 进行增加
(7) increment_b: 对 b 进行增加
(8) process_interpreter: 解释执行过程
(9) END

拓扑图如下:
(1) -> (2) -> (3) -> (4) -[条件边]         ->   (5) -> (6) -> (4)
                      |                         |
                      -[条件边]-> (8) -> (9)     -> (7) -> (4)

使用如下变量名约定
builder = StateGraph(...)
graph = builder.compiler()
"""

import operator
from typing import Annotated, TypedDict, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.config import get_stream_writer
from langchain_openai import ChatOpenAI
import random
from dotenv import load_dotenv
import os
load_dotenv()


# 自定义 reducer，用于追加列表元素
def append_reducer(existing: list, new: int) -> list:
    """追加新元素到列表"""
    return existing + [new]


# 定义 State
class State(TypedDict):
    a: int
    b: int
    a_list: Annotated[list[int], append_reducer]
    b_list: Annotated[list[int], append_reducer]
    upper_bound: int
    min_increment: int
    max_increment: int
    theory_analyse: str
    process_interpreter: str


# 初始化 LLM
# llm = ChatOpenAI(model="gpt-4", temperature=0)
provider = "WILDCARD"
model = "gpt-5-mini"
base_url = os.environ[f"{provider}_BASE_URL"]
api_key = os.environ[f"{provider}_API_KEY"]
# 固定了下随机种子: 期望能输出相同的结果, 但事实上好像不生效
llm = ChatOpenAI(model=model, base_url=base_url, api_key=api_key, seed=1024)


# Node 1: 设置默认值
def set_default(state: State) -> State:
    """设置默认值并初始化列表"""
    return {
        "a": state.get("a", 0),
        "b": state.get("b", 0),
        "a_list": state.get("a", 0),
        "b_list": state.get("b", 0),
        "upper_bound": state.get("upper_bound", 10),
        "min_increment": state.get("min_increment", 1),
        "max_increment": state.get("max_increment", 3),
    }


# Node 2: 理论分析
def theory_analysis(state: State) -> State:
    """使用大模型分析循环次数"""
    prompt = f"""
    给定初始值 a={state['a']}, b={state['b']}, 上界={state['upper_bound']}.
    每次循环时，a 和 b 分别增加 [{state['min_increment']}, {state['max_increment']}] 范围内的随机整数。
    当 a + b >= {state['upper_bound']} 时循环结束。
    
    请分析：
    1. 最少需要多少次循环？（最理想情况）
    2. 最多需要多少次循环？（最坏情况）
    
    请简洁回答。
    """
    
    response = llm.invoke(prompt)
    
    return {
        "theory_analyse": response.content
    }


# Node 3: 条件判断前的空节点
def before_condition_passthrough(state: State) -> State:
    """条件判断前的 passthrough 节点"""
    return {}


# Node 4: 条件判断后的空节点
def after_condition_passthrough(state: State) -> State:
    """条件判断后的 passthrough 节点"""
    return {}


# Node 5: 增加 a
def increment_a(state: State) -> State:
    """对 a 进行随机增加"""
    increment = random.randint(state['min_increment'], state['max_increment'])
    new_a = state['a'] + increment
    
    writer = get_stream_writer()
    writer({"update_a": f"update a from {state['a']} to {new_a}"})

    return {
        "a": new_a,
        "a_list": new_a,
    }


# Node 6: 增加 b
def increment_b(state: State) -> State:
    """对 b 进行随机增加"""
    increment = random.randint(state['min_increment'], state['max_increment'])
    new_b = state['b'] + increment

    writer = get_stream_writer()
    writer({"update_b": f"update a from {state['b']} to {new_b}"})
    
    return {
        "b": new_b,
        "b_list": new_b,
    }


# Node 7: 解释执行过程
def process_interpreter(state: State) -> State:
    """使用大模型解释整个执行过程"""
    actual_loops = len(state['a_list']) - 1  # 减去初始值
    
    prompt = f"""
    请描述以下增量过程：
    
    初始值：a={state['a_list'][0]}, b={state['b_list'][0]}
    上界：{state['upper_bound']}
    增量范围：[{state['min_increment']}, {state['max_increment']}]
    
    执行过程：
    a 的变化：{state['a_list']}
    b 的变化：{state['b_list']}
    
    理论分析：
    {state['theory_analyse']}
    
    实际循环次数：{actual_loops}
    最终结果：a={state['a']}, b={state['b']}, a+b={state['a'] + state['b']}
    
    请总结整个过程，并比较理论预估和实际执行的差异。
    """
    
    response = llm.invoke(prompt)
    
    return {
        "process_interpreter": response.content
    }


# 条件判断函数
def should_continue(state: State) -> Literal["continue", "end"]:
    """判断是否继续循环"""
    current_sum = state['a'] + state['b']
    if current_sum < state['upper_bound']:
        return "continue"
    else:
        return "end"


# 构建图
builder = StateGraph(State)

# 添加节点
builder.add_node("set_default", set_default)
builder.add_node("theory_analysis", theory_analysis)
builder.add_node("before_condition_passthrough", before_condition_passthrough)
builder.add_node("after_condition_passthrough", after_condition_passthrough)
builder.add_node("increment_a", increment_a)
builder.add_node("increment_b", increment_b)
builder.add_node("process_interpreter", process_interpreter)

# 添加边
builder.add_edge(START, "set_default")
builder.add_edge("set_default", "theory_analysis")

# 添加边
builder.add_edge("theory_analysis", "before_condition_passthrough")

# 条件边：从 before_condition_passthrough 出发
builder.add_conditional_edges(
    "before_condition_passthrough",
    should_continue,
    {
        "continue": "after_condition_passthrough",
        "end": "process_interpreter"
    }
)

# 并行增加 a 和 b
builder.add_edge("after_condition_passthrough", "increment_a")
builder.add_edge("after_condition_passthrough", "increment_b")

# 从 increment_a 和 increment_b 回到 before_condition_passthrough 进行下一轮判断
builder.add_edge("increment_a", "before_condition_passthrough")
builder.add_edge("increment_b", "before_condition_passthrough")

builder.add_edge("process_interpreter", END)

# 编译图
graph = builder.compile()


# 测试运行
if __name__ == "__main__":
    # with open("graph.png", "wb") as fw: 
    #     fw.write(graph.get_graph().draw_mermaid_png())

    # # 示例 1: 使用默认值
    # result = graph.invoke({})
    # print("=" * 50)
    # print("示例 1: 使用默认值")
    # print("=" * 50)
    # print(f"最终 a: {result['a']}")
    # print(f"最终 b: {result['b']}")
    # print(f"a + b: {result['a'] + result['b']}")
    # print(f"a 变化过程: {result['a_list']}")
    # print(f"b 变化过程: {result['b_list']}")
    # print(f"\n理论分析:\n{result['theory_analyse']}")
    # print(f"\n过程解释:\n{result['process_interpreter']}")
    
    # 示例 2: 自定义参数
    print("\n" + "=" * 50)
    print("示例 2: 自定义参数")
    print("=" * 50)
    result2 = graph.invoke({
        "a": 2,
        "b": 3,
        "upper_bound": 20,
        "min_increment": 2,
        "max_increment": 5
    })
    print(f"最终 a: {result2['a']}")
    print(f"最终 b: {result2['b']}")
    print(f"a + b: {result2['a'] + result2['b']}")
    print(f"a 变化过程: {result2['a_list']}")
    print(f"b 变化过程: {result2['b_list']}")
    print(f"\n理论分析:\n{result2['theory_analyse']}")
    print(f"\n过程解释:\n{result2['process_interpreter']}")