# -*- coding: utf-8 -*-
"""
进化审计模块（evolve_audit.py）

触发方式（dj_queue 异步任务）：
  - 每日定时：python manage.py run_evolve_audit
  - score完成后自动触发（tasks.py hook）

两大核心逻辑：
  1. 低分追溯（_audit_low_score_project）
     综合评分 < LOW_SCORE_THRESHOLD 时，用 Sonnet-4 分析是哪条规则缺陷导致，
     输出增量修改提案（仅针对 Tier2/Tier3 可迭代层），存入 pending-proposals/。

  2. 高分提炼（_extract_high_score_patterns）
     综合评分 ≥ HIGH_SCORE_THRESHOLD，提炼爆款套路，存入 pending-proposals/ 实验区，
     人工审核后晋升为正式规则。

强制风控约束：
  - Tier1（顶层铁律）+ Tier4（合规熔断）永久只读，任何情况禁止AI修改
  - 所有提案须人工审核，无全自动生效
  - 单次 Sonnet-4 输出上限 MAX_AUDIT_TOKENS，防止长篇重写
  - 月度预算上限触达时自动暂停（MONTHLY_EVOLVE_BUDGET_CNY）
"""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# ── 配置常量 ─────────────────────────────────────────────────────────────────
LOW_SCORE_THRESHOLD: float = float(os.environ.get("EVOLVE_LOW_SCORE_THRESHOLD", "70"))
HIGH_SCORE_THRESHOLD: float = float(os.environ.get("EVOLVE_HIGH_SCORE_THRESHOLD", "90"))
AUDIT_WINDOW_DAYS: int = int(os.environ.get("EVOLVE_AUDIT_WINDOW_DAYS", "1"))
MAX_PROJECTS_PER_AUDIT: int = int(os.environ.get("EVOLVE_MAX_PROJECTS_PER_AUDIT", "10"))
MAX_AUDIT_TOKENS: int = int(os.environ.get("EVOLVE_MAX_AUDIT_TOKENS", "4096"))
MONTHLY_EVOLVE_BUDGET_CNY: float = float(os.environ.get("EVOLVE_MONTHLY_BUDGET_CNY", "50.0"))

# 技能规则根路径（demo4book 里的 skill-rules/）
_SKILL_RULES_ROOT: Path = (
    Path(getattr(settings, "FUSION_SKILL_ROOT", "demo4book"))
    / "short-drama-script-creator"
    / "config"
    / "skill-rules"
)
_PROPOSALS_DIR: Path = _SKILL_RULES_ROOT / "pending-proposals"

# 只读层（禁止 AI 提案涉及）
_READONLY_TIERS = {1, 4}
_ITERABLE_TIERS = {2, 3}


# ── 提案存储（DB优先 + JSON文件兜底）────────────────────────────────────────
def _save_proposal(proposal: Dict[str, Any], project_ids: Optional[List[str]] = None, score_avg: Optional[float] = None) -> Optional[str]:
    """
    将规则修改提案写入 DB（SkillRuleConfig，status=draft）。
    写 DB 失败时兜底写 JSON 文件。
    返回 DB record ID（str）或 None。
    """
    try:
        from apps.skill.models import SkillRuleConfig

        # 从提案中解析 scope 信息
        root_causes = proposal.get("rootCauses") or proposal.get("extractedPatterns") or []

        # 强制前置校验：没有 root_causes 的提案直接拦截（避免空循环落到文件兜底绕过检查）
        if not root_causes:
            logger.warning("[EvolveAudit] 提案缺少 rootCauses/extractedPatterns，已拦截。")
            return None

        for cause in root_causes[:1]:
            tier = int(cause.get("tier") or 2)

            # 强制校验：Tier1/4 只读，禁止任何 AI 提案写入
            if tier not in _ITERABLE_TIERS:
                logger.warning(
                    "[EvolveAudit] 提案试图修改只读层 tier=%s，已拦截。", tier
                )
                return None
            target_path = cause.get("targetRule") or cause.get("targetPath") or ""
            # 简单解析 scope：tier2.genres.xxx → genre=xxx
            scope_type = "global"
            scope_key = ""
            if "genres." in target_path:
                parts = target_path.split("genres.")
                scope_type = SkillRuleConfig.SCOPE_GENRE
                scope_key = parts[-1].split(".")[0]
            elif "main_pipeline" in target_path:
                scope_type = SkillRuleConfig.SCOPE_NODE
                scope_key = proposal.get("nodeId", "")

            section = cause.get("proposedSection") or "genre_full"

            row = SkillRuleConfig.objects.create(
                tier=tier,
                scope_type=scope_type,
                scope_key=scope_key,
                section=section,
                content=cause,
                version_tag="draft",
                status=SkillRuleConfig.STATUS_DRAFT,
                source=SkillRuleConfig.SOURCE_EVOLVE,
                note=proposal.get("summary") or "",
                trigger_project_ids=project_ids or [],
                trigger_score_avg=score_avg,
            )
            logger.info("[EvolveAudit] 提案已写入DB: %s", row.id)
            return str(row.id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("[EvolveAudit] DB写入失败，兜底写文件: %s", exc)

    # 兜底：写 JSON 文件
    _PROPOSALS_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    proposal_type = proposal.get("type", "unknown")
    filename = f"{ts}_{proposal_type}_{uuid.uuid4().hex[:8]}.json"
    path = _PROPOSALS_DIR / filename
    path.write_text(json.dumps(proposal, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("[EvolveAudit] 提案已保存至文件（DB兜底）: %s", path.name)
    return None


def list_pending_proposals() -> List[Dict[str, Any]]:
    """列出所有待审核提案（优先从 DB，再从文件目录）。"""
    results = []
    # DB 中的 draft
    try:
        from apps.skill.models import SkillRuleConfig
        for row in SkillRuleConfig.objects.filter(status=SkillRuleConfig.STATUS_DRAFT).order_by("-created_at")[:50]:
            results.append({
                "id": str(row.id),
                "tier": row.tier,
                "scope_type": row.scope_type,
                "scope_key": row.scope_key,
                "section": row.section,
                "source": row.source,
                "note": row.note,
                "created_at": row.created_at.isoformat() if row.created_at else "",
                "trigger_score_avg": row.trigger_score_avg,
                "content_preview": str(row.content)[:200],
            })
    except Exception as exc:  # noqa: BLE001
        logger.warning("[EvolveAudit] DB 查询 draft 失败: %s", exc)

    # 文件目录中的 pending（兜底）
    if _PROPOSALS_DIR.exists():
        for f in sorted(_PROPOSALS_DIR.glob("*.json")):
            try:
                results.append(json.loads(f.read_text(encoding="utf-8")))
            except Exception:  # noqa: BLE001
                pass
    return results


def approve_proposal(proposal_id: str, approved_by: str = "admin") -> bool:
    """
    人工审核通过：DB record 调用 approve()，文件目录则移动到 approved/。
    """
    # 先尝试 DB
    try:
        from apps.skill.models import SkillRuleConfig
        row = SkillRuleConfig.objects.filter(id=proposal_id, status=SkillRuleConfig.STATUS_DRAFT).first()
        if row:
            row.approve(approved_by=approved_by)
            logger.info("[EvolveAudit] DB提案已通过: %s", proposal_id)
            return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("[EvolveAudit] DB approve失败: %s", exc)

    # 兜底：文件
    src = _PROPOSALS_DIR / proposal_id
    if src.exists():
        approved_dir = _PROPOSALS_DIR / "approved"
        approved_dir.mkdir(exist_ok=True)
        src.rename(approved_dir / proposal_id)
        logger.info("[EvolveAudit] 文件提案已通过: %s", proposal_id)
        return True
    return False


def reject_proposal(proposal_id: str, reason: str = "") -> bool:
    """驳回提案（DB record 变 archived，文件移到 rejected/）。"""
    try:
        from apps.skill.models import SkillRuleConfig
        updated = SkillRuleConfig.objects.filter(id=proposal_id, status=SkillRuleConfig.STATUS_DRAFT).update(
            status=SkillRuleConfig.STATUS_ARCHIVED, note=reason
        )
        if updated:
            logger.info("[EvolveAudit] DB提案已驳回: %s", proposal_id)
            return True
    except Exception:  # noqa: BLE001
        pass

    src = _PROPOSALS_DIR / proposal_id
    if src.exists():
        rejected_dir = _PROPOSALS_DIR / "rejected"
        rejected_dir.mkdir(exist_ok=True)
        src.rename(rejected_dir / proposal_id)
        return True
    return False


# ── 月度预算检查 ─────────────────────────────────────────────────────────────
def _check_budget_headroom() -> bool:
    """
    简单文件锁机制：读取本月累计消耗估算（由 _record_token_cost 写入），
    如果超过预算则返回 False，跳过本次审计。
    """
    budget_file = _SKILL_RULES_ROOT / "evolve_cost_tracker.json"
    try:
        if budget_file.exists():
            data = json.loads(budget_file.read_text(encoding="utf-8"))
            current_month = datetime.utcnow().strftime("%Y-%m")
            month_cost = data.get(current_month, 0.0)
            if month_cost >= MONTHLY_EVOLVE_BUDGET_CNY:
                logger.warning(
                    "[EvolveAudit] 月度预算已达上限 %.2f CNY，暂停审计。", MONTHLY_EVOLVE_BUDGET_CNY
                )
                return False
    except Exception:  # noqa: BLE001
        pass
    return True


def _record_token_cost(tokens_used: int) -> None:
    """估算并累计 Sonnet-4 成本（约 $3/M tokens，按6.5汇率估算CNY）。"""
    SONNET_PRICE_PER_TOKEN_CNY = 3.0 * 6.5 / 1_000_000
    cost_cny = tokens_used * SONNET_PRICE_PER_TOKEN_CNY
    budget_file = _SKILL_RULES_ROOT / "evolve_cost_tracker.json"
    current_month = datetime.utcnow().strftime("%Y-%m")
    try:
        data: Dict[str, float] = {}
        if budget_file.exists():
            data = json.loads(budget_file.read_text(encoding="utf-8"))
        data[current_month] = data.get(current_month, 0.0) + cost_cny
        budget_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        logger.warning("[EvolveAudit] cost tracker 写入失败: %s", exc)


# ── LLM 调用工具 ─────────────────────────────────────────────────────────────
def _call_sonnet4_audit(system_prompt: str, user_content: str) -> Optional[Dict[str, Any]]:
    """
    调用 Sonnet-4 进行审计分析。
    返回解析后的 JSON dict；失败时返回 None。
    """
    try:
        import anthropic
    except ImportError:
        logger.error("[EvolveAudit] anthropic 包未安装，无法执行 Sonnet-4 审计")
        return None

    api_key = os.environ.get("ANTHROPIC_API_KEY") or getattr(settings, "ANTHROPIC_API_KEY", None)
    if not api_key:
        logger.error("[EvolveAudit] ANTHROPIC_API_KEY 未配置")
        return None

    if not _check_budget_headroom():
        return None

    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=MAX_AUDIT_TOKENS,
            system=system_prompt,
            messages=[{"role": "user", "content": user_content}],
        )
        raw_text = message.content[0].text if message.content else ""
        _record_token_cost(message.usage.input_tokens + message.usage.output_tokens)

        # 提取 JSON（允许 markdown 代码块包裹）
        text = raw_text.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
        return json.loads(text)
    except json.JSONDecodeError:
        logger.warning("[EvolveAudit] Sonnet-4 输出无法解析为JSON，原始文本=%s...", raw_text[:200])
        return None
    except Exception as exc:  # noqa: BLE001
        logger.error("[EvolveAudit] Sonnet-4 调用失败: %s", exc)
        return None


# ── 规则文件加载工具 ─────────────────────────────────────────────────────────
def _load_iterable_rules_summary() -> str:
    """加载 Tier2/Tier3 可迭代规则的摘要，供 Sonnet-4 参考。"""
    summaries = []
    for tier, filename in [(2, "tier2-genre-rules.json"), (3, "tier3-workflow-rules.json")]:
        path = _SKILL_RULES_ROOT / filename
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                summaries.append(f"=== Tier{tier}: {data.get('_meta', {}).get('name', filename)} ===")
                summaries.append(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
            except Exception:  # noqa: BLE001
                pass
    return "\n".join(summaries)


# ── 低分追溯 ─────────────────────────────────────────────────────────────────
_LOW_SCORE_AUDIT_SYSTEM = """你是短剧剧本质量审计专家，负责分析低分剧本的规则缺陷。

【核心约束】
1. 只分析 Tier2（品类专属规范）和 Tier3（创作流程）中的规则缺陷
2. 严禁提案修改 Tier1（顶层铁律）和 Tier4（合规熔断）
3. 提案必须是"增量修改"，禁止提案全面重写规则
4. 每次最多指出 3 个最高优先级的规则缺陷
5. 只输出 JSON，格式严格按照下面的 schema

输出 JSON schema：
{
  "type": "low-score-fix",
  "projectId": "...",
  "score": 数字,
  "lowDimensions": ["分数最低的维度名"],
  "rootCauses": [
    {
      "tier": 2或3,
      "targetRule": "tier2.genres.xxx 或 tier3.main_pipeline[n].quality_gates.xxx",
      "currentIssue": "当前规则缺失/模糊/不够强制的具体描述",
      "proposedAmendment": "建议的增量修改内容（≤100字）",
      "evidence": "从剧本中发现的具体问题示例（≤150字）"
    }
  ],
  "summary": "本次低分根因一句话总结（≤80字）"
}"""


def _audit_low_score_project(project_id: str, score: float, score_report: Dict[str, Any]) -> None:
    """对单个低分项目进行规则缺陷分析，输出修改提案。"""
    from .artifact_service import get_artifact
    from .models import Project

    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return

    # 提取低分维度
    dimensions = score_report.get("dimensions") or {}
    low_dims = [k for k, v in dimensions.items() if isinstance(v, (int, float)) and v < 75]

    # 加载剧本样本（节省token，只取前两集）
    episode_scripts = get_artifact(project, "episode_scripts") or {}
    episodes = (episode_scripts.get("episodes") or [])[:2]
    script_sample = json.dumps(episodes, ensure_ascii=False)[:3000]  # 截断防token超支

    rules_summary = _load_iterable_rules_summary()

    user_content = json.dumps({
        "projectId": project_id,
        "theme": project.theme or "",
        "score": score,
        "lowDimensions": low_dims,
        "scriptSample": script_sample,
        "currentTier2Tier3Rules": rules_summary[:5000],  # 截断
    }, ensure_ascii=False)

    result = _call_sonnet4_audit(_LOW_SCORE_AUDIT_SYSTEM, user_content)
    if not result:
        return

    proposal = {
        **result,
        "projectId": project_id,
        "score": score,
        "auditedAt": datetime.utcnow().isoformat(),
        "status": "pending_review",
        "reviewedBy": None,
    }
    _save_proposal(proposal)


# ── 高分提炼 ─────────────────────────────────────────────────────────────────
_HIGH_SCORE_EXTRACT_SYSTEM = """你是短剧爆款套路提炼专家，负责从高分/高商业价值剧本中萃取可复用规则。

【核心约束】
1. 提炼的是可以加入 Tier2（品类专属规范）的"新套路"，不是修改现有规则
2. 必须是从剧本文本中真实观察到的、现有规则库中尚未收录的模式
3. 提炼格式须适配 tier2-genre-rules.json 中对应题材的 requirements 列表结构
4. 禁止捏造或推测未在剧本中出现的模式
5. 只输出 JSON

输出 JSON schema：
{
  "type": "high-score-extract",
  "projectId": "...",
  "score": 数字,
  "genre": "题材标识",
  "extractedPatterns": [
    {
      "patternName": "套路名称（≤20字）",
      "targetTier": 2,
      "targetPath": "tier2.genres.xxx.requirements",
      "newRequirement": {
        "element": "模式元素（≤20字）",
        "standard": "量化执行标准（≤100字）"
      },
      "evidence": "剧本中的具体体现（≤150字）",
      "novelty": "与现有规则的区别（≤80字）"
    }
  ],
  "summary": "本次提炼的爆款规律一句话总结（≤80字）"
}"""


def _extract_high_score_patterns(project_id: str, score: float, score_report: Dict[str, Any]) -> None:
    """对高分项目提炼爆款套路，存入 pending-proposals/ 等待人工审核晋升。"""
    from .artifact_service import get_artifact
    from .models import Project

    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return

    episode_scripts = get_artifact(project, "episode_scripts") or {}
    episodes = (episode_scripts.get("episodes") or [])[:3]
    script_sample = json.dumps(episodes, ensure_ascii=False)[:4000]

    rules_summary = _load_iterable_rules_summary()

    user_content = json.dumps({
        "projectId": project_id,
        "theme": project.theme or "",
        "score": score,
        "scoreReport": score_report,
        "scriptSample": script_sample,
        "currentTier2Rules": rules_summary[:4000],
    }, ensure_ascii=False)

    result = _call_sonnet4_audit(_HIGH_SCORE_EXTRACT_SYSTEM, user_content)
    if not result:
        return

    proposal = {
        **result,
        "projectId": project_id,
        "score": score,
        "auditedAt": datetime.utcnow().isoformat(),
        "status": "pending_review",
        "stagingArea": "tier2.experiment",
        "reviewedBy": None,
    }
    _save_proposal(proposal)


# ── 主调度函数（dj_queue task 入口）────────────────────────────────────────
def run_daily_evolve_audit() -> Dict[str, Any]:
    """
    每日进化审计主函数，由 management command 或定时 dj_queue 任务调用。
    遍历过去 AUDIT_WINDOW_DAYS 天内的已评分项目，执行低分追溯和高分提炼。
    """
    from .models import Project

    since = timezone.now() - timedelta(days=AUDIT_WINDOW_DAYS)

    # 低分项目
    low_score_projects = (
        Project.objects.filter(
            overall_score__lt=LOW_SCORE_THRESHOLD,
            overall_score__isnull=False,
            updated_at__gte=since,
        )
        .order_by("overall_score")[:MAX_PROJECTS_PER_AUDIT]
    )

    # 高分项目
    high_score_projects = (
        Project.objects.filter(
            overall_score__gte=HIGH_SCORE_THRESHOLD,
            overall_score__isnull=False,
            updated_at__gte=since,
        )
        .order_by("-overall_score")[:MAX_PROJECTS_PER_AUDIT // 2]
    )

    low_count = high_count = 0
    errors = []

    for project in low_score_projects:
        try:
            from .artifact_service import get_artifact

            score_report = get_artifact(project, "score_report") or get_artifact(project, "script_score_report") or {}
            _audit_low_score_project(str(project.id), project.overall_score, score_report)
            low_count += 1
        except Exception as exc:  # noqa: BLE001
            logger.error("[EvolveAudit] 低分追溯失败 project=%s: %s", project.id, exc)
            errors.append(str(project.id))

    for project in high_score_projects:
        try:
            from .artifact_service import get_artifact

            score_report = get_artifact(project, "score_report") or get_artifact(project, "script_score_report") or {}
            _extract_high_score_patterns(str(project.id), project.overall_score, score_report)
            high_count += 1
        except Exception as exc:  # noqa: BLE001
            logger.error("[EvolveAudit] 高分提炼失败 project=%s: %s", project.id, exc)
            errors.append(str(project.id))

    summary = {
        "auditedAt": datetime.utcnow().isoformat(),
        "windowDays": AUDIT_WINDOW_DAYS,
        "lowScoreAudited": low_count,
        "highScoreExtracted": high_count,
        "errors": errors,
        "pendingProposalsDir": str(_PROPOSALS_DIR),
    }
    logger.info("[EvolveAudit] 每日审计完成: %s", summary)
    return summary


def trigger_audit_after_score(project_id: str) -> None:
    """
    ScoreAgent 完成后可调用此函数，根据分数决定触发低分追溯还是高分提炼。
    此函数应在 tasks.py 的 run_agent_post_chain 中异步调用（enqueue_on_commit）。
    """
    from .models import Project

    try:
        project = Project.objects.get(id=project_id)
    except Project.DoesNotExist:
        return

    score = project.overall_score
    if score is None:
        return

    if not _check_budget_headroom():
        logger.info("[EvolveAudit] 预算不足，跳过本次触发 project=%s", project_id)
        return

    from .artifact_service import get_artifact
    score_report = get_artifact(project, "score_report") or get_artifact(project, "script_score_report") or {}

    if score < LOW_SCORE_THRESHOLD:
        logger.info("[EvolveAudit] 触发低分追溯 project=%s score=%.1f", project_id, score)
        _audit_low_score_project(project_id, score, score_report)
    elif score >= HIGH_SCORE_THRESHOLD:
        logger.info("[EvolveAudit] 触发高分提炼 project=%s score=%.1f", project_id, score)
        _extract_high_score_patterns(project_id, score, score_report)
