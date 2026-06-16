# -*- coding: utf-8 -*-
"""
扫描硬编码 Prompt 模板并迁移到 AgentSkillDefinition

使用方式：
    python manage.py migrate_hardcoded_hints --dry-run
    python manage.py migrate_hardcoded_hints --execute
    python manage.py migrate_hardcoded_hints --execute --skill-ids brief.project_definition,structure-generator
    python manage.py migrate_hardcoded_hints --execute --force
    python manage.py migrate_hardcoded_hints --execute --scan-root apps/creation/orchestration

扫描策略：
- 默认扫描 apps/creation/orchestration/*_engine.py
- 使用 ast 模块解析 Python 文件，匹配以下命名模式的模块级常量：
    * SYSTEM_PROMPT / SYSTEM_HINT / PROMPT / PROMPT_TEMPLATE / HINTS
    * _SYSTEM_SUFFIX / _PROMPT_SUFFIX / _HINT_SUFFIX（任意业务后缀）
- 解析出 skill_id（从文件名 + 变量名推断；如 brief_engine.py + _BRIEF_SYSTEM → brief.*）
- 写入策略：update_or_create(skill_id=..., defaults={system_hint, lifecycle_status=draft, version=v0.0.1})
- --dry-run：只打印迁移预览，不写入 DB
- --force：强制覆盖已有 system_hint（默认跳过已有记录）

执行后输出：
- 扫描文件数
- 匹配提示词条数
- 实际导入技能数（CREATE / UPDATE / SKIP）
"""
from __future__ import annotations

import ast
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from django.core.management.base import BaseCommand, CommandError

from apps.skill.models import AgentSkillDefinition

logger = logging.getLogger(__name__)

# 默认扫描根目录（相对 backend/）
DEFAULT_SCAN_ROOT = "apps/creation/orchestration"

# 匹配的模块级常量名模式
HINT_VAR_NAME_PATTERNS = (
    re.compile(r"^_?(?P<base>SYSTEM_PROMPT|SYSTEM_HINT|PROMPT|PROMPT_TEMPLATE|HINTS)(?:_(?P<suffix>[A-Z0-9_]+))?$"),
)

# 文件名前缀到 agent 短名的映射（用于推断 skill_id）
_FILE_PREFIX_TO_AGENT = {
    "brief": "brief",
    "world": "world",
    "character": "character",
    "outline": "outline",
    "script": "script",
    "review": "review",
    "polish": "polish",
    "marketing": "marketing",
    "adapt": "adapt",
    "emotion_architect": "emotion",
    "insight": "insight",
    "score": "score",
    "score_quick": "score",
    "pacing_heuristics": "pacing",
    "quality_guard": "quality",
    "plot_structure_review": "plot",
    "agent_detection": "compliance",
    "agent_payload": "agent",
    "llm_node_engine": "llm",
    "llm_tokens": "llm",
    "sub_skill_runner": "sub_skill",
    "sub_skill_orchestrator": "sub_skill",
    "orchestrator": "orchestrator",
}

# 文件名前缀到默认 skill_layer 的映射
_FILE_PREFIX_TO_LAYER = {
    "brief": AgentSkillDefinition.LAYER_BUSINESS,
    "world": AgentSkillDefinition.LAYER_BUSINESS,
    "character": AgentSkillDefinition.LAYER_BUSINESS,
    "outline": AgentSkillDefinition.LAYER_BUSINESS,
    "script": AgentSkillDefinition.LAYER_BUSINESS,
    "review": AgentSkillDefinition.LAYER_QUALITY if hasattr(AgentSkillDefinition, "LAYER_QUALITY") else AgentSkillDefinition.LAYER_FOUNDATION,
    "polish": AgentSkillDefinition.LAYER_FOUNDATION,
    "marketing": AgentSkillDefinition.LAYER_BUSINESS,
    "adapt": AgentSkillDefinition.LAYER_TOOL,
    "emotion_architect": AgentSkillDefinition.LAYER_FOUNDATION,
    "insight": AgentSkillDefinition.LAYER_FOUNDATION,
    "score": AgentSkillDefinition.LAYER_QUALITY if hasattr(AgentSkillDefinition, "LAYER_QUALITY") else AgentSkillDefinition.LAYER_FOUNDATION,
    "pacing_heuristics": AgentSkillDefinition.LAYER_FOUNDATION,
}

# 业务子分类
_FILE_PREFIX_TO_SUBCATEGORY = {
    "brief": "立项",
    "world": "世界观",
    "character": "人设",
    "outline": "大纲",
    "script": "剧本",
    "review": "质检",
    "polish": "润色",
    "marketing": "营销",
    "adapt": "改编",
    "emotion_architect": "情绪",
    "insight": "洞察",
    "score": "评分",
    "pacing_heuristics": "节奏",
}


def _strip_snake_lower(name: str) -> str:
    """将常量名规范化为 skill_id 友好的小写串。"""
    return (name or "").strip().lower().lstrip("_")


def _infer_skill_id(file_stem: str, var_name: str) -> str:
    """
    推断 skill_id。

    优先级：
    1. 从 _FILE_PREFIX_TO_AGENT 查找 file_stem 对应的 agent 短名
    2. 变量名后缀部分拼到 agent 短名后
       如 brief_engine.py 中 _LAYER1_PEEL_SYSTEM → brief.layer1_peel
    3. 未匹配前缀时使用 file_stem + 变量名小写
    """
    agent = _FILE_PREFIX_TO_AGENT.get(file_stem, file_stem)
    var_low = _strip_snake_lower(var_name)

    # 去掉 _SYSTEM / _PROMPT / _HINT / _TEMPLATE 通用后缀
    for tail in (
        "_system",
        "_system_prompt",
        "_system_hint",
        "_prompt",
        "_prompt_template",
        "_hints",
        "_hint",
        "_template",
    ):
        if var_low.endswith(tail):
            var_low = var_low[: -len(tail)]
            break

    if not var_low or var_low == agent:
        return agent

    return f"{agent}.{var_low}"


def _infer_name(skill_id: str, var_name: str) -> str:
    """从 skill_id 推断展示名称。"""
    if "." in skill_id:
        head, tail = skill_id.split(".", 1)
        return f"{head}·{tail.replace('_', ' ')}"
    return skill_id.replace("_", " ")


def _extract_string_value(node: ast.AST) -> Optional[str]:
    """从 ast 节点中提取字符串字面量。"""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        # f-string：返回 None（不迁移动态提示词）
        return None
    return None


def _parse_python_file(path: Path) -> List[Tuple[str, str]]:
    """
    解析一个 *_engine.py 文件，返回 [(var_name, prompt_text), ...] 列表。
    仅匹配模块级（顶层）字符串常量，命中 HINT_VAR_NAME_PATTERNS。
    """
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (SyntaxError, UnicodeDecodeError) as exc:
        logger.warning("解析失败 %s: %s", path, exc)
        return []

    results: List[Tuple[str, str]] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if len(node.targets) != 1 or not isinstance(node.targets[0], ast.Name):
            continue
        var_name = node.targets[0].id
        if not any(p.match(var_name) for p in HINT_VAR_NAME_PATTERNS):
            continue
        text = _extract_string_value(node.value)
        if text and text.strip():
            results.append((var_name, text))
    return results


def _scan_root(scan_root: Path) -> List[Path]:
    """列出扫描根目录下所有 *_engine.py（不含 __pycache__）。"""
    if not scan_root.exists():
        raise CommandError(f"扫描根目录不存在: {scan_root}")
    files: List[Path] = []
    for p in sorted(scan_root.glob("*_engine.py")):
        if "__pycache__" in p.parts:
            continue
        files.append(p)
    return files


class Command(BaseCommand):
    help = "扫描硬编码 Prompt 模板并迁移到 AgentSkillDefinition 表（DB 化）"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="仅打印迁移预览，不写入数据库（默认）",
        )
        parser.add_argument(
            "--execute",
            action="store_true",
            default=False,
            help="实际写入数据库",
        )
        parser.add_argument(
            "--scan-root",
            type=str,
            default=DEFAULT_SCAN_ROOT,
            help=f"扫描根目录（默认 {DEFAULT_SCAN_ROOT}）",
        )
        parser.add_argument(
            "--skill-ids",
            type=str,
            default="",
            help="仅迁移指定的 skill_id 列表（逗号分隔）",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help="强制覆盖已有 system_hint（默认跳过已有记录）",
        )

    def handle(self, *args, **options):
        is_execute: bool = options["execute"]
        is_dry_run: bool = options["dry_run"] or not is_execute
        scan_root_arg: str = options["scan_root"]
        skill_ids_filter: str = options["skill_ids"]
        force: bool = options["force"]

        # 决定 backend 根目录
        backend_root = Path(__file__).resolve().parents[4]
        scan_root = (backend_root / scan_root_arg).resolve()
        if not scan_root.exists():
            raise CommandError(f"扫描根目录不存在: {scan_root}")

        skill_id_allowlist: Optional[List[str]] = None
        if skill_ids_filter:
            skill_id_allowlist = [s.strip() for s in skill_ids_filter.split(",") if s.strip()]

        mode_label = "[EXECUTE]" if is_execute else "[DRY-RUN]"
        self.stdout.write(self.style.NOTICE(
            f"{mode_label} 扫描根目录: {scan_root}"
        ))
        if skill_id_allowlist:
            self.stdout.write(f"  过滤 skill_id: {skill_id_allowlist}")
        self.stdout.write("")

        files = _scan_root(scan_root)
        if not files:
            self.stdout.write(self.style.WARNING(
                f"未找到任何 *_engine.py 文件: {scan_root}"
            ))
            return

        created = updated = skipped = 0
        matched_count = 0
        seen_skill_ids: set = set()

        for fpath in files:
            file_stem = fpath.stem  # e.g. brief_engine
            entries = _parse_python_file(fpath)
            if not entries:
                continue

            self.stdout.write(self.style.HTTP_INFO(f"📄 {fpath.relative_to(backend_root)}"))
            for var_name, prompt_text in entries:
                skill_id = _infer_skill_id(file_stem, var_name)
                matched_count += 1

                if skill_id_allowlist and skill_id not in skill_id_allowlist:
                    continue

                if skill_id in seen_skill_ids:
                    self.stdout.write(
                        f"  ↪ 跳过重复 skill_id={skill_id}（{var_name}）"
                    )
                    continue
                seen_skill_ids.add(skill_id)

                # 查重
                existing = AgentSkillDefinition.objects.filter(skill_id=skill_id).first()
                if existing and not force:
                    self.stdout.write(
                        f"  ⏭ SKIP {skill_id}（{var_name}，{len(prompt_text)} 字）— 已有记录"
                    )
                    skipped += 1
                    continue

                if is_dry_run:
                    action = "UPDATE" if existing else "CREATE"
                    self.stdout.write(
                        f"  🔍 {action} {skill_id}（{var_name}，{len(prompt_text)} 字）"
                    )
                    if existing:
                        updated += 1
                    else:
                        created += 1
                    continue

                # 实际写入
                layer = _FILE_PREFIX_TO_LAYER.get(file_stem, AgentSkillDefinition.LAYER_BUSINESS)
                sub_category = _FILE_PREFIX_TO_SUBCATEGORY.get(file_stem, "")
                name = _infer_name(skill_id, var_name)

                defaults = {
                    "system_hint": prompt_text,
                    "lifecycle_status": AgentSkillDefinition.LIFECYCLE_DRAFT,
                    "version": "v0.0.1",
                    "skill_layer": layer,
                    "sub_category": sub_category,
                }

                obj, is_created = AgentSkillDefinition.objects.update_or_create(
                    skill_id=skill_id,
                    defaults=defaults,
                )
                # 若已有记录但缺少 name/source_file 等元数据，补齐
                if not is_created and (not obj.name or not obj.skill_layer):
                    obj.name = obj.name or name
                    obj.skill_layer = obj.skill_layer or layer
                    obj.sub_category = obj.sub_category or sub_category
                    obj.save(update_fields=["name", "skill_layer", "sub_category", "updated_at"])

                action_label = "CREATED" if is_created else "UPDATED"
                self.stdout.write(self.style.SUCCESS(
                    f"  ✅ {action_label} {skill_id}（{var_name}，{len(prompt_text)} 字）"
                ))
                if is_created:
                    created += 1
                else:
                    updated += 1

        # 输出统计
        self.stdout.write("")
        self.stdout.write(self.style.NOTICE("=" * 60))
        self.stdout.write(self.style.NOTICE(
            f"{mode_label} 迁移报告"
        ))
        self.stdout.write(f"  扫描文件: {len(files)}")
        self.stdout.write(f"  匹配提示词: {matched_count}")
        self.stdout.write(f"  CREATE  : {created}")
        self.stdout.write(f"  UPDATE  : {updated}")
        self.stdout.write(f"  SKIP    : {skipped}")
        self.stdout.write(self.style.NOTICE("=" * 60))

        if is_dry_run:
            self.stdout.write(self.style.WARNING(
                "  （DRY-RUN 模式，加 --execute 真正写入；加 --force 覆盖已有记录）"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"  完成：共处理 {created + updated} 条；新记录均为 draft 状态，需 Admin 审核后 publish()"
            ))
