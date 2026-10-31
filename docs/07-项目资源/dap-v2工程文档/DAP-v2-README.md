# DAP-v2 · Data Agent 平台

面向数仓场景的企业级智能体平台：**NL2SQL 自助查询（P0）· 数据质量主动治理（P1）· ETL 编排开发（P2）**。

架构六层：接入(React控制台) → 网关(FastAPI+Strawberry GraphQL+REST/SSE) → 编排(LangGraph) → 六专业Agent → 知识引擎(TiDB语义层/Milvus混合RAG/Nebula血缘/规则引擎) → 工具层(MCP化,sql-executor四层护栏) → 数据平台(TiDB样例数仓)。

```
packages/dap_core   共享内核：配置/可观测/三级缓存/CRDB读写分离/韧性/AgentMessage契约
services/gateway    BFF：GraphQL + REST + SSE + 多租户RBAC + 限流
services/orchestrator  LangGraph 编排器
services/agents     insight / quality / rca / etl 四业务 Agent（metadata/gov 能力在 knowledge）
services/knowledge  元数据·语义层·RAG·血缘
services/tools      MCP 工具层：sql-executor(四层护栏)/metadata/lineage/quality/schedule
services/worker     Pulsar 消费者 + 质量检测调度 + outbox relay
web/console         React+TS+AntD 控制台
deploy/k8s          GitOps 单一事实源
tests/              e2e(Playwright) load(k6/Locust) bdd(behave) eval(NL2SQL评测)
seed/               TiDB 样例数仓（零售主题 ODS→ADS）
docs/               SAD/ADR/契约/测试报告
```

快速开始：`make help` · 部署：`make deploy` · 压测：`make load-test`
