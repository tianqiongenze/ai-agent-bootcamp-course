# FIX-LOG B2：L05–L08 批次修订记录

> 执行人：enhance-b2 ｜ 日期：2026-10-31 ｜ 依据：ENHANCE-SPEC-小白化改造规范 + R2 教育专家审查（L05–L08 节）+ R3 教授级高工技术审查（P0-2/P0-3/P0-6、P1-1/P1-3/P1-5/P1-6/P1-7/P1-8/P1-9/P1-11/P1-12/P1-13、P2-2/P2-4）
> 事实源：dap-v2 仓库真实文件（Makefile、deploy/k8s/*.yaml、services/worker/pipeline.py、services/tools/main.py、packages/dap_core/dap_core/db.py、seed/seed_warehouse.py、config.py）

## 一、修订文件清单（10 份）

| 文件 | 主要变更 |
|---|---|
| docs/03-教学方案/L05-数据基建五件套部署.md | 术语小白卡 7 条；五件套部署顺序链 flow；物流园类比前移；向量概念降级"今天不学，L08 再讲"；R3 P0-2 虚构 kustomize/make apply 全部改为真实命令（`kubectl -n $NS diff/apply -f labs/L05/`）；R3 P1-7 越权 `make diff` 改课程 ns 原生命令；TiDB 端口统一 NodePort 30210；PR-05 灌数改 `make seed`/seed_warehouse.py + TRUNCATE 红字警示（P1-12）；表名 retail_dw/dwd_order* → warehouse.ods_orders/dwd_trade_order_detail/dim_product；105.9 万挂 ODS 层并加 DWD 对比（P1-5）；布鲁姆目标5 按 R2 改写"论证 DEFERRED 理由"；难点改三步台阶 |
| docs/03-教学方案/L06-读写分离HPA与容量诚实.md | 术语小白卡 8 条（async/await、RPS 等）；读写分离请求链 + HPA 扩容决策链两条 flow；async 三前提 5′ 前置；婚礼酒席类比前移至难点；代码走读材料改为真实 `packages/dap_core/dap_core/db.py` DualPool（20s 探活、_pick DPC、db_pool_recovered 日志），"连续3次回切"改为与仓库一致的"探活成功即恢复"+开放讨论；`overlays/course g1-patch.yaml` 虚构路径 → labs/L06 清单 + kubectl diff/apply；PDB 名改 dap-gateway-pdb/dap-worker-pdb（P2-4）；HPA max=4/5 与 yaml 对齐说明；R2 时间问题：容量外推拆两段（算链 15′ 留实施=五格填空链，双口径辩论 10′ 移检查环节）；目标3 双动词拆分为目标3+目标4；指标名 dual_pool_degraded → 日志取证口径 |
| docs/03-教学方案/L07-NL2SQL管线全景.md | 术语小白卡 8 条（token/温度/JSON/幻觉/沙箱/run_id 等）；NL2SQL 五步管线 flow；外卖类比前移正文（资讯台阶1+板书），课后费曼改"自创类比"；R3 P2-2 增"教学五步 ↔ 代码四节点（retrieve/generate/validate_execute/verify）"映射；虚构 `insight-agent` CLI 全部改为真实链路（控制台/`POST /v1/query` → `GET /v1/runs/{run_id}`，events 步骤序列 + result.sql + model 字段）；表清单全错修正（dwd_trade_order_detail/dim_product/dws_store_daily_sales 等 11 真表）；Q17 SQL 与修复三步改为真实知识配置（CRDB metrics 同义词 + meta_tables 分层白名单），E2 复现改"插删错误同义词行"；E3 改幻觉列 col_check + fallback-template 兜底（删虚构 fuzz_json 模块）；评测命令改真实 `tests/eval/run_eval.py`；评测口径 24 题=12 core+12 held-out |
| docs/03-教学方案/L08-RAG知识引擎与混合检索.md | 术语小白卡 8 条（向量/embedding/cosine/chunk/OOV/语义缓存/置信门槛/RRF）；三路召回→合并去重→排序 flow；"查字典"与"切蛋糕"类比前移课堂正文/难点突破（课后附加题改自创类比）；"向量三分钟"前置补课；kb_chunks/kb_entities 虚构表 → 真实 metrics/meta_tables/meta_columns/few_shots（P1-13）；retriever.py/semantic_cache.py 虚构代码 → services/tools/main.py 真实 metadata_search 与 /mcp/semantic-cache/lookup 节选；evals.sem_cache_sweep 虚构模块 → lookup 收集 distance + 离线三档统计；R2 对照改"删 L1 同义词配置复现纯向量翻车"（真实可操作）；0.75 门槛标注教学口径；补"与业界 hybrid-RAG（RRF+重排）差距"说明（R3 时效性建议）；chunker/ingest 虚构命令 → labs/L08 SQL 模板 + init_db.py + POST /mcp/index/knowledge；PR-08 命令全部改为真实 API；三步台阶补齐三个难点 |
| docs/05-实验指导/L05-…五件套部署与灌数验证.md | P0-2/P1-7/P1-12/P1-5：kustomize→labs/L05 + kubectl diff/apply；make diff 越权说明与替代；灌数教师执行 + TRUNCATE 警示 + dap_app 只读验证；retail_dw.dwd_order → warehouse.ods_orders（≈105.9 万）+ DWD 对账；排障表按 infra 复用架构改写 |
| docs/05-实验指导/L06-…读写分离HPA与扩容演练.md | P2-4：describe pdb → dap-gateway-pdb/dap-worker-pdb；删手动 scale（与 HPA 冲突，改为施压触发并说明"漂移被 HPA 纠正"教学点）；"集群拐点"→"稳态实测口径 140 RPS（70% 缓存混合负载、err 2.4%、p95 3.34s）"；HPA min/max 与 yaml 对齐；压测脚本标注"基于 dap-v2 tests/load/k6_gateway.js 裁剪" |
| docs/05-实验指导/L07-…NL2SQL管线跑通与证据留痕.md | 证据包模板改 run_id 取证（真实字段：events 步骤序列/result.sql/execute.rows/model 四值枚举 qwen2.5:14b / qwen2.5-coder:7b / fallback-template / faq-hit）；认证说明区分网关 Bearer JWT 与工具层 x-internal-token |
| docs/05-实验指导/L08-…售后域知识索引构建与检索实验.md | P0-3/P1-13/P1-16：`make knowledge-rebuild` → init_db.py + POST /mcp/index/knowledge；`/kb/search` → POST /mcp/metadata.search；knowledge/ 目录 → labs/L08 SQL 模板 + 真实落库表（meta_tables/meta_columns/metrics/few_shots）；示例表名 ads_cs_sla_day → ads_store_gmv_trend；对比实验改"删 L1 同义词行"复现法；缓存观察记录 distance 值 |
| docs/07-项目资源/dap-v2工程文档/DAP-v2-README.md | P0-6：目录树重写为 R4 后真实三服务结构（删 orchestrator/agents/knowledge 空壳目录行）；"编排(LangGraph)"→"worker 内状态图编排（LangGraph 同构，ADR-002）"；"知识引擎 TiDB 语义层"→"CRDB 语义层"；补 seed/deploy 真实 make 目标 |
| docs/07-项目资源/dap-v2工程文档/RUNBOOK.md + SAD.md | P1-8：RUNBOOK"HPA max 已配（10/12）"→ 4/5（以 deploy/k8s yaml 为准）；SAD 部署视图 HPA 3-10/3-12 → 3-4/3-5；P1-9：SAD"100 万并发用户"→"100 万注册用户（≈10 万并发，设计目标）"；SAD"令牌桶限流"→"Redis INCR 窗口限流（R2 版），故障降级进程内桶"（与 gateway/main.py:149-160 一致） |

## 二、指标口径统一记录（R3 P1-1/P1-3/P1-6）

- k6 140 RPS：本批次文件统一为"**稳态实测**（70% 缓存混合负载，err 2.4%、p95 3.34s）"，不再使用"拐点"表述（L06 实验）；拐点明确为"需阶梯压测自测，不预设标准答案"。
- 基线测试数：本批次未直接引用历史数字；L07 评测口径写为"24 题（12 core + 12 held-out），基线 91.7%"，与 TEST-REPORT/PROGRESS 一致（当前单测基线 67 的统一口径由 L15/L01 批次负责，此处不越界改写）。
- 56s 指标：本批次 L05–L08 文件无 "~56s" 引用，无需标注 v2-r12 版本口径（已核查）。
- 420ms：仅在 L08 走读节选以"~420ms→~40ms 量级"出现，保留量级表述。

## 三、与仓库核验一致的关键事实（抽验）

| 文档声称 | dap-v2 仓库证据 | 结果 |
|---|---|---|
| HPA gateway 3-4 / worker 3-5 | deploy/k8s/04-gateway.yaml:84-85、03-worker.yaml:68-69 | ✓ |
| make 目标 deploy/diff/seed/test（无 apply/knowledge-rebuild/quality-scan） | 仓库根 Makefile | ✓ |
| DualPool 20s 探活、_pick 降级、db_pool_recovered | packages/dap_core/dap_core/db.py | ✓ |
| 管线四节点 retrieve/generate/validate_execute(col_check)/verify | services/worker/pipeline.py:113-223 | ✓ |
| metadata.search 三层 L1 metrics→L2 Milvus→L3 ILIKE meta_tables/few_shots | services/tools/main.py:383-432 | ✓ |
| 语义缓存阈值 0.92、lookup 返回 distance | tools/main.py:554-568、config.py:70 | ✓ |
| seed 表 11 张、ods_orders 主键 pay_amount 等列名 | seed/seed_warehouse.py DDL | ✓ |
| 灌数命令 DAP_WAREHOUSE_DSN=…:30210 uv run seed_warehouse.py | RUNBOOK 原文 | ✓ |

## 四、遗留与说明

1. `labs/L05/`、`labs/L06/`、`labs/L08/` 为课程侧教师发放材料目录（R3 P0-2 修正方案(b)的载体），需教师按 deploy/k8s 裁剪制作；文档已标注"教师发放/教师执行"边界。
2. L06 走读节选为真实 db.py 的简化走读版，省略 OCC/Tx/仓库池等与读写分离无关段落，节选内标注"与源码一致"处均已逐行比对。
3. flow 块、术语卡均按 ENHANCE-SPEC 书写（每讲 5–8 条、节点 ≤10 字、①②③ 编号），`build_ppt.py L05 L06 L07 L08` 重建成功：L05/L06/L07/L08 四份 pptx 无报错（WARN 为正文超预算自动分页提示，属正常行为）。
4. R3 P0-7（L03 引用 ADR-005/006）属 L01–L04 批次，未处理。
