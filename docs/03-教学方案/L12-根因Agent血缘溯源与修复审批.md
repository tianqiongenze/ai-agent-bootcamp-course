# 学习情境 L12：根因 Agent：血缘溯源与修复审批（6 学时）

> 载体：DAP-v2 双 Agent 协作——质量检测 Agent（L11）发现失败项后交给 RCA 根因 Agent：Nebula 血缘 GO 溯源（CRDB 双写兜底）→ 证据组装 → LLM 归因 → 修复建议（`suggestion` 字段含 SQL）→ 审批草稿 → 人工批准留痕 `audit_log`。
> 核心铁律：**Agent 只建议不执行；人批准才动数据；全程留痕可追责。**

## 一、学习情境基本信息

| 项目 | 内容 |
|---|---|
| 学习领域 | LF4 数据质量治理 Agent（本域收官讲：定位与闭环） |
| 讲次 | 第 12 讲（第 12 周） |
| 学时 | 6 学时＝校内理实一体 4 学时（六步法 240′）＋企业实训站 2 学时（PR 实战） |
| 布鲁姆主层级 | **分析／评价**（渗透：理解、应用） |
| 双元场地 | 校内：理实一体教室（演示区＋工位区＋会审圆桌区）；企业站：10.167.2.175/176 双节点 K8S 集群 · dap-v2 课程分支 `edu/2026-spring` |
| 企业站 PR 任务 | 注入一次数据缺失事故，跑通 RCA 全流程出具根因报告，完成三方会审与审批留痕，报告快照提 PR |
| 课后费曼任务 | 给"业务总监"（找一位非技术师生扮演）讲一次质量事故定位，10 分钟版，作为期末费曼答辩预演 |

## 二、任务描述

> 【委托单 #R-2412】委托方：业务总监＋治理委员会。昨晚 gmv 空值率告警已触发，但"哪张表、哪个任务、谁改的"没人说得清，修复全靠猜。要求 10 分钟内出根因报告：沿血缘上溯定位源头表、给出带 SQL 的修复建议、生成审批草稿；人批准后才准执行，全程留痕可追责。——DAP-v2 RCA 能力验收任务单

## 三、学习目标

1. 【理解】画出血缘图模型（Nebula：tag `tbl`、edge `derives_from` 由下游指向上游）与 CRDB `lineage_edges` 双写兜底的读写路径，说明"双写"防的是什么故障。
2. 【应用】用 `GO 1 TO 3 STEPS ... OVER derives_from` 从失败表上溯找到候选根因表，并能改用 `REVERSELY` 反查下游影响面（谁被波及）。
3. 【分析】拆解 RCA 六步流程（失败项→血缘上溯→证据组装→LLM 归因→修复建议 suggestion→审批留痕），标注每一步中"禁止 LLM 介入"的环节（血缘查询、证据数值、审批决定）。
4. 【评价】以业务总监／数据工程／审批人三种角色会审一份根因报告，识别 LLM 归因中的幻觉与证据不足（无证据字段支撑的结论必须打回）。
5. 【评价】论证"Agent 只建议不执行＋人工批准＋audit_log 追责"的合规价值，说明 suggestion SQL 为什么必须留在草稿态直到批准。

## 四、教学重点与难点

**教学重点**

1. 血缘图模型与方向语义：`derives_from`（下游→上游）如何同时支撑"根因上溯"（正向 GO）与"影响面下钻"（REVERSELY）。
2. RCA 六步闭环与治理红线：血缘与证据确定性、归因与建议由 LLM 起草、批准与执行永远属于人。

**教学难点（附突破策略）**

1. **边的方向与查询方向的空间想象**：学生常把"上溯"误写成 `REVERSELY`（取决于建模时边的朝向）。
   - 突破策略：白板 DAG＋"手指走边"——先 `SHOW EDGES` 确认语义（derives_from＝A 由 B 派生，边从 A 指向 B），再沿边方向走一遍；每次 GO 结果都与 CRDB `lineage_edges` 兜底表交叉验证，两边不一致即触发"血缘双源核对"讨论。
2. **评价 LLM 归因的可信度**：报告读起来"头头是道"但可能幻觉（编造表名/任务名/时间线）。
   - 突破策略：三方会审工坊＋"证据挂靠"规则——报告里每一条归因陈述必须能挂到具体证据字段（探针值/血缘路径/最后写入时间/任务日志），挂不上即打回；教师预先在一份报告中埋 2 处幻觉供学生抓。

## 五、教学准备

**环境**（讲师课前 1 天核验）

- `dap` 命名空间：rca-agent / quality-agent / nebula / crdb Ready；Nebula space `dap_lineage` 已含课程数仓血缘（3 跳以内）。
- 课程沙箱：TiDB `edu_shadow.dwd_order_detail`（供注入事故）；角色 Token：analyst（触发 RCA）、owner（审批）。
- 审批演示台：教师机投屏 `rca_reports` / `audit_log` 实时变化。

**资料**

- 代码：`dap-v2/services/rca-agent/lineage.py`（Nebula GO＋CRDB 兜底双源）、`rca.py`（证据组装→LLM 归因→suggestion 起草）、`approval.py`（审批状态机→audit_log）。
- 表卡：`lineage_edges(upstream, downstream, job)`（CRDB 兜底）、`rca_reports(report_id, result_id, lineage_path, evidence, attribution, suggestion, confidence, status)`、`audit_log(id, actor, action, object_id, before, after, comment, created_at)`。
- 会审材料：一份预先埋了 2 处幻觉的示例根因报告（脱敏打印件）。

**分组**：4 人一组；会审环节角色分配：业务总监／数据工程／审批人／记录员（轮流）。

## 六、教学过程设计

### 第 1 步：资讯（30 分钟）

【教师活动】
- 承接 L09–L11 三讲主线："反馈闭环让正确被复用（L09）、LLM 工程让系统挂了也兜得住（L10）、规则引擎让脏数据第一时间被发现（L11）——发现之后呢？谁改的？改哪？谁批准？"引出 RCA。
- 板书血缘模型与 RCA 管线：

```
血缘图（Nebula space: dap_lineage）
  tag:  tbl(name, domain, layer)          edge: derives_from（下游 ──► 上游）
  例：ads_gmv_board ─► dws_gmv_daily ─► dwd_order_detail ─► ods_orders
  （CRDB lineage_edges 同步双写：Nebula 不可用时兜底可查）

RCA 六步管线（services/rca-agent/）
quality_results(FAIL) ─①血缘上溯 GO 1 TO 3 STEPS─► 候选根因表集
                      ─②证据组装（逐表探针：行数/空值率/最后写入时间/任务日志）
                      ─③LLM 归因（输入=血缘路径+证据 → 输出=归因说明+confidence）
                      ─④修复建议 suggestion（含 SQL，仅草稿）
                      ─⑤审批草稿（status=pending）
                      ─⑥人工批准/驳回 ──► audit_log 留痕（append-only）
```

- 发放引导文：委托单 #R-2412 ＋ 表卡 ＋ 会审评分表。

【学生活动】
- 通读 `lineage.py` 的双源查询与 `approval.py` 的状态机（pending→approved/rejected）。
- 回答引导文 3 问：①血缘查询为什么绝不能交给 LLM（答错表等于全错）？②suggestion 里的 SQL 为什么不能由 Agent 直接执行？③audit_log 为什么设计成 append-only（改历史＝毁证据）？

【教学方法】主线串联法＋引导文法。

【设计意图】第 9–12 讲是一条完整的治理故事线，开讲先收线；三个问题分别钉住"确定性环节不交 LLM、执行权属人、留痕不可篡改"三条红线。

### 第 2 步：计划（30 分钟）

【教师活动】给出计划模板与红线（注入只限 edu_shadow 表、RCA 只用 analyst 触发、审批演示用 owner 且意见必填）。

【学生活动】小组产出四段计划：

| 子任务 | 关键命令/路径 | 预期证据 |
|---|---|---|
| 血缘查询 | `make nebula-console` GO 上溯/下钻 | 3 跳路径＋兜底表交叉验证 |
| RCA 全流程 | UPDATE 注入→scan→`POST /api/rca/run` | rca_reports 一行含 suggestion |
| 审批留痕 | `POST /api/rca/approve`（approve 与 reject 各一次） | audit_log 两行 |
| 三方会审 | 埋幻觉报告＋会审评分表 | 抓出 ≥2 处幻觉并写打回理由 |

【教学方法】小组计划法。

【设计意图】会审作为"评价"层级的落点，必须在计划阶段就明确角色分工与评分标准，防止演成朗诵。

### 第 3 步：决策（20 分钟）

【教师活动】逐组答辩，拷问：①你组打算从哪张表开始上溯、为什么不是从告警的表直接开始修？②如果 Nebula 查询超时，你的 B 计划是什么？（CRDB 兜底表。）③LLM 给出的 confidence=0.9 你信几分？以什么为准？（证据字段，不是模型自信度。）

【学生活动】陈述→质询→修订计划并签字。

【教学方法】专业对话。

【设计意图】"从哪开始上溯""兜底""置信度不等于证据"是本讲三个工程判断点，决策环节逐组过筛。

### 第 4 步：实施（90 分钟）

【教师活动】巡回指导；主持 4.4 会审工坊（前 5 分钟发放埋幻觉报告）；控制注入操作分时进行。
【学生活动】按计划执行；记录员维护"时间线证据链"（注入时刻→告警时刻→报告时刻→批准时刻）。
【教学方法】任务驱动＋角色扮演工坊。
【设计意图】先跑通确定性管线（4.1–4.3），再进入人的判断环节（4.4），体现"机器定位、人决策"的分工。

#### 4.1 血缘图建模与上溯/下钻查询（25′）

```bash
make nebula-console    # 进入 Nebula 控制台
```

```ngql
USE dap_lineage;
SHOW TAGS;      -- tbl
SHOW EDGES;     -- derives_from

-- 从失败表上溯找根因（边方向：下游→上游，故正向 GO 即上溯）
GO 1 TO 3 STEPS FROM "dws_gmv_daily" OVER derives_from
YIELD dst(edge) AS upstream, properties($$).name AS name, $$.layer AS layer;
-- 预期：dwd_order_detail / ods_orders（1~3 跳内的上游）

-- 影响面下钻：谁被这张脏表波及（沿边反方向）
GO 1 TO 3 STEPS FROM "dwd_order_detail" OVER derives_from REVERSELY
YIELD dst(edge) AS downstream;
-- 预期：dws_gmv_daily / ads_gmv_board（回答业务总监"哪些看板废了"）
```

CRDB 双写兜底交叉验证（`make crdb-sql`）：

```sql
SELECT upstream, job FROM lineage_edges WHERE downstream = 'dws_gmv_daily';
-- 与 Nebula GO 结果必须一致；不一致即触发"血缘双源核对"（以 ETL 双写日志为准修图）
```

任务单思考题：如果把边建成"上游→下游"（ingests_into），上面两条 GO 各要怎么改？（方向语义与查询方向是两回事，先 `SHOW EDGES` 再写查询。）

#### 4.2 RCA 全流程：注入事故→报告落库（30′）

```bash
# ① 注入事故：把课程沙箱表 9/30 分区约 8% 行的 gmv 置 NULL
make tidb-sql
```

```sql
UPDATE edu_shadow.dwd_order_detail SET gmv = NULL
WHERE dt = '2026-09-30' AND order_id % 12 = 0;   -- 仅课程沙箱表
```

```bash
# ② 触发巡检 → qr-gmv-null FAIL（复用 L11 链路）
make quality-scan
kubectl -n dap logs job/quality-scan-latest --tail=30 | grep FAIL

# ③ 以 analyst 触发 RCA（消费失败结果项）
curl -s -X POST "$GW/api/rca/run" -H "Authorization: Bearer $ANALYST_TOKEN" \
  -H 'Content-Type: application/json' -d '{"result_ids":["<本轮 qr-gmv-null 结果ID>"]}'
# ④ 观察 RCA 日志：血缘上溯 → 证据组装 → LLM 归因 → 起草 suggestion
kubectl -n dap logs deploy/rca-agent --tail=80 | grep -E "lineage|evidence|attribute|suggestion"

# ⑤ 读报告（重点看 suggestion 与 confidence）
make crdb-sql
```

```sql
SELECT report_id, lineage_path, root_cause_table, attribution, confidence, suggestion, status
FROM rca_reports ORDER BY created_at DESC LIMIT 1;
-- suggestion 示例（草稿，未执行）：
-- "UPDATE edu_shadow.dwd_order_detail SET gmv = amount - refund_amt
--  WHERE dt='2026-09-30' AND gmv IS NULL;"  status=pending
```

证据挂靠检查（任务单）：报告中每条归因陈述逐条标出支撑它的证据字段（探针值/血缘跳数/最后写入时间/任务日志），挂不上的记入"待质询清单"。

#### 4.3 审批留痕：批准与驳回双路径（20′）

```bash
# ① 驳回一次（意见必填——练习"打回"）
curl -s -X POST "$GW/api/rca/approve" -H "Authorization: Bearer $OWNER_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"report_id":"<ID>","action":"reject","comment":"suggestion 未带影响行数，补齐再审"}'
# 报告回 pending，可修改 suggestion 后再次提审

# ② 批准一次
curl -s -X POST "$GW/api/rca/approve" -H "Authorization: Bearer $OWNER_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"report_id":"<ID>","action":"approve","comment":"同意回补，限课程沙箱表，执行后复扫验证"}'

make crdb-sql
```

```sql
SELECT actor, action, object_id, comment, created_at
FROM audit_log ORDER BY created_at DESC LIMIT 3;   -- 驳回与批准两行俱在
```

规则研讨（任务单）：为什么审批人不能是触发 RCA 的同一角色（analyst）？（自审自批＝没有制衡；RBAC 上 owner 与 analyst 分离。）

#### 4.4 三方会审工坊：审一份埋了幻觉的报告（15′）

分组角色（轮流）：业务总监（只关心影响面与恢复时间）/ 数据工程（只认证据链与 SQL 可执行性）/ 审批人（只问风险：影响行数、可回滚性、留痕）。记录员按会审评分表打分。
流程：3 分钟读报告 → 每角色 2 分钟质询 → 1 分钟裁决（通过/打回/补证）。
抓幻觉线索：报告中被引用但血缘图里不存在的表名、对不上的时间线、没有 evidence 字段支撑的"任务 X 漏跑"结论（教师预埋 2 处）。

### 第 5 步：检查（40 分钟）

【教师活动】发布检查清单；抽查两组现场口头走一遍"从告警到批准"的完整时间线。
【学生活动】自查＋互查：
1. 上溯与下钻两条 GO 的返回集＋兜底表交叉验证结果；
2. 时间线证据链四时刻齐全（注入→告警→报告→批准）；
3. rca_reports 报告含 lineage_path / attribution / suggestion / confidence / status 五要素；
4. suggestion SQL 在沙箱手工 EXPLAIN 过（可执行、有 WHERE 限定）；
5. audit_log 驳回＋批准两行、comment 非空；
6. 会审评分表完整、幻觉抓取 ≥2 处且理由正确；
7. 注入已回滚（UPDATE 复位或表还原脚本执行）——**环境复原为硬性检查项**。

【教学方法】核对表法＋口头时间线复述。

【设计意图】"从告警到批准"的口头复述是 RCA 掌握度的试金石；环境复原延续 L10 建立的注入纪律。

### 第 6 步：评价＋学生讲堂（30 分钟）

【教师活动】主持讲堂（抽 3 组各 4′）＋评分＋布置任务。
【学生活动】讲堂主题抽签二选一：①"我是审批人：我为什么打回这份报告"；②"血缘的方向：一条边如何既找根因又算影响面"。互评量表打分。
【教学方法】费曼法＋同伴互评。
【设计意图】以"打回理由"和"方向语义"两个高认知负载点作为讲堂主题，直接对接课后费曼与期末答辩。

## 七、企业站实践任务卡（2 学时）

| 项目 | 内容 |
|---|---|
| 任务目标 | 模拟一次数据缺失事件，独立完成"注入→巡检→RCA→会审→审批→留痕"全流程并出具根因报告 |
| 场地/协作 | 企业实训站；4 人分工（注入操作/RCA 触发/会审三方），企业导师扮演"业务总监"参加会审质询 |
| 步骤 | ① 在 edu_shadow 注入 freshness 型事故（删除课程表当日分区或停模拟 ETL 任务）→ ② 触发巡检确认 FAIL → ③ 触发 RCA 并读报告（重点核对血缘路径跳数与证据字段）→ ④ 三方会审（企业导师质询影响面）→ ⑤ owner 批准/驳回各一次（comment 必填）→ ⑥ 执行已批准 suggestion（沙箱）并复扫验证恢复 → ⑦ 回滚注入、还原环境 → ⑧ 报告快照＋audit_log 查询结果提 PR |
| 交付物 | PR 含：根因报告快照（`docs/07-项目资源/rca-cases/<组号>.md`：时间线/血缘路径/证据表/归因/建议/会审意见）＋audit_log 两行查询结果＋复扫恢复证据 |
| 评审标准 | ① 血缘路径正确且与兜底表一致 ② 每条归因挂到证据字段（幻觉零容忍）③ suggestion SQL 沙箱可执行且带 WHERE 限定 ④ 审批链完整（驳回＋批准＋comment）⑤ 复扫证明数据恢复 ⑥ 环境已还原 |
| 双导师签栏 | 企业导师（签名/日期）：__________　校内导师（签名/日期）：__________ |

## 八、评价设计（任务单评分表，满分 100）

| 维度 | 权重 | 评价标准 |
|---|---|---|
| 资讯与计划 | 15 | 血缘模型与 RCA 六步图默画正确；会审角色分工明确 |
| 实施完成度 | 35 | 上溯/下钻＋兜底交叉验证（10）；全流程证据链四时刻（15）；审批双路径留痕（10） |
| 会审与思辨 | 25 | 幻觉抓取准确（15）；三角色质询切中各自关切（10） |
| 检查与证据 | 15 | 时间线复述流畅；环境复原确认；未验证项如实标注 |
| 学生讲堂表达 | 10 | 讲清"机器定位、人决策"的分工，4 分钟内完成 |

等级：≥90 优秀／75–89 良好／60–74 合格／<60 重做（限补一次）。

## 九、课后费曼任务

- **讲给谁**：找一位非技术的老师或同学扮演"业务总监"（最好对方真的会追问）。
- **讲什么**：完整讲一次质量事故定位——"昨晚告警响了，10 分钟内我们如何知道坏在哪张表、影响哪些看板、怎么修、谁批的"。全程不用"血缘""探针"这类黑话，用"上游水库/下游水表"之类的类比。
- **自评三问**：①对方听完能回答"坏在哪、影响了谁、谁批准修的"三问吗？②我有没有把"LLM 归因"讲成了"LLM 裁决"？（归因只是建议，批准的是人。）③我讲的时间线和我任务单里的四时刻证据一致吗？——任一问答"否"，重讲并录音自查。

## 十、教学反思栏（授课后 48 小时内填写）

| 反思维度 | 现象记录 | 原因分析 | 改进措施 |
|---|---|---|---|
| 目标达成度（5 条目标逐条） | | | |
| 难点突破效果（方向语义/幻觉识别） | | | |
| 时间分配偏差（哪一步超时） | | | |
| 会审工坊角色投入度 | | | |
| 学生典型错误与误解 | | | |
| LF4 域收官与 L13（ETL 编排）衔接 | | | |
