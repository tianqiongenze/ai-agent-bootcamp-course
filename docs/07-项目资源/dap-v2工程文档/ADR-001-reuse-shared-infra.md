# ADR-001：复用集群共享基础设施而非新建中间件
状态：Accepted · 2026-10-29
背景：集群 infra ns 已运行 TiDB v8.5.8 / CockroachDB 3节点 / Milvus v2.6.6 / NebulaGraph v3.8.3 / Pulsar 4.0.5 / Prometheus+Grafana+Loki。新建一套中间件需 ~30Gi 内存 requests，而 worker1 内存 requests 已 97%。
决策：全部复用现有中间件，仅新建 dap-redis（ns 内隔离，遵循集群各业务自建 redis 的惯例，避免污染 infra 共享实例的 db 编号）。
后果：+零新增中间件运维、资源省 30Gi+；−依赖 infra 可用性（已用 DPC 降级矩阵缓解）。
