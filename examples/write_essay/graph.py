"""帮我使用 langgraph 实现下面的功能

节点1: 生成一个标题
节点2: 设置 5 个关键词, 需要以json列表格式输出
节点3: 生成一篇文章, 字数在 200-250 字之间, 每个关键词需至少出现 3 次
节点4: 检查文章是否符合要求 (关键词是否均出现 3 次以上, 文章字数是否合适)
条件边
(1) 如果没有满足要求, 则使用当前标题, 关键词及要求, 重新让大模型改写, 返回至节点3
(2) 满足要求则结束
(3) 若重写了 3 次 (包含最初写的那次) 仍然不符合要求, 则结束

注意:
State 应该至少要包含:
- 标题
- 关键词
- 每轮写的文章, 每轮写的文章是否符合要求

使用如下变量名约定
builder = StateGraph(...)
graph = builder.compiler()
"""

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import AIMessage
from typing import TypedDict, List, Dict, Any
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
load_dotenv()

provider = "WILDCARD"
model = "gpt-5-mini"
base_url = os.environ[f"{provider}_BASE_URL"]
api_key = os.environ[f"{provider}_API_KEY"]
llm = ChatOpenAI(model=model, base_url=base_url, api_key=api_key)


# === 定义状态 ===
class ArticleState(TypedDict):
    title: str
    keywords: List[str]
    article: str
    valid: bool
    attempts: int
    history: List[Dict[str, Any]]  # 存放每轮生成结果（标题/关键词/文章/检查结果）

# === 节点1: 生成标题 ===
def generate_title(state: ArticleState):
    prompt = "请生成一个有创意的中文文章标题。"
    resp = llm.invoke(prompt)
    title = resp.content.strip()
    return {"title": title}

# === 节点2: 生成关键词 ===
def generate_keywords(state: ArticleState):
    prompt = f"请为标题《{state['title']}》生成5个相关关键词，并以JSON数组格式输出，例如：[\"关键词1\", \"关键词2\", ...]"
    resp = llm.invoke(prompt)
    import json, re
    text = resp.content.strip()
    # 尝试解析为 JSON
    match = re.search(r"\[.*\]", text, re.S)
    if match:
        keywords = json.loads(match.group(0))
    else:
        keywords = [k.strip() for k in text.split()[:5]]
    return {"keywords": keywords}

# === 节点3: 生成文章 ===
def generate_article(state: ArticleState):
    title = state["title"]
    keywords = state["keywords"]
    prompt = f"""请根据标题《{title}》和以下关键词:
{keywords}
写一篇200-250字的中文文章，每个关键词至少出现3次。
"""
    resp = llm.invoke(prompt)
    article = resp.content.strip()
    new_history = state.get("history", [])
    new_history.append({"attempt": state.get("attempts", 0) + 1, "article": article})
    return {"article": article, "attempts": state.get("attempts", 0) + 1, "history": new_history}

# === 节点4: 检查文章 ===
def check_article(state: ArticleState):
    article = state["article"]
    keywords = state["keywords"]

    # 检查字数
    word_count = len(article)
    word_ok = 200 <= word_count <= 250

    # 检查关键词次数
    keyword_ok = all(article.count(k) >= 3 for k in keywords)

    valid = word_ok and keyword_ok

    new_history = state["history"]
    new_history[-1]["valid"] = valid
    new_history[-1]["word_count"] = word_count
    new_history[-1]["keyword_check"] = {k: article.count(k) for k in keywords}

    return {"valid": valid, "history": new_history}

# === 条件边函数 ===
def need_rewrite(state: ArticleState) -> str:
    if state["valid"]:
        return "pass"
    elif state["attempts"] >= 3:
        return "fail"
    else:
        return "retry"

# === 构建图 ===
builder = StateGraph(ArticleState)

builder.add_node("生成标题", generate_title)
builder.add_node("生成关键词", generate_keywords)
builder.add_node("生成文章", generate_article)
builder.add_node("检查文章", check_article)

# 边连接
builder.add_edge(START, "生成标题")
builder.add_edge("生成标题", "生成关键词")
builder.add_edge("生成关键词", "生成文章")
builder.add_edge("生成文章", "检查文章")

# 条件边：根据检查结果决定下一步
builder.add_conditional_edges(
    "检查文章",
    need_rewrite,
    {
        "pass": END,
        "retry": "生成文章",  # 回到生成文章节点
        "fail": END
    },
)

graph = builder.compile()

# === 运行 ===
if __name__ == "__main__":
    initial_state: ArticleState = {
        "title": "",
        "keywords": [],
        "article": "",
        "valid": False,
        "attempts": 0,
        "history": [],
    }
    with open("graph.png", "wb") as fw: 
        fw.write(graph.get_graph().draw_mermaid_png())
    result = graph.invoke(initial_state)
    print("==== 最终结果 ====")
    print(f"标题: {result['title']}")
    print(f"关键词: {result['keywords']}")
    print(f"最终文章:\n{result['article']}")
    print(f"是否合格: {result['valid']}")
    print(f"总尝试次数: {result['attempts']}")
    print("历史记录:")
    for h in result["history"]:
        print(h)
