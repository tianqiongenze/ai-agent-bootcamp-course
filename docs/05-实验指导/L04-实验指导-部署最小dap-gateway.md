# 实验 L04：部署最小 dap-gateway 到课程命名空间

**（实验指导 ｜ 对应学习情境 L04 ｜ 企业站 2 学时 ｜ 实验④）**

| 项 | 内容 |
|---|---|
| 实验类型 | 综合性（部署 + 健康验证） |
| 实验环境 | 课程命名空间 `dap-course-XX`（教师已授权受限写权限）、课程仓库 |
| 分组 | 结对 |
| 提交物 | yaml 清单 + readyz 健康链截图 + 滚动更新回滚证据（步骤 4） |

---

## 一、实验目标

1. 【应用】编写 Deployment/Service/ConfigMap/Secret 四件套清单并部署最小 gateway。
2. 【应用】配置就绪探针打通 `readyz` 健康链，解释"就绪 ≠ 存活"。
3. 【分析】读 dap-v2 生产部署清单（`deploy/k8s/`），指出本实验清单与生产的 3 处差距。

## 二、环境与准备

- 镜像：课程私有仓库 gateway 镜像（教师发放地址与拉取 Secret）。
- 依赖最小化：本实验只部署 gateway + 其健康检查所需 Redis（其余数据基建 L05 再上）。
- 安全须知：Secret 用 K8S Secret 对象，严禁写进 yaml 明文；内部认证头 `x-internal-token` 注入 ConfigMap/Secret 由清单引用。

## 三、实验步骤

### 步骤 1：读生产清单找差距（20′）

阅读 `deploy/Dockerfile.gateway` 与 `deploy/k8s/` 中 gateway 相关清单，记录 3 处"生产有而最小版没有"的机制（如：PDB、NetworkPolicy、反亲和、HPA）。

✓ 验证点：差距清单写入 PR 描述（这就是本实验的"分析"考核点）。

### 步骤 2：编写并部署最小清单（50′）

```yaml
# 关键骨架提示（完整版由学生编写）
# deployment: replicas=1, image(镜像换 tag 部署：镜像更新必须换新 tag，同 tag 覆盖会被 kubelet IfNotPresent 缓存坑)
# readinessProbe: GET /readyz  port=8000  initialDelay=5  period=10
# livenessProbe:  GET /healthz port=8000  —— 两者职责不同，都要写
```

```bash
# 这步在干什么：把本组写的 yaml 清单一次性提交给集群（宿舍管理员开始安排床位）
kubectl -n dap-course-XX apply -f gateway/
# 这步在干什么：实时盯着 Pod 从拉镜像→启动→体检通过的全程（怎么判断对了：状态最终为 Running 且 READY 1/1）
kubectl -n dap-course-XX get pods -w      # 观察启动到 Ready
# 这步在干什么：临时打通一条本地到服务的通道（不出集群也能敲门）
kubectl -n dap-course-XX port-forward svc/gateway 8000:8000
# 这步在干什么：敲 readyz 门问"能接待客人吗"（怎么判断对了：返回 200；若依赖 Redis 未就绪会 503——这正是探针在干活）
curl -s localhost:8000/readyz             # 预期 200
```

✓ 验证点：截图——Pod Ready + `/readyz` 200 + `/healthz` 200。

### 步骤 3：制造一次"假就绪"再修复（20′）

1. 临时把 readinessProbe 改成 `tcpSocket` 仅探测端口（模拟"进程活着但依赖断了"）。
2. 教师侧断开 Redis → 观察 `/readyz` 仍 200（误判就绪）。
3. 恢复为依赖检查版探针，复测——体会 L04 讲义"就绪探针为什么不能只查进程存活"。

✓ 验证点：两次实验现象截图（前后对比）。

### 步骤 4：滚动更新与回滚补测（25′，校内子步骤 4 选做未完成者必做）

对应教学方案 L04 校内实施子步骤 4（选做）。滚动更新＝"餐厅翻台不闭店"：新厨师先到位试菜（readiness 通过）→旧厨师才下班（preStop 排空）→客人全程有饭吃。

```bash
# 这步在干什么：后台不停敲门，验证更新全程服务不断
watch curl -s -H "Host: gw-g0X.dap-course.local" http://10.167.2.175/api/ping
# 这步在干什么：换一批新模板（course-v1.1）的行李箱，逐个替换
kubectl -n dap-course-XX set image deploy/gateway gateway=<课程镜像>:course-v1.1
# 这步在干什么：盯着换箱进度（怎么判断对了：滚动完成且循环 curl 无失败）
kubectl -n dap-course-XX rollout status deploy/gateway
# 这步在干什么：查看历史版本并回滚演练（时光倒流键）
kubectl -n dap-course-XX rollout history deploy/gateway
kubectl -n dap-course-XX rollout undo deploy/gateway
```

✓ 验证点：循环 curl 成功率（应为 100% 或仅个别超时）＋history/undo 输出截图。

### 步骤 5：提交 PR（10′）

- 文件：`labs/L04-gateway-minimal/`（yaml + README 说明差距清单）。

## 四、常见坑与排障

| 现象 | 原因与处置 |
|---|---|
| ImagePullBackOff | 拉取 Secret 未挂或 tag 不存在；`kubectl describe pod` 看 Events |
| 探针一直失败但本地 curl 正常 | 探针路径/端口写错；或依赖了未部署的组件 |
| 镜像更新后集群仍是旧版 | 同 tag 覆盖 + IfNotPresent 缓存；**换新 tag** 是长期约定 |
| 服务间调用 401 | 少了 `x-internal-token` 头；本实验中检查 Secret 注入与引用 |

## 五、提交物与验收标准

| 提交物 | 验收标准 |
|---|---|
| yaml 清单 | 四件套齐全；探针依赖检查版；Secret 无明文 |
| 截图 | Ready + readyz/healthz + 假就绪前后对比 |
| 滚动更新证据 | 循环 curl 成功率 + rollout history/undo 输出 |
| 差距清单 | ≥3 处，准确对应生产清单 |

## 六、诚实清单（提交前必填）

| 未验证/未完成事项 | 原因 | 计划补救 |
|---|---|---|
|  |  |  |
