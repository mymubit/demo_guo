# -*- coding: utf-8 -*-
"""
种入 drama-skills 36个角色到 AgentDefinition。

用法：
  python manage.py seed_drama_skills
  python manage.py seed_drama_skills --force  # 强制更新已存在的角色
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.agent.models import AgentDefinition, AgentLlmRouteConfig, AgentPromptVersion
from apps.drama.defaults import (
    DRAMA_DEPARTMENTS, DRAMA_FAST_TRACK_ROLES, DRAMA_ROLE_DEFAULTS, DRAMA_VISIBLE_ROLES,
)


class Command(BaseCommand):
    help = "种入 drama-skills 36个专业角色到 AgentDefinition 表。"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            default=False,
            help="强制更新已存在的角色（会覆盖system_prompt等字段）",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="只打印将要创建的角色，不实际写入",
        )

    def handle(self, *args, **options):
        force = options["force"]
        dry_run = options["dry_run"]

        visible_count = len(DRAMA_VISIBLE_ROLES)
        total_count = len(DRAMA_ROLE_DEFAULTS)
        self.stdout.write(f"开始种入 drama-skills 角色 (force={force}, dry_run={dry_run})")
        self.stdout.write(
            f"总计 {total_count} 个角色（可见 {visible_count} 个：8核心+4复合，"
            f"其余 {total_count - visible_count} 个标记hidden不在UI展示）"
        )

        if dry_run:
            for role in DRAMA_ROLE_DEFAULTS:
                track = "⚡快速通道" if role["agent_id"] in DRAMA_FAST_TRACK_ROLES else "  专家通道"
                self.stdout.write(f"  {track} [{role['dept']:12}] {role['agent_id']:35} {role['name_zh']}")
            self.stdout.write(self.style.SUCCESS("Dry run 完成，未写入任何数据"))
            return

        created_count = 0
        updated_count = 0
        skipped_count = 0

        with transaction.atomic():
            for role in DRAMA_ROLE_DEFAULTS:
                agent_id = role["agent_id"]
                is_fast_track = agent_id in DRAMA_FAST_TRACK_ROLES

                defaults = {
                    "name": role["name"],
                    "name_zh": role["name_zh"],
                    "description": role["description"],
                    "category": "drama_skills",
                    "workspace_order": role["workspace_order"],
                    "is_enabled": True,
                    "is_system": True,
                    "version": "v1",
                    "lifecycle_status": AgentDefinition.LifecycleStatus.ACTIVE,
                    "default_output_artifact_key": role["default_output_artifact_key"],
                    "input_contract": role.get("input_contract") or {},
                    "output_contract": role.get("output_contract") or {},
                    "runtime_policy": role.get("runtime_policy") or {},
                    "ui_schema": {
                        "dept": role["dept"],
                        "is_fast_track": is_fast_track,
                        "is_composite": agent_id in {
                            "drama.market-analyst", "drama.narrative-engineer",
                            "drama.polish-master", "drama.production-pack",
                        },
                        "is_visible": agent_id in DRAMA_VISIBLE_ROLES,
                        "hidden": role.get("hidden", False),
                        "dept_order": role["workspace_order"] // 100,
                        "tier": role.get("tier", 3),
                    },
                }

                try:
                    agent, was_created = AgentDefinition.objects.get_or_create(
                        agent_id=agent_id,
                        defaults=defaults,
                    )

                    if was_created:
                        created_count += 1
                        self.stdout.write(self.style.SUCCESS(f"  ✅ 创建: {agent_id} ({role['name_zh']})"))
                    elif force:
                        for key, value in defaults.items():
                            setattr(agent, key, value)
                        agent.save()
                        updated_count += 1
                        self.stdout.write(f"  🔄 更新: {agent_id} ({role['name_zh']})")
                    else:
                        skipped_count += 1
                        self.stdout.write(f"  ⏭️  跳过: {agent_id} (已存在，使用 --force 强制更新)")

                    # 创建或更新 Prompt 版本
                    prompt_defaults = {
                        "system_prompt": role.get("system_prompt", ""),
                        "user_prompt_template": _build_user_prompt_template(role),
                        "output_format_prompt": (
                            "输出必须是合法JSON对象；遵循对应schema；"
                            "顶层用artifact_key标记产物，不得自创schema外字段。"
                        ),
                        "constraints_prompt": (
                            "不得触发其他Agent；不得引用不存在的文件路径；"
                            "不得输出非JSON文本；严格遵守短剧商业格式规范。"
                        ),
                        "few_shot_examples": [],
                        "is_active": True,
                        "change_notes": "drama-skills v3.0 初始化",
                        "created_by": "seed_drama_skills",
                    }

                    if was_created or force:
                        AgentPromptVersion.objects.update_or_create(
                            agent=agent,
                            version="v1",
                            defaults=prompt_defaults,
                        )

                    # 创建 LLM 路由配置（默认使用全局配置，可在Admin中覆盖）
                    runtime = role.get("runtime_policy", {})
                    AgentLlmRouteConfig.objects.get_or_create(
                        route_key=agent_id,
                        defaults={
                            "agent": agent,
                            "display_name": f"{role['name_zh']} ({role['name']})",
                            "max_tokens": runtime.get("max_completion_tokens", 8000),
                            "max_prompt_tokens": runtime.get("max_prompt_tokens", 20000),
                            "max_completion_tokens": runtime.get("max_completion_tokens", 8000),
                            "timeout_seconds": 600,
                            "temperature": runtime.get("temperature", 0.7),
                            "is_active": True,
                            "sort_order": role["workspace_order"],
                        },
                    )

                except Exception as exc:  # noqa: BLE001
                    self.stdout.write(self.style.ERROR(f"  ❌ 失败: {agent_id} - {exc}"))

        # ── 清理数据库中不再属于 DRAMA_ROLE_DEFAULTS 的旧角色 ──
        self.stdout.write("")
        self.stdout.write("正在清理已废弃的旧角色…")
        current_ids = {r["agent_id"] for r in DRAMA_ROLE_DEFAULTS}
        stale_agents = AgentDefinition.objects.filter(
            category="drama_skills",
            agent_id__startswith="drama.",
        ).exclude(agent_id__in=current_ids)

        deleted_agent_count = 0
        for stale in stale_agents:
            # 同时清理关联的路由配置和提示词版本
            AgentLlmRouteConfig.objects.filter(route_key=stale.agent_id).delete()
            AgentLlmRouteConfig.objects.filter(agent=stale).delete()
            stale.delete()
            deleted_agent_count += 1
            self.stdout.write(self.style.WARNING(f"  🗑️  删除: {stale.agent_id} ({stale.name_zh})"))

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"完成！创建 {created_count} 个，更新 {updated_count} 个，跳过 {skipped_count} 个，"
            f"清理 {deleted_agent_count} 个废弃角色"
        ))
        self.stdout.write(f"当前可用角色: {len(DRAMA_ROLE_DEFAULTS)} 个")
        self.stdout.write(f"快速通道角色: {len(DRAMA_FAST_TRACK_ROLES)} 个")


def _build_user_prompt_template(role: dict) -> str:
    """生成标准化的用户Prompt模板。"""
    return f"""# {role['name_zh']} 执行请求

## 项目信息
{{{{ project_brief }}}}

## 上游产物
{{{{ artifacts }}}}

## 知识与规则（Tier1-4）
{{{{ knowledge }}}}

## 运行参数
{{{{ params }}}}

---
请严格按照 {role['name_zh']} 的职责执行，输出合法JSON对象，遵循 {role['output_contract'].get('schema_version', 'v1')} schema。
"""
