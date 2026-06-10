"""
后台管理 API 模块
- Dashboard 核心指标与图表
- 用户管理（启用/禁用、重置密码）
- 会员管理（套餐 CRUD、卡密批量生成）
- 技能配置管理（加密配置、题材模板、钩子库）
- 订单管理（列表、退款）
- 系统统计与设置、缓存清理
"""

default_app_config = "apps.admin_panel.apps.AdminPanelConfig"
