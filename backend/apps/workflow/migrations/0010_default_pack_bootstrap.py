# P1-2 阶段：数据引导 —— 为短剧创作场景创建默认 FusionPipelinePack + Nodes
# 覆盖创作全链路 7 节点：brief / structure / character / outline / script / review / polish
# 每个节点通过 runner_path 路由到 workspace_bridge.run_workspace_node()
#   → 由旧 AgentOrchestrator 体系执行具体 Agent
# 新引擎（WorkflowEngine + SkillBridge）消费这些节点。
from django.db import migrations

WORKFLOW_RUNNER_PATH = "apps.creation.orchestration.workspace_bridge.run_workspace_node"

DEFAULT_NODES = [
    {
        "fusion_node_id": "node_brief",
        "name": "立项定义",
        "description": "用户需求 → 项目立项 brief（脚本定位、主题、风格）",
        "chain_order": 1,
        "runner_type": "fusion_node",
        "skill_id": "",
        "coin_cost": 10,
        "extra_config": {},
    },
    {
        "fusion_node_id": "node_structure",
        "name": "结构规划",
        "description": "集数、反转点、节奏分布、act 结构",
        "chain_order": 2,
        "runner_type": "fusion_node",
        "skill_id": "",
        "coin_cost": 10,
        "extra_config": {},
    },
    {
        "fusion_node_id": "node_character",
        "name": "角色塑造",
        "description": "主角、配角、反派的人设/动机/目标，生成角色库",
        "chain_order": 3,
        "runner_type": "fusion_node",
        "skill_id": "",
        "coin_cost": 10,
        "extra_config": {},
    },
    {
        "fusion_node_id": "node_outline",
        "name": "分集大纲",
        "description": "每集大纲 + 场景列表 + 对白骨架",
        "chain_order": 4,
        "runner_type": "fusion_node",
        "skill_id": "",
        "coin_cost": 20,
        "extra_config": {},
    },
    {
        "fusion_node_id": "node_script",
        "name": "剧本生成",
        "description": "逐集完整剧本（对白 / 舞台提示 / 场景标题）",
        "chain_order": 5,
        "runner_type": "fusion_node",
        "skill_id": "",
        "coin_cost": 30,
        "extra_config": {},
    },
    {
        "fusion_node_id": "node_review",
        "name": "AI 质检",
        "description": "AI 驱动质检：一致性、逻辑、节奏、对白质量",
        "chain_order": 6,
        "runner_type": "fusion_review",
        "skill_id": "",
        "coin_cost": 15,
        "extra_config": {},
    },
    {
        "fusion_node_id": "node_polish",
        "name": "润色优化",
        "description": "依据质检报告进行剧本润色与重写",
        "chain_order": 7,
        "runner_type": "fusion_node",
        "skill_id": "",
        "coin_cost": 20,
        "extra_config": {},
    },
]


def _create_default_pack(apps, schema_editor):
    FusionPipelinePack = apps.get_model("workflow", "FusionPipelinePack")
    FusionPipelineNode = apps.get_model("workflow", "FusionPipelineNode")

    # 确保幂等：已存在同名 pack 则跳过
    pack, created = FusionPipelinePack.objects.get_or_create(
        slug="short-drama-v1",
        defaults={
            "version": "short-drama-v1.0",
            "display_name": "短剧创作标准流程 v1",
            "description": "短剧剧本创作标准工作流：立项 → 结构 → 角色 → 大纲 → 剧本 → 质检 → 润色",
            "is_active": True,
            "is_published_to_portal": True,
            "is_default_for_creation": True,
            "pack_status": "active",
            "gray_weight": 100,
            "engine_config": {
                "enabled": True,
                "gray_weight": 100,
                "gray_traffic_salt": "short-drama-v1",
                "max_retries": 3,
                "timeout_seconds": 1800,
                "heartbeat_interval_seconds": 60,
            },
            "terminal_node_ids": ["node_polish"],
        },
    )

    if not created:
        # 已存在 pack，不再重新创建节点
        return

    for meta in DEFAULT_NODES:
        FusionPipelineNode.objects.create(
            pack=pack,
            fusion_node_id=meta["fusion_node_id"],
            name=meta["name"],
            description=meta["description"],
            chain_order=meta["chain_order"],
            website_index=meta["chain_order"],
            runner_type=meta["runner_type"],
            runner_path=WORKFLOW_RUNNER_PATH,
            skill_id=meta.get("skill_id", ""),
            coin_cost=meta["coin_cost"],
            extra_config=meta.get("extra_config", {}),
            runtime_config={
                "timeout_seconds": 600,
                "retry_policy": {"max_retries": 3, "backoff": "exponential", "base_seconds": 2},
                "allow_skip": False,
                "is_checkpoint": True,
            },
        )


def _rollback_default_pack(apps, schema_editor):
    FusionPipelinePack = apps.get_model("workflow", "FusionPipelinePack")
    try:
        pack = FusionPipelinePack.objects.get(slug="short-drama-v1")
        pack.delete()
    except FusionPipelinePack.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0009_fusionpipelinenode_skill_id"),
    ]

    operations = [
        migrations.RunPython(_create_default_pack, _rollback_default_pack),
    ]
