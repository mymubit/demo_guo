# ScriptForge AI - 短剧剧本创作平台

> **基于AI的专业短剧剧本创作平台，主链角色协作 + 独立质检环，将一句话创意或现成故事快速转化为完整可拍摄的A级剧本体系。**

## ✨ 项目概述

ScriptForge AI 是一个商业化的短剧剧本创作平台，采用「前端 React SPA + 后端 Django 6.0.5」架构。核心功能为 **Drama Skills 工作室**（`/drama`）：4 个主链生产角色（选题定调 → 剧本蓝图 → 分集设计 → 正文创作）+ 3 个质检环独立技能（评分/合规/修复）+ 1 个可选宣发交付工具，支持原创创作与故事改编双通道。

主 API 入口：
- `POST /api/drama/projects/` → `GET /api/drama/projects/<id>/progress/` → `POST .../run/<role_id>/`
- `GET /api/drama/roles/` — 获取角色列表（含部门分组）

技能库位置：`drama-skills/`（完整技能规范 SSOT，可直接复制到 Cursor/Codex/Trae 使用，详见 `drama-skills/README.md`）

---

## 🎯 核心特性

### Drama Skills 创作工作室
- 🎭 **4+3+1 角色体系**：选题定调官、剧本蓝图官、分集设计官、剧本正文官 + 评分/合规/修复质检环 + 宣发交付工具
- ⚡ **双通道创作**：原创创作通道（从零选题）/ 故事改编通道（自带故事、小说、大纲）
- 🎬 **四轴题材矩阵**：情感×身份×冲突×世界观（各 9 项）+ 69 风味标签，覆盖 8 大预设题材与创新组合
- 🔍 **十维质量评分**：格式/叙事/冲突/角色/情感/逻辑/爽点/钩子/付费点/赛道匹配，B 级（75）质检环把关
- 👥 **会员系统**：体验版 / 专业版 / 旗舰版三档套餐
- 💳 **订单与支付**：完整的订单与支付流程
- 📦 **作品管理**：云端保存、分享、多格式导出

### 后台管理
- 📊 **数据仪表盘**：用户/订单/营收/创作核心指标实时展示
- 👤 **用户管理**：用户列表、状态管理、密码重置
- 👑 **会员配置**：套餐管理、卡密生成与兑换
- ⚙️ **技能配置**：AI模型参数、题材模板、钩子库管理（加密存储）
- 💼 **订单管理**：订单查询、退款处理

---

## 🏗️ 技术架构

```
┌────────────────────────────────────────────────────────────┐
│                        前端 (React SPA)                      │
│  React 18 + Vite + TailwindCSS + Framer Motion + Zustand    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────┐
│                    Django 6.0.5 REST API                    │
│   Django REST Framework + JWT + Redis Cache + PostgreSQL     │
└──────────────────────────────┬──────────────────────────────┘
                               │
    ┌──────────────────────────┼──────────────────────────┐
    ▼                          ▼                          ▼
┌─────────┐              ┌──────────┐              ┌─────────┐
│ PostgreSQL │           │   Redis    │           │  MinIO / │
│  主数据库  │            │ 缓存/会话  │            │ 对象存储 │
└─────────┘              └──────────┘              └─────────┘
```

### 技术栈详情

| 层级 | 技术 | 版本 |
|------|------|------|
| **前端** | React | 18.3.1 |
| | Vite | 5.x |
| | TailwindCSS | 3.x |
| | React Router | 6.x |
| | Zustand (状态) | 4.x |
| | Framer Motion (动画) | 11.x |
| **后端** | Django | 6.0.5 |
| | Django REST Framework | 3.15.x |
| | PostgreSQL | 15+ |
| | Redis | 7.x |
| | dj_queue (Django 6 @task) | 0.13.x |
| | JWT (认证) | simplejwt |
| **开发** | Node.js | 18+ |
| | Python | 3.11+ |

---

## 🔐 安全设计（核心竞争力）

### 1. 技能引擎隔离
- 独立 Agent runtime 在 dj_queue worker 中异步执行，Prompt/Knowledge 存 DB
- 技能模板和参数加密存储，仅后台可访问
- AI API密钥 AES-256-CBC 加密，仅在内存解密使用

### 2. 数据暴露控制
- 作品列表/详情/分享页返回预渲染 HTML，不返回完整剧本 JSON
- 工作台 artifact 接口返回 JSON **仅限项目所有者**编辑使用
- 下载接口返回二进制文件流，无 JSON 包装

### 3. 请求签名机制
- 每个 API 请求包含 Timestamp + Nonce + HMAC-SHA256 签名
- 服务端**始终**基于 `request.body` 计算 body hash 验签，不信任客户端 `X-Body-Hash`
- 防重放：Nonce 在时间窗口内不可重复；Redis 不可用时拒绝请求（fail-close）
- 生产环境通过环境变量配置 `API_SIGN_SECRET`；**不应**将长期密钥编译进前端 bundle

### 4. 数字水印
- 导出 Markdown 植入零宽字符水印（`WatermarkService.embed_watermark`）
- 导出 HTML 含可见水印 token，与用户/项目绑定，便于溯源

### 5. 操作审计
- 所有写操作自动记录审计日志
- 记录用户、IP、设备指纹、请求摘要、响应状态
- 审计日志表不可修改，仅 INSERT 权限

---

## 🚀 快速开始

### 环境要求
```
Node.js >= 18
Python >= 3.11
PostgreSQL >= 15
Redis >= 7
```

### 1. 克隆项目

```bash
git clone <repository-url>
cd ScriptForge
```

### 2. 安装依赖

#### 方式一：根目录一键安装

```bash
npm run install:all
```

#### 方式二：分别安装

```bash
# 前端
cd frontend
npm install

# 后端
cd ../backend
pip install -r requirements.txt
```

### 3. 配置环境变量

#### 前端 (frontend/)

无需特殊配置，开发环境默认代理到 `http://localhost:8000`

#### 后端 (backend/)

```bash
cd backend
cp .env.example .env
# 编辑 .env 文件，填入数据库和密钥配置
```

关键配置项（**本机连 Docker 里的 Postgres/Redis**，见 `backend/.env.example`）：
```env
DB_HOST=localhost
DB_PORT=5432
REDIS_URL=redis://:dev_redis_change_me@127.0.0.1:6379/1
CACHE_URL=redis://:dev_redis_change_me@127.0.0.1:6379/2
POSTGRES_PASSWORD=dev_postgres_change_me
REDIS_PASSWORD=dev_redis_change_me
```

独立 Agent 模式下，创作知识/Prompt 已入库，**无需**配置外部技能根目录或挂载旧版资产目录。

### 3.5 启动基础设施（Windows 推荐）

仅 Docker 跑数据库与缓存，应用在本机 Python/Node 跑：

```bash
# 项目根目录
npm run docker:infra
```

### 4. 初始化数据库

```bash
# 项目根目录（需先 npm run docker:infra）
npm run dev:setup
cd backend
python manage.py seed_independent_agents
# 首次从外部资产目录导入知识（仅需一次；导入后可删除仓库外的旧资产目录）
# python manage.py inventory_external_assets --roots <legacy-asset-root-a> <legacy-asset-root-b> --output external_asset_inventory.json
# python manage.py import_agent_assets --inventory tmp/external_asset_inventory.json --commit
# python manage.py verify_agent_assets_import --inventory tmp/external_asset_inventory.json
# python manage.py verify_external_asset_removal --workspace-root ..
python manage.py createsuperuser
```

### 5. 启动开发服务器

#### 方式一：根目录并发启动（推荐）

```bash
# 在项目根目录（前端 + 后端 + dj_queue worker）
npm run dev
# 前端: http://localhost:5173
# 后端: http://localhost:8000
# worker: python manage.py dj_queue --mode async（创作任务异步执行）
```

#### 方式二：分别启动

```bash
npm run docker:infra

# 终端1 - 前端
cd frontend && npm run dev

# 终端2 - 后端
cd backend && python manage.py runserver 0.0.0.0:8000

# 终端3 - 任务 worker（Windows 必须，否则创作只入队不执行）
cd backend && python manage.py dj_queue --mode async
```

#### 全容器部署（生产）

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
# 或：npm run docker:prod
```

---

## 📂 项目结构

```
ScriptForge/
├── frontend/                           # React 前端应用
│   ├── src/
│   │   ├── main.jsx                   # 入口文件
│   │   ├── App.jsx                    # 根组件 + 路由配置
│   │   ├── components/
│   │   │   └── layout/                # 布局组件（MainLayout/AdminLayout）
│   │   ├── pages/                      # 页面组件
│   │   │   ├── Home/                  # 首页（Hero/功能/评价/FAQ/CTA）
│   │   │   ├── Auth/                  # 登录/注册
│   │   │   ├── Member/                # 会员中心
│   │   │   ├── Creation/              # 创作页（4阶段流程）
│   │   │   ├── Works/                 # 我的作品（列表/详情）
│   │   │   ├── Profile/               # 个人中心
│   │   │   ├── ShareView.jsx          # 作品分享页
│   │   │   ├── NotFound.jsx           # 404页面
│   │   │   └── Admin/                 # 后台管理页面
│   │   │       ├── Login.jsx          # 后台登录
│   │   │       ├── Dashboard.jsx      # 数据仪表盘
│   │   │       ├── Users.jsx          # 用户管理
│   │   │       ├── Members.jsx        # 会员配置
│   │   │       ├── SkillConfig.jsx    # 技能引擎配置
│   │   │       └── Orders.jsx         # 订单管理
│   │   ├── services/                  # API 服务层
│   │   │   └── api.js                 # Axios 封装 + 请求签名
│   │   ├── store/                     # Zustand 状态管理
│   │   │   ├── authStore.js           # 用户认证状态
│   │   │   └── memberStore.js         # 会员套餐状态
│   │   └── styles/                    # 全局样式
│   │       └── globals.css            # 自定义工具类
│   ├── index.html                     # HTML 模板
│   ├── vite.config.js                 # Vite 配置
│   ├── tailwind.config.js             # Tailwind 配置
│   └── package.json
│
├── backend/                            # Django 后端应用
│   ├── config/                        # 项目配置
│   │   ├── settings/base.py           # 基础设置
│   │   ├── urls.py                    # 路由配置
│   │   └── wsgi.py                    # WSGI 入口
│   ├── apps/                          # Django 应用模块
│   │   ├── users/                     # 用户模块（自定义User模型）
│   │   │   ├── models.py              # User + UserProfile (加密手机号/邮箱)
│   │   │   ├── serializers.py         # DRF 序列化器
│   │   │   ├── views_auth.py          # 登录/注册/刷新
│   │   │   ├── views.py               # 用户资料
│   │   │   ├── urls_auth.py           # /api/auth/
│   │   │   ├── urls.py                # /api/users/
│   │   │   └── admin.py
│   │   ├── membership/                # 会员模块
│   │   │   ├── models.py              # MembershipPlan/ UserMembership/ PromoCode
│   │   │   ├── services.py            # 会员业务逻辑
│   │   │   ├── serializers.py
│   │   │   ├── views.py               # 套餐列表/会员状态/卡密兑换
│   │   │   ├── urls.py                # /api/members/
│   │   │   └── admin.py
│   │   ├── orders/                    # 订单模块
│   │   │   ├── models.py              # Order + Payment
│   │   │   ├── services.py            # 订单与模拟支付
│   │   │   ├── serializers.py
│   │   │   ├── views.py               # 创建订单/模拟支付/订单列表
│   │   │   ├── urls.py                # /api/orders/
│   │   │   └── admin.py
│   │   ├── creation/                  # 创作模块（独立 Agent 主链路）
│   │   │   ├── models.py              # Project + ProjectFusionArtifact + AgentExecutionRun
│   │   │   ├── agent_runtime/         # 独立 Agent workspace / enqueue / execute
│   │   │   ├── services/submission.py # 提交（仅建项目 + seed brief）
│   │   │   ├── tasks.py               # run_independent_agent（主任务）
│   │   │   └── ...
│   │   ├── skill/                     # 技能配置模块（加密隔离）
│   │   │   ├── models.py              # SkillConfig + ThemeTemplate + HookLibrary
│   │   │   ├── services.py            # 技能配置服务（AES-256加密读/写）
│   │   │   ├── serializers.py
│   │   │   └── admin.py               # 仅超级管理员可访问
│   │   ├── security/                  # 安全模块
│   │   │   ├── models.py              # AuditLog（仅INSERT审计日志）
│   │   │   ├── services.py            # 加密/签名/水印/限流服务
│   │   │   ├── middleware.py          # 签名校验/限流/审计中间件
│   │   │   └── admin.py
│   │   ├── common/                    # 公共工具
│   │   │   ├── pagination.py          # 标准分页
│   │   │   ├── exceptions.py          # 自定义异常与处理器
│   │   │   ├── permissions.py         # 自定义权限类
│   │   │   └── utils.py               # 通用工具函数
│   │   └── admin_panel/               # 后台管理 API
│   │       ├── views.py               # 仪表盘/用户/套餐/配置/订单
│   │       ├── serializers.py
│   │       └── urls.py                # /api/admin/
│   ├── manage.py
│   ├── requirements.txt
│   └── .env.example
│
├── docs/                               # 项目文档
│   ├── PRD.md                         # 产品需求文档
│   ├── CREATION-BUSINESS-ARCHITECTURE.md  # 创作业务与流程架构（当前主链路）
│   └── TECH-ARCHITECTURE.md           # 技术架构文档
│
└── package.json                        # 根目录 NPM 脚本（并发启动）
```

---

## 🎨 UI 设计规范

### 色彩系统
```
主背景色:    #030d24 (navy-950)
次级背景:    #0a1f44 (navy-800)
主色调:      #667eea → #764ba2 (紫蓝渐变)
强调色:      #f6d365 → #fda085 (金色渐变)
文本色:      #ffffff / #e2e8f0
辅助文本:    #a0aec0 / #718096
```

### 组件样式
- **卡片**：`glass-card` - 毛玻璃背景 (backdrop-blur) + 半透明边框
- **按钮**：圆角 `rounded-xl`，悬停上浮 + 发光阴影
- **徽章**：圆角 `rounded-full`，金色边框与文字
- **动画**：Framer Motion 实现的渐入 + 微交互

### 响应式
- 移动端优先，三断点：sm / md / lg
- 移动端导航折叠为汉堡菜单
- 卡片网格在窄屏单列展示

---

## 🔧 API 设计原则

### 路由规范
```
POST /api/auth/login/          # 登录
POST /api/auth/register/       # 注册
POST /api/auth/refresh/        # 刷新 Token
GET  /api/users/me/            # 我的资料
GET  /api/members/plans/       # 套餐列表
POST /api/members/redeem/      # 卡密兑换
POST /api/orders/create/       # 创建订单
POST /api/creation/submit/     # 提交创作
GET  /api/creation/projects/<id>/workspace/  # 独立 Agent 工作台
POST /api/creation/projects/<id>/agents/<agent_id>/run/  # 运行 Agent
GET  /api/creation/progress/<id>/   # 进度查询（部分工具页仍用）
GET  /api/works/               # 作品列表
GET  /api/admin/dashboard/     # 管理仪表盘
...
```

### 请求头签名（安全机制）
每个 API 请求必须包含：
```
Authorization: Bearer <jwt-token>
X-Timestamp: <unix-seconds>
X-Nonce: <16位随机字符串>
X-Signature: HMAC-SHA256(secret, method + path + timestamp + nonce + body_hash)
X-Device-Fingerprint: <设备指纹>
```

### 响应规范
```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

---

## 👥 用户角色与权限

| 角色 | 权限 |
|------|------|
| **游客** | 浏览首页、查看示例、注册/登录 |
| **免费用户** | 体验创作1次，查看个人作品 |
| **付费会员** | 根据套餐等级获得 N 次/无限次创作，下载剧本，分享作品 |
| **企业会员** | 团队协作、API接入、私有模板、独立部署 |
| **管理员** | 管理用户/订单/套餐，查看数据仪表盘 |
| **超级管理员** | 技能引擎配置，修改AI参数/模板（最高权限）|

---

## 独立 Agent 创作流程（当前主链路）

| 步骤 | Agent | 输出产物 | 说明 |
|------|-------|----------|------|
| 0 | submit | project_brief | 提交时直接 seed，非 Agent 运行 |
| 1 | structure | structure_plan | 推荐起点 |
| 2 | character | character_bible | |
| 3 | outline | series_outline | |
| 4 | script | episode_scripts | 可分批 merge |
| 5+ | review / score / marketing 等 | 报告类 artifact | |

用户在工作台手动触发每个 Agent；同一项目同一时间仅允许一个 Agent 运行。运行前可调用 estimate API 查看 token 预估。

> 完整业务流程与分阶段创作架构见 [docs/CREATION-BUSINESS-ARCHITECTURE.md](docs/CREATION-BUSINESS-ARCHITECTURE.md)。`submit` 已 seed `project_brief`，推荐 Agent 运行顺序从 `structure` 起；`brief` Agent 为可选重跑。

---

## 历史架构（Legacy，已非 C 端主路径）

> 以下 7 节点自动流水线、`WorkflowEngine`、`node_index` 工作台接口**已删除或返回 404**；`CreationNode` / `SubSkillExecutionLog` / `CreationTask` / `WorkflowInstance` 等 Legacy 表**已通过迁移删除**。

### 7 节点创作流程（归档）

| 节点 | 名称 | 功能 | 耗时 |
|------|------|------|------|
| 1 | **信息收集** | 提取用户创意，生成项目简报 | 30秒 |
| 2 | **结构规划** | 6阶段架构 + 情绪节奏曲线 + 反转点设计 | 1分钟 |
| 3 | **人设开发** | 主角/反派/配角完整设定 + 关系图谱 | 1分钟 |
| 4 | **大纲撰写** | 每集钩子/反转/悬念设计 + 情绪强度标注 | 2分钟 |
| 5 | **剧本创作** | 逐集生成场景、动作、对话（最耗时节点） | 3-5分钟 |
| 6 | **质量审查** | 格式/节奏/内容/制作四维评分 + 问题清单 | 1分钟 |
| 7 | **输出交付** | 4格式导出 + 植入数字水印 + 生成分享链接 | 30秒 |

**总耗时**：约 8-12 分钟（80集标准项目）

---

## 🔒 后台技能配置（超级管理员专区）

路径：`/admin/skill-config`

### 可配置项

| 分类 | 配置项 | 说明 |
|------|--------|------|
| **AI模型** | `llm.api_endpoint` | 推理服务地址 |
| | `llm.api_key` | API Key（AES-256加密存储）|
| | `llm.temperature` | 生成温度（默认 0.7）|
| | `llm.max_tokens` | 最大 Token 数 |
| **质量审查** | `review.*_weight` | 四维评分权重设置 |
| | `review.pass_threshold` | 通过阈值（默认 70分）|
| **输出** | `export.format_B_template` | 格式模板内容 |
| | `export.enable_watermark` | 是否启用水印 |
| **合规** | `compliance.sensitive_words` | 敏感词列表 |

---

## 📖 文档

- **[创作业务架构](docs/CREATION-BUSINESS-ARCHITECTURE.md)** - 独立 Agent 主链路、Artifact 依赖、分阶段创作与交付闭环
- **[产品需求文档 (PRD)](docs/PRD.md)** - 完整的产品功能规格
- **[技术架构文档](docs/TECH-ARCHITECTURE.md)** - 技术选型与架构设计详解

---

## 🔮 后续扩展方向

- **多语言支持**：英文、日文、韩文界面与出海题材模板
- **小说转剧本**：上传小说自动转化为短剧格式
- **模板市场**：用户可上传/购买优秀剧本模板，分成机制
- **API 开放平台**：企业客户接入自有系统
- **实时协作编辑**：多人协同编辑剧本，版本管理
- **AI续写与精修**：基于已有剧本续写新集数，或修改段落

---

## ⚠️ 安全合规声明

1. 本平台生成内容基于用户输入创意，AI 仅辅助创作，版权归用户所有
2. 剧本文件内置数字水印，可追溯来源，严禁非法传播
3. 技能引擎与模板为核心商业机密，采用多层加密保护
4. 建议对重要项目进行版权登记，平台可辅助生成登记材料

---

## 📝 开发说明

### 常用命令

```bash
# 启动前后端开发服务器（并发）
npm run dev

# 仅前端
cd frontend && npm run dev         # http://localhost:5173

# 仅后端
cd backend && python manage.py runserver 0.0.0.0:8000

# 生产构建前端
npm run build

# 创建 Django 迁移
cd backend && python manage.py makemigrations
cd backend && python manage.py migrate
```

### 开发环境演示

**前端页面**（无需后端也可体验，API失败自动回退Mock数据）：
- 首页 `http://localhost:5173/`
- 登录 `http://localhost:5173/login`
- 会员中心 `http://localhost:5173/member`
- **创作页 `http://localhost:5173/creation`（核心体验页）**
- 作品列表 `http://localhost:5173/works`
- 后台 `http://localhost:5173/admin`

**后端 API**：
- 健康检查 `http://localhost:8000/api/health/`
- 管理后台 `http://localhost:8000/admin/`（Django Admin）

---

## 📞 联系方式

- 商务合作：business@scriptforge.ai
- 技术支持：support@scriptforge.ai
- 创作者社区：community.scriptforge.ai

---

**© 2026 ScriptForge AI. All rights reserved.**
