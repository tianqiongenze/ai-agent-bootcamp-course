# ADR-002：自研轻量状态图（LangGraph 同构形态）替代 langgraph 依赖
状态：Accepted · 2026-10-30
背景：编排需状态机+条件边+有界重试。langgraph 引入 langchain-core 全家桶（>100MB 依赖），且 CPU 推理慢的场景下其 checkpoint 生态价值有限。
决策：dap_core/graph.py 实现 StateGraph（节点+路由边+错误路由+步数上限），API 形态与 LangGraph 同构；管线（insight/quality+rca/etl）三图均基于它。
后果：+零重依赖、管线代码可测（48 单测覆盖）；−放弃 LangGraph 生态工具，如需 Studio/checkpoint 可平滑替换（接口同构）。
