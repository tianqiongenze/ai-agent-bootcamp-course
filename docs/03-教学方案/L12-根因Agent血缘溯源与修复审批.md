# 学习情境 L12：根因 Agent：血缘溯源与修复审批（6 学时）

> 载体：DAP-v2 RCA 流程（课程在真实接口上组合实现）——质量失败项（`/v1/quality/results`）→ 血缘溯源（`POST /mcp/lineage/impact`：Nebula space=`dap`，CRDB `lineage_edges` 双写兜底）→ LLM 归因（worker LLMClient）→ 修复建议草稿（approvals 表 `sql_or_payload`，status=pending）→ 审批中心 `POST /v1/approvals/{aid}/decide` → `audit_log` 留痕（append-only）。
> 核心铁律：**Agent 只建议不执行；人批准才动数据；全程留痕可追责。**

## 〇、本讲术语小白卡（先看懂再开工）

| 术语 | 人话解释 | 生活化类比 |
|---|---|---|
| 血缘 | 数据的族谱：这张表由哪张表加工来、又被谁加工走 | 户口本上的"生于谁、又生了谁" |
| 图数据库 | 专门存"谁和谁有关系"的库 | 微信好友关系网 |
| 上溯（REVERSELY） | 顺着族谱往"长辈"找，找病根 | 下游水质坏了，往上游找排污口 |
| 下钻（正向 GO） | 顺流往下找，看病传染了谁 | 这个排污口坏了，下游哪些村子没水喝 |
| 双写兜底 | 族谱抄两份放两家，一家失火烧另一家 | 重要证件复印两份分开放 |
| append-only | 日记只许写不许撕页，改历史＝毁证据 | 医院病历：只加不改 |
| confidence | 模型对自己结论的打分，≠证据 | 学生自评"我肯定对"不算数，要看答题过程 |

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

1. 【理解】画出血缘图模型（Nebula space=`dap`：tag `tbl`、edge `derives_from`，边方向与 CRDB `lineage_edges` 的"上游 src→下游 dst"一致）与双写兜底的读写路径，说明"双写"防的是什么故障。
2. 【应用】用 `POST /mcp/lineage/impact`（等价 nGQL：`GO ... OVER derives_from REVERSELY`）从失败表上溯找到候选根因表，并能用正向 GO 反查下游影响面（谁被波及）。
3. 【分析】拆解 RCA 六步流程（失败项→血缘上溯→证据组装→LLM 归因→修复建议草稿→审批留痕），标注每一步中"禁止 LLM 介入"的环节（血缘查询、证据数值、审批决定）。
4. 【评价】以业务总监／数据工程／审批人三种角色会审一份根因报告，识别 LLM 归因中的幻觉与证据不足（无证据字段支撑的结论必须打回）。
5. 【评价】论证"Agent 只建议不执行＋人工批准＋audit_log 追责"的合规价值，说明建议 SQL 为什么必须留在草稿态（approvals.status=pending）直到批准。

## 四、教学重点与难点

**教学重点**

1. 血缘图模型与方向语义：`derives_from` 边与 `lineage_edges` 的"上游 src→下游 dst"同向——正向 GO 查影响面（顺流而下），REVERSELY 上溯根因（逆流而上）。先看流向再决定顺走还是逆走。
2. RCA 六步闭环与治理红线：血缘与证据确定性、归因与建议由 LLM 起草、批准与执行永远属于人。

**根因定位血缘回溯链（课堂板书/PPT 用）**

```flow
质量FAIL → ①失败项取证 → ②血缘REVERSELY上溯 → ③候选根因表 → ④证据组装 → ⑤LLM归因 → ⑥人审批准
```

（一句话类比，随板书讲：血缘＝**河流**——下游水表读数异常（报表数字不对），先看河流流向图（边方向），再逆流而上找排污口（REVERSELY 上溯根因）；找到后顺流数一遍下游哪些村庄停水（正向 GO 算影响面）。）

**教学难点（附突破策略）**

1. **边的方向与查询方向的空间想象**：学生常把"上溯"误写成正向 GO（取决于建模时边的朝向）。
   - 三步台阶：台阶1（生活类比建立直觉）——河流流向图：先问"水往哪流"（边方向＝上游 src→下游 dst），再决定顺流（影响面）还是逆流（根因）；台阶2（看一次真实演示）——教师投屏 `POST /mcp/lineage/impact` 一次返回 upstream/downstream 两个方向的结果，对照 nGQL 的 REVERSELY 语句；台阶3（学生动手复现）——白板 DAG＋"手指走边"——先对照 `lineage_edges` 表确认语义（src＝上游、dst＝下游），再沿边方向走一遍；每次溯源结果都与 CRDB `lineage_edges` 兜底表交叉验证，两边不一致即触发"血缘双源核对"讨论。
2. **评价 LLM 归因的可信度**：报告读起来"头头是道"但可能幻觉（编造表名/任务名/时间线）；模型 confidence=0.9 只是"自信度"，不是证据。
   - 三步台阶：台阶1（生活类比建立直觉）——"学生拍胸脯说肯定对"不算数，要看答题过程每一步有没有依据；台阶2（看一次真实演示）——教师展示一份报告里 confidence=0.9 但证据挂不上号的归因，当场打回；台阶3（学生动手复现）——三方会审工坊＋"证据挂靠"规则——报告里每一条归因陈述必须能挂到具体证据字段（探针值/血缘路径/最后写入时间/任务日志），挂不上即打回；教师预先在一份报告中埋 2 处幻觉供学生抓。

## 五、教学准备

**环境**（讲师课前 1 天核验）

- `dataagent-v2` 命名空间：dap-tools（内嵌 NebulaLineage）/ dap-worker / nebula / dap-redis Ready；Nebula space=`dap` 已含课程数仓血缘（3 跳以内，真实链：ads_store_gmv_trend → dws_store_daily_sales → dwd_trade_order_detail → ods_orders）。
- 课程沙箱：TiDB `edu_shadow` 沙箱表（教师预建，供注入事故）；角色 Token：analyst（触发巡检/溯源）、approver（审批，与 analyst 分离）。
- 审批演示台：教师机投屏 approvals 表 / audit_log 实时变化（CRDB 查询为教师演示通道）。

**资料**

- 代码：`dap-v2/services/tools/main.py`（NebulaLineage：space=`dap`、`impact_upstream` 用 REVERSELY 上溯；`POST /mcp/lineage/impact` 一口返回 upstream＋downstream；`/mcp/lineage/upsert` 双写）、`services/gateway/main.py`（`GET /v1/approvals`、`POST /v1/approvals/{aid}/decide`）、`packages/dap_core/dap_core/audit.py`（audit_log 落库，append-only）。
- 表卡（真实字段）：`lineage_edges(id, tenant_id, src_table, dst_table, etl_job)`（CRDB 兜底，src＝上游）、`approvals(id, tenant_id, kind, summary, sql_or_payload, impact_analysis, status, requested_by, decided_by, decided_comment, created_at, decided_at)`、`audit_log(trace_id, tenant_id, actor, actor_type, action, target, detail, outcome, created_at)`。
- 会审材料：一份预先埋了 2 处幻觉的示例根因报告（脱敏打印件）。

**分组**：4 人一组；会审环节角色分配：业务总监／数据工程／审批人／记录员（轮流）。

## 六、教学过程设计

### 第 1 步：资讯（30 分钟）

【教师活动】
- 承接 L09–L11 三讲主线："反馈闭环让正确被复用（L09）、LLM 工程让系统挂了也兜得住（L10）、规则引擎让脏数据第一时间被发现（L11）——发现之后呢？谁改的？改哪？谁批准？"引出 RCA。
- 板书血缘模型与 RCA 管线：

```
血缘图（Nebula space: dap；CRDB lineage_edges 同步双写：Nebula 不可用时兜底可查）
  tag:  tbl(name)                          edge: derives_from(job)（方向＝上游 src ──► 下游 dst）
  例：ads_store_gmv_trend ─► dws_store_daily_sales ─► dwd_trade_order_detail ─► ods_orders
  （与 lineage_edges 的 src_table→dst_table 同向：正向 GO＝顺流查影响面，REVERSELY＝逆流上溯根因）

RCA 六步管线（课程在真实接口上组合）
quality_results(FAIL) ─①血缘上溯 POST /mcp/lineage/impact（REVERSELY）─► 候选根因表集
                      ─②证据组装（逐表探针：行数/空值率/最后写入时间/任务日志）
                      ─③LLM 归因（worker LLMClient：输入=血缘路径+证据 → 输出=归因说明+confidence）
                      ─④修复建议草稿（approvals 表：sql_or_payload 含 SQL，status=pending，不执行）
                      ─⑤审批中心 GET /v1/approvals → POST /v1/approvals/{aid}/decide
                      ─⑥人工批准/驳回 ──► audit_log 留痕（append-only，action=approval.decide）
```

- 发放引导文：委托单 #R-2412 ＋ 表卡 ＋ 会审评分表。

【学生活动】
- 通读 `tools/main.py` 的 NebulaLineage 双源查询与 `audit.py` 的 append-only 设计（审批状态机：approvals.status pending→approved/rejected）。
- 回答引导文 3 问：①血缘查询为什么绝不能交给 LLM（答错表等于全错）？②approvals 草稿里的 SQL 为什么不能由 Agent 直接执行？③audit_log 为什么设计成 append-only（改历史＝毁证据）？

【教学方法】主线串联法＋引导文法。

【设计意图】第 9–12 讲是一条完整的治理故事线，开讲先收线；三个问题分别钉住"确定性环节不交 LLM、执行权属人、留痕不可篡改"三条红线。

### 第 2 步：计划（30 分钟）

【教师活动】给出计划模板与红线（注入只限课程沙箱表、溯源/巡检用 analyst 触发、审批用 approver 且意见必填）。

【学生活动】小组产出四段计划：

| 子任务 | 关键命令/路径 | 预期证据 |
|---|---|---|
| 血缘查询 | `POST /mcp/lineage/impact` 上溯＋下钻 | upstream/downstream 两份结果＋兜底表交叉验证 |
| RCA 全流程 | UPDATE 注入→`POST /v1/quality/scan`→LLM 归因演示 | 审批草稿（approvals 一行 pending）＋报告快照 |
| 审批留痕 | `POST /v1/approvals/{aid}/decide`（approved 与 rejected 各一次） | audit_log 两行（action=approval.decide） |
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
# 这步在干什么：一次拿到"上游根因候选"与"下游影响面"两个方向（dap-tools 服务实现）
curl -s -X POST "$GW/mcp/lineage/impact" -H "x-internal-token: $INTERNAL_TOKEN" \
  -H 'Content-Type: application/json' -d '{"table":"dws_store_daily_sales"}'
# 预期：{"upstream":[{dwd_trade_order_detail,...},{ods_orders,...}],
#        "downstream":[{ads_store_gmv_trend,...}], "source":"nebula"}   ← source=crdb_fallback 说明走了兜底
```

等价 nGQL 原生查询（教师演示，理解边方向用）：

```ngql
USE dap;
SHOW TAGS;      -- tbl
SHOW EDGES;     -- derives_from

-- 从失败表上溯找根因（边方向＝上游→下游，故逆流上溯用 REVERSELY；源码 impact_upstream 即如此）
GO 1 TO 3 STEPS FROM "dws_store_daily_sales" OVER derives_from REVERSELY
YIELD dst_vertex_id($$) AS upstream;
-- 预期：dwd_trade_order_detail / ods_orders（1~3 跳内的上游）

-- 影响面下钻：谁被这张脏表波及（顺流而下，正向 GO）
GO 1 TO 3 STEPS FROM "dws_store_daily_sales" OVER derives_from
YIELD dst_vertex_id($$) AS downstream;
-- 预期：ads_store_gmv_trend（回答业务总监"哪些看板废了"）
```

CRDB 双写兜底交叉验证（CRDB 查询为教师演示通道，学生抄录结果比对）：

```sql
SELECT src_table, etl_job FROM lineage_edges WHERE dst_table = 'dws_store_daily_sales';
-- src＝上游；与血缘上溯结果必须一致；不一致即触发"血缘双源核对"（以 ETL 双写日志为准修图）
```

任务单思考题：如果把边建成"下游→上游"（与 lineage_edges 反向），上面两条查询各要怎么改？（方向语义与查询方向是两回事：先确认边朝向，再决定正走还是 REVERSELY。）

#### 4.2 RCA 全流程：注入事故→归因→审批草稿（30′）

```bash
# ① 注入事故：把课程沙箱表 9/30 分区约 8% 行的 gmv 置 NULL（仅课程沙箱表）
mysql -h 10.167.2.176 -P 4000 -u course_ro -p    # 连接串以教师发放为准（写操作需教师授权账号）
```

```sql
UPDATE edu_shadow.dwd_trade_order_detail SET gmv = NULL
WHERE dt = '2026-09-30' AND order_id % 12 = 0;   -- 仅课程沙箱表
```

```bash
# ② 触发巡检 → qr-gmv-null FAIL（复用 L11 链路）
curl -s -X POST "$GW/v1/quality/scan" -H "Authorization: Bearer $ANALYST_TOKEN" \
  -H 'Content-Type: application/json' -d '{"tenant_id":"edu"}'

# ③ 归因与报告生成（教师演示）：worker 以 LLMClient 读"血缘路径+证据"起草归因说明与修复建议，
#    写入 approvals 草稿（status=pending，不执行）
kubectl -n dataagent-v2 logs deploy/dap-worker --tail=80 | grep -iE "lineage|evidence|attribut|suggest"

# ④ 读审批草稿（重点看 sql_or_payload 与 impact_analysis）
curl -s "$GW/v1/approvals?status=pending" -H "Authorization: Bearer $ANALYST_TOKEN"
# 预期：一行 kind=fix_suggestion 草稿，summary＝归因摘要，
#       sql_or_payload ≈ "UPDATE edu_shadow.dwd_trade_order_detail SET gmv = amount - refund_amt
#                         WHERE dt='2026-09-30' AND gmv IS NULL;"（草稿，未执行）
```

证据挂靠检查（任务单）：草稿/报告中每条归因陈述逐条标出支撑它的证据字段（探针值/血缘跳数/最后写入时间/任务日志），挂不上的记入"待质询清单"。

#### 4.3 审批留痕：批准与驳回双路径（20′）

```bash
# ① 驳回一次（comment 必填——练习"打回"；decision 只有 approved/rejected 两个合法值）
curl -s -X POST "$GW/v1/approvals/<AID>/decide" -H "Authorization: Bearer $APPROVER_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"decision":"rejected","comment":"建议未带影响行数，补齐再审"}'
# 草稿回 pending，可修改后再次提审

# ② 批准一次
curl -s -X POST "$GW/v1/approvals/<AID>/decide" -H "Authorization: Bearer $APPROVER_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"decision":"approved","comment":"同意回补，限课程沙箱表，执行后复扫验证"}'

# ③ 查留痕（CRDB 查询为教师演示通道，学生抄录）
```

```sql
SELECT actor, actor_type, action, target, outcome, created_at
FROM audit_log ORDER BY created_at DESC LIMIT 5;
-- 预期：驳回与批准两行俱在（action=approval.decide，actor_type=human）
```

规则研讨（任务单）：为什么审批人不能是触发 RCA 的同一角色（analyst）？（自审自批＝没有制衡；RBAC 上 approver 与 analyst 分离——源码 `decide` 端点要求 approver/platform_admin 角色。）

#### 4.4 三方会审工坊：审一份埋了幻觉的报告（15′）

分组角色（轮流）：业务总监（只关心影响面与恢复时间）/ 数据工程（只认证据链与 SQL 可执行性）/ 审批人（只问风险：影响行数、可回滚性、留痕）。记录员按会审评分表打分。
流程：3 分钟读报告 → 每角色 2 分钟质询 → 1 分钟裁决（通过/打回/补证）。
抓幻觉线索：报告中被引用但血缘图里不存在的表名、对不上的时间线、没有 evidence 字段支撑的"任务 X 漏跑"结论（教师预埋 2 处）。

### 第 5 步：检查（40 分钟）

【教师活动】发布检查清单；抽查两组现场口头走一遍"从告警到批准"的完整时间线。
【学生活动】自查＋互查：
1. 上溯与下钻两条 GO 的返回集＋兜底表交叉验证结果；
2. 时间线证据链四时刻齐全（注入→告警→报告→批准）；
3. 审批草稿（approvals）含 summary 归因 / sql_or_payload 建议 / impact_analysis 影响分析 / status=pending 四要素，报告快照含血缘路径与证据表；
4. 建议 SQL 在沙箱手工 EXPLAIN 过（可执行、有 WHERE 限定）；
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
| 步骤 | ① 在课程沙箱表注入 freshness 型事故（删除课程表当日分区或停模拟 ETL 任务）→ ② 触发巡检确认 FAIL → ③ 走 RCA 流程并读审批草稿（重点核对血缘路径跳数与证据字段）→ ④ 三方会审（企业导师质询影响面）→ ⑤ approver 批准/驳回各一次（comment 必填）→ ⑥ 执行已批准建议 SQL（沙箱）并复扫验证恢复 → ⑦ 回滚注入、还原环境 → ⑧ 报告快照＋audit_log 查询结果提 PR |
| 交付物 | PR 含：根因报告快照（`docs/07-项目资源/rca-cases/<组号>.md`：时间线/血缘路径/证据表/归因/建议/会审意见）＋audit_log 两行查询结果＋复扫恢复证据 |
| 评审标准 | ① 血缘路径正确且与兜底表一致 ② 每条归因挂到证据字段（幻觉零容忍）③ 建议 SQL 沙箱可执行且带 WHERE 限定 ④ 审批链完整（驳回＋批准＋comment）⑤ 复扫证明数据恢复 ⑥ 环境已还原 |
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
- **讲什么**：完整讲一次质量事故定位——"昨晚告警响了，10 分钟内我们如何知道坏在哪张表、影响哪些看板、怎么修、谁批的"。全程不用"血缘""探针"这类黑话。课堂已用"河流-排污口"类比讲过血缘方向——课后**自创一个**属于你自己的类比（水库/水表版本也可以，讲顺就行），并说清类比里每个角色对应系统里的什么。
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
