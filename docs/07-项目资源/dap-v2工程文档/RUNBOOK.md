# DAP-v2 运维手册

## 访问入口
- 控制台：http://10.167.2.175:30281 （或 ingress `dataagent.platform.local`，本机 hosts 指向 10.167.2.175）
- GraphQL：http://10.167.2.175:30281/graphql · 指标：/metrics · 健康：/healthz /readyz
- Grafana：10.167.2.175:30082（已有集群面板，搜 dap_ 前缀指标）

## 演示账号
admin@dap.local/Admin@2026（平台管理员）· analyst/Analyst@2026 · engineer/Engineer@2026（tenant-beta）· approver/Approver@2026

## 常用运维
```bash
# 状态
kubectl -n dataagent-v2 get pods,hpa,ingress
# 发布（Mac 本地）：TAG 每次必须递增（同 tag 覆盖不触发滚动，IfNotPresent 缓存旧 digest）
TAG=v2-r<N+1> bash scripts/deploy.sh
# 漂移检测（DGO）：make diff（deploy.sh 会把 yaml tag 回写为本次 TAG）
# 质量巡检：控制台-质量中心-立即全量巡检（或 POST /v1/quality/scan）
# 初始化重跑：kubectl -n dataagent-v2 delete job dap-init; kubectl apply -f deploy/k8s/05-init-jobs.yaml
# 数仓重灌（Mac）：DAP_WAREHOUSE_DSN=mysql://root@10.167.2.175:30210/warehouse uv run --project packages/dap_core --with pymysql python seed/seed_warehouse.py
# 知识索引重建：kubectl -n dataagent-v2 exec deploy/dap-tools -- python /app/services/tools/init_db.py 后 POST /mcp/index/knowledge
# NL2SQL 评测（Mac，需 dap_core venv）：packages/dap_core/.venv/bin/python tests/eval/run_eval.py
# 单测+绑定校验（发布前必过）：cd packages/dap_core && uv run pytest ../../services ../../packages -q
```

## 发布铁律（v2-r5~r12 血泪沉淀）
1. **Dockerfile 单一事实源**：只用仓库 `deploy/Dockerfile.*`（COPY 内层包 `dap_core` + `PYTHONPATH=/app`）；deploy.sh 已改为校验而非生成——勿恢复生成逻辑（namespace 包陷阱：`COPY→/app/packages/...` + `PYTHONPATH=/app/packages` 会让 `import dap_core` 命中空目录，三服务齐崩）
2. **服务间调用必带 `x-internal-token`**（tools /mcp/* 401 拦截）；新增跨服务客户端时从环境 `DAP_JWT_SECRET` 取
3. **SQL 占位符绑定**：新增/修改 fetch 调用必须过 `tests/test_bindings.py`（SQL $N 数量 vs args 长度）——v2-r9 曾漏传 $1 致 metadata.search 全量 500
4. **NetworkPolicy**：default-deny 下 NodePort/外部访问依赖 06-pdb.yaml 的 ipBlock 白名单（10.167/16 + 192.168/16），新增源网段记得补
5. **同 tag 不滚动**：镜像更新必须换新 tag（v2-rN 递增）

## 反馈闭环（NL2SQL 100% 的机制）
1. 用户对结果差评并填修正 SQL → `POST /v1/feedback` → `few_shots` 表沉淀 + `/mcp/index/fewshot` 增量索引（Milvus 失败自动降级，CRDB 不丢）
2. 后续问题检索命中示例：**问题完全一致 → FAQ 直答**（跳过 LLM，model=faq-hit，秒级返回）；相似问题 → 示例作为 Few-shot 注入 Prompt
3. 评测轨迹：基线 50% → 知识库修复 91.7% → 反馈闭环 + FAQ 直答 **100%**（eval_v2r12.log）
4. 环境注意：本集群 CPU 不支持 X86_V2，pymilvus/NumPy 启动即降级（`milvus_degraded_at_boot`）——语义检索走 CRDB 关键词兜底（L3），few-shot 闭环不受影响

## 外部 LLM Key 接入（主路由切换）
1. `kubectl -n dataagent-v2 edit secret dap-secret` → DAP_LITELLM_API_KEY=<key>
2. `kubectl -n dataagent-v2 edit cm dap-config` → DAP_LLM_PRIMARY_MODEL=<外部模型名>
3. 在 LiteLLM 侧配置该模型（或直改 litellm 部署）；worker/tools 滚动重启
4. 验证：提交一条 /v1/query，run.result.model 应为新模型名（非 fallback-template）

## 容量扩容路径（到 100 万并发）
1. gateway/worker HPA max 已配（10/12）；先扩副本确认 worker1 CPU 余量
2. 新增 worker 节点（K8S join 即可，GitOps 自动调度）
3. Pulsar topic 分区扩容（jobs topic 已 6 分区，consumer Shared 自动均衡）
4. CRDB/TiDB 已分布式，无需变更；Milvus standalone → cluster（官方扩容路径）
5. 详见 docs/TEST-REPORT.md §容量外推

## 故障速查
| 症状 | 处置 |
|---|---|
| gateway 0/1 不就绪 | kubectl logs 看依赖项；tools 健康检查超时会被自动重建（DPM） |
| run 卡 queued | 看 worker 日志 `job_done/job_nack`；Pulsar 连接 `pulsar_consumer_up` |
| SQL 全被拦 | 确认 meta_tables 授权与租户 data_scope 通配 |
| LLM 超时 | Ollama 队列被大模型占满（集群共享）——降级模板自动生效，或接外部 Key |
| Redis 故障 | 主链不受影响（降级直穿）；恢复后 readyz 自动回归 |

## 备份策略（R4 新增——审查发现 CRDB/Milvus 零备份声明）
| 对象 | 策略 | 落地方式 |
|---|---|---|
| CRDB `dap`（平台库：runs/approvals/few_shots/审计） | 每日逻辑快照 | k8s CronJob `cockroach backup` 到 nfs-client StorageClass（既有 nfs-provisioner），保留 14 天；恢复：`RESTORE FROM ...` |
| TiDB `warehouse`（样例数仓，可重建） | 低优先：seed 脚本幂等可全量重建 | 不备份，重建路径 `make seed`（数据资产可再生产） |
| Milvus `dap_knowledge/dap_semantic_cache` | 可重建 | CRDB meta 是事实源，`POST /mcp/index/knowledge` 全量重建 |
| Redis | 纯缓存可丢 | 不备份 |
✅ **已落地（2026-10-31 R5 收口）**：deploy/k8s/07-backup.yaml（静态 PV dap-backup-pv→NFS /home/k8s-data/nfs/dap-backup + CronJob dap-backup-daily 每日 03:30 Asia/Shanghai）。已验证：手动 Job succeeded，产物 dap-20261031.sql = 20,372,407 字节 / 155 条 INSERT / 16 表全量含 DDL。恢复路径：空库执行该 .sql（COPY→INSERT 转换器经字节级回归）。实现教训：① CRDB information_schema 只暴露当前连接库——cockroach sql 必须带 -d dap（defaultdb 下查询返回空，曾致 BACKUP_TOO_SMALL 52B）；② nfs-client 动态供给在本集群从未工作（provisioner 无 pod），用静态 PV；③ jupyter 镜像默认用户 jovyan(1000) 无 NFS 写权限，CronJob 需 runAsUser: 0。

## CRDB secure 化路径（2026-10-31，数据库专用账号任务遗留项）

现状（2026-10-31 实测）：
- 三节点 `cockroachdb-a/b/c`（infra 命名空间）启动进程均含 `--insecure`（`/proc/1/cmdline` 实测）
- `cockroach sql --insecure -e "SELECT 1"` 实测通过 → 无认证体系，CREATE USER 无认证意义
- 影响：CRDB 无账号隔离，平台库 `dap` 直连无认证

目标路径（需 secure 模式重建，属集群级变更）：
1. 生成证书：`cockroach cert create-ca/node/client --certs-dir=/cockroach/certs --ca-key=...`
2. 证书入 K8s Secret，挂载到 StatefulSet pod（tls.crt/tls.key/ca.crt）
3. 启动参数移除 `--insecure`，改 `--certs-dir=/cockroach/certs`
4. 重建前先 `cockroach backup`（dap 库快照）；secure 化后以 root client cert 建账号：`CREATE USER dap_app` + `GRANT ALL ON DATABASE dap TO dap_app`，客户端证书按节点/应用分发
5. 服务侧切换：`DAP_DB_WRITE_DSN` / `DAP_DB_READ_DSN` 改为 `postgres://dap_app:<pw>@cockroachdb.infra:26257/dap?sslmode=verify-full&sslrootcert=<ca>`，写入 `dap-secret`
6. 验证：`cockroach sql --certs-dir ... -e "SELECT 1"`；应用 pod 实测读写；`cockroach auth-session`/pg 端口证书握手确认
7. 回滚：保留 insecure 状态的 STS yaml 备份与数据快照，切换失败回滚 insecure 部署

DEFERRED 原因（如实记录）：insecure 模式下创建用户无认证意义；secure 化需重建 CRDB 集群、协调证书分发与服务重启窗口，属集群级变更，超出本任务（账号最小改动）授权范围，须与集群管理员共同排期。

## 已知风险与遗留（R5 收口，2026-10-31，详见 TEST-REPORT §R5）
| 项 | 状态 | 说明 |
|---|---|---|
| DB 专用账号 | DEFERRED | CRDB 实测 `--insecure`（无认证体系），secure 化路径与回滚已成文于上节，须集群管理员共同排期 |
| 备份 CronJob | DEFERRED v2-r14 | 需协调 nfs 容量；CRDB/Milvus 重建路径见备份策略表 |
| bundle manualChunks | **已修（工作区）** | vite manualChunks 落地，`npm run build` 实测主包 35KB + echarts/vendor-antd 独立 chunk（原单包 1.68MB）；dist 待随 v2-r14 发布 |
| bcrypt | **已修（工作区）** | `dap_core/passwords.py` bcrypt(rounds=12)+遗留 sha256 回退；gateway login / init_db 已接线；存量用户回退路径兼容登录，写回需 init_db 重跑；镜像待 v2-r14 |
| Ingress TLS | **已落地** | `dap-tls` secret + ingress 443 实测，内部 CA（CN=dataagent-platform-ca），有效期至 2027-10-31；遗留续期与 CA 根分发 |
| SSE token in URL | **known-issue 已标注** | EventSource 不支持自定义 Header，JWT 走 `?token=`（泄露面：代理日志/Referer）；长期方案 HttpOnly Cookie 或一次性短 TTL ticket——`web/console/src/api.ts` streamRun 注释已记录 |
| 多轮对话 | **已修（工作区）** | 前端「追问上一题」`[上下文]` 注入 + worker `_strip_context_suffix` 防模板污染；E2E 未重跑；镜像待 v2-r14 |
| DAG 图形化 | DEFERRED（补录） | ETL DAG 仅 JSON/表格查看，需 X6/ReactFlow 类可视化，产品排期 |
| 审计 full_sql | **已修（工作区）** | `tools/main.py` 三处 audit detail 含 `full_sql` 前 2000 字符；镜像待 v2-r14 |

> v2-r14 发布提醒：工作区修复（bcrypt / full_sql / 多轮对话 / manualChunks / api.ts 注释）均**尚未部署**——gateway/tools/worker 仍运行 v2-r13 系镜像，需 TAG 递增走 `TAG=v2-r<N+1> bash scripts/deploy.sh`。
