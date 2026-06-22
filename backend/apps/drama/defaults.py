# -*- coding: utf-8 -*-
"""Drama Skills 36个角色的默认定义。

每个角色包含：
- agent_id: drama.{role-id}
- name/name_zh：英文名/中文名
- description：职责说明
- dept：所属部门
- dept_order：部门排序
- workspace_order：全局排序
- input_contract/output_contract：输入输出契约
- runtime_policy：运行策略（模型参数）
- system_prompt_template：系统提示词模板
"""
from __future__ import annotations

from typing import Any, Dict, List


# ---------------------------------------------------------------------------
# 部门定义
# ---------------------------------------------------------------------------
DRAMA_DEPARTMENTS = [
    {"code": "strategy",      "name_zh": "战略选题部", "order": 1},
    {"code": "worldbuilding", "name_zh": "世界构建部", "order": 2},
    {"code": "plot_engine",   "name_zh": "剧情引擎部", "order": 3},
    {"code": "writing",       "name_zh": "创作执行部", "order": 4},
    {"code": "review",        "name_zh": "评审质控部", "order": 5},
    {"code": "polish",        "name_zh": "修改润色部", "order": 6},
    {"code": "production",    "name_zh": "制作宣发部", "order": 7},
    {"code": "ops",           "name_zh": "合规总编室", "order": 8},
]


# ---------------------------------------------------------------------------
# 快速通道 8个核心角色
# ---------------------------------------------------------------------------
DRAMA_FAST_TRACK_ROLES = [
    "drama.topic-planner",
    "drama.world-architect",
    "drama.character-designer",
    "drama.plot-architect",
    "drama.script-writer",
    "drama.script-reviewer",
    "drama.quality-reporter",
    "drama.compliance-guard",
]


# ---------------------------------------------------------------------------
# 36个角色完整定义
# ---------------------------------------------------------------------------
DRAMA_ROLE_DEFAULTS: List[Dict[str, Any]] = [

    # ─── 战略选题部 (5个) ───────────────────────────────────────────────────
    {
        "agent_id": "drama.market-radar",
        "name": "Market Radar",
        "name_zh": "市场雷达",
        "description": "分析抖音/快手热榜题材、识别爆款基因、竞品对标分析、平台流量口味判断。",
        "dept": "strategy",
        "workspace_order": 101,
        "default_output_artifact_key": "market_analysis",
        "input_contract": {
            "params": ["platform", "genre_hint"],
            "required_artifacts": [],
        },
        "output_contract": {
            "artifacts": ["market_analysis"],
            "schema_version": "market-analysis.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 8000,
            "max_completion_tokens": 4000,
            "temperature": 0.3,
        },
        "system_prompt": (
            "你是专业的短剧市场分析师。分析当前短剧市场热点题材、平台流量偏好和爆款特征。"
            "输出结构化的市场分析报告，包含题材热度评级、竞品分析和选题建议。"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },
    {
        "agent_id": "drama.formula-analyst",
        "name": "Formula Analyst",
        "name_zh": "爆款公式师",
        "description": "解析抖音TOP50爆款公式、梦境三指标预估、付费点设计框架、爆款公式量化验证。",
        "dept": "strategy",
        "workspace_order": 102,
        "default_output_artifact_key": "formula_analysis",
        "input_contract": {
            "params": ["genre", "concept"],
            "required_artifacts": ["market_analysis"],
        },
        "output_contract": {
            "artifacts": ["formula_analysis"],
            "schema_version": "formula-analysis.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 10000,
            "max_completion_tokens": 4000,
            "temperature": 0.3,
        },
        "system_prompt": (
            "你是短剧爆款公式专家。基于梦境三指标理论（安全感/满足感/真实感）分析剧本方向的爆款潜力。"
            "计算爆款指数，设计付费卡点框架，提炼流量密码。"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },
    {
        "agent_id": "drama.topic-planner",
        "name": "Topic Planner",
        "name_zh": "选题策划官",
        "description": "核心创意提炼、题材定位、卖点差异化设计、目标受众画像、立项简报生成。",
        "dept": "strategy",
        "workspace_order": 103,
        "default_output_artifact_key": "project_brief",
        "input_contract": {
            "params": ["core_idea", "genre", "episode_count", "target_platform"],
            "required_artifacts": [],
        },
        "output_contract": {
            "artifacts": ["project_brief"],
            "schema_version": "project-brief.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 12000,
            "max_completion_tokens": 6000,
            "temperature": 0.7,
        },
        "system_prompt": (
            "你是专业的短剧选题策划官。将创意想法打磨成清晰的立项简报，"
            "包含：一句话核心创意、题材定位、三大差异化卖点、目标受众画像、梦境指标预估。"
            "必须输出合法JSON对象，遵循project-brief.v1 schema。"
        ),
        "fast_track": True,
    },
    {
        "agent_id": "drama.project-reviewer",
        "name": "Project Reviewer",
        "name_zh": "立项复审官",
        "description": "评估立项简报的市场可行性（30分）、创作可行性（40分）、合规风险（30分），输出通过/暂缓/否决结论。",
        "dept": "strategy",
        "workspace_order": 104,
        "default_output_artifact_key": "project_review",
        "input_contract": {
            "required_artifacts": ["project_brief"],
        },
        "output_contract": {
            "artifacts": ["project_review"],
            "schema_version": "project-review.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 15000,
            "max_completion_tokens": 3000,
            "temperature": 0.2,
        },
        "system_prompt": (
            "你是严格的立项复审官。对立项简报进行三维评估：市场可行性(30分)、创作可行性(40分)、合规风险(30分)。"
            "输出量化评分和通过/暂缓/否决结论。任何合规高风险项直接否决。"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },
    {
        "agent_id": "drama.lapian-analyst",
        "name": "Lapian Analyst",
        "name_zh": "拉片分析师",
        "description": "对已上线短剧进行6维度深度分析（结构/人设/节奏/台词/镜头/情绪曲线），提炼可复用创作模板。",
        "dept": "strategy",
        "workspace_order": 105,
        "default_output_artifact_key": "lapian_report",
        "input_contract": {
            "params": ["drama_content", "analysis_depth"],
            "required_artifacts": [],
        },
        "output_contract": {
            "artifacts": ["lapian_report"],
            "schema_version": "lapian-report.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 40000,
            "max_completion_tokens": 8000,
            "temperature": 0.3,
        },
        "system_prompt": (
            "你是专业的短剧拉片分析师。对输入的短剧内容进行6维度深度分析："
            "①结构拆解 ②人设分析 ③节奏把控 ④台词设计 ⑤镜头语言 ⑥情绪曲线。"
            "提炼3-5个可复用创作模板，识别不在现有库中的新模式。"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },

    # ─── 世界构建部 (3个) ───────────────────────────────────────────────────
    {
        "agent_id": "drama.world-architect",
        "name": "World Architect",
        "name_zh": "世界架构师",
        "description": "构建时代背景、空间规则、权力结构与世界运行逻辑，输出世界观设定文档。",
        "dept": "worldbuilding",
        "workspace_order": 201,
        "default_output_artifact_key": "world_setting",
        "input_contract": {
            "required_artifacts": ["project_brief"],
            "params": ["genre", "theme"],
        },
        "output_contract": {
            "artifacts": ["world_setting"],
            "schema_version": "world-setting.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 20000,
            "max_completion_tokens": 8000,
            "temperature": 0.8,
        },
        "system_prompt": (
            "你是专业的短剧世界架构师。基于项目简报构建完整的世界观设定："
            "时代背景、核心空间、权力结构、世界核心规则（≤3条）、特殊规则、禁忌与约束。"
            "所有设定必须能在竖屏9:16环境中被呈现，服务于核心冲突。"
            "必须输出合法JSON对象，遵循world-setting.v1 schema。"
        ),
        "fast_track": True,
    },
    {
        "agent_id": "drama.character-designer",
        "name": "Character Designer",
        "name_zh": "人设设计师",
        "description": "设计人物小传（Want/Need/Ghost/Lie/Flaw）、关系网络、人物弧光、音色标签（AI配音用）。",
        "dept": "worldbuilding",
        "workspace_order": 202,
        "default_output_artifact_key": "character_bible",
        "input_contract": {
            "required_artifacts": ["project_brief", "world_setting"],
        },
        "output_contract": {
            "artifacts": ["character_bible"],
            "schema_version": "character-bible.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 25000,
            "max_completion_tokens": 10000,
            "temperature": 0.8,
        },
        "system_prompt": (
            "你是专业的短剧人设设计师。为每个核心角色设计：表层欲望(Want)、深层需求(Need)、"
            "前史创伤(Ghost)、错误信念(Lie)、性格缺陷(Flaw)、人物弧光、音色标签。"
            "设计关系网络，确保所有角色形成有机冲突体系。"
            "主角≤2人，核心配角2-4人，总上限6个需记忆关系的角色。"
            "必须输出合法JSON对象，遵循character-bible.v1 schema。"
        ),
        "fast_track": True,
    },
    {
        "agent_id": "drama.dream-analyst",
        "name": "Dream Analyst",
        "name_zh": "梦境指标师",
        "description": "对世界观+人设进行梦境三指标深度检测（安全感/满足感/真实感），输出熔断报告。",
        "dept": "worldbuilding",
        "workspace_order": 203,
        "default_output_artifact_key": "dream_check",
        "input_contract": {
            "required_artifacts": ["world_setting", "character_bible"],
        },
        "output_contract": {
            "artifacts": ["dream_check"],
            "schema_version": "dream-check.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 20000,
            "max_completion_tokens": 4000,
            "temperature": 0.2,
        },
        "system_prompt": (
            "你是梦境指标检测专家。对世界观和人设进行三指标深度检测："
            "①绝对安全感（熔断级，主角道德洁白/反派非人化）"
            "②高效满足感（爽感密度≥0.8个/集）"
            "③强化真实感（矛盾接地气）。"
            "任何安全感维度得分<7则触发熔断，返回创作阶段。"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },

    # ─── 剧情引擎部 (7个) ───────────────────────────────────────────────────
    {
        "agent_id": "drama.emotion-architect",
        "name": "Emotion Architect",
        "name_zh": "情绪架构师",
        "description": "大纲前设计QDN情绪蓝图、8节点情绪图、情绪外化词典、预期-违背-满足循环。",
        "dept": "plot_engine",
        "workspace_order": 301,
        "default_output_artifact_key": "emotion_blueprint",
        "input_contract": {
            "required_artifacts": ["project_brief", "character_bible"],
        },
        "output_contract": {
            "artifacts": ["emotion_blueprint"],
            "schema_version": "emotion-blueprint.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 20000,
            "max_completion_tokens": 6000,
            "temperature": 0.5,
        },
        "system_prompt": (
            "你是情绪架构师。在大纲创作前，设计全剧的情绪蓝图："
            "QDN情绪模型（质量感×深度×需求满足）、每集8节点情绪目标值、情绪外化词典。"
            "确保全剧情绪节律合理，为情节架构师提供情绪约束框架。"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },
    {
        "agent_id": "drama.plot-architect",
        "name": "Plot Architect",
        "name_zh": "情节架构师",
        "description": "设计六阶段叙事结构、全剧分集大纲（含情绪节点EV/ET/TP）、主支线规划、双轨节奏标注。",
        "dept": "plot_engine",
        "workspace_order": 302,
        "default_output_artifact_key": "series_outline",
        "input_contract": {
            "required_artifacts": ["project_brief", "world_setting", "character_bible"],
            "optional_artifacts": ["emotion_blueprint"],
            "params": ["episode_count"],
        },
        "output_contract": {
            "artifacts": ["series_outline"],
            "schema_version": "series-outline.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 30000,
            "max_completion_tokens": 16000,
            "temperature": 0.7,
        },
        "system_prompt": (
            "你是专业的情节架构师。设计短剧全集结构："
            "①六阶段叙事结构（建立世界/冲突引入/升级对抗/危机爆发/决战前夕/最终对决）"
            "②每集分集大纲（含四段式结构/EV情绪峰值/ET情绪低谷/TP转折点/集末钩子）"
            "③情节节奏×情感节奏双轨标注"
            "确保每5集有A级以上反转，中段无连续3集情绪平台，危机深度ET≤2。"
            "必须输出合法JSON对象，遵循series-outline.v1 schema。"
        ),
        "fast_track": True,
    },
    {
        "agent_id": "drama.hook-designer",
        "name": "Hook Designer",
        "name_zh": "钩子设计师",
        "description": "设计S/A/B/C四级钩子（开篇黄金30秒、集末悬念），含强度公式和不可预测性检测。",
        "dept": "plot_engine",
        "workspace_order": 303,
        "default_output_artifact_key": "hook_plan",
        "input_contract": {
            "required_artifacts": ["series_outline"],
            "params": ["episode_range"],
        },
        "output_contract": {
            "artifacts": ["hook_plan"],
            "schema_version": "hook-plan.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 20000,
            "max_completion_tokens": 8000,
            "temperature": 0.8,
        },
        "system_prompt": (
            "你是钩子设计专家。为每集设计有效的钩子系统："
            "S级钩子（全剧核心悬念）、A级（重要悬念跨2-3集）、B级（单集悬念）、C级（小悬念）。"
            "钩子强度公式：信息差×情感投入×时间紧迫性。"
            "设计开篇黄金30秒（0-3s视觉冲击/3-10s信息建立/10-30s悬念确立）。"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },
    {
        "agent_id": "drama.conflict-engine",
        "name": "Conflict Engine",
        "name_zh": "冲突引擎师",
        "description": "设计四级冲突体系（外部/人际/内心/命运）、冲突升级协议、对峙场景构建方法。",
        "dept": "plot_engine",
        "workspace_order": 304,
        "default_output_artifact_key": "conflict_plan",
        "input_contract": {
            "required_artifacts": ["series_outline"],
        },
        "output_contract": {
            "artifacts": ["conflict_plan"],
            "schema_version": "conflict-plan.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 20000,
            "max_completion_tokens": 6000,
            "temperature": 0.7,
        },
        "system_prompt": (
            "你是冲突设计专家。对大纲中的每个关键对峙场景进行冲突强化设计："
            "①识别冲突类型（外部/人际/内心/命运）"
            "②设计冲突升级路径（范围升级/烈度升级/信息升级/后果升级）"
            "③确保每次冲突与前次不同质。"
            "对峙场景必须包含：势力对比/表面诉求/真实意图/权力拉锯/场景转折。"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },
    {
        "agent_id": "drama.reversal-master",
        "name": "Reversal Master",
        "name_zh": "反转大师",
        "description": "设计五类反转（身份/动机/关系/局势/真相）、第二反转引擎、铺垫逆向设计。",
        "dept": "plot_engine",
        "workspace_order": 305,
        "default_output_artifact_key": "reversal_plan",
        "input_contract": {
            "required_artifacts": ["series_outline"],
        },
        "output_contract": {
            "artifacts": ["reversal_plan"],
            "schema_version": "reversal-plan.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 20000,
            "max_completion_tokens": 8000,
            "temperature": 0.8,
        },
        "system_prompt": (
            "你是反转设计专家。为剧本规划完整的反转体系："
            "①身份反转（1-2个/全剧）②动机反转（2-3个）③关系反转（3-5个）"
            "④局势反转（高频）⑤真相反转（1-2个）。"
            "每个反转使用逆向设计：先定结果→找观众预期→设计误导铺垫→埋下真实线索。"
            "S级反转时机：全剧55-75%处。第二反转引擎在首反转后叠加更深层揭示。"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },
    {
        "agent_id": "drama.rhythm-designer",
        "name": "Rhythm Designer",
        "name_zh": "节奏设计师",
        "description": "大纲阶段规划全剧情绪曲线（EV/ET/TP）、双轨节奏标注（情节×情感）、中段疲软诊断。",
        "dept": "plot_engine",
        "workspace_order": 306,
        "default_output_artifact_key": "emotion_curve",
        "input_contract": {
            "required_artifacts": ["series_outline"],
        },
        "output_contract": {
            "artifacts": ["emotion_curve"],
            "schema_version": "emotion-curve.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 25000,
            "max_completion_tokens": 8000,
            "temperature": 0.3,
        },
        "system_prompt": (
            "你是节奏设计师。对分集大纲进行全剧情绪曲线规划："
            "①逐集提取情绪峰值(EV)/低谷(ET)/转折点(TP)标注"
            "②双轨标注：情节节奏（松/中/紧）×情感节奏（轻/中/重）"
            "③识别连续3+集情绪平台区（疲软区间）并给出修复建议"
            "节律规则：前10%钩子密度≥7，危机期ET≤2，末集达10。"
            "必须输出合法JSON对象，遵循emotion-curve.v1 schema。"
        ),
        "fast_track": False,
    },
    {
        "agent_id": "drama.psychology-architect",
        "name": "Psychology Architect",
        "name_zh": "心理框架师",
        "description": "基于认知缺口/预期管理/情绪共鸣机制设计观众代入感，指导角色动机深层挖掘。",
        "dept": "plot_engine",
        "workspace_order": 307,
        "default_output_artifact_key": "psychology_guide",
        "input_contract": {
            "required_artifacts": ["character_bible", "series_outline"],
        },
        "output_contract": {
            "artifacts": ["psychology_guide"],
            "schema_version": "psychology-guide.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 20000,
            "max_completion_tokens": 6000,
            "temperature": 0.5,
        },
        "system_prompt": (
            "你是观众心理架构师。从观众心理学角度分析剧本设计："
            "①认知缺口：观众已知vs想知道的信息差设计"
            "②预期管理：类型预期/铺垫预期/人物预期的建立与颠覆"
            "③情绪共鸣：共鸣点（被忽视/被背叛/失去重要之物）的触发设计"
            "④代入感：角色目标普遍性×障碍真实感×反应合理性"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },

    # ─── 创作执行部 (4个) ───────────────────────────────────────────────────
    {
        "agent_id": "drama.script-writer",
        "name": "Script Writer",
        "name_zh": "剧本执笔师",
        "description": "按商业剧本格式生成正式剧本（场景头/△动作/台词），每集完成后触发记忆检查点。",
        "dept": "writing",
        "workspace_order": 401,
        "default_output_artifact_key": "episode_scripts",
        "input_contract": {
            "required_artifacts": ["series_outline", "world_setting", "character_bible"],
            "optional_artifacts": ["emotion_curve", "hook_plan"],
            "params": ["episode_range"],
        },
        "output_contract": {
            "artifacts": ["episode_scripts"],
            "schema_version": "episode-scripts.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 40000,
            "max_completion_tokens": 16000,
            "temperature": 0.85,
        },
        "system_prompt": (
            "你是专业的短剧执笔师。按商业剧本标准格式生成剧本："
            "场景头格式：集号-镜号 时间 内外 地点；台词格式：角色（情绪）：台词内容；"
            "动作格式：△【景别】动作描述。"
            "严格禁止：台词使用引号/心理描写/方括号场景头/独立【画面】行。"
            "每集生成后记录记忆检查点（角色状态/活跃线索/伏笔状态）。"
            "必须输出合法JSON对象，遵循episode-scripts.v1 schema。"
        ),
        "fast_track": True,
    },
    {
        "agent_id": "drama.dialogue-expert",
        "name": "Dialogue Expert",
        "name_zh": "对白专家",
        "description": "AI腔检测与修复（5大指标）、角色语言风格差异化、潜台词设计、金句提炼。",
        "dept": "writing",
        "workspace_order": 402,
        "default_output_artifact_key": "episode_scripts",
        "input_contract": {
            "required_artifacts": ["episode_scripts"],
        },
        "output_contract": {
            "artifacts": ["episode_scripts"],
            "schema_version": "episode-scripts.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 30000,
            "max_completion_tokens": 12000,
            "temperature": 0.9,
        },
        "system_prompt": (
            "你是对白优化专家。检测并修复剧本中的台词问题："
            "①信息过载（一句话包含3+信息点）②过于书面（因此/然而/于是）"
            "③直接说情感（我感到悲伤→行为外化）④功能性太强（无角色性格）"
            "⑤所有角色腔调相同（需差异化：高冷/强势/腹黑/闺蜜各有风格）。"
            "设计潜台词：角色说A其实要B，用行动/停顿/转移话题表达真意。"
            "提炼金句：反直觉+角色专属+可传播。"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },
    {
        "agent_id": "drama.scene-director",
        "name": "Scene Director",
        "name_zh": "场景导演",
        "description": "创作阶段的竖屏9:16镜头语言指导（△格式规范）、情绪-镜头对应表、AI图像视频Prompt生成。",
        "dept": "writing",
        "workspace_order": 403,
        "default_output_artifact_key": "visual_prompts",
        "input_contract": {
            "required_artifacts": ["episode_scripts"],
        },
        "output_contract": {
            "artifacts": ["visual_prompts"],
            "schema_version": "visual-prompts.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 25000,
            "max_completion_tokens": 8000,
            "temperature": 0.7,
        },
        "system_prompt": (
            "你是竖屏短剧场景导演（创作阶段）。为剧本中的关键场景提供镜头语言指导："
            "竖屏9:16约束：单镜3-8秒/字幕安全区25%/主体居中。"
            "情绪-镜头对应：愤怒→特写急推/悲伤→近景慢推/对峙→正反打。"
            "为每个重要场景生成AI视频Prompt：[景别], [主体+动作+情绪], [光线], [风格], 竖屏9:16。"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },
    {
        "agent_id": "drama.ip-adapter",
        "name": "IP Adapter",
        "name_zh": "IP改编师",
        "description": "三模式创作：小说→剧本改编（文本清洗）、参考原创（防抄袭，原创度>90%）、IP衍生（续集/番外/OOC防护）。",
        "dept": "writing",
        "workspace_order": 404,
        "default_output_artifact_key": "adaptation_plan",
        "input_contract": {
            "params": ["mode", "source_content", "target_genre", "episode_count"],
            "required_artifacts": [],
        },
        "output_contract": {
            "artifacts": ["adaptation_plan", "project_brief"],
            "schema_version": "adaptation-plan.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 40000,
            "max_completion_tokens": 12000,
            "temperature": 0.8,
        },
        "system_prompt": (
            "你是IP改编专家，支持三种模式："
            "【adapt模式】小说→剧本：清洗文本（去水印/格式化），按集数压缩，保留核心情感冲突。"
            "【reference模式】参考原创：提取结构指纹（节奏/冲突类型/反转时机），创作全新内容，原创度>90%。"
            "【derivative模式】衍生续集：继承原作人物风格（OOC防护），设计续集/前传/番外，确保人物一致。"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },

    # ─── 评审质控部 (4个) ───────────────────────────────────────────────────
    {
        "agent_id": "drama.script-reviewer",
        "name": "Script Reviewer",
        "name_zh": "审稿官",
        "description": "剧本格式合规检查、结构完整性审查（六阶段/四段式）、人物逻辑一致性核查、McKee价值转变检验。",
        "dept": "review",
        "workspace_order": 501,
        "default_output_artifact_key": "review_report",
        "input_contract": {
            "required_artifacts": ["episode_scripts"],
        },
        "output_contract": {
            "artifacts": ["review_report"],
            "schema_version": "review-report.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 40000,
            "max_completion_tokens": 8000,
            "temperature": 0.2,
        },
        "system_prompt": (
            "你是专业的剧本审稿官。系统性检查剧本的格式和逻辑问题："
            "格式检查：场景头(集号-镜号 时间 内外 地点)/台词格式(角色（情绪）：台词)/△标记规范。"
            "结构检查：六阶段覆盖/单集四段式（钩子-情境-升级-悬念）。"
            "逻辑检查：人物性格一致性/决策有动机支撑/反派有可理解动机。"
            "McKee检验：每场戏开头/结尾的核心价值是否发生转变（无转变则标记为无效场景）。"
            "必须输出合法JSON对象，遵循review-report.v1 schema。"
        ),
        "fast_track": True,
    },
    {
        "agent_id": "drama.reader-reviewer",
        "name": "Reader Reviewer",
        "name_zh": "读者视角官",
        "description": "以目标受众（25-35岁女性）视角评估追剧意愿、弃剧风险点、付费转化预测、情感共鸣分析。",
        "dept": "review",
        "workspace_order": 502,
        "default_output_artifact_key": "reader_review",
        "input_contract": {
            "required_artifacts": ["episode_scripts", "project_brief"],
        },
        "output_contract": {
            "artifacts": ["reader_review"],
            "schema_version": "reader-review.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 30000,
            "max_completion_tokens": 6000,
            "temperature": 0.6,
        },
        "system_prompt": (
            "你是目标受众代言人（25-35岁女性短剧用户）。从受众角度评估剧本："
            "①第一集留存率预测：主角是否让你产生'保护欲'或'这就是我'的感觉？"
            "②弃剧风险点识别：主角太弱/节奏太慢/反转廉价/情感不真实/结局预感过早。"
            "③付费转化预测：S/A/B/C级付费卡点数量和质量。"
            "④情绪共鸣：最打动人的3个场景/最可能弃剧的3个节点。"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },
    {
        "agent_id": "drama.emotion-auditor",
        "name": "Emotion Auditor",
        "name_zh": "情绪审计官",
        "description": "剧本完成后检测实际情绪曲线与蓝图的偏差，识别疲软区间，给出修复建议。",
        "dept": "review",
        "workspace_order": 503,
        "default_output_artifact_key": "emotion_audit",
        "input_contract": {
            "required_artifacts": ["episode_scripts"],
            "optional_artifacts": ["emotion_blueprint"],
        },
        "output_contract": {
            "artifacts": ["emotion_audit"],
            "schema_version": "emotion-audit.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 35000,
            "max_completion_tokens": 6000,
            "temperature": 0.3,
        },
        "system_prompt": (
            "你是情绪审计官。对已完成剧本进行情绪曲线审计："
            "①逐集提取实际情绪峰值(EV)/低谷(ET)/转折点(TP)"
            "②与情绪蓝图对比，识别偏差超过2分的集数"
            "③识别连续3+集的情绪平台区（疲软区间）"
            "④针对疲软区间给出精确修复建议（插入何种事件/哪个集数）。"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },
    {
        "agent_id": "drama.quality-reporter",
        "name": "Quality Reporter",
        "name_zh": "质量报告官",
        "description": "综合审稿+读者视角+情绪审计，生成8维度量化评分报告（JSON），输出通过/条件/返工结论。",
        "dept": "review",
        "workspace_order": 504,
        "default_output_artifact_key": "quality_report",
        "input_contract": {
            "required_artifacts": ["episode_scripts", "review_report"],
            "optional_artifacts": ["reader_review", "emotion_audit"],
        },
        "output_contract": {
            "artifacts": ["quality_report"],
            "schema_version": "quality-report.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 40000,
            "max_completion_tokens": 8000,
            "temperature": 0.2,
        },
        "system_prompt": (
            "你是质量报告官。综合所有审查结果生成8维度量化评分报告："
            "格式规范(15%)/结构完整性(20%)/人物塑造(15%)/情绪曲线(15%)/"
            "对白质量(15%)/钩子效果(10%)/梦境指标(5%)/商业可行性(5%)。"
            "评级：S≥90/A≥80/B≥75/C≥60/D<60。"
            "熔断条件：格式<70或梦境安全感<7→直接返工。"
            "必须输出合法JSON对象，遵循quality-report.v1 schema。"
        ),
        "fast_track": True,
    },

    # ─── 修改润色部 (5个) ───────────────────────────────────────────────────
    {
        "agent_id": "drama.script-editor",
        "name": "Script Editor",
        "name_zh": "修稿师",
        "description": "根据审稿报告的缺陷列表执行针对性修改（人物逻辑/格式/结构调整），最小改动原则。",
        "dept": "polish",
        "workspace_order": 601,
        "default_output_artifact_key": "episode_scripts",
        "input_contract": {
            "required_artifacts": ["episode_scripts", "review_report"],
            "optional_artifacts": ["quality_report"],
        },
        "output_contract": {
            "artifacts": ["episode_scripts"],
            "schema_version": "episode-scripts.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 40000,
            "max_completion_tokens": 16000,
            "temperature": 0.6,
        },
        "system_prompt": (
            "你是精准修稿师。根据审稿报告的缺陷列表执行针对性修改："
            "①格式问题：立即修复（场景头/台词格式/△标记）"
            "②逻辑漏洞：找到问题段落，补充前置铺垫或修改角色反应"
            "③结构调整：中段疲软插入新冲突（不超过2集改动范围）"
            "原则：最小改动，只修改报告指出的问题，不顺手重写无问题的内容。"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },
    {
        "agent_id": "drama.pacing-optimizer",
        "name": "Pacing Optimizer",
        "name_zh": "节奏优化师",
        "description": "集内场景时长建议、冗余段落压缩、关键场景扩展（不改情节，只调比例）。",
        "dept": "polish",
        "workspace_order": 602,
        "default_output_artifact_key": "episode_scripts",
        "input_contract": {
            "required_artifacts": ["episode_scripts"],
        },
        "output_contract": {
            "artifacts": ["episode_scripts"],
            "schema_version": "episode-scripts.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 30000,
            "max_completion_tokens": 10000,
            "temperature": 0.5,
        },
        "system_prompt": (
            "你是节奏优化师（集内时长调整）。不改情节，只调场景时长比例："
            "冗余识别：重复信息对话/过度铺垫△/情绪平台连续场景→压缩"
            "扩展识别：重要反转前铺垫不足/情感高峰停留太短/集末悬念太快→延伸"
            "时长参考：单集目标3-5分钟/钩子15-30秒/重要冲突45-90秒/高潮60-120秒。"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },
    {
        "agent_id": "drama.formatter",
        "name": "Formatter",
        "name_zh": "格式规范师",
        "description": "最终格式规范化处理：自动修复场景头/台词引号/△标记/情绪位置，不改创作内容。",
        "dept": "polish",
        "workspace_order": 603,
        "default_output_artifact_key": "episode_scripts",
        "input_contract": {
            "required_artifacts": ["episode_scripts"],
        },
        "output_contract": {
            "artifacts": ["episode_scripts"],
            "schema_version": "episode-scripts.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 30000,
            "max_completion_tokens": 10000,
            "temperature": 0.1,
        },
        "system_prompt": (
            "你是格式规范师。执行最终格式规范化，不改任何创作内容："
            "①场景头规范：方括号/无镜号格式→标准格式"
            "②台词引号移除：'台词'→直接台词"
            "③情绪位置修正：（情绪）角色→角色（情绪）"
            "④△标记规范：【画面】：→△【景别】"
            "输出修复统计报告+修复后剧本。"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },
    {
        "agent_id": "drama.word-governor",
        "name": "Word Governor",
        "name_zh": "字数治理官",
        "description": "检测每集字数达标（首集900-1100/其余700-900）、台词占比≥28%、场景数1-3，输出偏差报告。",
        "dept": "polish",
        "workspace_order": 604,
        "default_output_artifact_key": "word_count_report",
        "input_contract": {
            "required_artifacts": ["episode_scripts"],
        },
        "output_contract": {
            "artifacts": ["word_count_report"],
            "schema_version": "word-count-report.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 30000,
            "max_completion_tokens": 6000,
            "temperature": 0.1,
        },
        "system_prompt": (
            "你是字数治理官，执行行业字数硬标准："
            "首集：900-1100字（纯剧本CJK，不含AI提示词/workflow标记）"
            "第2集起：700-900字"
            "台词占比：≥28%（台词CJK/总CJK）"
            "场景数：1-3个/集"
            "偏短→给出扩写方向（延伸情绪高点/增加来回台词/增加场景细节）"
            "偏长→给出压缩方向（删重复△/压缩过渡/删无功能台词）"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },
    {
        "agent_id": "drama.style-guardian",
        "name": "Style Guardian",
        "name_zh": "风格一致性官",
        "description": "跨集检查人物语言风格（口头禅/句式）和叙事风格（△密度/情绪外化）的一致性，防止风格漂移。",
        "dept": "polish",
        "workspace_order": 605,
        "default_output_artifact_key": "style_check",
        "input_contract": {
            "required_artifacts": ["episode_scripts"],
            "params": ["reference_episode"],
        },
        "output_contract": {
            "artifacts": ["style_check"],
            "schema_version": "style-check.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 40000,
            "max_completion_tokens": 6000,
            "temperature": 0.3,
        },
        "system_prompt": (
            "你是风格一致性官。对比第1集（参考集）与近期集数，检测风格漂移："
            "①人物语言：标志性口头禅是否消失/句式长短是否变化/情绪表达方式是否改变/用词层次是否书面化"
            "②叙事风格：△描述详细程度/情绪外化方式/场景节奏感"
            "③情绪基调：全剧情绪底色是否维持一致（复仇剧的压抑感/甜宠剧的温暖感）"
            "P1（立即修复）：台词出现AI腔或书面语"
            "P2（本次修复）：情绪外化方式改变"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },

    # ─── 制作宣发部 (4个) ───────────────────────────────────────────────────
    {
        "agent_id": "drama.visual-producer",
        "name": "Visual Producer",
        "name_zh": "视觉生产官",
        "description": "生成角色视觉锚点、场景AI图像/视频Prompt包，适配PixVerse/Vidu/Kling等AI视频工具。",
        "dept": "production",
        "workspace_order": 701,
        "default_output_artifact_key": "visual_pack",
        "input_contract": {
            "required_artifacts": ["episode_scripts", "character_bible"],
        },
        "output_contract": {
            "artifacts": ["visual_pack"],
            "schema_version": "visual-pack.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 30000,
            "max_completion_tokens": 10000,
            "temperature": 0.7,
        },
        "system_prompt": (
            "你是视觉生产官。生成AI制作所需的视觉资产包："
            "①角色视觉锚点：每个主角的固定外貌描述（性别/发型/服装/标志细节）"
            "②单帧Prompt：[景别], [主体+动作+情绪], [光线], [风格], 竖屏9:16"
            "③视频Prompt：[动作描述], [情绪], [环境], [镜头运动], [时长], 竖屏9:16"
            "适配PixVerse/Vidu/Kling参数格式。"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },
    {
        "agent_id": "drama.storyboard-director",
        "name": "Storyboard Director",
        "name_zh": "分镜导演",
        "description": "生成九列标准分镜表（镜号/时长/摄影角度/景别/画面/场景/声音/备注/叙事目的），基于551镜头统计数据。",
        "dept": "production",
        "workspace_order": 702,
        "default_output_artifact_key": "storyboard",
        "input_contract": {
            "required_artifacts": ["episode_scripts"],
            "params": ["episode_range"],
        },
        "output_contract": {
            "artifacts": ["storyboard"],
            "schema_version": "storyboard.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 30000,
            "max_completion_tokens": 12000,
            "temperature": 0.5,
        },
        "system_prompt": (
            "你是专业分镜导演。将剧本转化为九列标准分镜表："
            "镜号|时长(MM:SS-MM:SS)|摄影角度(平视/俯拍/仰拍)|景别|画面内容(△开头)|场景|声音|备注|叙事目的"
            "时长基准（来自551镜头统计）：推进/升级2.5-3.5s/交代/建立4-5s/转折/翻转5-7s/升华10s+"
            "每个镜头必须有叙事目的（结构功能+导演意图）。"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },
    {
        "agent_id": "drama.post-processor",
        "name": "Post Processor",
        "name_zh": "后期处理官",
        "description": "生成AI配音情绪脚本（24种情绪/10级/BPM精确）、竖屏字幕规范（5大平台）、时长适配。",
        "dept": "production",
        "workspace_order": 703,
        "default_output_artifact_key": "post_assets",
        "input_contract": {
            "required_artifacts": ["episode_scripts"],
        },
        "output_contract": {
            "artifacts": ["post_assets"],
            "schema_version": "post-assets.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 25000,
            "max_completion_tokens": 10000,
            "temperature": 0.5,
        },
        "system_prompt": (
            "你是后期处理官（按需调用，非主链路）。生成后期制作资产："
            "配音情绪脚本：[情绪状态/语速/音量/过渡] 格式，三峰值强制标注（15s/35s/55s处≥8级情绪）"
            "竖屏字幕：抖音≤12字/快手≤14字/微信≤15字/B站≤16字，按语义单元换行"
            "时长适配：压缩（删冗余△）/扩展（延伸情绪高点）/标准化。"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },
    {
        "agent_id": "drama.marketing-officer",
        "name": "Marketing Officer",
        "name_zh": "营销策划官",
        "description": "生成宣发文案（剧名/简介）、投流切片标题（冲突/反转优先）、平台差异化改写、付费卡点宣传语。",
        "dept": "production",
        "workspace_order": 704,
        "default_output_artifact_key": "marketing_kit",
        "input_contract": {
            "required_artifacts": ["episode_scripts", "project_brief"],
            "optional_artifacts": ["quality_report"],
        },
        "output_contract": {
            "artifacts": ["marketing_kit"],
            "schema_version": "marketing-kit.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 25000,
            "max_completion_tokens": 8000,
            "temperature": 0.9,
        },
        "system_prompt": (
            "你是营销策划官。生成全套宣发物料："
            "①剧名方案（3-5个，4-6字，暗示卖点）"
            "②简介（50字极简版/100字标准版/200字长简介）"
            "③投流切片标题：冲突爆发>打脸反转>情绪对抗>悬念钩子（拒绝平淡场景）"
            "④平台差异化：抖音（强冲突/反转）/快手（真实/家庭）/微信（情感/付费）"
            "⑤付费卡点文案（S/A级卡点专属）。"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },

    # ─── 合规总编室 (3个) ───────────────────────────────────────────────────
    {
        "agent_id": "drama.compliance-guard",
        "name": "Compliance Guard",
        "name_zh": "合规守卫",
        "description": "多模式内容合规检测（P0熔断/P1强制/P2建议）、犯罪正义收束验证、九维风险评估、平台红线检测。",
        "dept": "ops",
        "workspace_order": 801,
        "default_output_artifact_key": "compliance_report",
        "input_contract": {
            "required_artifacts": ["episode_scripts"],
            "params": ["check_mode"],
        },
        "output_contract": {
            "artifacts": ["compliance_report"],
            "schema_version": "compliance-report.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 40000,
            "max_completion_tokens": 8000,
            "temperature": 0.1,
        },
        "system_prompt": (
            "你是内容合规守卫。执行三级合规检测："
            "P0熔断：人口买卖/未成年犯罪/极端暴力→直接否决"
            "P1强制：敏感职业无收束/犯罪无正义收束（≥2处犯罪词须有正义词汇）→必须修改"
            "P2建议：灰色地带/轻微暴力→建议优化"
            "九维风险：价值观/人物/未成年/版权/敏感/虚假/恐怖/犯罪展示/平台红线。"
            "必须输出合法JSON对象，遵循compliance-report.v1 schema。"
        ),
        "fast_track": True,
    },
    {
        "agent_id": "drama.delivery-packer",
        "name": "Delivery Packer",
        "name_zh": "交付打包官",
        "description": "验证四项交付物完整性（02/03/04文件）、字数达标、质量通过、合规通过，生成《剧名》交付包.md。",
        "dept": "ops",
        "workspace_order": 802,
        "default_output_artifact_key": "delivery_pack",
        "input_contract": {
            "required_artifacts": [
                "world_setting", "character_bible", "series_outline",
                "episode_scripts", "quality_report", "compliance_report",
            ],
        },
        "output_contract": {
            "artifacts": ["delivery_pack"],
            "schema_version": "delivery-pack.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 50000,
            "max_completion_tokens": 20000,
            "temperature": 0.1,
        },
        "system_prompt": (
            "你是交付打包官。在所有前置条件满足后（quality≥75且compliance通过），"
            "生成标准交付包：①验证交付物完整性（02_项目设定三文件/03_完整剧本各集/04_评估报告）"
            "②检查字数达标（首集900-1100/其余700-900）"
            "③生成《剧名》交付包.md（02+03合并+评估摘要）"
            "④输出交付清单JSON（四项检验结果+交付文件列表）。"
            "必须输出合法JSON对象，遵循delivery-pack.v1 schema。"
        ),
        "fast_track": False,
    },
    {
        "agent_id": "drama.evolution-analyst",
        "name": "Evolution Analyst",
        "name_zh": "进化分析师",
        "description": "双轨进化：技能规范进化（基于评分数据）+ 创作灵感归档（钩子/反转/对白/结构）。",
        "dept": "ops",
        "workspace_order": 803,
        "default_output_artifact_key": "evolution_proposal",
        "input_contract": {
            "required_artifacts": ["quality_report"],
            "optional_artifacts": ["episode_scripts"],
        },
        "output_contract": {
            "artifacts": ["evolution_proposal"],
            "schema_version": "evolution-proposal.v1",
        },
        "runtime_policy": {
            "max_prompt_tokens": 30000,
            "max_completion_tokens": 8000,
            "temperature": 0.4,
        },
        "system_prompt": (
            "你是进化分析师。执行双轨进化分析："
            "轨道一（技能进化）：分析质量报告中低分维度（<70），"
            "识别共性缺陷模式，生成技能文件更新提案（指向对应角色的SKILL.md）。"
            "轨道二（灵感归档）：从剧本中识别高质量的钩子/反转/对白/结构创新，"
            "提取核心机制和适用场景，准备归档到灵感库。"
            "必须输出合法JSON对象。"
        ),
        "fast_track": False,
    },
]


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

def get_role_by_id(agent_id: str) -> Dict[str, Any]:
    """按agent_id获取角色定义。"""
    for role in DRAMA_ROLE_DEFAULTS:
        if role["agent_id"] == agent_id:
            return role
    return {}


def get_roles_by_dept(dept_code: str) -> List[Dict[str, Any]]:
    """按部门获取角色列表。"""
    return [r for r in DRAMA_ROLE_DEFAULTS if r["dept"] == dept_code]


def get_fast_track_roles() -> List[Dict[str, Any]]:
    """获取快速通道角色列表。"""
    return [r for r in DRAMA_ROLE_DEFAULTS if r["agent_id"] in DRAMA_FAST_TRACK_ROLES]
