# DAP-v2 · Data Agent 平台

面向数仓场景的企业级智能体平台：**NL2SQL 自助查询（P0）· 数据质量主动治理（P1）· ETL 编排开发（P2）**。

架构六层：接入(React控制台) → 网关(FastAPI+Strawberry GraphQL+REST/SSE) → 编排(worker 内状态图，LangGraph 同构，ADR-002) → 业务Agent(洞察/质量+根因/ETL) → 知识引擎(CRDB 语义层/Milvus 混合RAG/Nebula 血缘/规则引擎) → 工具层(MCP化,sql-executor四层护栏) → 数据平台(TiDB样例数仓)。

```
packages/dap_core   共享内核：配置/可观测/三级缓存/CRDB读写分离(DualPool)/韧性/AgentMessage契约
services/gateway    BFF：GraphQL + REST + SSE + 多租户 JWT RBAC + 限流（同步缓存路径）
services/worker     状态图编排 + 三条管线（pipeline.py：洞察 NL2SQL / 质量扫描+根因 / ETL 规划）
                    + Pulsar 共享订阅消费 + 确定性模板兜底(fallback_sql) + outbox relay
services/tools      MCP 工具层 + 知识引擎能力：sql-executor(四层护栏)/metadata.search/
                    lineage/quality/semantic-cache/index/knowledge（init_db.py 初始化）
web/console         React+TS+AntD 控制台（洞察/质量/ETL/审批/管理 五工作台）
deploy/k8s          GitOps 单一事实源（扁平 8 个 yaml：00-namespace-config ~ 07-backup）
tests/              smoke.sh + e2e(Playwright) load(k6/Locust) bdd(behave) eval(NL2SQL评测 run_eval.py)
seed/               TiDB 样例数仓（零售主题 ODS→ADS，seed_warehouse.py，make seed 调用）
docs/               SAD/ADR/契约/测试报告
```

> 结构说明：ADR-002 决策自研 StateGraph（与 LangGraph 同构、零依赖可测），编排与三条业务管线内聚于 `services/worker`，不再单设 orchestrator/agents/knowledge 目录；知识引擎的元数据语义层在 **CRDB**（平台库），Milvus 承担向量检索，Nebula 承担血缘（CRDB lineage_edges 双写兜底）。

快速开始：`make help` · 部署：`make deploy` · 灌数：`make seed` · 压测：`make load-test`
