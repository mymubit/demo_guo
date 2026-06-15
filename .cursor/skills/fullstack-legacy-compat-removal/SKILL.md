---
name: fullstack-legacy-compat-removal
description: 在 Django+DRF 后端迁移完成后，清理前端过渡兼容代码（旧响应体、双版本分页解析、fallback 分支、旧路由与 re-export 别名），仅保留 v2 API 逻辑。适用于用户提出移除 legacy 兼容、清理双版本适配器、删除旧导出别名或批量重构 api/adapters 时使用。
---

# Fullstack Legacy Compat Removal

## 项目基础信息

前后端分离项目：React + TailwindCSS 前端，Django+DRF 后端；

当前改造进度：

1. 作品列表已封装统一列表适配器，同时兼容后端两种返回结构：新版 `{data, pagination}` 分页格式、旧版 `{items}` 结构；
2. 创作模块接口已迁移至新版路由 `/api/creation/fusion/*`、`/api/creation/agents/catalog/`，`task_id` / `project_id` 新旧字段兼容逻辑收拢在适配器内；
3. works 作品分页、订单模块、会员模块均编写了双版本兼容适配代码，并且为了不破坏原有页面导入，保留了大量旧导出名称做过渡；
4. 全项目存在大量这类「新旧接口、新旧字段、新旧返回体、新旧路由、新旧导出名」的过渡兼容逻辑，目前过渡周期完成，不再需要兼容旧版后端结构。

## 本次核心需求

全面清理项目内所有新旧兼容过渡代码，**彻底移除旧分支判断、旧结构兼容、旧路由兜底、旧字段映射、旧导出别名**，只保留全新版接口逻辑、新版返回结构解析、新版字段定义、新版路由地址，最终实现：

1. 列表适配器：删除对旧 `{items}` 格式的兼容判断，仅适配后端标准返回 `{data, pagination}`，精简适配器冗余分支；
2. 创作模块：移除 `task_id` / `project_id` 新旧兼容映射逻辑，业务直接使用新版字段，删除适配器内旧字段兜底赋值代码；
3. works 分页逻辑：删除双格式判断解析代码，只编写针对 `{data, pagination}` 的解析逻辑，消除页面因双结构判断带来的冗余、隐患；
4. 订单、会员模块：剔除所有旧接口兼容分支、旧参数兼容、旧返回解析逻辑，完全对齐新版接口定义；
5. 删除所有为过渡兼容预留的旧导出别名，统一全部 import 导入路径与导出名称，清理冗余中转导出；
6. 全局检索其余散落的接口、组件、工具类中的新旧 if 判断、兜底赋值、分支兼容代码，一并剔除清理。

## 硬性约束

1. 最终只保留稳定新版业务逻辑，不能影响现有新版功能正常运行，保证页面渲染、分页、提交、查询、提交进度上报、数据存取完全正常；
2. 梳理每一处删除兼容的改动点，逐条说明原兼容逻辑作用、删除原因、改动后逻辑说明；
3. 若存在多处依赖联动改动，给出修改顺序，防止改完出现导入报错、数据取值 undefined、分页失效问题；
4. 改动完成后，顺带整理接口与数据解析统一规范，避免后续再次出现新旧两套兼容写法；
5. 不改动全局基础公共组件，仅清理业务层、接口层、适配器层过渡兼容代码。

用户会分批提供对应适配器、api 文件、页面组件代码，针对性逐条重构清理冗余兼容逻辑。

## 适用场景

当用户提出以下需求时使用本技能：

- 过渡周期结束，删除前端对旧版后端的全部兼容分支。
- 清理 `listAdapter`、`businessAdapters`、各模块 `services/*.js` 中的双结构/双字段判断。
- 移除 `api.js` 及 barrel 文件中的旧导出名、re-export 别名。
- 分批重构用户粘贴的适配器、API、页面代码，只保留新版契约。

与其他技能的分工：

- **本技能**：删除过渡兼容，只保留新版接口/字段/返回体；可改 adapter、service、业务页面取值。
- [fullstack-api-alignment](../fullstack-api-alignment/SKILL.md)：对齐阶段**新增**兼容层，不改 UI。
- [fullstack-cleanup-audit](../fullstack-cleanup-audit/SKILL.md)：废弃文件/目录清理，**禁止**改接口契约。
- [fullstack-refactor-plan](../fullstack-refactor-plan/SKILL.md)：架构分层与目录重构，非专项去兼容。
- [fullstack-testing](../fullstack-testing/SKILL.md)：去兼容后的定向回归用例。

## 工作原则

1. **先读再删**：必须读取用户提供的文件 + 全项目引用扫描，禁止凭记忆删分支。
2. **契约以新版后端为准**：`{ code, message, data, pagination }`、StandardPagination 字段、新版路由与字段名；不确定时读 backend View/Serializer/tests。
3. **自下而上删**：HTTP 解包 → listAdapter → businessAdapters → domain services → 页面取值 → 删除 barrel 别名并批量改 import。
4. **单批单域**：每次只处理用户指定的一批文件或一个业务域（如 works、orders、creation）。
5. **删后必验**：改完跑 lint/build；列表查分页、详情查字段、表单查提交与进度轮询。
6. **不动全局基础 UI**：`components/ui/*`、通用 Layout、主题、全局 axios 壳层仅去掉明确标注的 legacy 分支，不做视觉或交互重构。

## 分析前置步骤

动手前必须完成：

1. 定位前端根目录（如 `ScriptForge/frontend/src`）。
2. 读取 `services/http.js` 的 `parseResponse` 及拦截器，标记 legacy 分支。
3. 读取 `services/adapters/listAdapter.js`、`businessAdapters.js`。
4. 读取目标域 `services/{domain}.js` 与用户粘贴的页面/组件。
5. 对拟删符号做引用扫描（见 [REFERENCE.md](REFERENCE.md#引用扫描与遗留模式检索)）。
6. 对照后端：`apps/common/pagination.py`、对应 `urls.py`、View/Serializer。

## 推荐修改顺序（防联动断裂）

```
步骤0：确认本批文件的新版契约（后端或 OpenAPI）
步骤1：listAdapter / http 解包 — 去掉 items/无 code 等旧分支
步骤2：businessAdapters — 去掉 task_id↔project_id、蛇形双读等
步骤3：domain services — 只保留新版 URL、params、解析
步骤4：页面/业务组件 — 字段取值对齐新版，去掉双结构判断
步骤5：删除 barrel 旧别名 — 全局 rg 替换 import
步骤6：lint/build + 本域冒烟
```

同一批内**禁止**先删 barrel 别名再改实现；**禁止** adapter 与页面同时大改却不跑 build。

## 输出要求

### 用户粘贴代码要求「清理兼容」时

每批必须输出：

#### 1. 改动清单（逐条）

| # | 文件 | 原兼容逻辑 | 删除原因 | 改动后逻辑 | 风险 |
|---|------|-----------|---------|-----------|------|

#### 2. 本批修改顺序

说明为何按此顺序，以及跨文件依赖（谁 export、谁 import）。

#### 3. 代码变更

直接提交最小 diff；注释仅解释非显而易见的业务约束。

#### 4. 验证

- 执行的命令（lint/build）
- 本批影响的功能点手工检查项

#### 5. 批次末：统一规范摘要（首次批次可详、后续可简）

列表、详情、提交、进度四类接口的标准写法（见 REFERENCE）。

### 用户要「全盘方案」时

输出：遗留模式检索计划、分域批次建议、Git 分支策略、规范模板；**不**在用户未提供文件前臆改全库。

## 典型删除目标（摘要）

| 层级 | 常见路径 | 删除内容 |
|------|---------|---------|
| HTTP | `services/http.js` | 无 `code` 直返、`pagination` 内嵌双形态兜底 |
| 列表 | `services/adapters/listAdapter.js` | `result.items`、`Array.isArray(result)` 旧列表 |
| 业务 | `services/adapters/businessAdapters.js` | `task_id \|\| project_id`、HTML/快照双字段读 |
| 接口 | `services/*.js` | 旧 URL、旧 query、双版本 parse |
| 聚合 | `services/api.js`、`admin/index.js` | `export X as Y`、default 聚合仅服务于旧 import |
| 页面 | `pages/**`、`components/creation/**` | 本地双结构判断、旧字段 fallback |

删除前后对照与 grep 命令见 [REFERENCE.md](REFERENCE.md)。

## Git 分支策略（摘要）

```
main
 └── chore/remove-legacy-compat
      ├── chore/compat/http-list-adapter
      ├── chore/compat/creation
      ├── chore/compat/works-orders-membership
      └── chore/compat/export-aliases
```

- 每域独立分支，小步 commit：`refactor(api): drop legacy items pagination in works`。
- 单步失败用 `git revert`；禁止 force push main。

## 详细参考

- 检索命令、删除模式对照、改动清单模板、接口规范：[REFERENCE.md](REFERENCE.md)
