---
name: fullstack-frontend-alignment-refactor
description: 为停留在 v1.0 的前端制定与新版 Django+DRF 后端对齐的结构性重构方案，覆盖 axios/api 层重塑、类型枚举同步、鉴权刷新、适配器与 hooks 清理。适用于用户提出前端 v1.0 结构重构、API 层重组、适配器迁移或低风险渐进式前端现代化时使用。
---

# Frontend v1.0 结构性重构 + 对齐新版后端

## 项目基础信息

前后端分离项目
后端：Django + DRF，经过多轮迭代演进，接口路由、入参结构、响应体格式、分页规则、错误码体系、鉴权逻辑、数据字段定义、业务枚举、ORM模型字段均有大量更新迭代
前端：React v1.0 旧版本，配套技术栈：TailwindCSS + clsx + tailwind-merge + framer-motion + sonner + echarts-for-react
当前核心问题：前端接口、数据解析逻辑完全适配老旧后端版本，和新版后端严重不兼容，接口报错、数据解析异常、页面渲染失效、业务流程无法正常运行。

## 改造约束规则

1. ✅ **允许对前端业务代码、目录结构、请求架构、状态管理、API分层做合理结构性重塑重构**，优化原有混乱逻辑、解耦冗余代码；
2. ✅ **基础公共组件禁止改动**：项目已封装的全局基础组件（按钮、卡片、输入框、弹窗、分页、通用容器等）保持原有代码、入参、调用方式不变，只允许在业务层适配调用；
3. ❌ 不修改全站UI视觉风格、页面布局排版、用户交互流程、原有业务功能逻辑，不能删减、新增业务需求；
4. ❌ 禁止大规模推倒重写页面，仅做适配+结构性优化改造。

## 与其他技能的分工

| 技能 | 边界 |
|------|------|
| **本技能** | 结构性重构 + 后端对齐；可改 api/hooks/state/adapters，不可改 `@/components/ui` |
| [fullstack-api-alignment](../fullstack-api-alignment/SKILL.md) | 纯兼容适配，改动收敛在请求/解析层，尽量不动页面 JSX |
| [fullstack-refactor-plan](../fullstack-refactor-plan/SKILL.md) | 通用架构重构，不限于版本对齐场景 |
| [fullstack-ui-standardization](../fullstack-ui-standardization/SKILL.md) | 纯样式规范化，禁止改接口 |
| [fullstack-cleanup-audit](../fullstack-cleanup-audit/SKILL.md) | 废弃文件清理，禁止改接口契约 |
| [fullstack-testing](../fullstack-testing/SKILL.md) | 重构后回归用例与上线准入 |
| [fullstack-legacy-compat-removal](../fullstack-legacy-compat-removal/SKILL.md) | 过渡结束后删除兼容层 |

## 分析前置步骤

输出方案或动手改代码前，必须先读取实际项目，禁止凭猜测列接口：

1. 定位前端根目录（如 `ScriptForge/frontend`）与后端根目录。
2. 读取请求入口：`services/http.js` 或 `utils/request.ts`。
3. 扫描 API 分层：`services/*.js`、`src/api/`、散落 `request()` 调用。
4. 识别基础公共组件目录（通常 `@/components/ui/`），标记为**只读禁区**。
5. 读取适配层、常量、类型：`adapters/`、`constants/`、`types/`。
6. 读取后端契约：`urls.py`、ViewSet/Serializer、OpenAPI、`tests/`。
7. 抽样 3–5 条页面调用链：页面 → hook/service → 拦截器 → 后端。

## 输出要求

用户要「方案」时，必须按以下五段结构完整输出：

### 一、前期差异梳理方案

系统化排查前后端差异：URL、请求方式、入参、响应嵌套/字段更名、分页、错误码、Token 鉴权、枚举字典。

输出差异清单（模板见 [REFERENCE.md](REFERENCE.md#一差异清单模板)）。

### 二、底层架构结构性重塑

1. 重构全局 Axios 封装、请求/响应拦截，适配最新返回结构、异常处理、错误码、Sonner 提示。
2. 重构 `src/api`（或 `services/`）按业务模块拆分，消除重复请求，统一入参/出参类型。
3. 统一全局常量、枚举、类型，对齐后端字段，梳理废弃常量。
4. 改造鉴权、Token 刷新、权限判断，匹配后端最新规则。

### 三、业务层分层改造策略

1. 抽离数据处理函数、封装字段映射 adapter，清理冗余 `useEffect`、消除重复请求。
2. 优化组件内数据取值、拆分冗余业务子逻辑；**不得修改基础公共组件本身**。
3. 优化不合理状态管理，精简冗余全局/局部状态，修复数据同步错乱。
4. 提供典型改造前后代码示例（见 [REFERENCE.md](REFERENCE.md#三业务层改造示例)）。

### 四、分批次落地执行步骤

```
步骤1：新建 Git 独立改造分支，备份原始 v1.0，规划回滚策略
步骤2：底层请求架构重构适配，联调基础连通性
步骤3：全局枚举、常量、类型批量对齐后端
步骤4：API 接口文件批量重构适配新版出入参
步骤5：逐个页面/组件修正数据解析逻辑，单模块自测验证
步骤6：全业务流程整体回归测试，整理改动归档文档
```

每步附带：改动范围、验证方法、回滚点、完成判定。详细 checklist 见 [REFERENCE.md](REFERENCE.md#四分批次落地执行步骤)。

### 五、长期规范机制

1. 前后端接口同步对接规范，避免版本再次脱节。
2. 前端接口与数据处理编码规范，约束后续开发写法。

模板见 [REFERENCE.md](REFERENCE.md#五长期规范机制)。

## 当用户要求「直接执行改造」时

1. 先完成差异总表（至少覆盖指定模块 + 全局底层）。
2. **严格按步骤顺序**：步骤2 未验证通过，不进入步骤4/5。
3. 每次只改一个业务域（如 `works`、`auth`、`admin`）。
4. 字段映射优先放在 `adapters/`，业务 hook 次之，页面最后。
5. **`@/components/ui/**` 及等价基础组件目录零改动**；页面仅调整 props 传入值与数据绑定。
6. 禁止改 JSX 布局结构、className 视觉样式、交互事件语义。
7. 每批次改完跑 lint/build + 模块冒烟；输出变更摘要、残留差异、待后端确认项。

## 目标 API 目录结构（参考）

以项目现状为准，渐进迁移而非一次性搬家：

```
src/
├── api/                    # 或保留 services/，二选一为主入口
│   ├── client.ts           # axios 实例 + 拦截器
│   ├── types/              # 请求/响应 TS 类型
│   ├── adapters/           # 字段映射、列表归一化
│   ├── constants/          # 枚举、错误码、分页默认值
│   └── modules/            # 按业务域拆分
│       ├── auth.ts
│       ├── works.ts
│       └── creation.ts
├── hooks/                  # useXxxList、useXxxDetail 等业务数据 hook
└── components/ui/          # 🔒 只读，禁止修改
```

## Git 分支策略（摘要）

```text
main
└── feat/frontend-alignment-refactor
    ├── feat/far/01-backup-and-http
    ├── feat/far/02-enums-types
    ├── feat/far/03-api-works
    └── feat/far/04-pages-works
```

- Commit 格式：`refactor(api): modularize works endpoints and align pagination`
- 单步失败用 `git revert`；禁止 force push 已共享分支。
- 详细策略见 [REFERENCE.md](REFERENCE.md#四git-分支与回滚)。

## 详细参考

- 差异清单、底层重塑、业务层示例、分步 checklist、Git 策略、对接规范：[REFERENCE.md](REFERENCE.md)
