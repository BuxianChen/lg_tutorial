# lg_tutorial

langgraph 是什么, 怎么用: 部分(1)
langgraph 有什么优势: 部分(2)(3)

第一部分(langgraph基础): state, node, edge, conditional edge, graph, (非agent例子, 普通chatbot, 带搜索功能的chatbot, tool call agent)

第二部分(langgraph生态): langsmith, langgraph studio, 时光机

第三部分(实际的agent): 质检, llm-compiler

其他: Functional API, 并行的陷阱(pregel)

# 开发模式对比

全代码模式:

好处:
- 可以比较自由地实现并行等特殊逻辑, 可以显著提升效率
- 项目结构看上去相对优雅, IDE 支持比较好可以到处做跳转方便阅读, 拖拉拽经常要一个个点开来看, 操作体验比 IDE 跳转差
- langchain生态独有优点: 可以用langsmith看中间过程
- 可以显著降低节点数量和变量数量
- 把 git 用好的话, 可以较好的合作开发与版本管理

坏处:
- 快速调试时一般需要改代码, 在需要地方添加结束的边
- add_node, add_edge 写起来确实有些繁琐, 虽然可以输出 graph 的流程图观察

# 附录

```bash
uv init
uv add --prerelease=allow langgraph langchain langchain-openai
uv add ipykernel
uv add dotenv
```
