#!/usr/bin/env bash
# ============================================================================
# sync-from-project.sh — 课程仓库与载体项目 dap-v2 的同步脚本
# 依据《课程标准》§七：dap-v2 更新时，自动将其工程文档证据同步至
# docs/07-项目资源/，实现"课证融通、课随产动"。
#
# 用法：
#   ./scripts/sync-from-project.sh [DAP_V2_DIR]
#   DAP_V2_DIR 默认取 ../dap-v2（相对本仓库根），也可显式传入绝对路径。
#
# 行为：
#   1. 校验 dap-v2 目录与关键文件存在
#   2. 复制 ADR / SAD / TEST-REPORT / RUNBOOK / README / PROGRESS 到
#      docs/07-项目资源/dap-v2工程文档/
#   3. 输出同步清单与文件哈希（md5），便于核对版本
#   4. 只增改不删除（课程仓库中已有文件按源覆盖；课程自建文件不受影响）
# ============================================================================
set -euo pipefail

COURSE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DAP_V2_DIR="${1:-$COURSE_ROOT/../dap-v2}"
DEST_DIR="$COURSE_ROOT/docs/07-项目资源/dap-v2工程文档"

# --- 待同步清单：源相对路径 [ 目标文件名 ] ---
SYNC_MAP=(
  "docs/adr/ADR-001-reuse-shared-infra.md|ADR-001-reuse-shared-infra.md"
  "docs/adr/ADR-002-orchestration-engine.md|ADR-002-orchestration-engine.md"
  "docs/adr/ADR-003-v2-parallel-to-v1.md|ADR-003-v2-parallel-to-v1.md"
  "docs/adr/ADR-004-capacity-honesty.md|ADR-004-capacity-honesty.md"
  "docs/SAD.md|SAD.md"
  "docs/TEST-REPORT.md|TEST-REPORT.md"
  "docs/RUNBOOK.md|RUNBOOK.md"
  "README.md|DAP-v2-README.md"
  "PROGRESS.md|DAP-v2-PROGRESS.md"
)

# --- 关键行业参考资料（课程仓库内固定位置，不随项目变动） ---
REF_DIR="$COURSE_ROOT/docs/07-项目资源/行业参考资料"

echo "==> 课程仓库根：$COURSE_ROOT"
echo "==> 载体项目：  $DAP_V2_DIR"
[ -d "$DAP_V2_DIR" ] || { echo "!! 未找到 dap-v2 目录，请传入路径：$0 /path/to/dap-v2"; exit 1; }

mkdir -p "$DEST_DIR" "$REF_DIR"

CHANGED=0
for entry in "${SYNC_MAP[@]}"; do
  src_rel="${entry%%|*}"; dst_name="${entry##*|}"
  src="$DAP_V2_DIR/$src_rel"; dst="$DEST_DIR/$dst_name"
  if [ ! -f "$src" ]; then
    echo "  [跳过] 源不存在：$src_rel"
    continue
  fi
  if [ ! -f "$dst" ] || ! cmp -s "$src" "$dst"; then
    cp "$src" "$dst"
    echo "  [同步] $src_rel -> docs/07-项目资源/dap-v2工程文档/$dst_name"
    CHANGED=$((CHANGED + 1))
  else
    echo "  [一致] $dst_name"
  fi
done

echo
echo "==> 同步完成：$CHANGED 个文件更新。"
echo "==> 当前证据文档清单（md5 版本指纹）："
( cd "$DEST_DIR" && md5 -r *.md 2>/dev/null || md5sum *.md ) | sed 's/^/    /'

echo
echo "提示：若 dap-v2 的关键指标（评测准确率 / 时延 / 架构）发生变化，请同步复核："
echo "  1. docs/01-课程标准/课程标准.md（能力地图与指标引用）"
echo "  2. docs/03-教学方案/L01（演示指标）与 L03（ADR 数量与结论）"
echo "  3. docs/05-实验指导（实验命令与预期输出）"
echo "  4. 重新执行导出：python3 scripts/build_docs.py（Word/PDF 同步再生成）"
