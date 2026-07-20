# 零兼容硬切 — 设计规格

> 状态：待用户审阅  
> 日期：2026-07-20  
> 范围：`backend/`、`frontend/src/`、`drama-skills/`  
> 实施路径：契约先行、分层硬切（方案 2）

## 1. 背景与决策

仓库内存在多类「向后兼容 / 历史双读 / 别名兜底」逻辑：API 双字段、条件语言别名、`artifact_normalize` 字段与形状改写、题材 `fallback.yaml`、重型 JSON 修复与 LLM 二次纠错等。产品要求**全部移除**，运行时只认现行契约。

已确认决策：

| 决策点 | 选择 |
|--------|------|
| 清理深度 | **C**：零容忍全清（含条件语言统一、文档残留、题材 fallback） |
| 已落库旧数据 | **硬切**：不写迁移；旧形状直接失败 |
| `genres/fallback.yaml` | **删除**；未匹配题材规则 → 硬错误 |
| JSON 修复 | **最小集**：标准 JSON + 尾逗号；删 prose 抽取、单引号修复、LLM `json_repair` |
| 实施路径 | **方案 2**：Skills/契约 → Runtime → API/前端 → 测试收紧 |

## 2. 目标与非目标

### 目标

1. 每个业务概念只保留**一个正式名**；禁止 `A or B` 双读。
2. LLM 输出形状不符合 schema → 任务失败，不做静默别名/形状改写。
3. 题材规则仅 `genres/matrix.yaml`；无有效 theme 解析路径则报错。
4. 删除专为 BC 存在的测试；新增硬切断言测试。
5. Skills validator 防止已删兼容路径回潮（如 `fallback.yaml`）。

### 非目标

- 不做 DB / artifact 自动数据迁移。
- 不改写已入库的 Django migration 历史文件。
- 不引入新第三方库。
- 不删除「OpenAI 兼容」协议表述、审计历史模型、分数历史等产品语义。
- 不删除 i18n 标签兜底、`ApiError.fallbackMessage`、通用 KV 展示组件等非契约 BC。
- Manifest 内部字段 `bundle_version`（skills 包版本）保留；仅删除 API→前端对旧字段名 `bundle_version` 的回退。

## 3. 命名单一真相（SSOT）

| 概念 | 唯一正式名 | 禁止 |
|------|------------|------|
| 交付项（参数 / 条件 / 投影 / 落库） | `deliverables` | `delivery_items`；双读 |
| 外部评测文件名 | `source_filename` | `filename` |
| 外部评测正文 | `script_content` | `content` |
| Skills 包版本（API→前端） | `skills_bundle_version` | 前端回退读 `bundle_version` |
| Prompt 必填路径 | `schema_required_paths` | 顶层 `schema_required` 列表 |
| Artifact 版本 | 整数 `schema_version` | `*.v1` 字符串（保持现状） |
| 题材规则文件 | 仅 `genres/matrix.yaml` | `genres/fallback.yaml` |
| Identity 文档 | 现行 enum（含 `returning-elite`） | `dual-lead` |

### 3.1 `deliverables` 统一细则

- `contracts/parameters.yaml` 参数名保持 `deliverables`。
- `workbench/workbench.yaml`：`persist_path` → `creation_preferences.deliverables`；表单字段 key 与 `parameter_ref` 对齐为 `deliverables`。
- `runtime_projection` / `enable_when` / `module_enable_context`：只读 `deliverables`。
- 前端 settings / types：只认 `creation_preferences.deliverables`。
- 硬切：仅存 `delivery_items` 的旧项目设置不自动回读。

## 4. Runtime 硬切

### 4.1 `artifact_normalize`：兼容层 → 合成补全层

**删除**

- 字段别名（如 `open_hook`→`opening_hook`、`want`→`surface_desire`、合规/质检别名）。
- 形状改写（对象→`string[]`、曲线对象折叠、中文段落→结构化 `continuity_summary`）。
- 历史落库还原（`str(dict)` / JSON 字符串）。
- 十分制→百分制自动缩放。
- 「待补充 xxx」类缺省占位填充。

**保留**

- 从 `settings` / `matrix_synthesis` 写入 schema 要求且非 LLM 职责的字段（如 `theme_code`、`matrix_key`、`rule_params`）。
- 类型守卫：非预期根类型直接失败。

管线：`parse → normalize（薄）→ schema validate → substance gate`。

### 4.2 JSON 解析最小集

| 保留 | 删除 |
|------|------|
| 整段 markdown 围栏剥离 | `extract_json_object`（prose 抽取） |
| `json.loads` | 单引号修复 |
| 一次尾逗号替换后再 `loads` | `build_json_repair_user_prompt` 与 generation 中 LLM `json_repair` 二次调用 |

解析失败直接抛错；progress **不再**发起 repair 相位（删除 `json_repair` / `json_repair_ok` 相关路径）。

### 4.3 题材加载

- 删除 `drama-skills/foundation/rules/genres/fallback.yaml`。
- `validate_skills`：`genres/` 仅允许 `matrix.yaml`。
- `_resolve_theme_code`：有 `genre_matrix` → `"matrix"`；否则须有能映射到已存在规则文件的 `preset_theme_code`；空/无匹配 → 显式错误。
- 更新 `knowledge-sections.md`、`tier2-genre-rules.md`、README 等引用。

## 5. API / 前端表面

### 5.1 后端

- 外部评测 Serializer / views / `job_payload`：只认 `source_filename`、`script_content`。
- `prompt_builder`：只注入 `schema_required_paths`。
- `condition_eval.module_enable_context`：只读 `creation_preferences.deliverables`。
- skills_loader 选项导出：禁止 `id or code` 猜测式双读，对齐契约单一键。

### 5.2 前端

- `domain.ts`：去掉 `filename` / `content` 及重复交付字段。
- `LlmLogsPage`：删除未用 `mode`；`App.tsx` 仅保留 `/admin/llm/logs`，删除 `/admin/llm/chains`。
- `workbenchDefinition`：只读 `skills_bundle_version`。
- 修复稿 `ArtifactViews`：只渲染 `episodes[]`；删除扁平 `content` / `script_content` / `polished_text` 路径。
- `conditions.ts` / `modules.ts`：条件键统一 `deliverables`。

## 6. Skills / 文档

- 全库 `enable_when`、projection、workbench persist 对齐 `deliverables`。
- 清除 `dual-lead`（`theme-matrix.yaml` tag、`output-schemas.md` 等）。
- 保留 `DEPRECATED_TOKENS` 与「禁止重引 `artifact-chunk-map.yaml`」等**防回潮守卫**（非运行时兼容）。
- `EVOLUTION_LOG` 追加「零兼容硬切」记录。

## 7. 测试策略

### 删除或改写

专测 BC 的用例：别名保留、filename 回退、`json_repair` prompt、单引号修复、`delivery_items`→ctx 双读等。

### 新增硬切断言

1. 仅有旧键（如 `delivery_items`）时条件不成立 / 不投影。
2. 非法 JSON、散文夹 JSON → 解析失败。
3. 无 `genre_matrix` 且无有效 preset → 加载失败。
4. alias 键进入 normalize 后 → schema 失败。
5. 外部评测只接受新字段名。
6. `validate_skills`：仅 `matrix.yaml`。

### 回归顺序

Skills 校验 → backend 单测 → frontend 单测 → 关键烟（可选）。

## 8. 分层实施顺序（方案 2）

1. **Skills/契约**：删 fallback、统一 `deliverables`、清 `dual-lead`、更新 validator。
2. **Runtime**：瘦身 normalize、JSON 最小集、题材硬错误、去掉 LLM repair。
3. **API/前端**：双字段/双路由/旧 UI 路径清理。
4. **测试**：删 BC 用例、补硬切断言。

每层测试通过后再进入下一层。

## 9. 风险与接受标准

### 风险

- 现有项目 settings / artifact 若含旧键或旧形状，生成与展示会失败（已接受）。
- LLM 偶发松散输出将更高频率直接失败（以契约与 prompt 收紧补偿，不靠 normalize 兜底）。

### 接受标准

- 全仓无运行时「为兼容旧契约」的双读/别名路径（防回潮 validator 除外）。
- `genres/` 仅 `matrix.yaml`；无 fallback 文件。
- 无 LLM `json_repair` 二次调用；JSON 仅围栏 + loads + 尾逗号。
- 相关单测与 `validate_skills` 全绿。
