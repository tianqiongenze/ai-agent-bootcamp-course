# FIX-LOG：B3 批次（L09–L12）小白化改造 + 技术对齐修订记录

> 执行人：enhance-b3　批次：L09–L12（教学方案 4 份 + 实验指导 4 份）
> 依据：ENHANCE-SPEC-小白化改造规范、R2 教育专家审查（L09–L12 部分）、R3 教授级高工技术审查（P0-4/P0-3/P1-3 等）
> 事实源：dap-v2 真实仓库（逐项 Grep 取证：gateway/main.py、tools/main.py、resilience.py、cache.py、llm.py、audit.py、init_db.py、Makefile）

## 一、L09（FAQ 直答与反馈闭环）

| 类型 | 修订内容 |
|---|---|
| A 小白卡 | 新增"〇、本讲术语小白卡"8 条：API / Token / 403·422 / UPSERT / 幂等 / RBAC / 反馈闭环 / 直答vs缓存 |
| B flow | 新增 2 个：①反馈闭环主链（修正SQL→护栏→落库→索引→透传→直答→420ms）；②五问断路链 |
| C 类比前移 | "全班共用错题本"类比前移至重点部分与资讯板书；两难点补齐"三步台阶" |
| E 布鲁姆 | 目标5【评价】"设计第 58 条"→【创造】设计断路回归测试（并修复虚构前提，见下） |
| F 技术（R3 P0-4/P1-3） | ①虚构路径全量替换：`services/insight/*`→`services/gateway/main.py`（POST /v1/feedback:268）、`packages/dap_core/dap_core/sqlguard.py`、`services/worker/pipeline.py`、`services/tools/main.py`；②虚构测试 `tests/faq/test_faq_regression.py`"57 条"→改为真实空白（"FAQ 专项断路回归尚不存在"，企业站补测）；③ns `dap`→`dataagent-v2`，pods insight-*→dap-gateway/dap-worker/dap-tools；④`make gateway-forward/insight-logs/crdb-sql`→真实 kubectl 命令＋教师演示通道；⑤`/api/feedback`、`/api/query`→`/v1/feedback`、`/v1/query`；⑥"L2 Redis 语义缓存"概念错位修正（Redis＝精确缓存 C2，Milvus 0.92＝语义缓存 C3），"L2 检索透传"改称"向量检索层（检索 L2）透传"消除双关；⑦56s 标注"v2-r12 版本口径"，420ms 标注"R4 专项实测口径"；⑧虚构表名 ads_gmv_daily/ods_finance_orders→真实 ads_store_gmv_trend/warehouse.ods_orders |
| 实验指导 | 反馈通道写实为 POST /v1/feedback；增量索引标注 POST /mcp/index/fewshot；"时延<1s"补 420ms 参照口径；补 30 秒"看懂一次 curl"前置卡 |

## 二、L10（LLM 工程：路由、降级、缓存与成本）

| 类型 | 修订内容 |
|---|---|
| A 小白卡 | 新增 7 条：降级矩阵 / 缓存三级 / 熔断 / TBP / LRU / 契约测试 / chaos 注入 |
| B flow | 新增 2 个：①请求→缓存C1→C2→C3→主→备→模板→5s 响应主链；②熔断状态机链（真实参数：连续失败 5 次→OPEN→冷却 30s→半开→试探） |
| C 类比前移 | 消防通道（DPC）由课后费曼前移至重点部分与资讯点题；三级缓存"兜里草稿纸→班级错题本→年级题库"、保险丝三格、LRU 便利贴墙均入正文；费曼改为"自创新类比"（不许复用消防通道）；两难点补齐"三步台阶" |
| D 消歧（R2 最高优先级） | 全讲层级改名：缓存三级统一称 **C1 进程 LRU / C2 Redis 精确 / C3 Milvus 语义**；资讯阶段新增"三套编号消歧对照卡"（检索 L1-L3 / 缓存 C1-C3 / 护栏 G1-G4）；代码标签 layer=L1/L2/L3 与 C1/C2/C3 一一对应的关系显式说明；目标/重点/难点/板书/实验/企业站认领清单同步改名 |
| E 时间（R2 六步法） | 4.4"契约测试与成本核算 20′"→"DPC 讲解与成本布置 5′"（成本核算改为课后作业，契约测试为企业站补测任务）；4.3 熔断推演 20′→35′（15′ 弹性缓冲吸收 chaos 排队，缓冲使用规则成文）；检查清单、计划表同步更新 |
| F 技术（R3 P1-3 + 取证新发现） | ①56s 标注 v2-r12 口径（实验指导成本表同步标注，并补 v2-r13 99.0s）；②虚构代码路径 `services/llm-gateway/{config.yaml,router.py,cache.py,breaker.py}`→真实 `packages/dap_core/dap_core/{llm.py,resilience.py,cache.py}` + `services/worker/fallback_sql.py`；③虚构测试 `tests/llm/test_degradation_contract.py`→如实标注"仓库尚无 LLM 降级契约测试，企业站补测"（任务不变、前提变真）；④熔断参数由虚构"窗口20/失败率50%/冷却60s"改为源码真实值（failure_threshold=5、open_s=30s，resilience.py）；⑤TBP"剩余<800ms 不发起"改为真实语义（remaining_budget：预算耗尽抛 TimeoutError 不再外呼）；⑥虚构指标 `llm_cache_hits_total`→真实 `dap_cache_hits_total{layer}`；⑦L1 容量 512→真实 8192、TTL"对话1h/代码24h/知识7d"→真实"查询5min/字典1h"（config.py:67-70）；⑧LRU 示例代码替换为 cache.py 真实 L1Cache 摘录；⑨chaos 开关标注"课程环境教师侧专用，仓库本体无此端点"并给企业站替代手段；⑩`make gateway-forward`、`-n dap`、deploy/llm-gateway→真实命令 |
| 实验指导 | 缓存层级 C1/C2/C3 改名＋消歧注记；成本对照表补 420ms/56s 版本口径 |

## 三、L11（质量规则引擎与主动巡检）

| 类型 | 修订内容 |
|---|---|
| A 小白卡 | 新增 7 条：探针 / 阈值 / 空值率 / JSONB / 巡检 / 判定方向 / 告警疲劳 |
| B flow | 新增 1 个：质量巡检守护链（定时触发→取规则→拼探针→数仓执行→比对阈值→落库→失败项附建议） |
| C 类比前移 | "体温计只在发烧时叫人"（告警疲劳）与"判卷"（CASE WHEN）类比前移入资讯正文；两难点补齐"三步台阶"（JSONB 坑＝塑封袋便利贴类比） |
| E 布鲁姆 | 目标1【记忆/理解】双标签拆为两条：目标1【记忆】（说出五类规则名）＋目标2【理解】（缺陷形态/阈值/判定方向），后续目标顺延为 6 条，反思栏同步改"6 条目标逐条" |
| F 技术（R3 P0-3 + 取证新发现） | ①`make quality-scan`→真实 `POST /v1/quality/scan`（gateway main.py:306，等价控制台"质量中心-立即全量巡检"）；②虚构代码路径 `services/quality-agent/{probes.py,scanner.py,db.py}`→真实 `services/tools/main.py`（`_run_rule` probes 字典、`_params_of`）；③虚构 `migrations/seed_quality_rules.sql`→"课程环境种子规则由教师预置"；④虚构 direction='lt' 配置→真实"判定方向按类型写死"（逐类列出，源自 `_run_rule` 分支）；⑤probes 示例 SQL 替换为真实代码摘录（TiDB 语法）；⑥quality_results 表结构卡改为真实字段（id/rule_id/tenant_id/status/metric_value/detail/suggestion），虚构 quality_alerts 表改为"失败项 suggestion＋课程群机器人 dry-run"；⑦`make tidb-sql`/`make crdb-sql`→mysql 只读连接＋教师演示通道；⑧ns `dap`/quality-agent→dataagent-v2/dap-tools；⑨"每日 06:00 定时"表述改为"生产可由定时任务驱动" |
| 实验指导 | 触发巡检改为 curl POST /v1/quality/scan（附预期返回结构）；环境准备补"判定方向按类型写死"提示；提交物改失败项 suggestion 截图 |

## 四、L12（根因 Agent：血缘溯源与修复审批）

| 类型 | 修订内容 |
|---|---|
| A 小白卡 | 新增 7 条：血缘 / 图数据库 / 上溯REVERSELY / 下钻正向GO / 双写兜底 / append-only / confidence |
| B flow | 新增 1 个：根因定位血缘回溯链（FAIL→取证→REVERSELY上溯→候选根因→证据组装→LLM归因→人审批准） |
| C 类比前移 | "河流-排污口"血缘类比（上游找排污口/下游数停水村庄）由课后费曼前移至重点部分板书；费曼改为"自创类比"；两难点补齐"三步台阶"（含 confidence≠证据类比） |
| F 技术（R3 P0-4 + 取证新发现） | ①虚构 `services/rca-agent/{lineage.py,rca.py,approval.py}`→真实 `services/tools/main.py`（NebulaLineage）+ `services/gateway/main.py` + `packages/dap_core/dap_core/audit.py`；②Nebula space `dap_lineage`→真实 `dap`；③边方向语义翻转并按源码改正：lineage_edges 为 src(上游)→dst(下游)，故**上溯用 REVERSELY、影响面用正向 GO**（原方案写反），nGQL 示例、目标、重点、思考题全部同步；④虚构表 `rca_reports`→真实 approvals 草稿（kind/summary/sql_or_payload/impact_analysis/status）＋报告文档快照；⑤虚构 `POST /api/rca/run`、`POST /api/rca/approve`→真实 `GET /v1/approvals`、`POST /v1/approvals/{aid}/decide`（decision=approved/rejected）；⑥audit_log 查询改真实字段（trace_id/tenant_id/actor/actor_type/action/target/detail/outcome）；⑦`make nebula-console`→`curl POST /mcp/lineage/impact`（主）＋nGQL 教师演示（辅）；⑧示例表 `dws_gmv_daily`→真实 `dws_store_daily_sales`，血缘链示例改为真实四级链（ads_store_gmv_trend→dws_store_daily_sales→dwd_trade_order_detail→ods_orders）；⑨`edu_shadow.dwd_order_detail`→课程沙箱 `edu_shadow.dwd_trade_order_detail`（教师预建）；⑩ns `dap`、pods rca-agent/quality-agent→dataagent-v2/dap-tools；⑨owner 角色→真实 approver 角色（decide 端点 RBAC 实证） |
| 实验指导 | `ads_cs_sla_day`→真实 `ads_store_gmv_trend`；血缘溯源写实为 POST /mcp/lineage/impact＋lineage_edges 兜底；审批改为 approvals 草稿＋decide 端点＋audit_log 两行留痕 |

## 五、构建验证

```
python3 scripts/build_ppt.py L09 L10 L11 L12
→ L09 24页 / L10 31页 / L11 30页 / L12 29页，全部 [OK]，无报错（仅"正文超180字预算"类排版提示）
产物：docs/04-课件PPT/L09–L12 四份 .pptx
```

## 六、遗留事项（建议下一轮处理）

1. R3 建议"课程侧补建真实 labs/overlays 或课程版 Makefile"（涉及 L05/L08/L11 的 make 类目标），本批次已改用真实命令绕开，未新建课程 Makefile。
2. FAQ 断路事故独立复盘文档 `docs/07-项目资源/incidents/INC-faq-break.md` 建议按 R3 建议真实补写（L09 已改用 TEST-REPORT R4 #1 作素材来源）。
3. L09 目标5 / L10 企业站的"补一条回归/契约测试"现在对应真实空白，企业站落地时需教师提供测试骨架。
