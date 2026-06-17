# P2-1 阶段：为 7 个创作业务技能注册到 AgentSkillDefinition
# 让 SkillBridge 通过 skill_id 路由到 SkillInvoker.invoke()
#
# 7 个业务技能：
#   creation.brief          - 立项定义（theme/core_idea → 完整 brief）
#   creation.structure      - 结构规划（集数/反转点/节奏）
#   creation.character      - 角色塑造（主角/配角/反派）
#   creation.outline        - 分集大纲（场景/对白骨架）
#   creation.script         - 剧本生成（完整对白/舞台提示）
#   creation.review         - AI 质检（一致性/节奏/质量分）
#   creation.polish         - 润色优化（基于质检报告重写）
#
# 全部为 lifecycle_status=active, skill_layer=business, category=creator
from django.db import migrations


SKILL_CATALOG = [
    {
        "skill_id": "creation.brief",
        "name": "立项定义",
        "version": "1.0.0",
        "category": "creator",
        "skill_layer": "business",
        "sub_category": "立项",
        "lifecycle_status": "active",
        "gray_weight": 100,
        "quota_cost": 10,
        "timeout_seconds": 180,
        "system_hint": (
            "你是一名专业的短剧剧本策划。基于用户输入的主题、核心创意、目标受众和参考作品，"
            "生成一个完整的项目立项方案（Project Brief），包括：剧本定位、主题阐述、目标受众画像、"
            "风格调性、情感卖点、潜在风险。\n\n"
            "输出 JSON 格式：\n"
            "{\n"
            '  "positioning": "剧本一句话定位",\n'
            '  "theme_summary": "主题与价值观阐述",\n'
            '  "audience_profile": "目标受众画像",\n'
            '  "tone": "整体风格调性",\n'
            '  "selling_points": ["卖点1", "卖点2"],\n'
            '  "risks": ["潜在风险1"]\n'
            "}"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "theme": {"type": "string", "description": "题材关键词"},
                "core_idea": {"type": "string", "description": "核心创意描述"},
                "audience": {"type": "string"},
                "reference_work": {"type": "string"},
            },
            "required": ["theme", "core_idea"],
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "positioning": {"type": "string"},
                "theme_summary": {"type": "string"},
                "audience_profile": {"type": "string"},
                "tone": {"type": "string"},
                "selling_points": {"type": "array", "items": {"type": "string"}},
                "risks": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["positioning", "theme_summary"],
        },
        "tags": ["短剧", "立项", "brief"],
    },
    {
        "skill_id": "creation.structure",
        "name": "结构规划",
        "version": "1.0.0",
        "category": "creator",
        "skill_layer": "business",
        "sub_category": "结构",
        "lifecycle_status": "active",
        "gray_weight": 100,
        "quota_cost": 10,
        "timeout_seconds": 240,
        "system_hint": (
            "你是短剧结构规划专家。基于项目立项方案，规划：\n"
            "1. 集数与单集时长\n"
            "2. 起承转合的 Act 划分\n"
            "3. 关键反转点位置\n"
            "4. 节奏曲线（紧张-放松-冲突）\n"
            "5. 钩子设置（每集结尾）\n\n"
            "输出 JSON 格式：\n"
            "{\n"
            '  "episode_count": 30,\n'
            '  "acts": [{"name": "第一幕", "episodes": "1-8", "purpose": "..."}],\n'
            '  "plot_twists": [{"episode": 8, "type": "大反转", "description": "..."}],\n'
            '  "pacing_curve": [0.3, 0.4, 0.6, 0.5, 0.7, 0.8, 0.9],\n'
            '  "hooks": [{"episode": 1, "hook": "..."}]\n'
            "}"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "brief": {"type": "object"},
                "episode_count": {"type": "integer"},
                "target_platform": {"type": "string"},
            },
            "required": ["brief", "episode_count"],
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "episode_count": {"type": "integer"},
                "acts": {"type": "array"},
                "plot_twists": {"type": "array"},
                "pacing_curve": {"type": "array"},
                "hooks": {"type": "array"},
            },
            "required": ["episode_count", "acts"],
        },
        "tags": ["短剧", "结构", "节奏"],
    },
    {
        "skill_id": "creation.character",
        "name": "角色塑造",
        "version": "1.0.0",
        "category": "creator",
        "skill_layer": "business",
        "sub_category": "人设",
        "lifecycle_status": "active",
        "gray_weight": 100,
        "quota_cost": 15,
        "timeout_seconds": 240,
        "system_hint": (
            "你是角色塑造专家。基于项目立项和结构规划，设计完整角色库。\n"
            "每位角色需要：\n"
            "- 基本信息（姓名/年龄/职业）\n"
            "- 核心动机（推动剧情的核心欲望/恐惧）\n"
            "- 性格特质（2-3 个标签）\n"
            "- 人物弧光（在剧中的成长或转变）\n"
            "- 关键关系（与其他角色的羁绊）\n\n"
            "至少 3 个角色（主角/对手/导师），输出 JSON 数组。\n"
            "示例：\n"
            '[{"name": "林晚晴", "role": "主角", "motivation": "...", "arc": "..."}]'
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "brief": {"type": "object"},
                "structure": {"type": "object"},
            },
            "required": ["brief"],
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "characters": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "role": {"type": "string"},
                            "background": {"type": "string"},
                            "motivation": {"type": "string"},
                            "traits": {"type": "array"},
                            "arc": {"type": "string"},
                            "relationships": {"type": "array"},
                        },
                        "required": ["name", "motivation"],
                    },
                },
            },
            "required": ["characters"],
        },
        "tags": ["短剧", "人设", "角色"],
    },
    {
        "skill_id": "creation.outline",
        "name": "分集大纲",
        "version": "1.0.0",
        "category": "creator",
        "skill_layer": "business",
        "sub_category": "大纲",
        "lifecycle_status": "active",
        "gray_weight": 100,
        "quota_cost": 20,
        "timeout_seconds": 300,
        "system_hint": (
            "你是分集大纲撰写专家。基于项目立项、结构和角色库，"
            "为每一集生成：\n"
            "- 集标题（一句话点题）\n"
            "- 场景列表（每集 3-5 个场景）\n"
            "- 关键对白骨架（不超过 3 句）\n"
            "- 钩子（结尾）\n"
            "- 节奏指标（紧张度 0-1）\n\n"
            "输出 JSON 数组，每集一个对象。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "brief": {"type": "object"},
                "structure": {"type": "object"},
                "characters": {"type": "array"},
                "episode_from": {"type": "integer"},
                "episode_to": {"type": "integer"},
            },
            "required": ["brief", "structure", "characters"],
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "outlines": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "episode": {"type": "integer"},
                            "title": {"type": "string"},
                            "scenes": {"type": "array"},
                            "key_dialogues": {"type": "array"},
                            "hook": {"type": "string"},
                            "tension_level": {"type": "number"},
                        },
                        "required": ["episode", "title", "scenes"],
                    },
                },
            },
            "required": ["outlines"],
        },
        "tags": ["短剧", "大纲", "分集"],
    },
    {
        "skill_id": "creation.script",
        "name": "剧本生成",
        "version": "1.0.0",
        "category": "creator",
        "skill_layer": "business",
        "sub_category": "剧本",
        "lifecycle_status": "active",
        "gray_weight": 100,
        "quota_cost": 30,
        "timeout_seconds": 600,
        "system_hint": (
            "你是短剧剧本撰写专家。基于大纲生成完整剧本，要求：\n"
            "- 场景标题清晰\n"
            "- 角色对白生动、有节奏感\n"
            "- 舞台提示精炼（动作/表情/情绪）\n"
            "- 节奏紧凑、无废话\n"
            "- 符合短视频特性（每集 2 分钟左右，1000-1500 字）\n\n"
            "格式：\n"
            "## 第 N 集：标题\n\n"
            "### 场景 1：地点/时间\n"
            "**角色名**：（动作/表情）台词\n\n"
            "### 场景 2：...\n"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "outlines": {"type": "array"},
                "characters": {"type": "array"},
                "episode_from": {"type": "integer"},
                "episode_to": {"type": "integer"},
            },
            "required": ["outlines", "characters"],
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "scripts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "episode": {"type": "integer"},
                            "title": {"type": "string"},
                            "content": {"type": "string"},
                            "word_count": {"type": "integer"},
                        },
                        "required": ["episode", "title", "content"],
                    },
                },
            },
            "required": ["scripts"],
        },
        "tags": ["短剧", "剧本", "对白"],
    },
    {
        "skill_id": "creation.review",
        "name": "AI 质检",
        "version": "1.0.0",
        "category": "quality",
        "skill_layer": "business",
        "sub_category": "质检",
        "lifecycle_status": "active",
        "gray_weight": 100,
        "quota_cost": 15,
        "timeout_seconds": 300,
        "system_hint": (
            "你是剧本质检专家。对剧本进行多维度评分：\n"
            "1. 一致性（人物/设定/前后逻辑）\n"
            "2. 节奏（紧张度分布、推进效率）\n"
            "3. 对白质量（自然度/信息量/情感张力）\n"
            "4. 钩子（每集结尾吸引力）\n"
            "5. 价值观合规（无不当内容）\n\n"
            "输出 JSON：\n"
            "{\n"
            '  "overall_score": 85,\n'
            '  "consistency": 90, "pacing": 80, "dialogue": 85, "hook": 75, "compliance": 95,\n'
            '  "issues": [{"episode": 3, "type": "节奏拖沓", "severity": "medium", "description": "..."}],\n'
            '  "suggestions": ["..."]\n'
            "}"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "scripts": {"type": "array"},
                "brief": {"type": "object"},
            },
            "required": ["scripts"],
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "overall_score": {"type": "number"},
                "consistency": {"type": "number"},
                "pacing": {"type": "number"},
                "dialogue": {"type": "number"},
                "hook": {"type": "number"},
                "compliance": {"type": "number"},
                "issues": {"type": "array"},
                "suggestions": {"type": "array"},
            },
            "required": ["overall_score"],
        },
        "tags": ["短剧", "质检", "评分"],
    },
    {
        "skill_id": "creation.polish",
        "name": "润色优化",
        "version": "1.0.0",
        "category": "creator",
        "skill_layer": "business",
        "sub_category": "润色",
        "lifecycle_status": "active",
        "gray_weight": 100,
        "quota_cost": 20,
        "timeout_seconds": 600,
        "system_hint": (
            "你是剧本润色专家。基于质检报告和原剧本，"
            "针对每个问题进行精准重写：\n"
            "- 保留核心剧情与角色设定\n"
            "- 改善对白自然度与情感张力\n"
            "- 增强节奏与钩子\n"
            "- 修复一致性问题\n\n"
            "输出润色后的完整剧本，结构与原剧本一致。"
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "scripts": {"type": "array"},
                "review": {"type": "object"},
            },
            "required": ["scripts", "review"],
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "polished_scripts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "episode": {"type": "integer"},
                            "title": {"type": "string"},
                            "content": {"type": "string"},
                            "changes": {"type": "array"},
                        },
                        "required": ["episode", "title", "content"],
                    },
                },
            },
            "required": ["polished_scripts"],
        },
        "tags": ["短剧", "润色", "重写"],
    },
]


def _register_creation_skills(apps, schema_editor):
    AgentSkillDefinition = apps.get_model("skill", "AgentSkillDefinition")
    from django.utils import timezone

    now = timezone.now()
    for skill in SKILL_CATALOG:
        AgentSkillDefinition.objects.update_or_create(
            skill_id=skill["skill_id"],
            defaults={
                "name": skill["name"],
                "version": skill["version"],
                "category": skill["category"],
                "skill_layer": skill["skill_layer"],
                "sub_category": skill.get("sub_category", ""),
                "lifecycle_status": skill["lifecycle_status"],
                "gray_weight": skill["gray_weight"],
                "gray_traffic_salt": f"skill:{skill['skill_id']}",
                "is_active": True,
                "content": skill.get("system_hint", ""),
                "system_hint": skill.get("system_hint", ""),
                "input_schema": skill.get("input_schema", {}),
                "output_schema": skill.get("output_schema", {}),
                "quota_cost": skill.get("quota_cost", 10),
                "timeout_seconds": skill.get("timeout_seconds", 300),
                "retry_policy": {
                    "max_attempts": 3,
                    "backoff_seconds": 2.0,
                },
                "tags": skill.get("tags", []),
                "published_at": now,
            },
        )


def _rollback_creation_skills(apps, schema_editor):
    AgentSkillDefinition = apps.get_model("skill", "AgentSkillDefinition")
    AgentSkillDefinition.objects.filter(
        skill_id__in=[s["skill_id"] for s in SKILL_CATALOG]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("skill", "0030_agentskilldefinition_gray_and_version_fields"),
    ]

    operations = [
        migrations.RunPython(_register_creation_skills, _rollback_creation_skills),
    ]
