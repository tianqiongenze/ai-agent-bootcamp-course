# DAP-v2 软件架构文档（SAD）

> 版本 2.0 · 2026-10-30 · 架构责任人：JoelGong
> 本文档是 DAP-v2 架构的**单一事实源**（ADS 铁律），与 `deploy/k8s/`（GitOps 清单）双向核对。
> 方法论对齐：TOGAF ADM · 两份落地资料（《数仓不需要更多人，需要 Data Agent》四层模型 /《三个 Agent 落地数仓实战复盘》五层架构+三场景）

## 1. 架构驱动因素（ADR 输入）

| 驱动因素 | 约束/目标 |
|---|---|
| 容量目标 | 100 万并发用户（**设计目标**；本集群 2 节点实测上限+线性外推验收，见测试报告 §容量） |
| 场景 | P0 NL2SQL 自助查询 · P1 数据质量主动治理 · P2 ETL 编排开发（优先级 P0>P1>P2） |
| 硬件 | 10.167.2.175（master, 16C/126G）+ 10.167.2.176（worker, 64C/125G/3T），无 GPU |
| 存量约束 | master CPU requests 99% / worker1 内存 requests 97%；v1（dataagent-prod/course）并行不动 |
| 合规 | 四层安全护栏强制；PII 脱敏；全量审计；写操作人工审批 |

## 2. 逻辑视图：六层架构

```
L0 接入层   React18+TS+AntD 控制台（洞察/质量/ETL/审批/管理 五工作台）
            ingress-nginx(dataagent.platform.local) + NodePort 30281
L1 网关层   dap-gateway ×3：FastAPI + Strawberry GraphQL + REST + SSE
            多租户 JWT RBAC · per-tenant 令牌桶限流 · GraphQL 深度防护
L2 编排层   dap-worker ×3：状态图编排（LangGraph 同构，ADR-002）
            Pulsar 共享订阅消费 · 同步缓存路径/异步任务路径
L3 Agent层  insight(NL2SQL) · quality+rca(质量双Agent) · etl(编排) —— 边界明确互不越权
L4 知识引擎 dap-tools ×2 内：元数据+语义层(CRDB) · Milvus 混合RAG · Nebula 血缘(CRDB兜底)
L5 工具层   MCP 化标准接口：sql-executor(四层护栏) · metadata.search · quality · lineage
L6 数据平台 TiDB v8.5.8（目标数仓，零售样例 ODS→ADS）· CRDB(平台库,读写分离) · Pulsar · dap-redis
```

**LLM 供给**：LiteLLM 网关（qwen2.5:14b 主路由 + qwen2.5-coder:7b fallback + 确定性模板三级降级）；外部商用 API Key 到位后仅需改 ConfigMap `DAP_LLM_PRIMARY_MODEL`。

## 3. 数据视图

- **CRDB `dap`**（平台库）：runs/run_events/approvals/quality_rules+results/metrics/few_shots/meta_tables+columns/lineage_edges/etl_drafts/outbox/audit_log/feedback/tenants/users
  - 读写分离：写 DSN `cockroachdb-a:26257` · 读 DSN `cockroachdb-b:26267`（读库故障自动降级写库，DPC）
  - 事件可靠性：outbox 表 + relay（EER）；乐观锁 `version` 列（OCC）
- **TiDB `warehouse`**（样例数仓 105.9万订单）：ods_orders / ods_refund_orders / dwd_trade_order_detail / dim_(store,region,product,date) / dws_(store,product)_daily_sales / ads_(store_gmv_trend, category_topn)
- **Milvus**：dap_knowledge（表/列/指标/few-shot 向量）、dap_semantic_cache（L3 语义缓存，cosine≥0.92）
- **NebulaGraph space=dap**：tag tbl / edge derives_from（CRDB lineage_edges 双写兜底）

## 4. 关键机制

| 机制 | 实现 |
|---|---|
| 四层护栏 | sqlglot L1 语法白名单(仅SELECT/WITH) → L2 资源(强制LIMIT 1000/20s/20万行) → L3 权限(租户表通配授权+PII列脱敏) → L4 审批(写/DDL→approvals 工作流) |
| 三级缓存 | L1 进程 LRU → L2 redis(TTL 5min/1h) → L3 语义(Milvus 0.92)；响应带 cache_hit/cache_layer；指标 dap_cache_hits_total{layer} |
| 降级体系 | LLM→模板 · 读库→写库 · Milvus→CRDB关键词 · Nebula→CRDB血缘 · Redis→直穿 · Pulsar→503+本地排队（DPC 契约测试覆盖） |
| 自愈 | CRDB/Redis/httpx 客户端探活失败自动重建（DPM）；Pulsar 断连 5s 重连 |
| 可观测 | /metrics 三服务全暴露 + pod annotations（Prometheus 抓取）+ Loki 日志 + Grafana 面板（30082） |

## 5. 部署视图（与 deploy/k8s 一致）

| Deployment | 副本 | 资源(request) | 探针 |
|---|---|---|---|
| dap-gateway | 3 (HPA 3-10) | 150m/256Mi | readyz(全依赖)+preStop 5s |
| dap-worker | 3 (HPA 3-12) | 150m/384Mi | readyz |
| dap-tools | 2 | 100m/256Mi | readyz |
| dap-redis | 1 | 50m/128Mi | redis-cli ping |

镜像：`10.167.2.175:30500/dap/{gateway,tools,worker}:latest`；前端 dist 烘焙进 gateway 镜像。

## 6. 与资料的映射

- 资料[1] 四层模型 → 本架构 L1-L5 展开；六专业 Agent → 3 业务 Agent+知识引擎服务（metadata/gov 能力内聚）
- 资料[1] §5 NL2SQL 提升 → Schema Linking(检索先行) + Few-shot(知识库) + 自校验(执行重试≤2) + 人工反馈回流(feedback→few_shots)
- 资料[2] 五层架构 → 工具层标准接口(不直连引擎) + 规则引擎/LLM 混合(质量规则确定性执行、RCA 用 LLM)
- 资料[2] 三场景 → P0/P1/P2 里程碑；ROI 优先级一致
