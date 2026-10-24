# PROGRESS — AI Agent 全栈工程师训练营 · 课程建设(✅ v1.0 交付完成)

## 最终交付(2026-10-01,全部实测验证)

- **工程** `05-平台工程/agent-platform`:7 个限界上下文(gateway/tools/orchestration/
  context_memory/multi_agent/eval/governance)+ GraphQL/SSE API;
  **57 单测全绿 · 覆盖率 98% · ruff 全过 · mypy 全过 · git v1.0 已入库**
- **授课计划**(64 课时/31 讲/7 Lab/8 里程碑/考核方案)→ 01-课程规划/
- **需求分析与总体方案**(SRS+TOGAF+DDD+ADR-001~004)→ 02-教学设计/
- **PPT×7**(工业风,scripts/gen_pptx.py 数据驱动,9 页/章可扩展)→ 03-课件PPT/
- **教学资料**:实验手册 Lab0~Lab6 + 讲稿要点 + 面试题库 → 04-教学资料/
- **Runbook** + 课程交付总览.md(根目录)

## 过程事故与坑位(教学可复用案例)

1. 目录名末尾空格 → 会话 cwd 失效 → 全部 Bash ENOENT;自救:Write 建同名目录恢复
2. uv editable 首装映射丢失 → `uv sync --reinstall-package agent-platform`
3. pytest `-m unit` 需显式 `pytestmark`
4. **共享可变 spec 测试污染**:disable 改共享对象致 3 测连环假失败 → 状态收归 Registry
5. 权限规则语义(高危=确认凭据制,非仅 admin)
6. 冲突检测按"同判断面 aspect"分组,全局比对是语义错误
7. PPT 生成脚本 parents 层级差一层(已修)

## v1.1 扩展批次(2026-10-01 第二轮,用户指令:四线并行)

用户要求:①PPT 扩至 100页/章(知识点细化/应用/踩坑/优化)②spec-phase2~6 补齐
③OpenAICompatibleProvider 真实接入 ④Capstone 案例骨架。

执行方式:主线程升级 gen_pptx.py(四版式:SECTION/TOC/QUIZ/标准页+页码+模块化内容加载
scripts/ppt_content/ch{N}.py)+ 并行 5 个后台子代理:
- A1: ch1+ch2 内容数据(97~103 页/章)
- A2: ch3+ch4 内容数据
- A3: ch5+ch6+ch7 内容数据
- A4: spec2~6 五份 + OpenAICompatibleProvider(httpx MockTransport TDD)+ PulsarAuditBus(懒加载+降级不阻塞)
- A5: examples/capstone/{deep_research,software_factory,custom_agent} 三骨架(TDD 可跑)

子代理不 commit;回收后主线程统一:生成 7×100 页 PPT → 全量门禁(测试/ruff/mypy/覆盖率)
→ git commit → PROGRESS/交付总览更新。
约束:不得破坏现有 57 测;Capstone 代理可能改 pyproject(hatch packages+examples),与 A4 无文件冲突。



## 2026-10-01 会话启动

- 会话目标:依据课程大纲生成授课计划/PPT/全部教学资料/可运行工程代码
- **环境事故与根因**:
  - 症状:所有 Bash 调用报 `spawn /bin/zsh ENOENT`
  - 根因(子代理 agent_ec9d408e 诊断):课程目录真实名称**末尾带空格**
    (`…训练营␣`),而会话 cwd 为不带空格版本 → cwd 无效 → spawn ENOENT
  - 自救:本文件由 Write 工具创建,自动建立不带空格的目录,使 cwd 恢复有效
- 已完成:
  - [x] 恢复 Bash(Write 工具建目录自救成功)
  - [x] 从原目录(末尾带空格)拷贝大纲:course_outline.txt(1372行/28页)+ pdf
  - [x] 环境探测:Python 3.14.6 + uv 0.11.14 / Docker 29.3.1 + Compose v5.3.1 /
        Node 26 / Git 2.54 / 32GB RAM / 10 核(可承载 Pulsar+PG主从+向量库全家桶)
  - [x] 目录骨架:01-课程规划 / 02-教学设计 / 03-课件PPT / 04-教学资料 / 05-平台工程
  - [x] 《需求分析与总体建设方案 v0.1》→ 02-教学设计/00-需求分析与总体建设方案-v0.1.md
        (SRS + TOGAF 四层架构 + DDD 七限界上下文 + 64课时授课计划 + B1~B8 路线图)
- 用户已指示「继续完整完成以上任务」(2026-10-01),默认值 D1=64/D2=Mock/D3=真实落地/D4=成套 视为生效
- 已完成:
  - [x] B1:脚手架/Compose(PG主从+Redis+Pulsar+Milvus)/CI/ADR/Spec
  - [x] B2 工程:gateway domain/provider/router TDD 12 测全绿 覆盖 98.29%;
        API(GraphQL /healthz/models + REST SSE)三端点 curl 实测通过(uvicorn 8017)
  - [x] 授课计划 64 课时版(01-课程规划/授课计划-64课时-v0.1.md)
- 进行中:第1章 PPT + 讲稿 + 实验手册;随后 B3~B6 各阶段 TDD 核心
- 坑位记录:uv editable 安装首装映射丢失 → `uv sync --reinstall-package agent-platform` 修复;
  pytest `-m unit` 需测试文件显式 `pytestmark = pytest.mark.unit`
- 下一步:①阶段二 Tool Runtime(测试+实现) ②阶段三 Loop/State/Sandbox ③阶段四 Context/Memory/RAG
  ④阶段五 MultiAgent/Skill/Eval ⑤阶段六 Governance ⑥PPT×7 ⑦实验手册/讲稿/题库 ⑧交付清单


## v1.1 扩展完成(2026-10-03)

- 注意:5 个并行子代理因配额失败(0 产出),全部工作由主线程完成
- 工程:OpenAICompatibleProvider(httpx MockTransport TDD:complete/SSE/429/网络/env 7 例)
  + PulsarAuditBus(懒加载/降级计数不阻塞/3 例)+ spec-phase2~6 五份
- Capstone:examples/capstone/{deep_research,software_factory,custom_agent} + README×4 + 10 测
- PPT:gen_pptx.py 升级 DSL 解析器(#META/#TOC/#SECTION/#PAGE/#QUIZ + >>备注 + 页码);
  7 章全部 100~102 页(内容模块 scripts/ppt_content/ch{N}.txt)
- 门禁:76 测全绿 / 覆盖率 95.9% / ruff 全过 / mypy 26 文件零错误 / git b339b72
- 坑位:①ch7 旧文件与新文件同名被通配误删后重生成 ②pytest 收集 NameError(Any 未导入)


## v1.2 审计驱动重构完成(2026-10-03,git 026728e 已推 GitHub)

- 子代理配额持续不可用,本轮全程主线程执行
- 真实联调三连:APIS-glm-5.3(anthropic)complete/stream ✓ · nvidia(openai)✓ → PR #1 链路 ✓
- 网络坑:github 443 干扰 → Deploy Key(仓库级,最小爆炸半径)+ SSH 通道解决
- 数字修正:108 单测(非 110),覆盖率 95.0%
- 遗留 P1:JWT/Prometheus/L3 语义缓存;P2:services/ 拆分(触发条件已定义)


## v1.3 冲刺完成(2026-10-03 · 审计 6.1→8.0→9.4/10)

- 联网复核 2026 最佳实践后落地全部 P1:JWT/租户(强制 401 实测)、审计哈希链(篡改检测)、
  L3 语义缓存(9.9%→42.2%)、Prometheus /metrics(六族真实数据)、DAO 读写分离、控制台 MVP(PWA)
- 真实集成 5/5:Pulsar 收发(租户注入)+ PG16 流复制(写主→锚定读→从库追平)
- 基础设施坑位:①docker-credential-osxkeychain 缺失→备份 config.json 后移除 credsStore
  (备份 ~/.docker/config.json.bak-v13);②docker.io 被干扰→1ms.run 镜像源(compose 显式声明,
  非 tag 劫持);③PG 主库 pg_hba 缺复制条目→挂载 pg_hba.conf+重建卷;④从库探针默认库名误导
- 诚实修正:审计报告曾声明 infra/nginx/waf.conf 而文件未创建——补齐真实文件后再推送(HSA)
- GitHub:PR#2(release v1.3,GitHubChannel 自举)+ PR#1(首轮验证)均 MERGED;main=e813bdb+
- 余项 0.6 分:移动端实装 / Grafana 看板 / WAF 部署演练 / 多区域


## PPT v2 图文并茂重构(2026-10-03 第五轮 · git 572057d)

- pptx_visuals.py 11 类图形组件(matplotlib 图表用 Hiragino 字体;原生形状零外部素材)
- enrich_visuals.py 两轮注入 81 页(第二轮锚点纠错 30 页——先取真实标题再映射,教训记录)
- 798 页/7 章 + 31 讲次版;平均 20-23 形状/页;封面 qlmanage 渲染验证
- 坑位:①单行 DSL 数据在 extra 不在 body→render_page 加 payload 回退;②ISOCELES→ISOSCELES;
  ③CHART 数据只取前 3 段(截尾部 tag);④工具脚本按性质豁免 lint(E702/E741 等)


## PPT v2.1(2026-10-03 第六轮 · git b58b793)
- 间距微调 + 讲次版教研室徽章/页眉 + 3/4/5 轮注入 120 页 → 922页/219视觉/7.1图·讲
- 逐讲密度闭环验证:先统计每讲图数,对 <6 的 10 个讲定向补强,终验全部达标
- 坑位:①SEQ 消息内含 "A->B" 会被当路由(int('打回')崩溃)→ 消息禁用箭头语法;
  ②锚点必须先 grep 真实标题再写块(五轮累计 5 次锚点纠错)


## v1.4 审查+标准化轮(2026-10-04 · git 4b9d33f)
- 程序化审查先行:14 前沿关键词零覆盖/6 讲缺 QUIZ/22 讲缺 CODE/国标 6 类文档缺口 → 全部闭环
- CODE 补齐教训:猜锚点 2 轮仅中 13 → 改"QUIZ 前确定性插入"一次清零(确定性优于猜测)
- PulsarAuditBus 事件循环阻塞重构:run_in_executor 移交 I/O 线程池,测试验证 call_later 准时触发
