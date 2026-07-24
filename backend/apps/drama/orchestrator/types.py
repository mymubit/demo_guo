# -*- coding: utf-8 -*-
"""V3 产品命令类型常量（对齐 docs/contracts/v3/commands.md）。"""

SYNC_COMMANDS = frozenset({"create_project"})

ASYNC_LIVE_COMMANDS = frozenset(
    {
        "generate_topic_brief",
        "generate_blueprint",
        "generate_episode_plan",
        "revise_episode_plan",
        "write_episode_batch",
        "score_quality",
        "check_compliance",
        "revise_from_findings",
        "prepare_delivery",
    }
)

SYNC_CONFIRM_COMMANDS = frozenset(
    {
        "confirm_topic_brief",
        "confirm_blueprint",
        "confirm_episode_plan",
        "confirm_script_candidate",
    }
)

SYNC_MUTATION_COMMANDS = frozenset({"accept_findings"})

# 模型试连：同步 live（commands.md 异步=否）
SYNC_PROVIDER_TEST_COMMANDS = frozenset({"test_model_provider"})

# W5 起无剩余异步 stub
ASYNC_STUB_COMMANDS = frozenset()
