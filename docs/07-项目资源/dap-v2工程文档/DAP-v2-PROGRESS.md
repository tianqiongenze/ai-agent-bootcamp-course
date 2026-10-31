# DAP-v2 实施进度锚点（跨会话恢复用）

> 项目：Data Agent 平台 v2 —— 数仓智能体平台（NL2SQL 洞察 / 数据质量双Agent / ETL 编排）
> **状态：✅ v2-r13 已上线（2026-10-31）。R4 四视角复审闭环：评测 24 题 held-out+bootstrap CI 口径 exec 91.7%（CI 79.2–100，held-out 91.7%，faq 直答命中实测 420ms）；R3「FAQ 断路/反馈越权」等 12 项审查问题修复；依赖漂移双连爆（numpy<2 钉版本 + pymilvus int64）修复；57 测/冒烟 9/9/E2E 7/7 全绿。评分卡见 docs/TEST-REPORT.md R4 节。**

## R3 能力落地（v2-r5~r12，当前线上 v2-r12）
- [x] PII 结果脱敏：meta 标记 + 列名启发式兜底（sqlguard.redact_rows）
- [x] 人工反馈闭环：feedback → few_shots → 增量索引（Milvus 降级不丢）→ 检索 L3 ILIKE 命中
- [x] FAQ 直答：问题精确命中修正示例 → 照抄 SQL 跳过 LLM（model=faq-hit）——"人工修一次，同类永久正确"
- [x] 执行前自校验：规则引擎列归属检查（col_map 空自动跳过）
- [x] 防回归：tests/test_bindings.py 占位符绑定校验（v2-r9 漏参 500 的教训）
- [x] 评测轨迹（HSA 含倒退实验）：91.7 → 75/33（候选淹没，回退）→ 91.7 → **100/100/100，均时延 56.3s**（tests/eval/eval_v2r12.log）
- [x] 铁律沉淀 RUNBOOK「发布铁律」节：Dockerfile 单一事实源 / 内部认证 / 绑定测试 / NetworkPolicy 白名单 / 同 tag 不滚动

## 生产部署（v2-r4 基础设施，已上线）
- [x] strawberry 0.339 兼容：MaxAliases 更名 MaxAliasesLimiter → 防护扩展挂 Schema + 版本自适应探测（gateway/schema.py，修复曾致 gateway 崩溃循环）
- [x] deploy.sh 收口：**删除 Dockerfile 生成逻辑**，deploy/Dockerfile.* 仓库内单一事实源（修 PYTHONPATH namespace 陷阱复坑）；tag sed 回写任意旧版
- [x] NetworkPolicy 补 ipBlock 白名单（10.167/16 节点网 + 192.168/16 pod 网段）——NodePort 曾被 default-deny 误伤
- [x] smoke.sh 适配安全层：护栏带内部 token / SSE 用真实 run_id / curl -m 替代 timeout（macOS）
- [x] 验证：48 测全绿 · import 真实验证（strawberry 0.339）· 冒烟 9/9 · insight run 端到端 done（60s LLM）
- 入口：控制台 http://10.167.2.175:30281（admin@dap.local/Admin@2026）· 镜像 registry/dap/*:v2-r4

## 第 2 轮审查修复（已随 v2-r4 上线）
- [x] 资料[1]/[2]（Data Agent 2026 手册 + 三 Agent 复盘）对照落地 12 项：JWT fail-fast、CORS 白名单、SPA 路径穿越、先落库再发布、GraphQL 强制鉴权+租户过滤+深度/别名限制、Redis 分布式限流、tools 内部认证、outbox SKIP LOCKED+按 topic 投递、关停超时对齐、L1Cache 真 LRU、sqlguard 封堵 OUTFILE/锁语句、PDB+NetworkPolicy+Secret 出 git
- [x] 复审协同 bug：gateway L2 缓存 r2 NameError（缓存整体失效）、worker ToolsClient 缺内部 token（管线全 401）、deploy.sh 漏 apply 06-pdb.yaml
- [x] NL2SQL 增强：pipeline.py 列级反向索引 Schema Linking（资料[1] §5.2，91.7% 失败案例的改进路径）
- [x] 前端：ChartPanel 自动图表推荐（echarts，表格/图表切换+复制SQL+导出CSV）、审批意见 Modal 审计留痕、主题美化
- [x] 验证：48/48 测（86.66%）· py_compile 全过 · ruff F/E9=0 · tsc 0 错 · 已随 v2-r4 发布上线（见上方「生产部署」节）

## 已交付（全部完成）
- [x] M0 dap_core 共享内核（48测/86.8%覆盖）：config/observability/三级缓存/CRDB读写分离(DPM自愈)/韧性(TBP限流熔断)/AgentMessage/四层SQL护栏(sqlglot)/状态图(ADR-002)/审计/outbox
- [x] M1-M3 services：gateway(GraphQL+REST+SSE+RBAC+限流) / tools(知识引擎+MCP工具层:元数据混合检索/Milvus/Nebula血缘/质量规则引擎/SQL沙箱) / worker(Pulsar消费+三条Agent管线+outbox relay+质量巡检调度+应用侧DLQ) / 前端控制台(React18+TS+AntD 五工作台,烘焙进gateway镜像)
- [x] M2 数据：TiDB warehouse 零售数仓（ODS 105.9万订单→DWD 101万→DWS 19万→ADS）+ CRDB dap 库 schema+种子 + Milvus 知识索引 + Nebula dap space
- [x] M4-M5 双Agent+ETL：质量扫描(8规则)+RCA根因(血缘+LLM)+修复审批草稿；ETL需求→SQL+DAG+质量规则→人审
- [x] 部署：ns dataagent-v2（gateway×3/tools×2/worker×3/redis×1，HPA，GitOps yaml 单一事实源），镜像 registry 10.167.2.175:30500/dap/*
- [x] M7 测试全绿：冒烟9/9、Playwright E2E 7/7、NL2SQL评测91.7%(12题全LLM真实生成)、k6 26865请求@140RPS@2.4%err、Locust混合流、混沌降级4/4
- [x] M8 docs/TEST-REPORT.md（容量外推：100万用户≈4-8台64C节点）+ SAD.md + ADR-001~004 + RUNBOOK.md

## 访问入口
控制台 http://10.167.2.175:30281 （admin@dap.local/Admin@2026）· GraphQL /graphql · Grafana 30082
测试产物：tests/eval/eval_report.json · tests/load/k6_summary.json · tests/e2e/pw_final.log · tests/smoke.sh

## 已知限制（诚实声明 HSA）
- 集群共享（42 ns），master CPU requests 99%/worker1 内存 requests 高位——HPA max 已按实际资源收敛(4/5)；redis nodeSelector 改为 kubernetes.io/os: linux 任一调度
- LLM：本地 qwen2.5:14b CPU 推理 45-90s/次且与集群共享争抢；外部 API Key 到位后改 dap-secret(DAP_LITELLM_API_KEY)+cm(DAP_LLM_PRIMARY_MODEL) 即切主路由（RUNBOOK §外部LLM接入）
- 100 万并发为设计目标+外推口径（ADR-004），本集群物理不可实测 10 万并发
- v1 存量（dataagent-prod/course）未动，v2 独立命名空间

## 恢复锚点
若需继续迭代：代码在本地 dap-v2/（git 已 init）；部署在 master:/root/dap-v2-build（rsync 同步）。发布：`TAG=v2-$(date +%Y%m%d%H%M) bash scripts/deploy.sh`；漂移检测 `make diff`。
