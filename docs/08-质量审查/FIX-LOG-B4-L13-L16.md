# FIX-LOG B4：L13–L16 小白化改造与技术对齐记录

> 批次：enhance-b4（L13 ETL 编排 / L14 安全护栏 / L15 测试与统计 / L16 发布答辩）
> 依据：ENHANCE-SPEC-小白化改造规范、R2 教育专家审查（L13–L16 节）、R3 教授级高工技术审查（P0-5、P1-1、P1-6、P2-3 及仓库核验）
> 仓库核验基准：dap-v2 真实仓库（Makefile、packages/dap_core/pyproject.toml 与 tests/、deploy/k8s/07-backup.yaml、tests/eval/run_eval.py、docs/TEST-REPORT.md）
> PPT 重建：`python3 scripts/build_ppt.py L13 L14 L15 L16` 全部成功（25/24/24/24 页，仅页数 WARN 无错误）

## 一、每讲必做项（ENHANCE-SPEC A–C）

| 讲 | A 术语小白卡 | B flow 块 | C 类比前移＋三步台阶 |
|---|---|---|---|
| L13 | 新增 7 条：cron、DAG、上游/下游任务、草稿态、git diff --stat、审批留痕、质量规则 | 2 个：ETL 五步链路＋人审三查子链 | cron 五格钟面（3′ 补台阶进资讯）；"和面→烤面包→抹果酱"DAG 类比；两难点均补三步台阶（实习生初稿类比/DAG 时刻表演示） |
| L14 | 新增 7 条：正则、词边界、AST、注入攻击、脱敏、加盐哈希、纵深防御 | 2 个：恶意请求四层拦截链＋机场安检对照链 | 机场安检四道闸类比前移至资讯 30 秒开场；两难点补三步台阶（保安类比＋`\b` 演示＋动手算账；"听字面 vs 听懂"＋变体复现） |
| L15 | 新增 7 条：p95、均值陷阱、覆盖率、held-out、bootstrap 置信区间、拐点、测试金字塔 | 2 个：测试金字塔证据链＋k6 判读三问链 | **"9 人 1 秒＋1 人 100 秒"均值陷阱类比从课后费曼前移至教学重点 2 正文**；体检套餐类比前移进重点 1；两难点补三步台阶（掷硬币直觉→现场幂次演算→动手跑 bootstrap；门禁 100%/50% 类比→读真实报告→分级门禁收束） |
| L16 | 新增 6 条：门禁（AND）、readyz 探针、回滚、DEFERRED、retro、红灯演练 | 2 个：发布门禁五项主链＋"一项红"阻断分支链 | —（R2 评定本讲"缺口基本无"） |

## 二、R2 问题修复（D 项）

| 问题 | 修复 |
|---|---|
| L16 目标 4 伪布鲁姆（答辩【创造】实为评价＋表达） | 改标【评价】为主、创造渗透，目标文字改为"对作品与证据作出评判与辩护"（R2 §2.2） |
| L16"每组 12 分钟"零容错，弹注改默认 | 4.4 改"每组 12 分钟（讲授 8＋对话 2＋合议 2）默认"；附录 B 单组时间轴 15′/组→12′/组并重排四段；弹性方案改为围绕 12′ 默认的伸缩描述 |
| L13/L14/L15 伪布鲁姆 | R2 §2.2 清单未列出本批次三讲问题（L14 目标 5 被评为正面示范），未改动布鲁姆标注口径 |
| R2 L13 小白卡/图解建议 | cron 钟面、"和面→烤面包"DAG、三权分立话术均已落入正文/难点/讲堂 |

## 三、R3 技术错误修复（E/F 项，均经 dap-v2 仓库核实）

| 位置 | 原文 | 修正 | 仓库证据 |
|---|---|---|---|
| L15 教学方案 4.1 / 实验 L15 步骤 1 / L16 4.1 | `pytest tests/ -q --cov=app …`、`pytest --cov=packages …` | 统一为真实入口 `cd packages/dap_core && uv run pytest ../../services ../../packages -q -p no:cacheprovider --cov=dap_core … --cov-fail-under=80`，并注明"仓库根直跑 pytest 会 exit 5（收集 0 测试）"（P0-5） | dap-v2/Makefile `test` 目标；pyproject `[tool.pytest.ini_options]` 无 addopts → 所有 pytest 命令显式补 `-p no:cacheprovider` |
| L15 实验"基线 48 测不回归" | 历史数字钉死 | 改为"以 dap-v2 当前 main 为基线（67 测/覆盖 87%），门禁以 make test 实时输出为准"（P1-6）；67 测经 `grep -c "def test"` 实数核验 | packages/dap_core/tests/*.py 共 67 个测试函数 |
| L14 教学方案 4.1 | `pytest tests/test_sqlguard.py -q -k …`（文件不存在） | 改为 `cd packages/dap_core && uv run pytest tests/test_guard_graph.py -q -p no:cacheprovider`；4.4 示例断言对齐真实 API `analyze()`（allowed/layer） | packages/dap_core/tests/test_guard_graph.py（TestSQLGuard） |
| L14 教学方案 PR 任务 | `tests/test_sqlguard_attack.py` | 路径明确为课程新增 `packages/dap_core/tests/test_sqlguard_attack.py` | 单测均位于 packages/dap_core/tests/ |
| L15 教学方案 4.3 | `k6 run loadtest/staircase.js --summary-export=reports/k6-staircase.json`（路径虚构） | 改为真实脚本与产物 `k6 run tests/load/k6_gateway.js --summary-export=tests/load/k6_summary.json`；阶梯版由教师发放 | tests/load/ 目录 |
| L15 教学方案 4.3 拐点表述 | "140RPS 前后的那档就是单副本的诚实容量" | 改为"历史实测稳态 ~140RPS 仅为 70% 缓存混合负载参照口径，非新问句全链路标准答案，学生以本档实测判读"（P1-1） | R3 P1-1 |
| L15 教学方案 4.4 | `python scripts/eval_nl2sql.py --set heldout12 --bootstrap 10000`（模块不存在） | 改为真实脚本 `tests/eval/run_eval.py`（24 题内嵌含 held-out 12），bootstrap 由教师发放脚本对 eval_report.json 重采样 | tests/eval/run_eval.py（无 argparse/bootstrap 参数，故不虚构 CLI） |
| L16 4.1 / 企业站卡 | `make release-gate`（目标不存在） | 删除虚构目标：改为教师提供 `scripts/release_gate.sh` 包装真实五件套（readyz→make test→make smoke→make e2e→备份核验），并注明仓库 Makefile 无该目标 | dap-v2/Makefile 全部目标：setup/test/lint/build/push/deploy/diff/seed/smoke/e2e/load-test/clean |
| L16 4.1 | `kubectl -n course-ns get cronjob dap-daily-backup`＋`ls /nfs/backup/dap/latest/` | 改为生产基线 `kubectl -n dataagent-v2 get cronjob dap-backup-daily`（课程 ns 同名规范）；产物对齐真实命名 `dap-YYYYMMDD.sql`（~20MB，实测 20,372,407B 量级） | deploy/k8s/07-backup.yaml（CronJob dap-backup-daily，schedule 30 3 * * *） |
| L14 教学方案 4.3 | `kubectl -n course-ns …` | `kubectl -n dap-course-XX …`（课程 ns 命名规范） | R3 P0-4 口径 |
| L14 正则护栏误报 | 无误报率说明 | 新增工程诚实注记：正则/启发式护栏有固有误报率（列名 PII 识别实测 F1≈0.938，非 100%），命中/放行均需人工复核——L4 审批层存在的理由之一（教学方案 4.2 难点注记＋实验 L14 步骤 1 提示） | team-lead 指定口径；sqlguard.py R4 误杀修复注释佐证启发式固有局限 |
| L14 实验 L14 样本 1/2 | `DROP TABLE dwd_order`（表名虚构）、`SELECT * FROM dim_store`（仅 60 行，LIMIT 截断无现象） | 改为 `DROP TABLE ods_orders`、`SELECT * FROM ods_orders`（~105.9 万行，截断可感知）（P2-3） | seed 真实表清单；R3 P2-3 |
| L15/L16 E2E 命令 | `npx playwright test e2e/ --reporter=line` | 统一 `make e2e`（= cd tests/e2e && npx playwright test） | Makefile `e2e` 目标 |
| L15/L16 K8s 版本 | 未标注教学集群版本事实 | L16 教学方案 4.1 与实验 L16 步骤 1 增口径注记：K8S v1.28.2（v2-r12 仓库基线；v1.28 已于 2024-10 EOL，2026 生产主流 1.31–1.33，教学集群版本见 RUNBOOK） | dap-v2/docs/TEST-REPORT.md 头部 |
| L16 GitOps 属性 | 未标注部署简化属性 | L16 增注："部署为教学简化版（手动 kubectl apply/make deploy）；生产 GitOps（ArgoCD/Flux）为演进路线" | dap-v2 部署实态（scp+kubectl apply）；**注：team-lead 指示引用"ADR-002 选项 B"，经核验 ADR-002 为编排引擎决策、无 GitOps/选项 B 内容，故改引仓库实态避免虚构引用** |
| L16 课后费曼 420ms | 无锚 | 补"约两次眨眼"锚＋"R4 专项端到端实测口径"（P1-4 精神） | R3 P1-4 |
| L15 企业站卡 | `pytest --cov` 本地验证 | 替换为真实命令全串 | Makefile test 目标 |

## 四、未改动声明

- 学时数、六步法时间轴（除 R2 明确要求的 L16 答辩 12′/组默认化）、考核权重、各讲头部布鲁姆主层级标注：按 ENHANCE-SPEC"不动"条款保留。
- 实验指导 L13：R3 未发现与仓库不符的命令/路径（83 分，sqlglot 校验与 EXPLAIN 五查均与实现一致），未做技术性改动。
- `docs/07-项目资源/dap-v2工程文档/`（RUNBOOK/SAD/README 等）属其他批次/顶层文件职责，本批次未触碰。

## 五、遗留建议（供统筹）

1. `make release-gate` 若希望保留为一键门禁体验，建议在课程版 Makefile 真实添加该 target（包装 test/smoke/e2e/readyz/备份五步），本批次文档已按"无此目标"口径书写，两处可随时对齐。
2. GitOps 生产路线引用建议在顶层文档统一（本批次暂引仓库实态而非 ADR-002）。
3. 420ms 专项计时原始输出建议归档 `tests/artifacts/`（R3 P2-7），归档后可将课程口径从"文字声明"升级为"文件可核验"。
