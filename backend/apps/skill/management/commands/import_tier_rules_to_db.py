# -*- coding: utf-8 -*-
"""
导入 tier1-4 JSON 规则到 SkillRuleConfig 表

使用方式：
    python manage.py import_tier_rules_to_db
    python manage.py import_tier_rules_to_db --tier tier1
    python manage.py import_tier_rules_to_db --tier tier2 --scope-key family-revenge
    python manage.py import_tier_rules_to_db --dry-run
    python manage.py import_tier_rules_to_db --execute --force

扫描来源：
- apps/skill/config/*.json          通用配置（含 tier 规则 / 节奏启发 / 评分阈值等）
- apps/creation/orchestration/pacing_heuristics.py  节奏启发式（特殊处理：Python 字典）
- demo4book/short-drama-script-creator/config/skill-rules/tier*.json（若存在）
- ai-drama-skills-v2/config/*.json（若存在）

识别策略：
- 文件名 / 配置键以 tier1 / tier2 / tier3 / tier4 开头 → 对应 Tier 编号
- JSON 顶层结构含 `tier` 字段 → 优先使用
- content 中 `section` 字段若存在 → 写入 SkillRuleConfig.section
- scope_type / scope_key 推断：
    * tier1 → global（全剧铁律）
    * tier2 → genre（题材）— 从 scope_key 或 config_key 推断题材代码
    * tier3 → node（节点）— 从 scope_key 或 config_key 推断节点 ID
    * tier4 → global（合规红线）
- 兼容旧数据：scope_key 为空时降级到 global scope_type

互补关系：
- 本命令与 import_skill_rules_to_db 互补不冲突：
  * import_skill_rules_to_db 处理 demo4book/skill-rules/tier2-genre-rules.json /
    tier3-workflow-rules.json，写入 SkillRuleConfig
  * 本命令覆盖其余来源（apps/skill/config/、ai-drama-skills-v2/config/、
    pacing_heuristics.py），写入 SkillRuleConfig 同样表
  * 写入时使用 (tier, scope_type, scope_key, section) 唯一定位，已存在 active 记录默认跳过
"""
from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from django.core.management.base import BaseCommand, CommandError

from apps.skill.models import SkillRuleConfig

logger = logging.getLogger(__name__)

# tier 名称与编号映射
TIER_NAME_MAP = {
    "tier1": 1,
    "tier2": 2,
    "tier3": 3,
    "tier4": 4,
}

# tier → 默认 scope_type 映射
TIER_DEFAULT_SCOPE = {
    1: SkillRuleConfig.SCOPE_GLOBAL,
    2: SkillRuleConfig.SCOPE_GENRE,
    3: SkillRuleConfig.SCOPE_NODE,
    4: SkillRuleConfig.SCOPE_GLOBAL,
}

# 已知的 JSON 配置键 → tier 映射（apps/skill/config/ 下的特殊文件）
CONFIG_KEY_TIER_OVERRIDE = {
    "tier1-iron-rules": 1,
    "tier2-genre-rules": 2,
    "tier3-workflow-rules": 3,
    "tier4-compliance-rules": 4,
    "pacing-heuristics": 3,  # 节奏启发按节点级处理
    "tier-full": 1,
    "rhythm-rules": 1,
}

# 文件名前缀识别
TIER_PREFIX_RE = re.compile(r"^tier([1-4])", re.IGNORECASE)
GENRE_CODE_RE = re.compile(r"^(?:tier2-)?genre-rules-([a-z0-9\-]+)$", re.IGNORECASE)
NODE_ID_RE = re.compile(r"^tier3-node-([a-z0-9\-]+)$", re.IGNORECASE)


def _detect_tier(filename: str, content: Any) -> Optional[int]:
    """
    根据文件名与 JSON 内容推断 tier 编号。
    优先级：content.tier > 文件名 tier 前缀 > CONFIG_KEY_TIER_OVERRIDE
    """
    if isinstance(content, dict):
        t = content.get("tier")
        if isinstance(t, int) and 1 <= t <= 4:
            return t
        if isinstance(t, str) and t.lower() in TIER_NAME_MAP:
            return TIER_NAME_MAP[t.lower()]

    stem = Path(filename).stem
    m = TIER_PREFIX_RE.match(stem)
    if m:
        return int(m.group(1))
    if stem in CONFIG_KEY_TIER_OVERRIDE:
        return CONFIG_KEY_TIER_OVERRIDE[stem]
    return None


def _infer_scope(
    tier: int,
    filename: str,
    content: Any,
    scope_key_override: Optional[str] = None,
) -> Tuple[str, str]:
    """
    推断 (scope_type, scope_key)。

    优先级：
    1. scope_key_override（命令行参数）
    2. content.scope_type + content.scope_key
    3. 文件名规律：
        - tier2-*.json  → genre, 题材代码（推断或为空）
        - tier3-*.json  → node,  节点 ID
        - 其他 → TIER_DEFAULT_SCOPE
    4. tier 默认 scope
    """
    if scope_key_override is not None:
        return TIER_DEFAULT_SCOPE.get(tier, SkillRuleConfig.SCOPE_GLOBAL), scope_key_override

    if isinstance(content, dict):
        st = content.get("scope_type")
        sk = content.get("scope_key")
        if isinstance(st, str) and st in {SkillRuleConfig.SCOPE_GLOBAL, SkillRuleConfig.SCOPE_GENRE, SkillRuleConfig.SCOPE_NODE}:
            return st, str(sk or "")

    stem = Path(filename).stem.lower()

    if tier == 2:
        m = GENRE_CODE_RE.match(stem)
        if m:
            return SkillRuleConfig.SCOPE_GENRE, m.group(1)
        return SkillRuleConfig.SCOPE_GENRE, ""

    if tier == 3:
        m = NODE_ID_RE.match(stem)
        if m:
            return SkillRuleConfig.SCOPE_NODE, m.group(1)
        # 尝试 content 中找 node_id
        if isinstance(content, dict):
            nid = content.get("node_id") or content.get("nodeId")
            if isinstance(nid, str) and nid:
                return SkillRuleConfig.SCOPE_NODE, nid
        return SkillRuleConfig.SCOPE_NODE, ""

    return TIER_DEFAULT_SCOPE.get(tier, SkillRuleConfig.SCOPE_GLOBAL), ""


def _infer_section(content: Any, filename: str) -> str:
    """从 content 或文件名推断 section 字段。"""
    if isinstance(content, dict):
        s = content.get("section")
        if isinstance(s, str) and s.strip():
            return s.strip()
    stem = Path(filename).stem
    return stem or "tier_full"


def _split_into_sections(content: Any) -> List[Tuple[str, Any]]:
    """
    将一个 JSON 对象拆分为多条 (section, payload) 记录。
    - 若顶层 _meta.version 存在但其他字段都成 section 形式，则把每个顶层 key 当作一个 section
    - 若顶层有 _sections 数组则按其拆分
    - 否则整体作为一个 section（section 名取自 caller 默认推断）
    """
    if not isinstance(content, dict):
        return [("tier_full", content)]

    # 显式 _sections 数组
    sections = content.get("_sections")
    if isinstance(sections, list) and sections:
        result = []
        for item in sections:
            if not isinstance(item, dict):
                continue
            name = item.get("name") or item.get("section") or "tier_full"
            payload = item.get("content") if "content" in item else item
            result.append((str(name), payload))
        if result:
            return result

    # 顶层 key 即 section 的常见模式
    meta_keys = {"_meta", "_version", "tier", "version", "_note", "scope_type", "scope_key"}
    body = {k: v for k, v in content.items() if k not in meta_keys}
    if 1 < len(body) <= 30:
        return list(body.items())
    return [(_infer_section(content, "tier_full.json"), content)]


def _collect_json_files(
    backend_root: Path,
    workspace: Path,
    tier_filter: Optional[int],
) -> List[Tuple[Path, int]]:
    """
    收集所有候选 JSON 文件并预判 tier。
    返回 [(path, tier), ...]，过滤掉 tier 不在 tier_filter 的项。
    """
    candidates: List[Tuple[Path, int]] = []

    # 1) apps/skill/config/*.json
    app_config = backend_root / "apps" / "skill" / "config"
    for fpath in sorted(app_config.rglob("*.json")):
        if "__pycache__" in fpath.parts:
            continue
        try:
            content = json.loads(fpath.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            logger.debug("解析 JSON 失败 %s: %s", fpath, exc)
            continue
        tier = _detect_tier(fpath.name, content)
        if tier is None:
            continue
        if tier_filter and tier != tier_filter:
            continue
        candidates.append((fpath, tier))

    # 2) demo4book/.../config/skill-rules/tier*.json
    sd_root = workspace / "demo4book" / "short-drama-script-creator" / "config" / "skill-rules"
    if sd_root.exists():
        for fpath in sorted(sd_root.glob("tier*.json")):
            tier_name = fpath.stem.split("-")[0].lower()  # tier1 / tier2 / ...
            tier = TIER_NAME_MAP.get(tier_name)
            if tier is None:
                continue
            if tier_filter and tier != tier_filter:
                continue
            candidates.append((fpath, tier))

    # 3) ai-drama-skills-v2/config/*.json
    ai_root = workspace / "ai-drama-skills-v2" / "config"
    if ai_root.exists():
        for fpath in sorted(ai_root.glob("*.json")):
            if "skill-rules" in fpath.name.lower():
                continue
            try:
                content = json.loads(fpath.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                logger.debug("解析 JSON 失败 %s: %s", fpath, exc)
                continue
            tier = _detect_tier(fpath.name, content)
            if tier is None:
                continue
            if tier_filter and tier != tier_filter:
                continue
            candidates.append((fpath, tier))

    # 去重（按 path）
    seen = set()
    unique: List[Tuple[Path, int]] = []
    for p, t in candidates:
        if p in seen:
            continue
        seen.add(p)
        unique.append((p, t))
    return unique


def _collect_pacing_heuristics(backend_root: Path) -> Optional[Tuple[Path, int]]:
    """从 apps/creation/orchestration/pacing_heuristics.py 提取节奏启发规则。
    由于该文件内嵌 Python 字典且未提供 __all__ 接口，我们直接读源文件解析字面量。
    """
    fpath = backend_root / "apps" / "creation" / "orchestration" / "pacing_heuristics.py"
    if not fpath.exists():
        return None
    return (fpath, 3)  # tier3 — 节点级


def _extract_pacing_dict(fpath: Path) -> Optional[Dict[str, Any]]:
    """
    通过 AST 解析 pacing_heuristics.py 中名为 _PAGING_RULES / PACING_RULES / _RULES 的 dict。
    解析失败时返回 None。
    """
    try:
        import ast

        source = fpath.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(fpath))
    except (SyntaxError, UnicodeDecodeError) as exc:
        logger.debug("pacing 解析失败 %s: %s", fpath, exc)
        return None

    candidate_names = {"_PACING_RULES", "PACING_RULES", "_RULES", "RULES"}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in candidate_names and isinstance(node.value, ast.Dict):
                try:
                    return ast.literal_eval(node.value)
                except Exception:
                    continue
    return None


class Command(BaseCommand):
    help = "将 tier1-4 JSON 规则从各配置源导入 SkillRuleConfig 表"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="仅预览，不写入数据库（默认）",
        )
        parser.add_argument(
            "--execute",
            action="store_true",
            default=False,
            help="实际写入数据库",
        )
        parser.add_argument(
            "--tier",
            type=str,
            default="",
            choices=["", "tier1", "tier2", "tier3", "tier4", "1", "2", "3", "4"],
            help="仅导入指定 tier（tier1-4 或 1-4）",
        )
        parser.add_argument(
            "--scope-key",
            type=str,
            default="",
            help="强制覆盖 scope_key（如 family-revenge / node-5-script）",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help="强制覆盖已有 active 记录（默认跳过）",
        )

    def handle(self, *args, **options):
        is_execute: bool = options["execute"]
        is_dry_run: bool = options["dry_run"] or not is_execute
        tier_arg: str = options["tier"]
        scope_key: str = options["scope_key"] or None
        force: bool = options["force"]

        # tier 过滤器
        tier_filter: Optional[int] = None
        if tier_arg:
            if tier_arg.startswith("tier"):
                tier_filter = TIER_NAME_MAP.get(tier_arg.lower())
            else:
                try:
                    tier_filter = int(tier_arg)
                except ValueError:
                    tier_filter = None
            if tier_filter is None:
                raise CommandError(f"无效的 tier: {tier_arg!r}")

        # 路径
        backend_root = Path(__file__).resolve().parents[4]
        workspace = backend_root.parent

        mode_label = "[EXECUTE]" if is_execute else "[DRY-RUN]"
        self.stdout.write(self.style.NOTICE(
            f"{mode_label} 扫描 tier={tier_arg or 'ALL'} scope_key={scope_key or '<auto>'} "
            f"backend={backend_root}"
        ))

        # 收集文件
        json_files = _collect_json_files(backend_root, workspace, tier_filter)
        pacing = _collect_pacing_heuristics(backend_root)

        self.stdout.write(f"  发现候选 JSON 文件: {len(json_files)}")
        if pacing:
            self.stdout.write(f"  + pacing_heuristics.py（tier3）")

        # 统计
        created = updated = skipped = errors = 0
        processed = 0

        # 处理 pacing 启发式（特殊）
        if pacing and (tier_filter is None or tier_filter == 3):
            fpath, tier = pacing
            data = _extract_pacing_dict(fpath)
            if data:
                scope_type, sk = _infer_scope(
                    tier, fpath.name, data, scope_key_override=scope_key
                )
                # pacing 不拆分 section，整体作为 tier3_node_pacing
                section = "tier3_node_pacing"
                self._write_or_preview(
                    tier=tier,
                    scope_type=scope_type,
                    scope_key=sk or "",
                    section=section,
                    content=data,
                    version="v5.0.0",
                    source_label=str(fpath.relative_to(backend_root)),
                    is_execute=is_execute,
                    force=force,
                )
                processed += 1

        # 处理 JSON 文件
        for fpath, tier in json_files:
            try:
                content = json.loads(fpath.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                self.stdout.write(self.style.ERROR(
                    f"  ❌ 解析失败 {fpath.relative_to(backend_root)}: {exc}"
                ))
                errors += 1
                continue

            # 顶层 _meta / version
            version = "v5.0.0"
            if isinstance(content, dict):
                meta = content.get("_meta") or {}
                if isinstance(meta, dict) and isinstance(meta.get("version"), str):
                    version = meta["version"]
                elif isinstance(content.get("_version"), str):
                    version = content["_version"]

            scope_type, scope_key_inferred = _infer_scope(
                tier, fpath.name, content, scope_key_override=scope_key
            )

            # 拆分为多条 section
            sections = _split_into_sections(content)
            if not sections:
                continue

            for section_name, section_payload in sections:
                # 跳过纯元数据字段
                if section_name in {"_meta", "_version", "tier", "version", "_note"}:
                    continue

                self._write_or_preview(
                    tier=tier,
                    scope_type=scope_type,
                    scope_key=scope_key_inferred or "",
                    section=section_name or "tier_full",
                    content=section_payload,
                    version=version,
                    source_label=str(fpath.relative_to(backend_root)),
                    is_execute=is_execute,
                    force=force,
                )
                processed += 1

        # 读回统计
        created = self._stats["created"]
        updated = self._stats["updated"]
        skipped = self._stats["skipped"]

        self.stdout.write("")
        self.stdout.write(self.style.NOTICE("=" * 60))
        self.stdout.write(self.style.NOTICE(f"{mode_label} 导入报告"))
        self.stdout.write(f"  处理记录数 : {processed}")
        self.stdout.write(f"  CREATE     : {created}")
        self.stdout.write(f"  UPDATE     : {updated}")
        self.stdout.write(f"  SKIP       : {skipped}")
        self.stdout.write(f"  解析错误   : {errors}")
        self.stdout.write(self.style.NOTICE("=" * 60))

        if is_dry_run:
            self.stdout.write(self.style.WARNING(
                "  （DRY-RUN 模式，加 --execute 真正写入；加 --force 覆盖已有 active 记录）"
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                "  完成。可在「技能规则」管理页或 Django Admin 中查看与编辑。"
            ))

    # ──────────── 内部辅助 ────────────

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._stats = {"created": 0, "updated": 0, "skipped": 0}

    def _write_or_preview(
        self,
        *,
        tier: int,
        scope_type: str,
        scope_key: str,
        section: str,
        content: Any,
        version: str,
        source_label: str,
        is_execute: bool,
        force: bool,
    ) -> None:
        """执行单条规则导入或预览，统计累加到 self._stats。"""
        # 兼容旧数据：scope_key 为空 → 降级到 global
        if not scope_key:
            scope_type = SkillRuleConfig.SCOPE_GLOBAL

        existing = SkillRuleConfig.objects.filter(
            tier=tier,
            scope_type=scope_type,
            scope_key=scope_key,
            section=section,
            status=SkillRuleConfig.STATUS_ACTIVE,
        ).first()

        if existing and not force:
            self.stdout.write(
                f"  ⏭ SKIP [tier{tier}·{scope_type}·{scope_key or 'global'}/{section}] "
                f"({source_label})"
            )
            self._stats["skipped"] += 1
            return

        if not is_execute:
            action = "UPDATE" if existing else "CREATE"
            self.stdout.write(
                f"  🔍 {action} [tier{tier}·{scope_type}·{scope_key or 'global'}/{section}] "
                f"v={version}  ({source_label})"
            )
            if existing:
                self._stats["updated"] += 1
            else:
                self._stats["created"] += 1
            return

        # 实际写入
        if existing and force:
            existing.status = SkillRuleConfig.STATUS_ARCHIVED
            existing.save(update_fields=["status", "updated_at"])

        SkillRuleConfig.objects.create(
            tier=tier,
            scope_type=scope_type,
            scope_key=scope_key,
            section=section,
            content=content,
            version_tag=version,
            status=SkillRuleConfig.STATUS_ACTIVE,
            source=SkillRuleConfig.SOURCE_FILE,
            note=f"由 import_tier_rules_to_db 导入·{source_label}",
            approved_by="system_import",
        )
        action = "UPDATED" if existing else "CREATED"
        self.stdout.write(self.style.SUCCESS(
            f"  ✅ {action} [tier{tier}·{scope_type}·{scope_key or 'global'}/{section}] "
            f"v={version}  ({source_label})"
        ))
        if existing:
            self._stats["updated"] += 1
        else:
            self._stats["created"] += 1
