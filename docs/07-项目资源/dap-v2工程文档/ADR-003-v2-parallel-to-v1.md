# ADR-003：v2 全新命名空间并行建设，v1 存量不动
状态：Accepted（用户决策）· 2026-10-29
背景：dataagent-prod(v0.3.3) 仍在高频发版（6h 前有 rollout），dataagent-course 为教学环境。
决策：新建 ns `dataagent-v2`，以 course 线 API 设计为蓝本全新实现；v1 不迁移不干扰。
后果：+零风险并行；−资源并存（已按小 requests 设计）；后续若 v1 停止演进可迁移其租户数据（表结构兼容清单见 RUNBOOK）。
