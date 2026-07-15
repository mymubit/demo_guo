#!/usr/bin/env bash
# 本地一键启动：Postgres/Redis 用本机已有服务（或仅起 docker 基础设施），
# 后端 / Celery / 前端在宿主机进程运行，无需整栈 docker。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

EAGER=0
SKIP_FRONTEND=0
INFRA_ONLY=0

usage() {
  cat <<'EOF'
用法: ./scripts/dev-local.sh [选项]

  （默认）起后端 + Celery + 前端；若本机无 Postgres/Redis，则尝试
        docker compose up -d postgres redis

  --eager         同步执行 Celery（不启 worker，适合纯 UI 联调）
  --no-frontend   只起后端（与 Celery，除非 --eager）
  --infra-only    只确保 Postgres/Redis 可用后退出
  -h, --help      显示帮助
EOF
}

for arg in "$@"; do
  case "$arg" in
    --eager) EAGER=1 ;;
    --no-frontend) SKIP_FRONTEND=1 ;;
    --infra-only) INFRA_ONLY=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "未知参数: $arg" >&2; usage >&2; exit 2 ;;
  esac
done

log() { printf '\n==> %s\n' "$*"; }
die() { printf '错误: %s\n' "$*" >&2; exit 1; }

need_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "缺少命令: $1"
}

wait_tcp() {
  local host="$1" port="$2" name="$3" i=0
  while ! (echo >/dev/tcp/"$host"/"$port") >/dev/null 2>&1; do
    i=$((i + 1))
    if [ "$i" -ge 60 ]; then
      die "$name ($host:$port) 未就绪"
    fi
    sleep 1
  done
}

ensure_env() {
  if [ ! -f "$ROOT/backend/.env" ]; then
    log "生成 backend/.env（本地默认）"
    cat >"$ROOT/backend/.env" <<EOF
SECRET_KEY=dev-only-change-me
DEBUG=true
DJANGO_ENV=development
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=scriptforge
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=127.0.0.1
DB_PORT=5432

REDIS_URL=redis://127.0.0.1:6379/0
CELERY_BROKER_URL=redis://127.0.0.1:6379/1
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/2

CORS_ALLOWED_ORIGINS=http://localhost:5173
DRAMA_SKILLS_ROOT=$ROOT/drama-skills

LLM_ENABLED=false
LLM_API_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
EOF
  fi

  # 从 .env 读取关键变量（仅 KEY=VALUE，忽略注释/空行）
  set -a
  # shellcheck disable=SC1091
  source "$ROOT/backend/.env"
  set +a

  export DJANGO_ENV="${DJANGO_ENV:-development}"
  export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings.development}"
  export DRAMA_SKILLS_ROOT="${DRAMA_SKILLS_ROOT:-$ROOT/drama-skills}"
  export DB_HOST="${DB_HOST:-127.0.0.1}"
  export DB_PORT="${DB_PORT:-5432}"
  export DB_NAME="${DB_NAME:-scriptforge}"
  export DB_USER="${DB_USER:-postgres}"
  export DB_PASSWORD="${DB_PASSWORD:-postgres}"
}

ensure_infra() {
  local need_docker=0
  if ! (echo >/dev/tcp/"$DB_HOST"/"$DB_PORT") >/dev/null 2>&1; then
    need_docker=1
  fi
  if ! (echo >/dev/tcp/127.0.0.1/6379) >/dev/null 2>&1; then
    need_docker=1
  fi

  if [ "$need_docker" -eq 1 ]; then
    need_cmd docker
    log "本机 Postgres/Redis 不可用，启动 docker 基础设施"
    if [ ! -f "$ROOT/.env" ]; then
      cp "$ROOT/.env.example" "$ROOT/.env"
    fi
    docker compose up -d postgres redis
    wait_tcp "$DB_HOST" "$DB_PORT" "Postgres"
    wait_tcp 127.0.0.1 6379 "Redis"
  else
    log "检测到本机 Postgres ($DB_HOST:$DB_PORT) 与 Redis (6379)"
  fi

  # 确保业务库存在（失败不致命：可能已有库或权限不足）
  if command -v psql >/dev/null 2>&1; then
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
      -tc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}'" 2>/dev/null \
      | grep -q 1 \
      || PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d postgres \
           -c "CREATE DATABASE ${DB_NAME}" >/dev/null 2>&1 \
      || true
  fi
}

ensure_python() {
  need_cmd python3
  if [ -d "$ROOT/backend/.venv" ] && [ ! -x "$ROOT/backend/.venv/bin/python" ]; then
    log "清理不完整的 venv"
    rm -rf "$ROOT/backend/.venv"
  fi
  if [ ! -d "$ROOT/backend/.venv" ]; then
    log "创建 Python venv"
    python3 -m venv "$ROOT/backend/.venv"
  fi
  # shellcheck disable=SC1091
  source "$ROOT/backend/.venv/bin/activate"
  if [ ! -f "$ROOT/backend/.venv/.deps-ok" ] \
    || [ "$ROOT/backend/requirements.txt" -nt "$ROOT/backend/.venv/.deps-ok" ]; then
    log "安装后端依赖"
    pip install -q --upgrade pip
    pip install -q -r "$ROOT/backend/requirements.txt"
    touch "$ROOT/backend/.venv/.deps-ok"
  fi
}

ensure_frontend() {
  need_cmd npm
  if [ ! -d "$ROOT/frontend/node_modules" ]; then
    log "安装前端依赖"
    npm --prefix "$ROOT/frontend" install
  fi
}

migrate() {
  log "执行数据库迁移"
  (
    cd "$ROOT/backend"
    python manage.py migrate --noinput
  )
}

PIDS=()
cleanup() {
  local pid
  for pid in "${PIDS[@]:-}"; do
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
    fi
  done
  wait >/dev/null 2>&1 || true
}
trap cleanup EXIT INT TERM

start_backend() {
  log "启动 Django http://127.0.0.1:8000"
  (
    cd "$ROOT/backend"
    python manage.py runserver 127.0.0.1:8000
  ) &
  PIDS+=("$!")
}

start_celery() {
  if [ "$EAGER" -eq 1 ]; then
    export CELERY_TASK_ALWAYS_EAGER=true
    log "Celery eager 模式（进程内同步执行，不启 worker）"
    return
  fi
  log "启动 Celery worker"
  (
    cd "$ROOT/backend"
    celery -A config worker -l info
  ) &
  PIDS+=("$!")
}

start_frontend() {
  log "启动前端 http://127.0.0.1:5173"
  (
    cd "$ROOT/frontend"
    # 走 Vite 代理 /api → 后端，避免写死跨域绝对地址
    VITE_API_BASE_URL= npm run dev -- --host 127.0.0.1 --port 5173
  ) &
  PIDS+=("$!")
}

ensure_env
ensure_infra

if [ "$INFRA_ONLY" -eq 1 ]; then
  log "基础设施就绪"
  trap - EXIT INT TERM
  exit 0
fi

ensure_python
migrate
start_celery
start_backend

if [ "$SKIP_FRONTEND" -eq 0 ]; then
  ensure_frontend
  start_frontend
fi

cat <<EOF

本地开发已启动
$([ "$SKIP_FRONTEND" -eq 0 ] && echo '  前端: http://127.0.0.1:5173' || echo '  前端: （已跳过）')
  后端: http://127.0.0.1:8000
  健康: http://127.0.0.1:8000/health/
  技能: $DRAMA_SKILLS_ROOT
$([ "$EAGER" -eq 1 ] && echo '  Celery: eager（同步）' || echo '  Celery: worker 已启动')

Ctrl+C 结束全部进程。首次登录可另开终端执行:
  cd backend && source .venv/bin/activate && python manage.py createsuperuser
EOF

# 任一子进程退出则整体退出（兼容无 wait -n 的 bash）
while true; do
  for pid in "${PIDS[@]}"; do
    if ! kill -0 "$pid" >/dev/null 2>&1; then
      wait "$pid" >/dev/null 2>&1 || true
      exit 1
    fi
  done
  sleep 1
done
