# Fullstack Cleanup Audit — 详细参考

## 引用扫描方法

对每条「待删除/待移动/待重命名」候选，至少执行以下检查：

### 后端（Django）

```bash
# 文件名/模块名引用
rg -l "模块名或文件名" backend/ --glob '!**/__pycache__/**' --glob '!**/migrations/**'

# URL 注册
rg "path\(|router\.|include\(" backend/config backend/apps

# INSTALLED_APPS / 中间件 / Celery task
rg "模块名" backend/config

# 动态导入
rg "importlib|__import__|getattr" backend/
```

### 前端（React）

```bash
# 静态 import / 动态 import
rg -l "组件名或文件名" frontend/src/

# 路由懒加载
rg "lazy\(|createBrowserRouter|Route" frontend/src/

# 构建配置 alias
rg "alias|resolve" frontend/vite.config.* frontend/webpack.config.*
```

### 通用

```bash
# CI / Docker / 脚本引用
rg "文件名" .github/ scripts/ docker-compose* Makefile package.json

# Git 追踪状态
git log --oneline -5 -- 路径
git ls-files 路径
```

**判定规则**：

- 零引用 + 非路由/非迁移/非 env → 倾向 🟢
- 仅测试/fixture 引用 → 🟡，确认测试是否仍有效
- 被 urls / router / INSTALLED_APPS / CI 引用 → 🔴

---

## 分步执行与校验

### Phase 0：先核对确认

**目标**：冻结清单，标记基线，确认高危项。

**操作**：

1. 创建分支：`git checkout -b chore/cleanup-audit-YYYYMMDD`
2. 记录基线 commit：`git rev-parse HEAD`
3. 输出四类清单，提交为「盘点文档」或 PR 描述（不改动代码）
4. 列出所有 🔴 项，等待用户逐条确认

**校验**：

- [ ] 清单覆盖 backend / frontend / scripts / CI / docs
- [ ] 每条删除项有引用扫描结果
- [ ] 用户已确认所有 🔴 项

**回滚**：直接切回主分支，无代码变更。

---

### Phase 1：小批量删除

**目标**：清理 🟢 项，少量 🟡 项。

**操作顺序**（每批 ≤10 个文件）：

1. `frontend/dist/`、`backend/**/__pycache__/`、`*.pyc`、`.cache/`、日志文件
2. 明确废弃的 `*.bak`、`*.old`、`tmp/` 内容
3. 注释掉的大段死代码（优先删整块，不删业务分支）
4. `package.json` / `requirements.txt` 中零引用的依赖

**每批校验**：

```bash
# 后端
cd backend && python manage.py check
cd backend && python manage.py test --keepdb -v1  # 或项目惯用测试命令

# 前端
cd frontend && npm run build
cd frontend && npm run lint  # 若有
```

**回滚**：

```bash
git checkout -- 本批路径
# 或
git revert HEAD
```

---

### Phase 2：迁移归类

**目标**：代码归位，不改逻辑。

**归类规则**：

| 代码特征 | 后端目标 | 前端目标 |
|----------|----------|----------|
| 纯函数、无 IO | `apps/{app}/utils/` 或 `common/utils/` | `utils/` 或 `features/{domain}/utils/` |
| 业务编排、事务 | `apps/{app}/services.py` | `features/{domain}/services/` |
| 复杂只读查询 | `apps/{app}/selectors.py` | `features/{domain}/hooks/` + service |
| 权限判断 | `apps/{app}/permissions.py` | 路由 meta + 权限组件 |
| HTTP 请求 | — | `services/modules/` |
| 可复用 UI | — | `components/common/` |
| 页面入口 | — | `pages/` |
| 领域组件 | — | `features/{domain}/components/` |

**每批校验**：

```bash
# 确认无残留旧路径 import
rg "旧路径片段" backend/ frontend/src/

# 启动验证
cd backend && python manage.py runserver --noreload  # 冒烟
cd frontend && npm run dev  # 冒烟
```

**回滚**：`git revert` 整批 commit；禁止手改 half-migrated 状态。

---

### Phase 3：统一重命名

**目标**：文件、导出符号、引用一致。

**操作**：

1. 先重命名文件/目录
2. 更新所有 import / export
3. 更新路由、测试、文档中的路径
4. 布尔变量补 `is/has/can/should` 前缀（仅在同文件或小范围批次内）

**每批校验**：

```bash
rg "旧名称" backend/ frontend/src/  # 应为零或仅 CHANGELOG 残留
npm run build && python manage.py test
```

**回滚**：Git revert；重命名批次必须独立 commit。

---

### Phase 4：逐轮自测

**目标**：确认功能与启动无回归。

**后端冒烟清单**：

- [ ] `manage.py check` 通过
- [ ] 迁移无 pending：`showmigrations` 无 `[ ]` 新增异常
- [ ] 核心 API 抽样：`/api/v1/` 下登录、列表、详情各 1 个
- [ ] Admin / Celery（若有）可启动

**前端冒烟清单**：

- [ ] 生产构建成功
- [ ] 登录 / 登出 / 401 跳转
- [ ] 核心页面路由可访问（含懒加载 chunk）
- [ ] 控制台无新增 import 404

**回滚策略**：

- 单批 revert → 全量 tag 回退：`git checkout baseline-tag`

---

## 长期命名与目录规约

### 后端 Django

#### 目录

```text
backend/
├── config/                 # 项目配置，不含业务
│   └── settings/           # base / dev / prod 分环境
├── apps/{domain}/          # 业务 app，单 app 单职责
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── services.py         # 写操作、事务、编排
│   ├── selectors.py        # 复杂读查询
│   ├── permissions.py
│   ├── filters.py
│   ├── tasks.py
│   ├── tests/
│   └── migrations/         # 仅 Alembic/Django 迁移，禁放业务脚本
├── common/                 # 跨 app 通用能力
└── scripts/                # 一次性/运维脚本，禁 import 进 runtime
```

#### 文件命名

| 类型 | 规范 | 示例 |
|------|------|------|
| Python 模块 | `snake_case.py` | `workspace_service.py` |
| 测试 | `test_{模块}.py` | `test_workspace_service.py` |
| 管理命令 | `{verb}_{noun}.py` | `seed_membership.py` |
| 迁移 | Django 自动生成，禁手改表结构 |

#### 符号命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 变量 / 函数 | `snake_case` | `get_active_project` |
| 类 | `PascalCase` | `WorkspaceService` |
| 常量 | `UPPER_SNAKE_CASE` | `MAX_RETRY_COUNT` |
| 布尔 | `is_/has_/can_/should_` 前缀 | `is_active` |
| 私有 | `_leading_underscore` | `_validate_payload` |
| Model 字段 | `snake_case`，FK 带 `_id` 后缀可选 | `created_at` |
| URL name | `kebab-case` 或 `snake_case` 统一一种 | `project-list` |
| API 路径 | 复数名词，`/api/v1/projects/` | 不改现有路径 |

#### 分层禁令

- View：禁写 >20 行业务逻辑 → 下沉 `services.py`
- Serializer：禁调用外部 API、禁事务 → 仅校验与序列化
- Model：禁跨 app 复杂查询 → 用 `selectors.py`

---

### 前端 React

#### 目录

```text
frontend/src/
├── app/                    # 入口、Provider、Router
├── pages/                  # 路由级页面，薄层
├── features/{domain}/      # 领域模块
│   ├── components/
│   ├── hooks/
│   ├── services/
│   └── utils/
├── components/
│   ├── common/             # 无业务耦合
│   └── layout/
├── services/
│   ├── http/               # client、拦截器、错误码
│   └── modules/            # 按后端 resource 分文件
├── hooks/                  # 全局通用 hooks
├── utils/
├── constants/
├── types/                  # TS 项目
└── assets/
```

#### 文件命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 组件 | `PascalCase.jsx/tsx` | `ProjectWorkspace.jsx` |
| Hook | `use{Name}.js/ts` | `useProjectList.js` |
| Service | `{resource}Service.js` | `creationService.js` |
| 工具 | `camelCase.js` | `formatDate.js` |
| 常量 | `camelCase.js` 或 `{domain}Constants.js` | `errorCodes.js` |
| 样式模块 | `{Component}.module.css` | 与组件同名 |
| 测试 | `{name}.test.jsx` | 与源文件同目录或 `__tests__/` |

#### 符号命名

| 类型 | 规范 | 示例 |
|------|------|------|
| 组件 | `PascalCase` | `PostScriptPanel` |
| 函数 / 变量 | `camelCase` | `fetchProjectList` |
| 常量 | `UPPER_SNAKE_CASE` | `API_BASE_URL` |
| 布尔 state/props | `is/has/can/should` | `isLoading` |
| 事件处理 | `handle` + 动作 | `handleSubmit` |
| 回调 props | `on` + 动作 | `onSubmit` |
| 自定义 Hook | `use` + 名词 | `useWorkspace` |
| CSS 类 | `kebab-case` 或 Tailwind 工具类 | 不混用多种方案 |

#### 分层禁令

- Page：禁直接拼 API 路径 → 用 `services/modules`
- 组件：禁 >300 行不拆分 → 抽子组件 + Hook
- 通用组件：禁 import 业务 service

---

## 配置文件精简指南

### 后端 `settings/`

| 检查项 | 动作 |
|--------|------|
| 重复定义 | 合并到 `base.py`，环境文件只覆盖差异 |
| 未读取的键 | grep 全项目引用后删除 |
| 硬编码密钥 | 迁到环境变量，保留 `.env.example` 占位 |
| 废弃 APP | 从 `INSTALLED_APPS` 移除前确认无迁移依赖 |

### 前端构建配置

| 检查项 | 动作 |
|--------|------|
| 未使用的 alias | 删除 |
| 重复 proxy 规则 | 合并 |
| 过期 plugin | 移除并验证 build |
| `.env*` | 只保留 `.env.example` 入仓，本地/生产不入库 |

### 依赖

```bash
# Python：对比 import 与 requirements
pipdeptree  # 可选，查孤儿包

# Node：查未使用依赖（需按需安装 depcheck）
npx depcheck frontend/
```

删除依赖前确认：CI、脚本、构建插件链无引用。

---

## 常见可删模式（ScriptForge 类项目）

| 模式 | 示例路径 | 条件 |
|------|----------|------|
| 前端构建产物 | `frontend/dist/` | 在 `.gitignore` 中，可删可重建 |
| Python 缓存 | `**/__pycache__/`, `*.pyc` | 始终 🟢 |
| IDE | `backend/.idea/` | 应 gitignore，🟢 |
| 日志 | `backend/logs/*.log` | 非运行时锁定，🟢 |
| 临时目录 | `backend/tmp/` | 确认无脚本依赖，🟡 |
| 重复 skills 副本 | 多份相同 SKILL.md | 保留 `.cursor/skills/` 权威副本 |

**禁止删除（默认 🔴）**：

- `migrations/`（除合并冲突垃圾文件）
- `.env`、生产密钥
- `nginx/` 部署配置（未确认环境前）
- 被 `urls.py` / 前端 router 注册的模块

---

## 输出示例片段

### 删除项示例

| 路径 | 类型 | 风险等级 | 删除理由 | 引用扫描结果 |
|------|------|----------|----------|--------------|
| `frontend/dist/` | 构建产物 | 🟢 | Vite 可重建 | 无源码 import |
| `backend/tmp/old_seed.py` | 过期脚本 | 🟡 | 注释标注 deprecated | 仅 docs 引用 |

### 移动项示例

| 原路径 | 目标路径 | 风险等级 | 归类逻辑 | 需同步更新的引用 |
|--------|----------|----------|----------|------------------|
| `apps/creation/views.py` 内 `build_prompt()` | `apps/creation/services/prompt_service.py` | 🟡 | 业务编排下沉 service | `views.py`, `tests/test_views.py` |

### 重命名示例

| 范围 | 原名 | 规范名称 | 风险等级 | 命名依据 |
|------|------|----------|----------|----------|
| 组件 | `projectWksp` | `ProjectWorkspace` | 🟡 | React PascalCase |
| 函数 | `get_data` | `getProjectData` | 🟢 | camelCase + 领域前缀 |
