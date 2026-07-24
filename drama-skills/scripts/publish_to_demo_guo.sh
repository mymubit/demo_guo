#!/usr/bin/env bash
# 将本目录 drama-skills 复制推送到独立仓库 demo_guo 的 drama-skills 分支。
# 用法（在 ScriptForge 根目录或任意位置）：
#   ./drama-skills/scripts/publish_to_demo_guo.sh
# 可选环境变量：
#   DEMO_GUO_REPO_URL  默认 https://github.com/mymubit/demo_guo.git
#   DEMO_GUO_BRANCH    默认 drama-skills
set -euo pipefail

SKILLS_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
REPO_URL="${DEMO_GUO_REPO_URL:-https://github.com/mymubit/demo_guo.git}"
BRANCH="${DEMO_GUO_BRANCH:-drama-skills}"
WORKDIR="$(mktemp -d)"
trap 'rm -rf "$WORKDIR"' EXIT

echo "==> 校验技能库"
python3 "$SKILLS_ROOT/tools/validators/validate_all.py"

if ! git ls-remote "$REPO_URL" HEAD &>/dev/null; then
  echo "错误: 无法访问远程仓库 $REPO_URL"
  echo "请先在 GitHub 创建空仓库 demo_guo（勿初始化 README），再重试。"
  exit 1
fi

echo "==> 准备导出到 $WORKDIR/repo"
mkdir -p "$WORKDIR/repo"
(
  cd "$SKILLS_ROOT"
  tar cf - \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='scripts/publish_to_demo_guo.sh' \
    .
) | (cd "$WORKDIR/repo" && tar xf -)

cp "$SKILLS_ROOT/scripts/publish_to_demo_guo.sh" "$WORKDIR/repo/scripts/publish_to_demo_guo.sh"
chmod +x "$WORKDIR/repo/scripts/publish_to_demo_guo.sh"

cat > "$WORKDIR/repo/.gitignore" <<'EOF'
__pycache__/
*.pyc
.venv/
.DS_Store
EOF

if [[ ! -f "$WORKDIR/repo/REPOSITORY.md" ]]; then
  cat > "$WORKDIR/repo/REPOSITORY.md" <<'EOF'
# demo_guo · drama-skills 分支

本仓库为 ScriptForge `drama-skills/` 的**独立副本**（复制，非迁移）。

- 上游：`mymubit/demo4book` 目录 `drama-skills/`
- ScriptForge 引用：设置 `DRAMA_SKILLS_ROOT` 指向本仓库 clone 路径

## 校验

```bash
python3 tools/validators/validate_all.py
```
EOF
fi

cd "$WORKDIR/repo"

if git ls-remote --heads "$REPO_URL" "$BRANCH" | grep -q "$BRANCH"; then
  echo "==> 拉取已有分支 $BRANCH"
  git init -q
  git remote add origin "$REPO_URL"
  git fetch origin "$BRANCH" --depth=1
  git checkout -B "$BRANCH" "origin/$BRANCH"
else
  if git ls-remote "$REPO_URL" HEAD &>/dev/null; then
    echo "==> 远程仓库存在，创建本地分支 $BRANCH"
    git init -q -b "$BRANCH"
    git remote add origin "$REPO_URL"
  else
    echo "==> 远程仓库为空或不可达，初始化新仓库"
    git init -q -b "$BRANCH"
    git remote add origin "$REPO_URL"
  fi
fi

git add -A
if git diff --cached --quiet; then
  echo "==> 无变更，跳过提交"
else
  git commit -m "chore: 同步 drama-skills 自 ScriptForge $(date -u +%Y-%m-%d)"
fi

echo "==> 推送到 $REPO_URL ($BRANCH)"
git push -u origin "$BRANCH"

echo "==> 完成"
