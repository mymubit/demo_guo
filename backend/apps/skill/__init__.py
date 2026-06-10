"""
apps/skill 模块

技能引擎配置与后台管理模块

主要功能：
- SkillConfig：技能引擎的加密配置（LLM API Key、模型参数等
- ThemeTemplate：短剧题材模板（8大热门题材
- HookLibrary：钩子库（开场/反转/悬念/金句）
- DialogueTemplate：常见对话模板
- ScriptGenerator：基于模板生成剧本（模板版 +  （模板：模板）
"""

default_app_config = 'apps.skill.apps.SkillConfig'
