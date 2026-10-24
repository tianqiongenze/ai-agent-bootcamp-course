# 实验手册 Lab0 ~ Lab6(v1.0)

> 每个 Lab 对应一个里程碑;验收标准可逐条核对,全部命令在 macOS(Docker)/Linux 验证路径。
> 工程根目录:`05-平台工程/agent-platform`(下称 `$AP`)

---

## Lab0 · 环境搭建(M0,30 分钟)

**目标**:一键起全套环境,跑通第一个 GraphQL 查询与 SSE 流。

```bash
cd $AP
make setup        # uv 自动管理 Python 3.12 并装依赖
make infra        # PG 主从 + Redis + Pulsar + Milvus(首次拉镜像约 3-5 分钟)
make test         # 单元测试全绿
make dev          # 起服务 http://127.0.0.1:8000
```

**验收**
- [ ] `curl -s localhost:8000/healthz` 返回 `{"status":"ok",...}`
- [ ] GraphQL 查询 `{ models { name role } }` 返回 primary/fallback
- [ ] `docker exec ap-pg-replica psql -U agent -tAc "SELECT pg_is_in_recovery()"` 输出 `t`(从库真实在复制)
- [ ] `pytest -m unit` 全绿(57 个)

---

## Lab1 · LLM Gateway(M1,90 分钟)

**任务**:TDD 补全 Gateway 的结构化输出能力。

1. 红:在 `tests/unit/gateway/` 新增测试——`response_schema` 传入时,MockProvider 返回非法 JSON 应触发一次"错误反喂重试"后成功;
2. 绿:在 `gateway/` 实现 `schema_out.py`(校验 → 反喂 → 二次失败降级默认值);
3. 重构:把重试次数提取为配置。

**验收**
- [ ] 新测试全绿,总覆盖率仍 ≥80%
- [ ] `curl -N -X POST :8000/v1/chat/completions -d '{"messages":[{"role":"user","content":"hello"}]}'` 打字机输出
- [ ] 把 `LLM_MODEL_CHAIN` 首模型改为不存在模型,请求自动 fallback 成功(router.attempts 留痕 2 次)

---

## Lab2 · Tool Runtime(M2,90 分钟)

**任务**:注册一套业务工具并接入审计。

1. 用 `@tool` 装饰器注册 5 个工具:`search_code`(read)/`read_file`(read)/`write_file`(write)/`run_test`(write)/`drop_table`(dangerous);
2. `mask_args={"api_key"}` 演示脱敏;
3. 构造 `role="readonly"` 调用写工具 → 断言 `PermissionDeniedError`。

**验收**
- [ ] `registry.discover("搜索")` 命中 search_code
- [ ] dangerous 工具无 confirmed 被拒,带 confirmed 通过
- [ ] 审计事件含 masked 参数,`sk-` 开头值不可见
- [ ] 慢工具超时返回 ok=False 且审计留痕

---

## Lab3 · Agent Loop 与 Sandbox(M3,120 分钟)

**任务**:让 Agent 在演示仓库完成代码理解任务并从断点恢复。

1. 实现一个 `ScriptedDecider` 模拟 LLM 决策(search → read → finish);
2. `max_iterations=2` 下跑 3 步任务 → 验证 FAILED + Checkpoint 保存;
3. `resume_from` 续跑 → COMPLETED 且历史完整;
4. Sandbox:尝试读仓库外文件、执行 `rm -rf /` → 均被拦截。

**验收**
- [ ] 中断恢复演示成功(steps 保留)
- [ ] 连续 3 个相同动作触发 `LoopFailedError("dead loop")`
- [ ] SandboxViolation 三例(越界读/越界写/危险命令)全部拦截

---

## Lab4 · Context / Memory / RAG(M4,120 分钟)

**任务**:为 Codebase Agent 装上检索与记忆。

1. 用 `Chunk(id,text,source)` 对演示仓库 10+ 文件建索引;
2. `HybridRetriever.search("鉴权")` 验证双通道融合;
3. `MemoryStore` 写入项目记忆(构建命令/技术栈),`task_summary()` 生成恢复锚点;
4. `compress_history` 对 50 条历史压缩,报告压缩比。

**验收**
- [ ] 检索 top1 命中 auth 相关 chunk 且 via 含两个通道
- [ ] Token 压缩比 < 0.5 且头尾信息保留
- [ ] 回答带 source 引用(文件级)

---

## Lab5 · Multi-Agent 与 Eval(M5,120 分钟)

**任务**:六角色可维护性分析 + 回归对比。

1. 实现 6 个 Worker(Architecture/Test/Security/Performance/Docs/Report),Supervisor 并行调度;
2. 构造 ≥20 题 Golden Dataset(输入 + 期望关键词 + 期望工具);
3. 跑 v1/v2 两版 agent_fn,输出 `RegressionDelta`;
4. 人为让两个 Worker 在同一 aspect 结论相反,观察仲裁。

**验收**
- [ ] 报告含全部子结论,超时 Worker 被隔离
- [ ] success_rate / tool_call_accuracy 有数字输出
- [ ] 回归报告能指出 improved/regressed 用例

---

## Lab6 · 生产化演练(M6,90 分钟)

**任务**:灰度发布 + 故障复现。

1. `FeatureFlags.set("prompt_v2", enabled=True, rollout_percent=50)` → 验证同一用户判定恒定、1000 用户命中 40%~60%;
2. TraceCollector 构造含失败 span 的调用链 → `healthy is False`;
3. ReplayStore 录制 3 组输入输出,回放比对一致;
4. CostLedger 双模型记账,输出报表含 _total。

**验收**
- [ ] 灰度一致性 + 比例区间两项断言通过
- [ ] 失败任务 Trace 可读(哪个 span 失败一目了然)
- [ ] Runbook:对照 `docs/runbooks/` 一条告警一条处置

---

## Capstone(选做其一)

A. 深度研究平台 MVP:Skill 沉淀竞品分析方法论 + 检索工具 + 证据链输出
B. 软件工厂 MVP:PM/架构/开发/QA 四角色 + GitHub 分支/PR 流程 + 测试验收
C. 自选业务 Agent:按第七章"业务拆解七步"完整走一遍并答辩

**答辩要求**:用数据说话(任务成功率/成本/延迟),对照 Eval 报告讲解一次迭代决策。
