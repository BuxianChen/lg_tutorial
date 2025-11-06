# langgraph tutorial

大纲:

Part 0: LangChain

Part 1: langgraph基础

- ✅ State
- ✅ Node
- ✅ Edge, Conditional Edge, Graph
- ✅ 对比 Dify 拖拉拽模式

Part 2: langgraph特性

- ✅ langsmith 集成
- ✅ langgraph cli, langgraph studio, langgraph sdk
- ✅ langgraph 流式输出
- ✅ checkpointer (检查点/存储), time travel (时光机)
- ❌ subgraph

Part 3: 用langgraph搭建的一些agent例子

- ❌ 实际例子: 完成大体 graph 流程, 差具体实现
- ✅ Tool Use Agent
- ❌ Python Interpreter
- ❌ plan and execute

TODO:

- `checkpointer` vs `store`
- langgraph + FastAPI 部署
- langgraph 并行陷阱
- `create_agent` + deepagents
- langgraph Functional API
- langgraph Pregel
- Human-in-the-loop
- Middleware
- Inject State

# 开发模式对比

好处:
- 可以比较自由地实现并行等特殊逻辑, 可以显著提升运行效率
- 代码上可以做一些共用的函数, 例如画布模式下两个函数节点都需要调用一个公共函数, 只能复制相应的代码到每个函数节点里
- 项目结构看上去相对优雅, IDE 支持比较好可以到处做跳转方便阅读, 拖拉拽经常要一个个点开来看, 操作体验比 IDE 跳转差
- langchain生态独有优点: 可以用langsmith看中间过程
- 可以显著降低节点数量和变量数量
- 把 git 用好的话, 可以进行合作开发与版本管理
- 函数节点: 拖拉拽模式的实现往往基于 python 沙盒, 即通过把代码发送给沙盒服务器, 在沙盒服务器上执行完毕后再将结果返回工作流流程, 这会产生网络请求, 导致运行速度拖慢. 并且沙盒可使用的 python 三方包是受限的, 不能随意控制.

坏处:
- add_node, add_edge 写起来确实有些繁琐, 虽然可以输出 graph 的流程图进行观察
- 节点的入参一般都要是全局状态 state, 然后在函数内部取相应的字段, 不容易看清输入变量(应该可以弄个装饰器来统一解决)
- langchain 生态本身做了多轮重构, 导致 import 的方式总是发生变化, 并且拆分的包比较多: langchain-core, langchain, langgraph, ... 各个包的兼容性也很难确保.

# 附录

```bash
uv init
uv add -U langgraph langchain langchain-openai langgraph-cli[inmem] langgraph-sdk langchain-experimental
uv add ipykernel
uv add dotenv
```
