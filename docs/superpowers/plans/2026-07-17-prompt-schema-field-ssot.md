# Prompt/Schema 共用字段表 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让 LLM 输出契约以 JSON Schema 为唯一字段表：prompt 自动注入「嵌套必填路径 + 写死键名的最小合法示例」，减少靠 `artifact_normalize` 事后打补丁。

**Architecture:** 在 `drama-skills` 的 schema 之上新增纯函数 `schema_prompt_contract`：递归抽取 required 路径、从 schema/`valid-artifacts.json` 生成紧凑示例。`PromptBuilder` 输出契约段改为注入该表与示例；CI/单测保证示例能过 Schema 校验，且 prompt 含 `opening_hook`/`surface_desire` 等嵌套键。归一化层保留为兜底，但试点产物（`story_bible`、`narrative_plan`）以「先说对键名」为主。

**Tech Stack:** Django + `apps.drama.services.prompt_builder` / `skills_loader`；JSON Schema Draft 2020-12（`drama-skills/schemas/artifacts/*/1.schema.json`）；pytest / Django TestCase；Vitest 不涉及（本计划后端为主）。

## Global Constraints

- 禁止为对齐字段引入新第三方库；只用标准库 `json` + 现有 `SchemaValidator` / `SkillsBundleLoader`。
- Schema 文件仍是机器 SSOT：`drama-skills/schemas/artifacts/<key>/1.schema.json`；不得手写第二份字段清单作为权威源。
- Prompt 注入的示例必须能通过对应 artifact schema 校验（`additionalProperties: false` 时不得含多余键）。
- 试点范围仅 `story_bible` + `narrative_plan`；其他产物只接通用注入管道，不强制改 fewshot/SKILL。
- 中文备注可存在于 prompt 旁注，但 JSON 键名必须与 schema 完全一致（如 `opening_hook`，不是「开场钩子」）。
- 归一化（`artifact_normalize.py`）本计划不删除，只加测试证明「schema 合法输出无需依赖别名也能过」；禁止扩大别名表作为本计划主交付。
- 代码注释与测试说明默认中文；commit message 用英文 conventional 前缀（`feat:` / `test:`）。

---

## File Structure

| 文件 | 职责 |
|------|------|
| `backend/apps/drama/services/schema_prompt_contract.py` | **新建**：从 JSON Schema 抽取必填路径 + 生成/裁剪最小示例 |
| `backend/apps/drama/services/prompt_builder.py` | 调用上者，替换薄弱的 `_output_schema_hints` / 顶层-only `schema_required` |
| `backend/apps/drama/tests/test_schema_prompt_contract.py` | **新建**：契约抽取与示例校验单测 |
| `backend/apps/drama/tests/test_prompt_schema_injection.py` | **新建**：PromptBuilder 对两个试点角色的注入断言 |
| `drama-skills/roles/drama-episode-designer/SKILL.md` | 标准输出要求补英文键名 |
| `drama-skills/roles/drama-story-bible/SKILL.md` | 人物/结构输出要求补英文键名（若缺失） |
| `drama-skills/roles/drama-story-bible/fewshots.v1.yaml` | 至少一个完整合法 `output`（或改为引用 fixture 片段） |
| `drama-skills/knowledge/output-schemas.md` | 加「由 schema 生成/须与 schema 一致」警告；修正明显漂移说明（可选小改） |

```text
JSON Schema (SSOT)
       │
       ▼
schema_prompt_contract.extract_required_paths()
schema_prompt_contract.build_output_skeleton()
       │
       ▼
PromptBuilder「## 输出契约」
  - 必填路径表（含嵌套）
  - 最小合法 JSON 示例（键名写死）
       │
       ▼
LLM  → parse → normalize(兜底) → schema validate
```

---

### Task 1: Schema → 必填路径抽取器

**Files:**
- Create: `backend/apps/drama/services/schema_prompt_contract.py`
- Test: `backend/apps/drama/tests/test_schema_prompt_contract.py`

**Interfaces:**
- Consumes: `dict` JSON Schema（Draft 2020-12 object）
- Produces:
  - `extract_required_paths(schema: dict[str, Any], *, max_paths: int = 80) -> list[str]`
  - 路径格式：`opening_hook` 顶层用字段名；嵌套用点号，数组项用 `[]`，例如 `episode_narrative_designs[].opening_hook`、`characters[].arc.start`

- [ ] **Step 1: Write the failing test**

```python
# backend/apps/drama/tests/test_schema_prompt_contract.py
from django.test import SimpleTestCase

from apps.drama.services.schema_prompt_contract import extract_required_paths


class ExtractRequiredPathsTests(SimpleTestCase):
    def test_narrative_plan_includes_nested_opening_hook(self) -> None:
        schema = {
            "type": "object",
            "required": ["episode_narrative_designs"],
            "properties": {
                "episode_narrative_designs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["episode", "opening_hook", "ending_hook"],
                        "properties": {
                            "episode": {"type": "integer"},
                            "opening_hook": {"type": "string"},
                            "ending_hook": {"type": "string"},
                        },
                    },
                }
            },
        }
        paths = extract_required_paths(schema)
        self.assertIn("episode_narrative_designs", paths)
        self.assertIn("episode_narrative_designs[].opening_hook", paths)
        self.assertIn("episode_narrative_designs[].ending_hook", paths)

    def test_story_bible_includes_character_arc_start(self) -> None:
        schema = {
            "type": "object",
            "required": ["characters"],
            "properties": {
                "characters": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "surface_desire", "arc"],
                        "properties": {
                            "name": {"type": "string"},
                            "surface_desire": {"type": "string"},
                            "arc": {
                                "type": "object",
                                "required": ["start", "end"],
                                "properties": {
                                    "start": {"type": "string"},
                                    "end": {"type": "string"},
                                },
                            },
                        },
                    },
                }
            },
        }
        paths = extract_required_paths(schema)
        self.assertIn("characters[].surface_desire", paths)
        self.assertIn("characters[].arc.start", paths)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python manage.py test apps.drama.tests.test_schema_prompt_contract.ExtractRequiredPathsTests --settings=config.settings.test -v2`  
（若本地无 Postgres，可用已验证可跑通的 `DJANGO_SETTINGS_MODULE=config.settings.local` + 直接 `python -c` 导入；CI 环境用 test settings。）

Expected: `ImportError` 或 `ModuleNotFoundError: schema_prompt_contract`

- [ ] **Step 3: Write minimal implementation**

```python
# backend/apps/drama/services/schema_prompt_contract.py
from __future__ import annotations

from typing import Any


def extract_required_paths(
    schema: dict[str, Any],
    *,
    max_paths: int = 80,
) -> list[str]:
    """递归抽取 JSON Schema required 路径（含数组 items）。"""
    paths: list[str] = []
    _walk_object(schema, prefix="", out=paths, max_paths=max_paths)
    # 去重且保持稳定顺序
    seen: set[str] = set()
    ordered: list[str] = []
    for path in paths:
        if path not in seen:
            seen.add(path)
            ordered.append(path)
    return ordered[:max_paths]


def _walk_object(
    schema: dict[str, Any],
    *,
    prefix: str,
    out: list[str],
    max_paths: int,
) -> None:
    if len(out) >= max_paths:
        return
    if not isinstance(schema, dict):
        return
    required = schema.get("required") or []
    props = schema.get("properties") if isinstance(schema.get("properties"), dict) else {}
    for key in required:
        key_s = str(key)
        path = f"{prefix}.{key_s}" if prefix else key_s
        out.append(path)
        if len(out) >= max_paths:
            return
        child = props.get(key_s)
        if isinstance(child, dict):
            _walk_node(child, prefix=path, out=out, max_paths=max_paths)


def _walk_node(
    schema: dict[str, Any],
    *,
    prefix: str,
    out: list[str],
    max_paths: int,
) -> None:
    if len(out) >= max_paths:
        return
    schema_type = schema.get("type")
    if schema_type == "object" or "properties" in schema or "required" in schema:
        _walk_object(schema, prefix=prefix, out=out, max_paths=max_paths)
        return
    if schema_type == "array" or "items" in schema:
        items = schema.get("items")
        if isinstance(items, dict):
            _walk_node(items, prefix=f"{prefix}[]", out=out, max_paths=max_paths)
```

- [ ] **Step 4: Run test to verify it passes**

Run: same as Step 2  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/apps/drama/services/schema_prompt_contract.py backend/apps/drama/tests/test_schema_prompt_contract.py
git commit -m "$(cat <<'EOF'
feat: extract nested required paths from artifact JSON Schema

EOF
)"
```

---

### Task 2: Schema → 最小合法输出骨架

**Files:**
- Modify: `backend/apps/drama/services/schema_prompt_contract.py`
- Modify: `backend/apps/drama/tests/test_schema_prompt_contract.py`
- Read-only: `drama-skills/build/fixtures/artifacts/valid-artifacts.json`
- Read-only: `apps.core.schema_validator.SchemaValidator` + `SkillsBundleLoader`

**Interfaces:**
- Consumes: artifact schema dict；可选 `fixture: dict[str, Any]`（来自 valid-artifacts）
- Produces:
  - `build_output_skeleton(schema: dict[str, Any], *, fixture: dict[str, Any] | None = None, max_chars: int = 3500) -> dict[str, Any]`
  - 规则：优先用 fixture 裁剪到 schema 允许的键；无 fixture 时按 type 填占位（string→短中文占位，integer→1，array→单元素，object→递归 required）
  - `render_contract_block(artifact_key: str, schema: dict, *, fixture: dict | None, max_chars: int = 3500) -> str`：返回可拼进 system prompt 的 Markdown 文本

- [ ] **Step 1: Write the failing test**

```python
from django.test import override_settings, SimpleTestCase

from apps.core.schema_validator import SchemaValidator
from apps.drama.services.schema_prompt_contract import build_output_skeleton
from apps.drama.services.skills_loader import SkillsBundleLoader
from apps.drama.tests.helpers import FIXTURES, SKILLS_ROOT


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class BuildOutputSkeletonTests(SimpleTestCase):
    def test_narrative_plan_skeleton_validates(self) -> None:
        loader = SkillsBundleLoader()
        schema = loader.load_artifact_schema("narrative_plan")
        skeleton = build_output_skeleton(
            schema, fixture=FIXTURES["narrative_plan"]
        )
        self.assertIn("opening_hook", skeleton["episode_narrative_designs"][0])
        SchemaValidator().validate_file(
            skeleton, "schemas/artifacts/narrative_plan/1.schema.json"
        )

    def test_story_bible_skeleton_uses_surface_desire_not_want(self) -> None:
        loader = SkillsBundleLoader()
        schema = loader.load_artifact_schema("story_bible")
        skeleton = build_output_skeleton(schema, fixture=FIXTURES["story_bible"])
        char = skeleton["characters"][0]
        self.assertIn("surface_desire", char)
        self.assertNotIn("want", char)
        self.assertIn("start", char["arc"])
        SchemaValidator().validate_file(
            skeleton, "schemas/artifacts/story_bible/1.schema.json"
        )
```

- [ ] **Step 2: Run test to verify it fails**

Expected: `ImportError: cannot import name 'build_output_skeleton'`

- [ ] **Step 3: Write minimal implementation**

在 `schema_prompt_contract.py` 追加（保持可测、可裁剪）：

```python
import json
from copy import deepcopy


def build_output_skeleton(
    schema: dict[str, Any],
    *,
    fixture: dict[str, Any] | None = None,
    max_chars: int = 3500,
) -> dict[str, Any]:
    if fixture is not None:
        skeleton = _prune_to_schema(deepcopy(fixture), schema)
    else:
        skeleton = _synthesize_from_schema(schema)
    # 超长则截断字符串叶节点（保留结构与键名）
    blob = json.dumps(skeleton, ensure_ascii=False)
    if len(blob) > max_chars:
        skeleton = _shrink_strings(skeleton, max_chars=max_chars)
    return skeleton


def render_contract_block(
    artifact_key: str,
    schema: dict[str, Any],
    *,
    fixture: dict[str, Any] | None = None,
    max_chars: int = 3500,
) -> str:
    paths = extract_required_paths(schema)
    skeleton = build_output_skeleton(schema, fixture=fixture, max_chars=max_chars)
    example = json.dumps(skeleton, ensure_ascii=False, indent=2)
    lines = [
        f"- artifact_key: {artifact_key}",
        "- 下列字段名必须原样使用（禁止 want/need/open_hook 等别名键）：",
        "- 必填路径:",
        *[f"  - {path}" for path in paths],
        "- 最小合法示例（键名写死，可改文案不可改键名）:",
        "```json",
        example,
        "```",
        "- 仅输出一个 JSON 对象；不要 markdown 围栏；不要 schema 外字段。",
    ]
    return "\n".join(lines)


def _prune_to_schema(value: Any, schema: dict[str, Any]) -> Any:
    # object: 只保留 properties 中的键；补齐 required 缺失
    # array: 对 items schema 处理每个元素，至少保留 1 个（若 minItems）
    # 实现时按 schema type 分支；additionalProperties=false 时删除未知键
    ...


def _synthesize_from_schema(schema: dict[str, Any]) -> Any:
    # string -> "示例"
    # integer -> 1
    # number -> 1
    # boolean -> True
    # enum -> enum[0]
    # object -> {req: synthesize(prop)}
    # array -> [synthesize(items)] * max(minItems or 1, 1) 并尊重 maxItems
    ...
```

实现注意：
- `story_bible.series_structure.six_stage_structure` 的 `minItems/maxItems=6` 必须生成恰好 6 项。
- `hook_grade` 等 enum 必须取 schema 允许值。
- `_prune_to_schema` 若 fixture 缺 `opening_hook`，用 `_synthesize_from_schema` 对该字段补齐，而不是留下缺口。

- [ ] **Step 4: Run test to verify it passes**

Expected: PASS（两个骨架均通过 SchemaValidator）

- [ ] **Step 5: Commit**

```bash
git add backend/apps/drama/services/schema_prompt_contract.py backend/apps/drama/tests/test_schema_prompt_contract.py
git commit -m "$(cat <<'EOF'
feat: build schema-valid output skeletons for prompt contracts

EOF
)"
```

---

### Task 3: PromptBuilder 注入完整契约块

**Files:**
- Modify: `backend/apps/drama/services/prompt_builder.py`
- Create: `backend/apps/drama/tests/test_prompt_schema_injection.py`
- Read-only: `SkillsBundleLoader.get_output_artifact_by_role` / `load_artifact_schema`

**Interfaces:**
- Consumes: `render_contract_block`；`FIXTURES[artifact_key]`（若存在）
- Produces: `PromptBuilder.build` 的 system_prompt 含嵌套必填路径与示例 JSON；user_prompt.`output.schema_required_paths` 为完整路径列表（替换仅顶层的 `schema_required`）

- [ ] **Step 1: Write the failing test**

```python
from django.test import TestCase, override_settings

from apps.drama.services.prompt_builder import PromptBuilder
from apps.drama.tests.helpers import SKILLS_ROOT, create_project, create_user


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT, LLM_ENABLED=False)
class PromptSchemaInjectionTests(TestCase):
    def setUp(self) -> None:
        self.user = create_user()
        self.project = create_project(self.user)
        self.settings = {
            "title": "玉碎宫门",
            "entry_type": "original_track",
            "episode_count": 40,
            "genre_matrix": {
                "emotion": "ambition",
                "identity": "hidden-elite",
                "conflict": "power",
                "world": "ancient",
            },
        }

    def test_episode_designer_prompt_locks_opening_hook_key(self) -> None:
        system, user = PromptBuilder().build(
            "drama.episode-designer",
            settings=self.settings,
            workflow_state={"current_phase": "episode_design"},
            artifacts={},
        )
        self.assertIn("opening_hook", system)
        self.assertIn("episode_narrative_designs[].opening_hook", system)
        self.assertIn('"opening_hook"', system)  # 示例里的 JSON 键
        self.assertNotIn("必填字段: episode_narrative_designs\n", system)  # 旧的仅顶层提示可消失或并存，但必须有嵌套路径

    def test_story_bible_prompt_locks_surface_desire_and_arc_start(self) -> None:
        system, _user = PromptBuilder().build(
            "drama.story-bible",
            settings=self.settings,
            workflow_state={"current_phase": "blueprint"},
            artifacts={},
        )
        self.assertIn("surface_desire", system)
        self.assertIn("characters[].arc.start", system)
        self.assertIn('"surface_desire"', system)
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL — system prompt 可能只有顶层 `必填字段: episode_narrative_designs`，无 `opening_hook` 路径表

- [ ] **Step 3: Write minimal implementation**

修改 `prompt_builder.py`：

1. 删除或收缩 `_output_schema_hints` 中与 schema 重复的硬编码列表（保留少量「禁止 schema 外字段」等行为约束即可）。
2. 在组装「## 输出契约」处：

```python
from apps.drama.services.schema_prompt_contract import (
    extract_required_paths,
    render_contract_block,
)
from apps.drama.tests.helpers import FIXTURES  # 禁止：测试 helpers 不能被生产代码 import
```

**正确做法：** 在 `skills_loader` 或 `schema_prompt_contract` 增加：

```python
def load_artifact_fixture(loader: SkillsBundleLoader, artifact_key: str) -> dict[str, Any] | None:
    data = loader.load_json("build/fixtures/artifacts/valid-artifacts.json")
    item = data.get(artifact_key)
    return item if isinstance(item, dict) else None
```

然后：

```python
artifact_key = self.loader.get_output_artifact_by_role(role)
schema = self.loader.load_artifact_schema(artifact_key)
fixture = load_artifact_fixture(self.loader, artifact_key)
contract_block = render_contract_block(
    artifact_key, schema, fixture=fixture, max_chars=3500
)
system_parts.extend(["", "## 输出契约", contract_block])
```

User prompt：

```python
"output": {
    "artifact_key": artifact_key,
    "schema_version": schema_version,
    "schema_required_paths": extract_required_paths(schema),
}
```

（可暂时保留 `schema_required` 顶层列表作兼容，但测试以 `schema_required_paths` 为准。）

- [ ] **Step 4: Run test to verify it passes**

Run: `python manage.py test apps.drama.tests.test_prompt_schema_injection -v2`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/apps/drama/services/prompt_builder.py backend/apps/drama/services/schema_prompt_contract.py backend/apps/drama/services/skills_loader.py backend/apps/drama/tests/test_prompt_schema_injection.py
git commit -m "$(cat <<'EOF'
feat: inject nested schema field table and skeleton into role prompts

EOF
)"
```

---

### Task 4: 角色 SKILL 用「中文含义 + 英文键名」对齐

**Files:**
- Modify: `drama-skills/roles/drama-episode-designer/SKILL.md`
- Modify: `drama-skills/roles/drama-story-bible/SKILL.md`（标准输出/人物字段段）
- Test: `backend/apps/drama/tests/test_prompt_schema_injection.py`（可追加：skill 文本经 loader 进入 prompt 后仍含键名——Task 3 已覆盖；本任务加文件内容断言或文档级检查）

**Interfaces:**
- Consumes: schema 字段名（人工抄写到 SKILL，须与 Task 2 路径一致）
- Produces: 人类可读职责说明不再只写「集首钩子」而不写 `opening_hook`

- [ ] **Step 1: Write the failing test**

```python
from pathlib import Path
from django.test import SimpleTestCase
from apps.drama.tests.helpers import SKILLS_ROOT


class SkillKeyAlignmentTests(SimpleTestCase):
    def test_episode_designer_skill_mentions_opening_hook_key(self) -> None:
        text = (
            Path(SKILLS_ROOT) / "roles/drama-episode-designer/SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("`opening_hook`", text)
        self.assertIn("`ending_hook`", text)
        self.assertIn("`paywall_hook`", text)

    def test_story_bible_skill_mentions_surface_desire_key(self) -> None:
        text = (
            Path(SKILLS_ROOT) / "roles/drama-story-bible/SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("`surface_desire`", text)
        self.assertIn("`deep_need`", text)
        self.assertIn("`arc.start`", text)  # 或 arc 对象字段说明中的 start
```

- [ ] **Step 2: Run test to verify it fails**

Expected: FAIL — SKILL 目前多为中文「集首钩子」无反引号键名

- [ ] **Step 3: Write minimal implementation**

`drama-episode-designer/SKILL.md` 将「标准输出要求」改为：

```markdown
## 标准输出要求（键名必须与 schema 一致）

- `title`：每集标题
- `core_event`：每集核心事件
- `characters`：出场人物名数组
- `goal_conflict`：Goal × Conflict
- `emotion_intensity`：情绪强度 1–10
- `satisfaction_points`：爽点字符串数组
- `opening_hook`：集首钩子（禁止写成 open_hook / opening）
- `ending_hook`：集末钩子（禁止写成 cliffhanger 顶层键）
- `reversal`：单集反转
- `foreshadowing.setup` / `foreshadowing.payoff`
- `paywall_hook`：付费卡点
- `rhythm_tag`：双轨节奏标注
- `hook_grade`：S|A|B|C
- `emotion_nodes.EV` / `ET` / `TP`
```

`drama-story-bible/SKILL.md` 在人物相关处明确：

```markdown
- 人物欲望字段：`surface_desire`（想要）、`deep_need`（需要）；禁止输出 want/need 作为键名
- 弧光对象：`arc.start` / `arc.turning_point_1` / `arc.turning_point_2` / `arc.end`；禁止 initial/midpoint/final
```

- [ ] **Step 4: Run test to verify it passes**

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add drama-skills/roles/drama-episode-designer/SKILL.md drama-skills/roles/drama-story-bible/SKILL.md backend/apps/drama/tests/test_prompt_schema_injection.py
git commit -m "$(cat <<'EOF'
docs: align role SKILL output checklists with schema field keys

EOF
)"
```

---

### Task 5: Few-shot 至少一个完整合法 output

**Files:**
- Modify: `drama-skills/roles/drama-story-bible/fewshots.v1.yaml`
- Optional Create: `drama-skills/roles/drama-episode-designer/fewshots.v1.yaml`（若 loader 已支持按角色加载；无则跳过 episode fewshot 文件，仅依赖 prompt skeleton）
- Test: `backend/apps/drama/tests/test_schema_prompt_contract.py` 或新建 fewshot 校验测

**Interfaces:**
- Consumes: `FIXTURES["story_bible"]` 结构
- Produces: PromptBuilder fewshot 段出现完整键（至少 SB001）

- [ ] **Step 1: Write the failing test**

```python
import yaml
from pathlib import Path
from django.test import SimpleTestCase, override_settings

from apps.core.schema_validator import SchemaValidator
from apps.drama.tests.helpers import SKILLS_ROOT


@override_settings(DRAMA_SKILLS_ROOT=SKILLS_ROOT)
class StoryBibleFewshotSchemaTests(SimpleTestCase):
    def test_first_fewshot_output_validates(self) -> None:
        path = Path(SKILLS_ROOT) / "roles/drama-story-bible/fewshots.v1.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        output = data["fewshots"][0]["output"]
        # 当前 fewshot 只有 synopsis 局部 → 应先 FAIL，改完后 PASS
        SchemaValidator().validate_file(
            output, "schemas/artifacts/story_bible/1.schema.json"
        )
```

若项目禁止在测试里直接依赖 PyYAML 而 loader 已有解析，改用 `SkillsBundleLoader` 内部加载后取出；以仓库现有 YAML 加载方式为准。

- [ ] **Step 2: Run test to verify it fails**

Expected: Schema validation FAIL（缺 world_rules/characters/…）

- [ ] **Step 3: Write minimal implementation**

将 `fewshots.v1.yaml` 的 **第一个** `output` 替换为从 `valid-artifacts.json` 的 `story_bible` 缩略版（保留全部 required 键；长文本可缩短）。其余 case 可仍为短样例，但在文件头 `note` 写明：「仅 case_id=SB001 为 schema 完整示例；其余为风格示意」。

禁止在 fewshot 中使用 `want`/`initial` 等别名键。

- [ ] **Step 4: Run test to verify it passes**

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add drama-skills/roles/drama-story-bible/fewshots.v1.yaml backend/apps/drama/tests/test_schema_prompt_contract.py
git commit -m "$(cat <<'EOF'
fix: make story-bible primary fewshot a schema-valid full example

EOF
)"
```

---

### Task 6: 文档与归一化边界（收尾）

**Files:**
- Modify: `drama-skills/knowledge/output-schemas.md`（文首 SSOT 说明强化）
- Modify: `backend/apps/drama/tests/test_artifact_normalize.py`（加「已是合法键名时 normalize 不改键」断言，防止回归）
- Modify: （可选）`backend/apps/drama/services/artifact_normalize.py` 顶部 docstring 标明「兜底，非字段 SSOT」

**Interfaces:**
- Consumes: Task 2–5 已稳定的字段名
- Produces: 团队约定——改字段先改 schema，再跑测试；normalize 只做兼容

- [ ] **Step 1: Write the failing test**

```python
def test_normalize_preserves_canonical_opening_hook(self) -> None:
    raw = {
        "episode_narrative_designs": [
            {
                "episode": 1,
                "title": "入宫",
                "core_event": "暗语试探",
                "goal_conflict": "潜伏×暴露",
                "emotion_intensity": 7,
                "opening_hook": "殿前暗语对上",
                "ending_hook": "陆珩未揭穿",
                "satisfaction_points": ["过关"],
                "reversal": "知情不报",
                "paywall_hook": "身份将露",
                "rhythm_tag": "tight",
                "foreshadowing": {"setup": [], "payoff": []},
                "hook_grade": "A",
                "characters": ["沈玉楼"],
                "emotion_nodes": {
                    "EV": {"value": 7},
                    "ET": {"value": 3},
                    "TP": {"content": "暗语试探"},
                },
            }
        ]
    }
    out = normalize_narrative_plan(raw, {"title": "玉碎宫门"})
    self.assertEqual(
        out["episode_narrative_designs"][0]["opening_hook"],
        "殿前暗语对上",
    )
```

（若已有同类测试可扩展而非重复。）

- [ ] **Step 2: Run test** — 若已通过可直接作为回归锁

- [ ] **Step 3: Update `output-schemas.md` header**

```markdown
> **机器 SSOT**：`schemas/artifacts/<artifact_key>/1.schema.json`。
> **Prompt 字段表**：运行时由 `schema_prompt_contract` 从 schema 生成，禁止在 prompt_builder 手写第二份必填清单。
> 本 Markdown 仅供人读；若与 schema 冲突，以 schema 为准。
```

- [ ] **Step 4: Run related tests**

```bash
cd backend
python manage.py test \
  apps.drama.tests.test_schema_prompt_contract \
  apps.drama.tests.test_prompt_schema_injection \
  apps.drama.tests.test_artifact_normalize.NarrativePlanNormalizeTests \
  -v2
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add drama-skills/knowledge/output-schemas.md backend/apps/drama/services/artifact_normalize.py backend/apps/drama/tests/test_artifact_normalize.py
git commit -m "$(cat <<'EOF'
docs: declare schema as sole field SSOT; keep normalize as fallback only

EOF
)"
```

---

## Self-Review

**1. Spec coverage**
- 共用字段表 → Task 1–3（抽取 + 注入）
- 输出示例写死必填键名 → Task 2–3、Task 5
- 减少事后打补丁 → Task 4–6（源头对齐 + normalize 降级为兜底）；不在本计划删除别名映射（YAGNI，保留兼容）

**2. Placeholder scan**
- 已避免 “TBD / 类似 Task N”；Task 2 的 `_prune_to_schema` 在步骤中给出了行为规则与关键约束（六幕数量、enum），实现时按规则写满，不得留空函数体提交。

**3. Type consistency**
- `extract_required_paths` / `build_output_skeleton` / `render_contract_block` / `load_artifact_fixture` 命名在 Task 1–3 一致
- 路径约定统一为 `foo[].bar.baz`
- user_prompt 字段升级为 `schema_required_paths`

**Out of scope（勿膨胀）**
- 重写全部角色 fewshot
- 前端展示文案
- 删除 `normalize_story_bible` / `normalize_narrative_plan` 别名逻辑
- 引入 JSON Schema → Pydantic 代码生成

---

## Manual verification（工程师本地）

1. 重启 Django + Celery。
2. 触发「分集设计」执行，到 LLM 调用日志打开 system prompt，确认含：
   - `episode_narrative_designs[].opening_hook`
   - 示例 JSON 中的 `"opening_hook": ...`
3. 触发「剧本蓝图」，确认含 `surface_desire` 与 `arc.start`，且无把 `want` 当键名的示例。
4. 故意用旧模型若仍漏字段，normalize 仍可兜底；但 prompt 侧不应再教模型写错键名。
