# -*- coding: utf-8 -*-
"""一键配置火山方舟 + 智谱原生 GLM-5 + Agent 分模型路由。"""
from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from apps.skill.llm.setup_provisioning import (
    AGENT_PRESET_KEYS,
    NATIVE_PRESET_KEYS,
    NODE_PRESET_KEYS,
    PRESET_ENDPOINT_ENV,
    AgentLlmRoutingService,
)
from apps.skill.llm.providers import LlmProviderService


class Command(BaseCommand):
    help = "同步模型目录、创建火山/智谱 Provider、绑定各 Agent 节点模型"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="仅打印路由计划，不写入数据库",
        )
        parser.add_argument(
            "--plan-only",
            action="store_true",
            help="展示当前路由与 Provider 绑定状态",
        )
        parser.add_argument(
            "--skip-bind",
            action="store_true",
            help="只创建 Provider，不绑定融合节点",
        )

    def handle(self, *args, **options):
        if options["plan_only"]:
            self._print_plan()
            return

        dry_run = bool(options["dry_run"])
        provider_map = AgentLlmRoutingService.provision_all_providers(dry_run=dry_run)

        if dry_run:
            self.stdout.write(self.style.WARNING("dry-run：未写入数据库"))
            self._print_env_checklist()
            return

        if not provider_map:
            self._print_env_checklist()
            raise CommandError(
                "未创建任何 Provider。请配置 VOLCANO_ARK_API_KEY / ZHIPU_API_KEY 等环境变量后重试。"
            )

        LlmProviderService.set_global_enabled(True)

        if not options["skip_bind"]:
            bound_nodes = AgentLlmRoutingService.bind_fusion_node_providers(provider_map)
            bound_agents = AgentLlmRoutingService.bind_agent_route_providers(provider_map)
            self.stdout.write(
                self.style.SUCCESS(
                    f"已绑定 {bound_nodes} 个融合节点、{bound_agents} 个辅助 Agent Provider"
                )
            )

        AgentLlmRoutingService.activate_default_provider(provider_map)
        self.stdout.write(self.style.SUCCESS(f"已创建/更新 {len(provider_map)} 个 Provider"))
        self._print_plan()

    def _print_env_checklist(self) -> None:
        self.stdout.write("\n火山方舟（Model ID 或 ep-xxx）：")
        self.stdout.write("  VOLCANO_ARK_API_KEY=方舟 API Key")
        self.stdout.write("  VOLCANO_ARK_KEY_TYPE=coding_plan  # Coding Plan / Agent Plan 订阅 Key（推荐）")
        self.stdout.write("  VOLCANO_ARK_KEY_TYPE=payg          # 按量付费 Key")
        self.stdout.write("  未设置 VOLCANO_EP_* 时，自动使用目录 Model ID（如 deepseek-v4-flash）")
        for preset in sorted(set(NODE_PRESET_KEYS.values()) | set(AGENT_PRESET_KEYS.values())):
            if preset in NATIVE_PRESET_KEYS:
                continue
            env_name = PRESET_ENDPOINT_ENV.get(preset, "")
            if env_name:
                self.stdout.write(f"  {env_name}=ep-xxx  (可选，preset: {preset})")

        self.stdout.write("\n智谱原生（GLM-5）：")
        self.stdout.write("  ZHIPU_API_KEY=智谱 API Key")
        self.stdout.write("  ZHIPU_GLM5_MODEL=glm-5  (可选，默认 glm-5)")

    def _print_plan(self) -> None:
        plan = AgentLlmRoutingService.routing_plan()
        self.stdout.write("\n=== Agent 模型路由 ===\n")
        self.stdout.write(f"火山 Base URL: {plan['volcano_base_url']}")
        self.stdout.write(f"火山 Key 类型: {plan.get('volcano_key_type', 'payg')}")
        self.stdout.write(f"火山 API Key: {'已配置' if plan['volcano_api_key_set'] else '未配置'}")
        self.stdout.write(f"智谱 API Key: {'已配置' if plan['zhipu_api_key_set'] else '未配置'}\n")

        self.stdout.write("主链节点：")
        for node_id, preset in NODE_PRESET_KEYS.items():
            meta = plan["nodes"][node_id]
            channel = meta.get("channel", "?")
            pid = meta.get("provider_id") or "未绑定"
            self.stdout.write(f"  {node_id} → {preset} [{channel}] → {pid}")

        self.stdout.write("\n辅助 Agent：")
        for agent_id, preset in AGENT_PRESET_KEYS.items():
            meta = plan["agents"][agent_id]
            channel = meta.get("channel", "?")
            pid = meta.get("provider_id") or "未绑定"
            self.stdout.write(f"  {agent_id} → {preset} [{channel}] → {pid}")
