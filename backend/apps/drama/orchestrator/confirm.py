# -*- coding: utf-8 -*-
"""V3 同步确认命令：candidate → committed，并推进项目阶段。"""
from __future__ import annotations

import copy

from django.db import transaction

from apps.drama.models import V3ArtifactVersion, V3CommandRun, V3Project, V3ScriptDraft
from apps.drama.orchestrator.artifacts import latest, next_version
from apps.drama.skills_bridge.recipe_map import recipe_for
from apps.drama.skills_bridge.validate import validate_artifact_payload

_TOPIC_KEY = "project_brief"
_BLUEPRINT_KEYS = tuple(recipe_for("generate_blueprint")["writes"])
_EPISODE_PLAN_KEY = "episode_plan"
_SCRIPT_KEY = "episode_scripts"
_MEMORY_KEY = "memory_checkpoint"
_SCRIPT_KEYS = tuple(recipe_for("write_episode_batch")["writes"])
_DRAFT_REVISION_NOTE = "人工已修订正文，续写须对齐最新脚本"


class ConfirmError(Exception):
    """确认失败（人话消息）。"""


def _resolve_project(*, owner, payload: dict) -> V3Project:
    project_id = (payload or {}).get("project_id")
    if not project_id:
        raise ConfirmError("缺少项目，请先打开一个创作项目")
    try:
        project = V3Project.objects.get(id=project_id, owner=owner)
    except (V3Project.DoesNotExist, ValueError, TypeError) as exc:
        raise ConfirmError("项目不存在或无权访问") from exc
    return project


def _pick_candidates(
    *,
    project: V3Project,
    keys: list[str],
    artifact_version_ids: list | None,
) -> dict[str, V3ArtifactVersion]:
    if artifact_version_ids:
        selected = list(
            V3ArtifactVersion.objects.filter(
                project=project,
                id__in=artifact_version_ids,
                status=V3ArtifactVersion.Status.CANDIDATE,
            )
        )
        by_key = {item.artifact_key: item for item in selected}
        missing = [key for key in keys if key not in by_key]
        if missing:
            raise ConfirmError(f"缺少待确认候选产物：{'、'.join(missing)}")
        return {key: by_key[key] for key in keys}

    result: dict[str, V3ArtifactVersion] = {}
    missing: list[str] = []
    for key in keys:
        art = latest(project, key, status=V3ArtifactVersion.Status.CANDIDATE)
        if art is None:
            missing.append(key)
        else:
            result[key] = art
    if missing:
        raise ConfirmError(f"缺少待确认候选产物：{'、'.join(missing)}")
    return result


def _commit_candidates(
    *,
    project: V3Project,
    candidates: dict[str, V3ArtifactVersion],
) -> list[str]:
    committed_ids: list[str] = []
    for key, candidate in candidates.items():
        # 旧 committed 与同 key 其它 candidate 一并 superseded，避免残留多候选
        V3ArtifactVersion.objects.filter(
            project=project,
            artifact_key=key,
            status__in=(
                V3ArtifactVersion.Status.COMMITTED,
                V3ArtifactVersion.Status.CANDIDATE,
            ),
        ).exclude(id=candidate.id).update(status=V3ArtifactVersion.Status.SUPERSEDED)
        candidate.status = V3ArtifactVersion.Status.COMMITTED
        candidate.save(update_fields=["status"])
        committed_ids.append(str(candidate.id))
    return committed_ids


def _commit_topic_draft(*, project: V3Project) -> list[str]:
    draft = latest(project, _TOPIC_KEY, status=V3ArtifactVersion.Status.DRAFT)
    if draft is None:
        raise ConfirmError("没有可确认的草稿，请先保存草稿")
    V3ArtifactVersion.objects.filter(
        project=project,
        artifact_key=_TOPIC_KEY,
        status=V3ArtifactVersion.Status.COMMITTED,
    ).exclude(id=draft.id).update(status=V3ArtifactVersion.Status.SUPERSEDED)
    V3ArtifactVersion.objects.filter(
        project=project,
        artifact_key=_TOPIC_KEY,
        status=V3ArtifactVersion.Status.CANDIDATE,
    ).exclude(id=draft.id).update(status=V3ArtifactVersion.Status.SUPERSEDED)
    draft.status = V3ArtifactVersion.Status.COMMITTED
    draft.save(update_fields=["status"])
    return [str(draft.id)]


def confirm_topic_brief(*, owner, payload: dict) -> dict:
    """确认选题简报；stage topic→blueprint。支持 use_draft 提交草稿。"""
    project = _resolve_project(owner=owner, payload=payload)
    use_draft = bool((payload or {}).get("use_draft"))
    version_ids = (payload or {}).get("artifact_version_ids")
    with transaction.atomic():
        if use_draft:
            committed_ids = _commit_topic_draft(project=project)
        else:
            candidates = _pick_candidates(
                project=project,
                keys=[_TOPIC_KEY],
                artifact_version_ids=version_ids,
            )
            committed_ids = _commit_candidates(project=project, candidates=candidates)
        if project.stage == V3Project.Stage.TOPIC:
            project.stage = V3Project.Stage.BLUEPRINT
            project.save(update_fields=["stage", "updated_at"])
    return {"artifact_ids": committed_ids, "stage": project.stage}


def confirm_blueprint(*, owner, payload: dict) -> dict:
    """确认蓝图五产物；stage→episodes。"""
    project = _resolve_project(owner=owner, payload=payload)
    version_ids = (payload or {}).get("artifact_version_ids")
    with transaction.atomic():
        candidates = _pick_candidates(
            project=project,
            keys=list(_BLUEPRINT_KEYS),
            artifact_version_ids=version_ids,
        )
        committed_ids = _commit_candidates(project=project, candidates=candidates)
        project.stage = V3Project.Stage.EPISODES
        project.save(update_fields=["stage", "updated_at"])
    return {"artifact_ids": committed_ids, "stage": project.stage}


def confirm_episode_plan(*, owner, payload: dict) -> dict:
    """确认分集规划候选；当前 stage=episodes 时推进到 writing。"""
    project = _resolve_project(owner=owner, payload=payload)
    version_ids = (payload or {}).get("artifact_version_ids")
    with transaction.atomic():
        candidates = _pick_candidates(
            project=project,
            keys=[_EPISODE_PLAN_KEY],
            artifact_version_ids=version_ids,
        )
        committed_ids = _commit_candidates(project=project, candidates=candidates)
        if project.stage == V3Project.Stage.EPISODES:
            project.stage = V3Project.Stage.WRITING
            project.save(update_fields=["stage", "updated_at"])
    return {"artifact_ids": committed_ids, "stage": project.stage}


def _scenes_to_script(draft_payload: dict) -> str:
    """将 V3ScriptDraft 的 scenes/beats 转为 episode_scripts.script 文本。"""
    lines: list[str] = []
    for scene in (draft_payload or {}).get("scenes") or []:
        if not isinstance(scene, dict):
            continue
        heading = str(scene.get("heading") or "").strip()
        if heading:
            lines.append(heading)
        for beat in scene.get("beats") or []:
            if not isinstance(beat, dict):
                continue
            text = str(beat.get("text") or "").strip()
            if beat.get("type") == "dialogue":
                character = str(beat.get("character") or "").strip()
                lines.append(f"{character}: {text}" if character else text)
            elif text:
                lines.append(text)
    return "\n".join(line for line in lines if line).strip()


def _merge_script_drafts(*, project: V3Project) -> dict:
    """将各集 draft 合并进已有 scripts 结构，并校验 schema。"""
    drafts = list(
        V3ScriptDraft.objects.filter(project=project).order_by("episode_number")
    )
    if not drafts:
        raise ConfirmError("没有可确认的正文草稿，请先保存各集草稿")

    base = latest(
        project, _SCRIPT_KEY, status=V3ArtifactVersion.Status.COMMITTED
    ) or latest(project, _SCRIPT_KEY, status=V3ArtifactVersion.Status.CANDIDATE)
    if base is None:
        raise ConfirmError("没有可合并的正文底稿，请先生成正文候选或确认正式版")

    merged = copy.deepcopy(base.payload or {})
    episodes = list(merged.get("episodes") or [])
    by_num = {
        ep.get("episode_number"): ep
        for ep in episodes
        if isinstance(ep, dict) and isinstance(ep.get("episode_number"), int)
    }
    for draft in drafts:
        ep = by_num.get(draft.episode_number)
        if ep is None:
            raise ConfirmError(
                f"第 {draft.episode_number} 集草稿无法合并：底稿中尚无该集"
            )
        script_text = _scenes_to_script(draft.payload or {})
        if not script_text:
            raise ConfirmError(f"第 {draft.episode_number} 集草稿正文为空，请补充后再确认")
        scenes = (draft.payload or {}).get("scenes") or []
        ep["script"] = script_text
        ep["scene_count"] = max(1, len(scenes) if isinstance(scenes, list) else 1)
        ep["word_count"] = max(1, len(script_text))
        dialogue_beats = 0
        total_beats = 0
        for scene in scenes if isinstance(scenes, list) else []:
            if not isinstance(scene, dict):
                continue
            for beat in scene.get("beats") or []:
                if not isinstance(beat, dict):
                    continue
                total_beats += 1
                if beat.get("type") == "dialogue":
                    dialogue_beats += 1
        if total_beats > 0:
            ep["dialogue_ratio"] = round(dialogue_beats / total_beats, 4)

    merged["episodes"] = sorted(
        by_num.values(), key=lambda item: item.get("episode_number") or 0
    )
    errors = validate_artifact_payload(_SCRIPT_KEY, merged)
    if errors:
        raise ConfirmError(f"正文草稿校验未通过：{errors[0]}")
    return merged


def _max_episode_number(scripts_payload: dict) -> int:
    max_ep = 0
    for ep in scripts_payload.get("episodes") or []:
        if not isinstance(ep, dict):
            continue
        num = ep.get("episode_number")
        if isinstance(num, int) and num > max_ep:
            max_ep = num
    return max_ep if max_ep >= 1 else 1


def _minimal_memory_checkpoint(*, episode: int) -> dict:
    """无既有检查点时构造可通过 schema 校验的最小 payload。"""
    return {
        "episode": episode,
        "character_states": [],
        "active_clues": [],
        "foreshadowing": [],
        "rhythm_state": {
            "plot_pace": "medium",
            "emotion_pace": "medium",
            "episode_ev": 5,
        },
        "next_episode_constraints": [_DRAFT_REVISION_NOTE],
    }


def _refresh_memory_checkpoint_after_drafts(
    *,
    project: V3Project,
    scripts_payload: dict,
) -> str:
    """合并草稿后刷新 committed memory_checkpoint（与 scripts 同事务）。"""
    max_ep = _max_episode_number(scripts_payload)
    base = latest(
        project, _MEMORY_KEY, status=V3ArtifactVersion.Status.COMMITTED
    ) or latest(project, _MEMORY_KEY, status=V3ArtifactVersion.Status.CANDIDATE)
    if base is not None:
        checkpoint = copy.deepcopy(base.payload or {})
    else:
        checkpoint = _minimal_memory_checkpoint(episode=max_ep)

    checkpoint["episode"] = max_ep
    constraints = checkpoint.get("next_episode_constraints")
    if not isinstance(constraints, list):
        constraints = []
    else:
        constraints = list(constraints)
    if _DRAFT_REVISION_NOTE not in constraints:
        constraints.append(_DRAFT_REVISION_NOTE)
    checkpoint["next_episode_constraints"] = constraints

    errors = validate_artifact_payload(_MEMORY_KEY, checkpoint)
    if errors:
        raise ConfirmError(f"记忆检查点校验未通过：{errors[0]}")

    V3ArtifactVersion.objects.filter(
        project=project,
        artifact_key=_MEMORY_KEY,
        status__in=(
            V3ArtifactVersion.Status.COMMITTED,
            V3ArtifactVersion.Status.CANDIDATE,
        ),
    ).update(status=V3ArtifactVersion.Status.SUPERSEDED)
    art = V3ArtifactVersion.objects.create(
        project=project,
        artifact_key=_MEMORY_KEY,
        version=next_version(project.id, _MEMORY_KEY),
        status=V3ArtifactVersion.Status.COMMITTED,
        payload=checkpoint,
    )
    return str(art.id)


def _commit_script_drafts(*, project: V3Project) -> list[str]:
    """use_drafts=true：合并草稿为新 committed episode_scripts，并刷新 memory_checkpoint。"""
    merged = _merge_script_drafts(project=project)
    V3ArtifactVersion.objects.filter(
        project=project,
        artifact_key=_SCRIPT_KEY,
        status__in=(
            V3ArtifactVersion.Status.COMMITTED,
            V3ArtifactVersion.Status.CANDIDATE,
        ),
    ).update(status=V3ArtifactVersion.Status.SUPERSEDED)
    scripts_art = V3ArtifactVersion.objects.create(
        project=project,
        artifact_key=_SCRIPT_KEY,
        version=next_version(project.id, _SCRIPT_KEY),
        status=V3ArtifactVersion.Status.COMMITTED,
        payload=merged,
    )
    checkpoint_id = _refresh_memory_checkpoint_after_drafts(
        project=project,
        scripts_payload=merged,
    )
    return [str(scripts_art.id), checkpoint_id]


def confirm_script_candidate(*, owner, payload: dict) -> dict:
    """确认正文候选；支持 use_drafts 合并人工草稿为新 committed。不强制改 stage。"""
    project = _resolve_project(owner=owner, payload=payload)
    use_drafts = bool((payload or {}).get("use_drafts"))
    version_ids = (payload or {}).get("artifact_version_ids")
    with transaction.atomic():
        if use_drafts:
            committed_ids = _commit_script_drafts(project=project)
        else:
            candidates = _pick_candidates(
                project=project,
                keys=list(_SCRIPT_KEYS),
                artifact_version_ids=version_ids,
            )
            committed_ids = _commit_candidates(project=project, candidates=candidates)
    return {"artifact_ids": committed_ids, "stage": project.stage}


def run_confirm_command(
    *,
    owner,
    command_type: str,
    payload: dict,
    idempotency_key: str = "",
) -> V3CommandRun:
    """同步确认命令入口：创建 run 并执行 confirm_*。"""
    with transaction.atomic():
        run = V3CommandRun.objects.create(
            owner=owner,
            command_type=command_type,
            status=V3CommandRun.Status.RUNNING,
            idempotency_key=idempotency_key or "",
            request_payload=payload or {},
        )
        try:
            project = _resolve_project(owner=owner, payload=payload or {})
            run.project = project
            run.save(update_fields=["project", "updated_at"])
            if command_type == "confirm_topic_brief":
                result = confirm_topic_brief(owner=owner, payload=payload or {})
            elif command_type == "confirm_blueprint":
                result = confirm_blueprint(owner=owner, payload=payload or {})
            elif command_type == "confirm_episode_plan":
                result = confirm_episode_plan(owner=owner, payload=payload or {})
            elif command_type == "confirm_script_candidate":
                result = confirm_script_candidate(owner=owner, payload=payload or {})
            else:
                raise ConfirmError("未知确认命令")
            run.status = V3CommandRun.Status.SUCCEEDED
            run.result_payload = result
            run.error_message = ""
            run.save(
                update_fields=["status", "result_payload", "error_message", "updated_at"]
            )
        except ConfirmError as exc:
            run.status = V3CommandRun.Status.FAILED
            run.error_message = str(exc)
            run.save(update_fields=["status", "error_message", "updated_at"])
        return run
