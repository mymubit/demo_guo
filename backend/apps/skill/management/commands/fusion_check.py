# -*- coding: utf-8 -*-
"""校验网站能否正确挂载 demo4book 融合技能（技能 SSOT，网站只读）。"""
import json

from django.core.management.base import BaseCommand

from apps.workflow.fusion import FusionCliRunner, FusionNodeRegistry, get_artifact_registry, get_fusion_config


class Command(BaseCommand):
    help = "检查 FUSION_SKILL_ROOT 与融合子技能 CLI 是否可用"

    def handle(self, *args, **options):
        cfg = get_fusion_config()
        health = cfg.health()
        self.stdout.write(json.dumps(health, ensure_ascii=False, indent=2))
        if not health.get("ok"):
            self.stderr.write(self.style.ERROR("融合技能健康检查失败"))
            return

        registry = FusionNodeRegistry(cfg)
        art_reg = get_artifact_registry(cfg)
        nodes = registry.pipeline_nodes_legacy_shape()
        self.stdout.write(
            self.style.SUCCESS(
                f"主链 {len(nodes)} 步 · 版本 {cfg.version} · 终点 {cfg.terminal_nodes}"
            )
        )
        for n in nodes:
            key = art_reg.artifact_key_for_index(n["index"])
            self.stdout.write(f"  {n['index']}. {n['name']} ({n['fusion_node_id']}) -> {key}")

        if art_reg.total_main_nodes() != len(nodes):
            self.stderr.write(self.style.ERROR("artifact_registry 与 node_registry 步数不一致"))
            return

        for idx in range(1, art_reg.max_node_index() + 1):
            if not art_reg.artifacts_for_node(idx) and idx <= 5:
                self.stderr.write(self.style.ERROR(f"节点 {idx} 缺少 artifact 映射"))
                return

        try:
            FusionCliRunner(cfg)
            self.stdout.write(self.style.SUCCESS("Node.js CLI 运行环境 OK"))
        except Exception as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            return

        self.stdout.write(self.style.SUCCESS("artifact 映射单源校验通过"))
