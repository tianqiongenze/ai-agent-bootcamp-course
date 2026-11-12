# 学习情境 L07：NL2SQL 管线全景——从一句话到一条安全 SQL（6 学时）

## 一、学习情境基本信息

| 项目 | 内容 |
|---|---|
| 学习领域 | LF3 智能查询服务开发：NL2SQL 与知识引擎 |
| 讲次 | 第 07 讲（第 7 周） |
| 学时 | 6 学时（校内理实一体 4 学时 + 企业站实践 2 学时） |
| 布鲁姆主层级 | **应用**（记忆、理解、分析渗透） |
| 双元场地 | 校内：理实一体机房；企业站：DAP-v2 集群，洞察 Agent 服务 `insight-agent` |
| 前置 | L05 数仓已灌 105.9 万订单；L06 网关读写路径理解；LiteLLM→qwen2.5:14b 服务可达 |
| 企业站 PR 任务 | **PR-07**：跑通 3 条指定问句，逐条交付"问句 → 生成 SQL → 行数/结果 → 护栏记录"证据链 |
| 课后费曼任务 | 用**自创**的生活化类比（不许照抄课堂的"外卖下单"）把管线讲给完全不懂 AI 的听众并录 3 分钟音频 |

## 〇、本讲术语小白卡（先看懂再开工）

| 术语 | 人话解释 | 生活化类比 |
|---|---|---|
| token | AI 读字按"块"计费，约一个词一块 | 按字数收费的代写服务 |
| 温度 temperature | 厨师发挥的随机度：0.1＝照菜谱做，1.0＝自由发挥 | 老师傅 vs 创意厨师 |
| JSON | 程序的记事格式：冒号左边是名字，右边是值 | 快递单：收件人：张三 |
| 幻觉 | AI 一本正经编造不存在的东西（如表里没有的列） | 考试不会做还硬编答案 |
| 沙箱 | 带围栏的试车场：SQL 先在里面跑，出事不伤真库 | 驾校教练车，撞了不算事故 |
| run_id | 平台给每次查询发的取件码，凭它查全过程记录 | 快递单号 |
| confidence | 管线对自己答案的把握分（0–1），仅供参考不等于对 | 天气预报的降水概率 |
| Schema Linking | 先猜你要哪几张表哪几列，只把这些塞给 AI | 图书管理员先定位书架，不搬整个馆 |

## 二、任务描述（客户委托单）

> **委托单编号：DAP-NL2SQL-07**
> 业务方在门户输入一句自然语言："2026年5月销售额最高的10个品类"。洞察 Agent 组委托你们：全程追踪这句话如何变成一条安全可执行的 SQL——跑通管线并留存每步产物；解剖评测集 Q17 题从"错选表"到修复的完整过程；亲手触发 LLM 输出的幻觉列校验与重试路由，最后交付 3 条问句的 SQL 与行数证据链，证明"答案不是编的"。

## 三、学习目标

1. 【记忆】按序复述 NL2SQL 五步教学链：意图理解 → Schema Linking（列级反向索引）→ LLM 生成（LiteLLM→qwen2.5:14b，温度 0.1，JSON 模式）→ 自校验（列归属 + 重试≤2）→ 沙箱执行（四层护栏）；并说出它与代码"四节点"的映射（意图理解＋Schema Linking 合并为 retrieve 检索节点，即"四节点五产物"）。
2. 【理解】解释列级反向索引为什么能把 prompt 从"全库 schema"压缩到"表 X 字段清单"，以及对准确率与 token 成本的双面收益。
3. 【应用】通过控制台/网关跑通管线并留存五类产物（意图与候选表 / 候选字段注入 / SQL / 校验记录 / 执行行集），解释每个产物中关键字段的来源。
4. 【分析】定位 Q17（"2026年5月销售额最高的10个品类"）错选表根因，说明"同义词映射 + 分层白名单"修复方案并复现修复前后对比。
5. 【理解】说明幻觉列校验后的重试路由（重试≤2 次后转模板兜底），并说出对应日志/指标名。

## 四、教学重点与难点

**教学重点**
1. 管线逐环产物与数据流：每一环的输入、输出、失败出口（缺一环讲不清整链）。教学"五步"与代码"四节点"映射：retrieve（含①意图理解＋②Schema Linking）→ generate（③生成）→ validate_execute（⑤沙箱执行）→ verify（④自校验复核）。

```flow
问句 → ①意图理解 → ②Schema Linking → ③LLM 生成 → ④自校验 → ⑤沙箱执行 → 结果
```

2. Q17 真实错题的根因分析：Schema Linking 层的"列→表"映射错误如何污染下游所有环节。

**教学难点**
1. 学生普遍低估 Schema Linking 的价值，认为"把全库 schema 塞进 prompt 也行"。
   **突破策略（三步台阶）**：
   - 台阶1·类比直觉（前移正文）：管线＝"外卖下单"——意图＝读懂备注、Schema Linking＝只带相关餐厅的菜单、生成＝后厨照单做、自校验＝出餐前核对、沙箱执行＝食安检查。全库塞 prompt＝把全城外卖菜单都带给一个厨师。
   - 台阶2·看演示：现场算账＋干扰实验——① token 账：全库 5 层 11 表 ≈ 12k token/次 vs 命中 2 表 ≈ 800 token/次（成本 15 倍差）；② 给 qwen2.5:14b 看全部表时现场复现"错选 ODS 表"（Q17 旧版行为），只看白名单表时稳定正确。
   - 台阶3·动手复现：学生在 E2 亲手插入"错误同义词"复现错选表，再删除修复，diff 两次产物。
2. "自校验放在 LLM 之后"的必要性（LLM 会幻觉出不存在或不在白名单的列）。
   **突破策略（三步台阶）**：
   - 台阶1·类比直觉：出餐前核对＝"菜单上没有的菜不能端出去"；LLM 幻觉＝厨师凭空发明菜单上没有的菜。
   - 台阶2·看演示：幻觉注入演示——构造"利润率排名"问句诱导模型生成数仓不存在的利润率列，观察校验拦截并触发重试/模板兜底，展示 run 产物里的 col_check 记录。
   - 台阶3·动手复现：学生用自己设计的"不存在指标"问句复现一次拦截（E3）。

## 五、教学准备

| 类别 | 内容 |
|---|---|
| 环境 | DAP-v2 课程环境：控制台/网关可提交问句（`POST /v1/query` 返回 run_id，`GET /v1/runs/{run_id}` 取全过程记录）；TiDB 数仓就绪（真实 11 表：`ods_orders`、`ods_refund_orders`、`dwd_trade_order_detail`、`dim_store/region/product/date`、`dws_store_daily_sales`、`dws_product_daily_sales`、`ads_store_gmv_trend`、`ads_category_topn`）；LiteLLM 网关路由 `qwen2.5:14b`（`temperature=0.1`，JSON 模式） |
| 代码 | `services/worker/pipeline.py`（洞察管线：retrieve / generate / validate_execute / verify 四节点，StateGraph 编排，LangGraph 同构 ADR-002）；`packages/dap_core/dap_core/db.py` 的 `get_warehouse_pool`（沙箱执行连 TiDB）；知识库配置在 CRDB `metrics`（指标同义词与口径）/`meta_tables`（分层白名单）/`meta_columns`/`few_shots` 表 |
| 评测 | `tests/eval/run_eval.py`（运行：`packages/dap_core/.venv/bin/python tests/eval/run_eval.py`）；评测集 24 题（12 core + 12 held-out），基线 91.7%；结果 `tests/eval/eval_report.json` |
| 工具 | 控制台账号、curl、jq、mysql 客户端（复核行数）；任务单含"证据链粘贴区" |
| 分组 | 沿用结对；每组认领 1 条"必翻车问句"用于 L08 铺垫（如"订单号 O 开头怎么查"） |

## 六、教学过程设计（六步法：资讯 30′/计划 30′/决策 20′/实施 90′/检查 40′/评价+学生讲堂 30′）

### 6.1 资讯（30′）

**【教师活动】**
1. **外卖类比先行（前移正文）**：板书"外卖下单"五步——意图＝读懂你想吃啥、Schema Linking＝只带相关餐厅的菜单、生成＝后厨照单做、自校验＝出餐前核对、沙箱执行＝食安检查。先给类比再进演示。
2. 以 Q17 问句开场，先演示最终效果（门面在最后揭穿）——在控制台提交问句，或用网关 API：

```bash
# 这步在干什么：向网关提交一条自然语言问句，平台返回 run_id（取件码）
curl -s -X POST http://<网关>/v1/query \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"question": "2026年5月销售额最高的10个品类"}'
# {"run_id": "run-3f2a…", "status": "queued", "cache": {"cache_hit": false, "cache_layer": "none"}}

# 这步在干什么：凭 run_id 取回全过程记录（产物都在这里）
curl -s http://<网关>/v1/runs/run-3f2a… -H "Authorization: Bearer $TOKEN" | jq .
```

```json
// GET /v1/runs/{run_id} 返回（节选，字段为真实结构）
{"run": {
  "status": "done", "model": "qwen2.5:14b", "latency_ms": 8600,
  "result": {"sql": "SELECT p.category, SUM(t.pay_amount) AS sales_amt FROM dwd_trade_order_detail t JOIN dim_product p ON t.product_id = p.product_id WHERE t.pay_time >= '2026-05-01' AND t.pay_time < '2026-06-01' GROUP BY p.category ORDER BY sales_amt DESC LIMIT 10",
             "steps": [{"step": "retrieve", "hits": 6}, {"step": "generate"}, {"step": "execute", "rows": 10}]},
  "events": [{"step": "retrieve", "detail": {"hits": 6, "candidates": ["dwd_trade_order_detail", "dim_product"]}},
             {"step": "generate", "detail": {"model": "qwen2.5:14b"}},
             {"step": "col_check", "detail": {"bad": []}},
             {"step": "execute", "detail": {"rows": 10}}]
}}
```

3. 板书管线数据流（含每步失败出口），并讲清"教学五步 ↔ 代码四节点"映射：

```
问句 ─①意图理解─▶ domain / time_range / metrics / topn
      ─②Schema Linking（列级反向索引）─▶ 候选表 + "表X字段清单" prompt 注入        ┐ retrieve 节点
      ─③LLM 生成（LiteLLM→qwen2.5:14b，temp=0.1，JSON 模式）─▶ {sql, tables}       ← generate 节点
           ├─ JSON 解析失败 → 剥围栏/正则提段/重生成 1 次
      ─④自校验：列归属（SQL 中每列 ∈ 候选表字段清单？）+ 只读白名单预检              ┐ validate_execute/verify
           ├─ 违规 → 带违规原因重试路由回 ③（≤2 次）→ 仍败 → 确定性模板兜底          ┘ （col_check 事件）
      ─⑤沙箱执行（四层护栏：语法白名单 / 强制 LIMIT+超时 / 租户表授权 / 高危审批）
─▶ 行集 + 行数证据（execute 事件 rows 字段）
```

4. 讲解三个关键设计动机：① 反向索引 = "列名/同义词 → 表.列"的倒排，把 12k token 压到 ~800；② 温度 0.1 + JSON 模式 = 让同一个问句的输出尽量确定、可解析（评测集可回归的前提）；③ confidence 是"管线把握分"（0–1），它表达模型自信，**不等于答案正确**——判断对错靠对账。
5. 预告评测基线：24 题全集 91.7%（22/24，其中 12 题为 held-out 考试卷）——"你们今天要亲手抓到那 2 题中的一题的历史版本"。

**【学生活动】** 复画管线图并给每步标注"失败出口"；在任务单记录 token 账与温度/JSON 模式的两个"为什么"；抄下 run_id 的取证方法（凭单号查全过程）。

**【教学方法】** 演示导入 + 板书数据流 + 追问。

**【设计意图】** 先见结果再见骨架，动机（成本、确定性）先行，避免管线沦为名词背诵；失败出口为实施环节的容错实验建立预期。

### 6.2 计划（30′）

**【教师活动】** 指导各组排实施顺序与证据采集计划（三实验 + 一复盘）：

| 序 | 实验 | 产物 | 时间盒 |
|---|---|---|---|
| E1 | 管线全流程追踪（自选问句 + Q17） | 两条 run 记录（events + result） | 25′ |
| E2 | Q17 错选表复现与修复对比 | 修复前后 2 条 run 记录 + 指标配置 diff | 25′ |
| E3 | 幻觉列校验与重试/兜底路由注入 | col_check 违规记录 + 兜底返回 | 25′ |
| E4 | 行数复核（mysql 直查对账） | 对账 SQL 与行数 | 15′ |

**【学生活动】** 结对定自选问句（避开 Q17）；预写 E2 的"预期差异"（旧配置会把"销售额"链到哪张表？）；分配 Driver/Navigator 轮换点。

**【教学方法】** 实验矩阵计划法。

**【设计意图】** 把 90′ 实施拆成可验收的四个实验，每个实验都有对照物（前后/两侧），训练"对比取证"习惯。

### 6.3 决策（20′）

**【教师活动】** 审核各组问句是否覆盖不同环节风险（时间解析 / 多表 JOIN / 聚合维度各至少一题）；统一安全口径：所有跑数走课程账号（平台侧自动走只读护栏与沙箱）；**E2 的指标表写入由教师统一操作**（学生观察取证，不直接改共享知识库）。run_id 按问句登记避免混淆。

**【学生活动】** 微调问句清单；确认取证结构 `out/{qid}/run_record.json + run_events.json`。

**【教学方法】** 清单审核 + 教师放行。

**【设计意图】** 问句覆盖度直接决定证据链的教学价值；取证规范为评测回归（L15）留档。

### 6.4 实施（90′）

> 以下 `run.sh` 指任务单上的两条固定 curl（提交问句拿 run_id → 凭 run_id 取记录），见 6.1 演示。

#### 子步骤 1（25′）：E1 全流程追踪与产物解读

```bash
bash run.sh "2026年5月销售额最高的10个品类" out/q17/   # 内部：POST /v1/query + 轮询 GET /v1/runs/{id}
jq '.run.events' out/q17/run_record.json
# retrieve 事件：{"hits": 6, "candidates": ["dwd_trade_order_detail", "dim_product", …]}
# generate 事件：{"model": "qwen2.5:14b"}
# col_check 事件：{"bad": []}
# execute 事件：{"rows": 10}
jq -r '.run.result.sql' out/q17/run_record.json
```

任务单必答：②的候选表里为什么没有 `ods_orders`？（答：分层白名单只收 DWD/DWS/DIM/ADS，ODS 原始层不对外。）`model` 字段如果显示 `fallback-template` 说明什么？（答：LLM 不可用，走了确定性模板兜底。）

#### 子步骤 2（25′）：E2 Q17 错选表复现与修复对比（本讲核心）

> 复现原理（与真实事故一致）：Q17 曾错选 `ods_orders`——旧版知识库把"销售额"的同义词直接映射到了 ODS 明细最直白的金额列（`total_amount`，含运费口径且原始层不该对外）。错选发生在 CRDB `metrics`/`meta_tables` 知识配置，**配置可插拔即事故可复现**。

```bash
# 教师操作：往 metrics 表临时插入一条"错误同义词"（复现旧版配置）
#   INSERT INTO metrics(...) VALUES('销售额','ods_orders.total_amount',…)  -- 教师侧执行
bash run.sh "2026年5月销售额最高的10个品类" out/q17_old/
jq -r '.run.result.sql' out/q17_old/run_record.json
# SELECT … FROM ods_orders …            ← 错选表：口径错（含运费）+ 层次错（ODS 暴露）

# 教师操作：DELETE 该错误行（修复：现行配置）——同义词归一到 dwd_trade_order_detail.pay_amount
bash run.sh "2026年5月销售额最高的10个品类" out/q17/
jq -r '.run.result.sql' out/q17/run_record.json
# SELECT … FROM dwd_trade_order_detail … ← 修复生效
```

修复三步（对照 CRDB 知识配置讲解）：
1. **分层白名单**：Schema Linking 只在 DWD/DWS/DIM/ADS 层的表/列上建倒排（`meta_tables.layer` 过滤）；
2. **同义词映射**：`销售额/营业额/营收 → dwd_trade_order_detail.pay_amount`（明细口径）、`销售额(日汇总场景) → dws_store_daily_sales.gmv`（汇总口径）——落在 CRDB `metrics` 表；
3. **评测回归**：

```bash
packages/dap_core/.venv/bin/python tests/eval/run_eval.py --only Q17   # PASS
packages/dap_core/.venv/bin/python tests/eval/run_eval.py              # 24 题 91.7% 不回退
```

#### 子步骤 3（25′）：E3 幻觉列校验与兜底路由

```bash
# ① 幻觉列注入：诱导生成数仓不存在的"利润率"列（问句本身合法，列不存在）
bash run.sh "2026年5月各品类利润率排名前10" out/hallu/
jq '.run.events[] | select(.step=="col_check")' out/hallu/run_record.json
# {"step": "col_check", "detail": {"bad": ["profit_margin"]}}   ← 校验拦截
jq -r '.run.model' out/hallu/run_record.json
# 重试 ≤2 次仍败 → model=fallback-template：确定性模板兜底，返回
# "该指标未在数仓口径中定义，建议口径：利润率=…"（诚实失败优于编造）
# ② JSON 容错走读（教师带读 pipeline.py generate 节点）：解析失败 → 剥 ```json 围栏 → 正则提段 → 重生成 1 次
```

#### 子步骤 4（15′）：E4 行数对账（证明"答案不是编的"）

```bash
mysql -h 10.167.2.175 -P 30210 -u dap_app -p -e "
SELECT COUNT(*) FROM (SELECT p.category, SUM(t.pay_amount) amt
  FROM dwd_trade_order_detail t JOIN dim_product p ON t.product_id=p.product_id
  WHERE t.pay_time>='2026-05-01' AND t.pay_time<'2026-06-01'
  GROUP BY p.category ORDER BY amt DESC LIMIT 10) t;"
# 与 run 记录 execute 事件 rows 字段一致（=10）→ 对账通过
```

**【教师活动】** 巡回；在 E2 处集中演示一次"配置差异 diff"（`diff <(jq -S . out/q17_old/run_record.json) <(jq -S . out/q17/run_record.json)`，只看生成的 SQL 两行）把"修复"从概念变成可见的两行差异；收集各组幻觉列案例（哪个列名被幻觉最多——常见 `profit_margin`/`user_name`）。

**【学生活动】** 按实验矩阵执行并粘贴证据；每完成一实验在任务单打勾并记录偏差（如兜底触发与预期不符，原样记录留讨论）。

**【教学方法】** 对比实验法 + 注入式测试（错误同义词/幻觉列注入）。

**【设计意图】** E2 是全课"用数据说话"的样板：错误可复现、修复可 diff、回归有指标；E3 让学生站在管线作者视角制造故障，理解容错代码存在的理由（而非"别人写好的黑盒"）。

### 6.5 检查（40′）

**【教师活动】** 按证据链四查验收：① 两条 run 记录齐全且字段能解释；② Q17 前后对比两条 SQL + 错误同义词配置 diff；③ col_check 违规记录 + 兜底返回；④ 对账行数一致。追问两组："如果 qwen2.5:14b 换成 72b，哪些环节可能要重调？"（答：JSON 模式稳定性↑可简化容错；幻觉列概率↓但 validator 不能删——护栏与模型能力解耦）。

**【学生活动】** 组间交换证据链互查（重点查 run 记录 execute.rows 与对账 SQL 是否真跑过）；登记缺项并现场补跑或如实标注。

**【教学方法】** 证据链核验 + 迁移追问。

**【设计意图】** "护栏与模型能力解耦"是本讲最重要的架构判断，用换模型思想实验检验学生是否真正理解各环节存在的原因。

### 6.6 评价 + 学生讲堂（30′）

**【教师活动】** 按第八节评分；学生讲堂："我用自创类比讲管线"（随机抽 3 组各 3 分钟，类比须自创、映射必须保真：意图/Schema Linking/生成/自校验/沙箱执行五步一个不漏）；布置 L08 预习：思考"为什么 Q17 对了，'订单号 O 开头怎么查'这类问句还是会翻车"。

**【学生活动】** 类比讲解（类比必须保真：映射错一处扣分）；听众互评"类比是否帮理解而非误导"；完成自评三问。

**【教学方法】** 费曼讲堂 + 类比保真互评。

**【设计意图】** 类比是对理解的最强压缩测试——映射错（如把自校验说成"做错了重做"漏掉列归属）立即暴露理解空洞；预习问题直通 L08 混合检索。

## 七、企业站实践任务卡（2 学时）

### 任务卡 PR-07：三条问句证据链交付

| 项目 | 内容 |
|---|---|
| 任务目标 | 跑通 3 条指定问句，交付"问句→SQL→行数/结果→护栏记录"完整证据链，并修复其中暴露的一个索引缺口 |
| 前置条件 | E1-E4 校内完成；`dap_app` 只读账号可用 |
| 指定问句 | ① "2026年第二季度各区域的订单量排名" ② "复购客户（≥2 单）贡献的销售额占比" ③ 各组自选 1 条（需覆盖时间筛选或 JOIN 之外的第三种风险：模糊条件/口径词） |

**步骤：**

```bash
for q in "2026年第二季度各区域的订单量排名" "复购客户（≥2单）贡献的销售额占比" "<自选>"; do
  bash run.sh "$q" "out/pr07/$(echo $q|md5sum|cut -c1-6)/"   # 同 E1：POST /v1/query → GET /v1/runs/{id}
done
# 每条问句交付：
#  1) run 记录取证（run_record.json：events 五步 + result.sql + execute.rows）
#  2) 对账：mysql 用同 SQL 复核行数/金额，截图
#  3) 若自校验有 retry≥1：解释违规原因与重试后行为
#  4) 若问句失败：定位失败在第几步 + 根因（索引缺口/口径未定义/模型解析），能修索引的修，不能修的写入"未解决清单"
```

**交付物（PR 内容）：** `docs/07-项目资源/g{N}/L07-证据链.md`（3 问句 × 4 要素表格化）、`out/pr07/` run 记录、知识配置补丁建议（若发现同义词/白名单缺口，写清建议条目交教师评审）。**必须含**"失败与未解决清单"栏。

**评审标准（企业导师三查）：** 查链（SQL 与结果能互相对账）；查真（产物时间戳/行数可复核，禁止手改 jsonl 产物）；查根因（失败项定位到管线步骤，不允许写"模型不行"了事）。

| 双导师签栏 | 意见 | 签名/日期 |
|---|---|---|
| 校内导师 | | |
| 企业导师 | | |

## 八、评价设计（任务单评分表）

| 维度 | 权重 | 90-100 分标准 | 75-89 分标准 | 60-74 分标准 | <60 分标准 |
|---|---|---|---|---|---|
| 管线复述（资讯） | 15% | 五步 + 失败出口全对 | 五步对 | 漏一步 | 靠提示 |
| E1 产物解读（实施） | 20% | 五件产物字段全部能解释 | 4 件 | 3 件 | 未跑通 |
| E2 根因分析（实施） | 25% | 复现+配置 diff+回归三证齐全，能讲清分层白名单逻辑 | 缺回归 | 缺 diff | 未复现 |
| E3 容错实验（实施） | 20% | 三 case + 幻觉注入全做且解释路由 | 缺一项 | 仅跑通 | 未做 |
| E4 对账（实施） | 10% | 3 条问句全对账一致 | 2 条 | 1 条 | 未对账 |
| 学生讲堂（评价） | 10% | 类比映射全保真 | 一处失真 | 多处失真 | 讲不出 |

**红线**：手改产物文件伪造"正确 SQL"或对账截图与实际行数不符，本讲 0 分重做（HSA）。

## 九、课后费曼任务

| 项目 | 内容 |
|---|---|
| 讲给谁 | 完全不懂 AI 与数据库的家人/朋友 |
| 讲什么 | 用**自创**类比讲五步管线（课堂已给"外卖下单"，费曼要求自创一套新类比，如"医院挂号""快递下单"），录 3 分钟音频：每一步映射必须保真（意图/Schema Linking/生成/自校验/沙箱执行一个不漏），并回答对方至少 1 个追问（如"为什么不让 AI 直接连数据库跑？"——答：幻觉列/口径错/权限，四层护栏的存在理由） |
| 自评三问 | ① 我的类比里哪一步映射最勉强，听众听懂了吗？② 我能不能不用任何类比，直接用三句话讲清"为什么先 Schema Linking 再生成"？③ 如果业务问"利润率"而数仓没有这列，我的系统会发生什么——我能把整条失败路径背出来吗？ |

## 十、教学反思栏

| 反思维度 | 记录（课后填写） |
|---|---|
| "全 schema 也行"误区破除效果 | |
| E2 复现成功率与卡点 | |
| 幻觉列高频名单（收集数据） | |
| 类比讲解中的典型失真 | |
| 未解决清单汇总（转 L08 议题） | |
