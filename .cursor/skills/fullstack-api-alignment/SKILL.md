---
name: fullstack-api-alignment
description: 为停留在 v1.0 的 React 前端制定与迭代后 Django+DRF 后端对齐的分阶段适配方案，覆盖 URL/入参/响应/分页/错误码/枚举/鉴权差异审计与兼容改造。适用于用户提出前后端版本对齐、接口兼容迁移、分页错误适配或低风险 API 层迭代修复时使用。
---

# Fullstack API Alignment

## 项目基础信息

1. 整体架构：前后端分离，后端 Django + DRF，前端 React + TailwindCSS + clsx + tailwind-merge + framer-motion + sonner + echarts-for-react
2. 版本差异问题：
   - 前端目前停留在 v1.0 旧版本代码
   - 后端已经经过多轮迭代升级：接口路径、请求入参结构、返回体格式、字段命名、分页规则、鉴权逻辑、业务枚举、数据模型均存在大量变更
   - 前端大量接口请求、数据解析逻辑仍适配老版后端，出现接口报错、字段缺失、赋值异常、分页错乱、页面渲染异常、业务功能不可用等兼容问题

## 本次需求目标

请你输出一套「前端 v1.0 对齐新版后端」完整适配改造方案，低风险、可分步迭代改造，不推翻重写前端整体架构，最大程度复用现有页面、组件、业务逻辑，完成前后端版本对齐。

## 适用场景

当用户提出以下需求时使用本技能：

- 梳理前后端接口差异清单（URL、入参、响应、分页、错误码、枚举、鉴权）。
- 制定全局请求层一次性适配方案（axios 拦截、分页封装、错误提示、Token）。
- 规划 `services/` 或 `src/api` 分层迭代改造步骤与回归测试。
- 直接执行兼容性修改（仅限请求层、解析层、常量/类型层）。
- 制定接口对接规范，防止前后端再次脱节。

与其他技能的分工：

- **本技能**：前后端版本对齐、兼容性适配，不改 UI/交互/业务流程。
- [fullstack-refactor-plan](../fullstack-refactor-plan/SKILL.md)：架构分层、目录重构、Service 抽取。
- [fullstack-ui-standardization](../fullstack-ui-standardization/SKILL.md)：纯样式规范化，禁止改接口。
- [fullstack-cleanup-audit](../fullstack-cleanup-audit/SKILL.md)：废弃文件清理，禁止改接口契约。
- [fullstack-legacy-compat-removal](../fullstack-legacy-compat-removal/SKILL.md)：过渡结束后删除兼容层。
- [fullstack-testing](../fullstack-testing/SKILL.md)：对齐完成后的契约回归验证。

## 硬性约束

1. 只做兼容性修改，不改动原有页面布局、UI、交互逻辑、业务流程。
2. 改动尽量收敛在 api 请求层、数据解析层，避免大面积修改页面内部 JSX。
3. 提供典型修改示例代码，方便批量套用修改其余接口。
4. 给出 Git 分支管理策略，支持分批提交、出错可回滚。
5. 禁止为了对齐随意引入新第三方库；优先复用现有 `request`、`adapters`、`constants`。
6. 禁止私自修改后端接口或数据库；发现后端缺陷应单独标注，不在对齐 PR 中夹带。

## 分析前置步骤

输出方案或动手改代码前，必须先读取实际项目，禁止凭猜测列接口：

1. 定位应用根目录（如 `ScriptForge/frontend`、`ScriptForge/backend`）。
2. 读取前端请求入口：`services/http.js` 或 `utils/request.ts`、`services/api.js`。
3. 读取适配层：`services/adapters/`、`hooks/useFormErrors.js` 等数据转换工具。
4. 读取常量/枚举：`services/constants/errorCodes.js`、`businessEnums.js`、类型定义目录。
5. 批量扫描业务接口文件：`services/*.js`、`services/admin/`、`src/api/`（以项目实际目录为准）。
6. 读取后端契约来源：`config/urls.py`、`apps/*/urls.py`、ViewSet/Serializer、OpenAPI/Swagger（如有）、`tests/` 中的接口用例。
7. 抽样对比 3–5 个高频页面（列表、详情、表单提交）的调用链：页面 → service → 拦截器 → 后端。

差异排查命令与清单模板见 [REFERENCE.md](REFERENCE.md#一差异梳理思路)。

## 输出要求

用户要「方案」时，必须按以下四段结构完整输出：

### 1. 差异梳理思路

给出前后端接口比对排查方法，批量找出：

- URL 变更
- 请求方式变更
- 入参字段增减/重命名
- 响应结构层级改动
- 分页参数变更
- 状态码/错误码体系改动
- 枚举值定义变动
- 鉴权规则变更清单

输出差异总表（模板见 REFERENCE）。

### 2. 全局底层适配改造方案（优先改动，一次性全局生效）

1. 统一 axios 请求拦截、响应拦截适配新版后端返回格式
2. 全局分页、通用请求参数封装改造
3. 全局错误码、异常提示、Sonner 报错提示逻辑适配后端新规范
4. 全局鉴权、Token 处理、跨域相关逻辑对齐后端最新规则

### 3. 分层迭代改造执行步骤（按优先级排序）

```
步骤1：底层请求工具全局适配改造 + 自测基础连通性
步骤2：公共枚举、常量、类型定义批量对齐后端最新字段
步骤3：逐个模块业务接口文件（services/ 或 src/api）批量修改请求参数、解析逻辑
步骤4：对应页面、组件修正数据取值代码，修复渲染报错
步骤5：全流程功能回归测试方案，验证前后端交互全部正常
```

每步必须附带：改动范围、验证方法、回滚点、完成判定标准。详细 checklist 见 [REFERENCE.md](REFERENCE.md#三分层迭代改造执行步骤)。

### 4. 配套编码约束

- 改造完成后制定接口对接规范，避免后续前后端版本再次脱节。
- 给出接口同步核对常态化机制。

规范模板见 [REFERENCE.md](REFERENCE.md#五配套编码约束与常态化机制)。

## 当用户要求「直接执行适配」时

1. 先完成差异总表（至少覆盖用户指定模块 + 全局底层）。
2. **严格按步骤顺序**：步骤1 未验证通过，不进入步骤3。
3. 每次只改一个业务域或一类接口（如 `works`、`auth`、`admin/billing`）。
4. 优先在 `adapters/` 做字段映射，避免页面层散落 `?.` 链式兜底。
5. 页面层改动仅限：字段名取值修正、分页字段名、枚举显示映射；禁止改 JSX 结构。
6. 每批次改完立即跑 lint/build，并执行该模块冒烟用例。
7. 全部完成后输出：变更摘要、残留差异、待后端确认项。

## 典型改造模式（优先复用）

| 层级 | 项目常见路径 | 职责 |
|------|-------------|------|
| HTTP 客户端 | `services/http.js` | 拦截、解包 `{code,data,message}`、401 刷新、429 |
| 列表适配 | `services/adapters/listAdapter.js` | 统一 `pagination` / `items` |
| 业务适配 | `services/adapters/businessAdapters.js` | 蛇形→前端字段、枚举翻译 |
| 业务接口 | `services/{domain}.js` | URL、params、调用 adapter |
| 常量枚举 | `services/constants/` | 与后端 TextChoices 对齐 |
| 错误提示 | `utils/userError.js` + `sonner` | 按 `err.code` 映射文案 |

改造前后代码对照见 [REFERENCE.md](REFERENCE.md#二全局底层适配改造方案)。

## Git 分支策略（摘要）

```
main
 └── feat/api-alignment          # 集成分支
      ├── feat/api-alignment/http-base
      ├── feat/api-alignment/enums
      ├── feat/api-alignment/works
      └── feat/api-alignment/auth
```

- 每步独立分支，小步 commit；格式：`fix(api): align works list pagination with v2 backend`。
- 单步失败用 `git revert <commit>`，禁止在同一分支上 force push。
- 详细策略见 [REFERENCE.md](REFERENCE.md#四git-分支管理策略)。

## 详细参考

- 差异排查、全局适配、示例代码、分步 checklist、Git 策略、对接规范：[REFERENCE.md](REFERENCE.md)
