from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

OVERRIDES = {
    "t1.global.episode_structure.four-act": {
        "status": "verified",
        "targets": ["episode.structure.use-four-segments", "episode.ending.leave-open-question-or-threat"],
        "decision": "单集四段式比例与集末开放问题/威胁已拆入约束和原子规则。",
        "tests": ["v6/evaluations/tests/test_scene_system_validators.py"],
    },
    "t1.global.information_asymmetry_mechanics.core": {
        "status": "verified",
        "targets": [
            "information.asymmetry.use-canonical-type",
            "information.truth.delay-core-reveal",
            "information.mystery.replace-closed-loop",
        ],
        "decision": "三类信息差、核心真相延迟和滚动悬念已结构化。",
        "tests": [
            "v6/artifacts/components/scene-system.schema.json",
            "v6/evaluations/tests/test_scene_system_validators.py",
        ],
    },
    "t1.global.dialogue_craft.intention": {
        "status": "verified",
        "targets": ["dialogue.line.require-action-intent", "dialogue.line.forbid-known-setting-exposition"],
        "decision": "关键台词行动意图和禁止已知设定解释已拆分。",
        "tests": ["v6/artifacts/components/scene-system.schema.json"],
    },
    "t1.global.dialogue_craft.subtext": {
        "status": "verified",
        "targets": ["dialogue.subtext.separate-line-from-desire", "dialogue.line.limit-main-information-point"],
        "decision": "潜台词差异与单句单信息点已拆分。",
        "tests": ["v6/artifacts/components/scene-system.schema.json"],
    },
    "t1.global.dialogue_craft.scene-rhythm": {
        "status": "verified",
        "targets": [
            "dialogue.rhythm.follow-power-change",
            "dialogue.exchange.compress-static-question-answer",
            "confrontation.design.five-elements",
        ],
        "decision": "权力变化、上风易手和静态问答压缩已闭合。",
        "tests": ["v6/evaluations/tests/test_scene_system_validators.py"],
    },
    "t1.global.writing_requirements.scene-unit": {
        "status": "verified",
        "targets": ["scene.unit.define-goal-conflict-risk", "scene.unit.require-value-change"],
        "decision": "场景目标、阻碍、风险和价值变化已结构化。",
        "tests": [
            "v6/artifacts/components/scene-system.schema.json",
            "v6/evaluations/tests/test_scene_system_validators.py",
        ],
    },
    "t1.global.writing_requirements.commercial-format": {
        "status": "verified",
        "targets": ["screenplay.format.use-canonical-patterns"],
        "decision": "场景头、对白和动作格式全部引用独立 V6 约束。",
        "tests": ["v6/artifacts/components/scene-system.schema.json"],
    },
    "t1.global.writing_prohibitions.format-ssot": {
        "status": "verified",
        "targets": ["screenplay.format.use-canonical-patterns"],
        "decision": "格式禁止项不重复维护，由 V6 场景约束与格式校验能力消费。",
        "tests": ["v6/artifacts/components/scene-system.schema.json"],
    },
    "t1.global.writing_prohibitions.ai-emotion": {
        "status": "verified",
        "targets": ["emotion.expression.use-filmable-channel", "emotion.expression.forbid-adjective-only-interiority"],
        "decision": "情绪直述禁止复用情绪域原子规则，不在场景域重复定义。",
        "tests": ["v6/evaluations/atomic-rules/emotion-system.yaml"],
    },
    "t1.global.writing_prohibitions.unfilmable": {
        "status": "verified",
        "targets": ["scene.content.keep-filmable", "scene.content.forbid-parenthetical-interiority"],
        "decision": "可拍摄渠道与不可拍摄解释禁令已拆分。",
        "tests": ["v6/evaluations/atomic-rules/scene-system.yaml"],
    },
    "t1.global.emotion_externalization_dict.usage": {
        "status": "verified",
        "targets": [
            "emotion.expression.use-filmable-channel",
            "emotion.expression.forbid-adjective-only-interiority",
        ],
        "decision": "情绪外化渠道与禁止形容词直述已拆分为场景能力规则。",
        "tests": ["v6/evaluations/atomic-rules/emotion-system.yaml"],
    },
    "t1.global.qdn_emotion_model.summary": {
        "status": "verified",
        "targets": [
            "emotion.qdn.record-evidence-by-dimension",
            "emotion.landmark.define-ev-et-tp",
            "emotion.rhythm.use-dual-track",
        ],
        "decision": "Q/D/N 改为三维证据，EV/ET/TP 和双轨节奏独立结构化，不伪造综合分。",
        "tests": [
            "v6/artifacts/components/emotion-system.schema.json",
            "v6/evaluations/tests/test_emotion_system_validators.py",
        ],
    },
    "t1.global.episode_emotion_8nodes.summary": {
        "status": "verified",
        "targets": [
            "emotion.episode.require-eight-event-nodes",
            "emotion.ev.avoid-three-episode-platform",
        ],
        "decision": "八节点结构和连续三集 EV 平台限制已进入 Schema 与确定性校验。",
        "tests": [
            "v6/artifacts/components/emotion-system.schema.json",
            "v6/evaluations/tests/test_emotion_system_validators.py",
        ],
    },
    "t1.global.world_rules.actionable": {
        "status": "verified",
        "targets": [
            "world.rule.must-change-action",
            "world.rule.define-operational-fields",
            "world.rule.drive-concrete-choice",
        ],
        "decision": "可行动性、适用对象、触发、代价、可见表现和具体选择引用已结构化。",
        "tests": [
            "v6/artifacts/components/world-system.schema.json",
            "v6/evaluations/tests/test_world_system_validators.py",
        ],
    },
    "t1.global.world_rules.power-structure": {
        "status": "verified",
        "targets": [
            "world.power.identify-scarce-resource-controller",
            "world.power.identify-rule-maker-and-cost-bearer",
            "world.power.define-exploitable-loophole",
            "world.power.sustain-main-conflict",
        ],
        "decision": "稀缺资源、控制者、制定者、代价承担者、制度缝隙和冲突压力已结构化。",
        "tests": ["v6/artifacts/components/world-system.schema.json"],
    },
    "t1.global.world_rules.information-release": {
        "status": "verified",
        "targets": [
            "world.reveal.through-action-and-consequence",
            "world.reveal.limit-new-layer-per-episode",
            "world.reveal.immediately-affect-choice",
        ],
        "decision": "行动后果展示、单集层数限制和首次出现立即影响选择已闭合。",
        "tests": ["v6/evaluations/tests/test_world_system_validators.py"],
    },
    "t1.global.world_rules.consistency": {
        "status": "verified",
        "targets": [
            "world.consistency.same-condition-same-consequence",
            "world.exception.predeclare-source-and-cost",
            "world.rule.register-before-use",
            "world.rule.forbid-temporary-solution-rule",
        ],
        "decision": "一致后果、例外来源与代价、规则预登记和禁止临时破局规则已闭合。",
        "tests": [
            "v6/artifacts/components/world-system.schema.json",
            "v6/evaluations/tests/test_world_system_validators.py",
        ],
    },
    "t1.global.character_rules.age-logic": {
        "status": "verified",
        "targets": [
            "character.age.use-tendency-as-advisory",
            "character.arc.turn-from-lie-through-events",
            "antagonist.require-understandable-motive",
            "antagonist.defeat.preserve-logic",
        ],
        "decision": "年龄经验降为建议；性格转变、反派动机和失败逻辑分别成为可验证规则。",
        "tests": ["v6/evaluations/tests/test_character_system_validators.py"],
    },
    "t1.global.character_rules.density-arc": {
        "status": "verified",
        "targets": [
            "character.count.limit-protagonists",
            "character.count.bound-core-supporting",
            "relationship.count.meet-maximum",
            "character.core.define-motivation-chain",
            "character.arc.define-four-points",
            "character.visual-anchor.identifiable-within-window",
        ],
        "decision": "人物数量、动机链、四点弧光、转折比例和视觉识别窗口已拆分。",
        "tests": [
            "v6/evaluations/tests/test_character_system_validators.py",
            "v6/artifacts/components/character-system.schema.json",
        ],
    },
    "t1.global.character_rules.relationship-dynamics": {
        "status": "verified",
        "targets": [
            "relationship.edge.define-dynamics",
            "relationship.change.require-visible-trigger",
            "character.supporting.require-independent-desire",
        ],
        "decision": "关系双方诉求、权力、状态、事件触发和配角独立欲望已闭合。",
        "tests": [
            "v6/evaluations/tests/test_character_system_validators.py",
            "v6/artifacts/components/character-system.schema.json",
        ],
    },
    "t1.global.character_rules.voice-anchor": {
        "status": "verified",
        "targets": [
            "character.voice.define-actionable-tag",
            "character.visual-anchor.make-filmable",
        ],
        "decision": "声音标签拆为词汇、句式、回避表达，视觉锚点拆为可拍摄结构。",
        "tests": ["v6/artifacts/components/character-system.schema.json"],
    },
    "t1.global.episode_card.required-fields": {
        "status": "verified",
        "targets": [
            "episode-plan.scope.global-structure-readonly",
            "episode-plan.card.required-content",
        ],
        "decision": "分集必填内容和不得改写全剧结构已拆分为两个单义规则。",
        "tests": [
            "v6/evaluations/tests/test_episode_plan_validators.py",
            "v6/evaluations/atomic-rules/episode-plan.yaml",
        ],
    },
    "t1.global.conflict_escalation.four-types": {
        "status": "verified",
        "targets": [
            "conflict.escalation.change-quality",
            "conflict.series.cover-three-types",
            "conflict.main.must-be-structural",
        ],
        "decision": "冲突类型、最少覆盖、结构性主冲突和禁止同烈度重复已分别原子化。",
        "tests": ["v6/evaluations/tests/test_episode_plan_validators.py"],
    },
    "t1.global.conflict_escalation.upgrade-protocol": {
        "status": "verified",
        "targets": [
            "conflict.escalation.change-quality",
            "conflict.escalation.follow-protocol-order",
            "confrontation.design.five-elements",
        ],
        "decision": "升级顺序、冲突质量变化和对峙五要素已分别原子化。",
        "tests": ["v6/evaluations/tests/test_episode_plan_validators.py"],
    },
    "t1.global.hook_effectiveness.levels": {
        "status": "verified",
        "targets": [
            "hook.grade.use-canonical-hierarchy",
            "hook.opening.layered-window",
            "hook.first-episode.meet-minimum-count",
        ],
        "decision": "等级定义、开场分层窗口和首集钩子数量已拆入原子规则与约束。",
        "tests": ["v6/evaluations/tests/test_episode_plan_validators.py"],
    },
    "t1.global.payment_checkpoint_3card.types": {
        "status": "verified",
        "targets": ["payment.card.use-canonical-type"],
        "decision": "情感、悬念和爽感三类卡点已迁入受约束枚举。",
        "tests": ["v6/artifacts/episode-plan/2.schema.json"],
    },
    "t1.global.payment_checkpoint_3card.timing": {
        "status": "verified",
        "targets": [
            "payment.first-checkpoint.use-window",
            "payment.habit-checkpoint.use-window",
            "payment.promise.meet-payoff-deadline",
            "foreshadow.s-reversal.meet-setup-window",
        ],
        "decision": "首卡、习惯卡、兑现期限和 S 级反转窗口均引用独立 V6 约束。",
        "tests": ["v6/evaluations/tests/test_episode_plan_validators.py"],
    },
    "t1.global.foreshadowing_rules.payoff": {
        "status": "verified",
        "targets": [
            "foreshadow.entry.track-setup-and-payoff",
            "foreshadow.payoff.deliver-emotional-value",
            "foreshadow.overdue.enter-memory-checkpoint",
            "execution.episode-context.load-minimum-sufficient-set",
        ],
        "decision": "埋点回扣追踪、三集情感兑现、逾期检查点和最小上下文已分别原子化。",
        "tests": ["v6/evaluations/tests/test_episode_plan_validators.py"],
    },
    "t1.global.foreshadowing_rules.types": {
        "status": "verified",
        "targets": [
            "foreshadow.type.use-canonical-set",
            "foreshadow.reversal.design-backward",
            "foreshadow.clue.appear-ordinary-before-reveal",
            "foreshadow.reversal.requires-verifiable-setup",
        ],
        "decision": "五类伏笔、逆向设计、普通细节呈现和可验证铺垫已分别原子化。",
        "tests": [
            "v6/evaluations/tests/test_episode_plan_validators.py",
            "v6/evaluations/atomic-rules/episode-plan.yaml",
        ],
    },
    "t1.global.rhythm_rules.act-pacing": {
        "status": "verified",
        "targets": [
            "series.stage.use-canonical-order",
            "series.stage.allocate-largest-remainder",
            "series.stage.override-only-from-project-brief",
            "rhythm.adjacent-episodes.must-vary",
        ],
        "decision": "六阶段顺序、比例换算、唯一覆盖源和连续同格限制已闭合。",
        "tests": ["v6/evaluations/tests/test_episode_plan_validators.py"],
    },
    "t1.global.learned_rules.lr003": {
        "status": "verified",
        "targets": ["hook.pre-paywall.meet-required-grade"],
        "decision": "付费墙前 S 级钩子已迁入独立原子规则和等级约束。",
        "tests": ["v6/evaluations/tests/test_episode_plan_validators.py"],
    },
    "t1.global.learned_rules.lr004": {
        "status": "verified",
        "targets": ["antagonist.defeat.preserve-logic"],
        "decision": "反派失败必须由既有选择、限制、证据或后果导致，禁止突然降智。",
        "tests": ["v6/evaluations/atomic-rules/character-system.yaml"],
    },
    "t1.global.learned_rules.lr008": {
        "status": "verified",
        "targets": ["execution.episode-context.load-minimum-sufficient-set"],
        "decision": "逐集生成上下文已迁入白名单式无状态能力。",
        "tests": ["v6/evaluations/tests/test_episode_plan_validators.py"],
    },
    "t1.global.dialogue_quality.voice-by-class": {
        "status": "verified",
        "targets": [
            "dialogue.voice.prioritize-character-tag",
            "dialogue.voice.treat-profile-as-advisory",
        ],
        "decision": "职业与阶层表达降级为非阻断建议，人物 voice_tag、经历、意图、关系和权力位置优先。",
        "tests": ["v6/evaluations/tests/test_dialogue_advisories.py"],
    },
    "t1.global.dialogue_quality.emotion-rhythm": {
        "status": "verified",
        "targets": ["dialogue.emotion.rhythm-adapt-without-overriding-voice"],
        "decision": "情绪节奏按上下文匹配，但不得覆盖人物声音、当前意图和权力位置。",
        "tests": ["v6/evaluations/tests/test_dialogue_advisories.py"],
    },
    "t1.global.ai_tone_forbidden.core": {
        "status": "verified",
        "targets": [
            "dialogue.ai-tone.flag-context-not-token",
            "dialogue.ai-tone.repair-and-read-aloud",
        ],
        "decision": "AI 腔改为上下文和词语堆积判断，单词不机械封禁，确认后才进入口语化修复与朗读检查。",
        "tests": [
            "v6/evaluations/tests/test_dialogue_advisories.py",
            "v6/evaluations/atomic-rules/dialogue-advisory.yaml",
        ],
    },
    "t1.global.continuity.checkpoint": {
        "status": "verified",
        "targets": [
            "continuity.context.require-immediate-predecessor",
            "continuity.checkpoint.emit-after-each-episode",
            "continuity.checkpoint.require-canonical-state",
            "execution.episode-context.load-minimum-sufficient-set",
        ],
        "decision": "逐集输入白名单、N-1 前驱绑定、每集检查点和检查点规范已分别结构化并具备确定性校验。",
        "tests": [
            "v6/artifacts/components/memory-checkpoint.schema.json",
            "v6/evaluations/tests/test_continuity_validators.py",
        ],
    },
    "t1.global.writing_requirements.episode-scope": {
        "status": "verified",
        "targets": [
            "continuity.context.use-explicit-episode-scope",
            "continuity.context.require-immediate-predecessor",
            "continuity.checkpoint.emit-after-each-episode",
            "scene.unit.define-goal-conflict-risk",
            "scene.unit.require-value-change",
        ],
        "decision": "episode_range、前驱输入、场景目标冲突、价值转变和逐集检查点均已进入独立规则与校验器。",
        "tests": [
            "v6/evaluations/tests/test_continuity_validators.py",
            "v6/evaluations/tests/test_scene_system_validators.py",
        ],
    },
    "t1.global.production_feasibility.tagging": {
        "status": "verified",
        "targets": ["production.episode.tag-resource-requirements", "production.assessment.never-delete-story"],
        "decision": "八类制片资源需求进入结构化枚举；评估仅描述需求，不得擅自删除或削弱剧情。",
        "tests": ["v6/artifacts/components/production-package.schema.json", "v6/evaluations/tests/test_production_validators.py"],
    },
    "t1.global.production_feasibility.alternative": {
        "status": "verified",
        "targets": ["production.high-complexity.require-alternative", "production.alternative.preserve-dramatic-function"],
        "decision": "高复杂度场景强制提供替代方案，并显式记录保留的戏剧功能和核心转折。",
        "tests": ["v6/artifacts/components/production-package.schema.json", "v6/evaluations/tests/test_production_validators.py"],
    },
    "t1.global.production_feasibility.camera-visible": {
        "status": "verified",
        "targets": ["production.content.require-camera-visible-information", "scene.content.keep-filmable", "scene.content.forbid-parenthetical-interiority"],
        "decision": "可拍摄性同时进入写场景能力与独立制片评估，并复用已验证的场景外化规则。",
        "tests": ["v6/evaluations/tests/test_scene_system_validators.py", "v6/evaluations/atomic-rules/production.yaml"],
    },
    "t1.global.budget_estimation.band-only": {
        "status": "verified",
        "targets": ["budget.estimate.use-band-without-quotes", "budget.amount.require-provenance"],
        "decision": "无真实报价上下文时只允许预算带；金额模式强制币种、地区、价格版本和未计入项。",
        "tests": ["v6/artifacts/components/production-package.schema.json", "v6/evaluations/tests/test_production_validators.py"],
    },
    "t1.global.platform_ops.release-check": {
        "status": "verified",
        "targets": ["release.check.require-canonical-evidence", "release.policy.block-unverified-or-expired"],
        "decision": "上架证据结构化；平台政策未核验或过期时确定性禁止 release_ready。",
        "tests": ["v6/artifacts/components/production-package.schema.json", "v6/evaluations/tests/test_production_validators.py"],
    },
    "t3.drama-script-writer.writing_requirements.episode-range": {
        "status": "verified",
        "targets": [
            "continuity.context.use-explicit-episode-scope",
            "continuity.context.require-immediate-predecessor",
            "execution.episode-context.load-minimum-sufficient-set",
            "screenplay.format.use-canonical-patterns",
            "dialogue.line.require-action-intent",
            "production.episode.tag-resource-requirements",
        ],
        "decision": "episode_range、逐集最小上下文、格式 SSOT、台词工艺与首稿制片标签已分别由无状态能力承接。",
        "tests": [
            "v6/evaluations/tests/test_continuity_validators.py",
            "v6/evaluations/tests/test_scene_system_validators.py",
            "v6/evaluations/tests/test_production_validators.py",
        ],
    },
    "t4.global.p0_categories.redlines": {
        "status": "verified", "targets": ["compliance.p0.block-on-redline", "compliance.fuse.block-p0-or-unresolved-p1"],
        "decision": "P0 类别与熔断裁决分离：语义分类产生 finding，确定性裁决禁止通过及下游执行。",
        "tests": ["v6/evaluations/tests/test_compliance_validators.py", "v6/evaluations/atomic-rules/compliance.yaml"],
    },
    "t4.global.p0_categories.horror-grading": {
        "status": "verified", "targets": ["compliance.horror.use-three-level-disposition"],
        "decision": "极端、高风险、中风险恐怖内容分别确定性映射为 P0、P1、P2，并写入统一 finding。",
        "tests": ["v6/evaluations/tests/test_compliance_validators.py"],
    },
    "t4.global.p1_categories.must-fix": {
        "status": "verified", "targets": ["compliance.p1.require-resolution", "compliance.fuse.block-p0-or-unresolved-p1"],
        "decision": "P1 必须以 resolved 状态闭环；未解决 P1 不能获得通过结论或进入下游。",
        "tests": ["v6/evaluations/tests/test_compliance_validators.py"],
    },
    "t4.global.p2_advisories.optimize": {
        "status": "verified", "targets": ["compliance.p2.record-without-blocking"],
        "decision": "P2 强制记录证据与建议，但在无 P0、未解决 P1 和其他门禁缺口时不阻断。",
        "tests": ["v6/evaluations/tests/test_compliance_validators.py"],
    },
    "t4.global.risk_assessment.nine-dimensions": {
        "status": "verified", "targets": ["compliance.risk.cover-nine-dimensions", "compliance.risk.never-default-unchecked-to-pass"],
        "decision": "九个维度在 Schema 中逐项枚举并要求恰好覆盖一次，not-checked 不得默认为 pass。",
        "tests": ["v6/artifacts/components/compliance-report.schema.json", "v6/evaluations/tests/test_compliance_validators.py"],
    },
    "t4.global.platform_specific.declared-target": {
        "status": "verified", "targets": ["compliance.platform.record-target-and-version", "release.policy.block-unverified-or-expired"],
        "decision": "有目标平台必须携带已核验规则版本；无平台时明确标记专项未检查。",
        "tests": ["v6/evaluations/tests/test_compliance_validators.py", "v6/evaluations/tests/test_production_validators.py"],
    },
    "t4.global.three_phase_checklist.gates": {
        "status": "verified", "targets": ["compliance.phase.use-canonical-checklist", "compliance.delivery.require-materials"],
        "decision": "立项、逐集、交付阶段独立枚举；交付材料缺失时不得输出通过结论。",
        "tests": ["v6/artifacts/components/compliance-report.schema.json", "v6/evaluations/tests/test_compliance_validators.py"],
    },
    "t4.global.fuse_behavior.guard": {
        "status": "verified", "targets": ["compliance.fuse.block-p0-or-unresolved-p1"],
        "decision": "P0 返回 block，未解决 P1 返回 revise，两者均设置 downstream_allowed=false。",
        "tests": ["v6/evaluations/tests/test_compliance_validators.py"],
    },
    "t4.global.justice_tail_rule.core": {
        "status": "verified",
        "targets": ["compliance.justice.apply-density-thresholds", "compliance.justice.require-ending-closure"],
        "decision": "语义扫描输出带位置的犯罪与正义收束证据；裁决器原样执行 2/5 触发、2/3 收束及最后 35% 窗口。",
        "tests": ["v6/evaluations/tests/test_compliance_validators.py", "v6/constraints/compliance.yaml"],
    },
    "t4.global.justice_tail_rule.whitewash-detection": {
        "status": "verified",
        "targets": ["compliance.whitewash.require-responsibility-consequence", "compliance.p1.require-resolution"],
        "decision": "疑似洗白表达仅作为语义证据标记；缺少责任或后果时才生成未解决 P1。",
        "tests": ["v6/evaluations/tests/test_compliance_validators.py"],
    },
    "t4.global.values_bottom_line.core": {
        "status": "verified",
        "targets": ["compliance.values.forbid-glorified-harm", "compliance.values.allow-motive-with-accountability"],
        "decision": "允许有动机的反派，但犯罪、虐待、歧视或反社会行为不得通过删除责任与后果被美化。",
        "tests": ["v6/evaluations/tests/test_compliance_validators.py"],
    },
    "t1.global.originality.protected-elements": {
        "status": "verified", "targets": ["originality.scan.cover-six-protected-elements", "originality.expression.borrow-only-abstract-mechanism"],
        "decision": "六类受保护元素逐项结构化；仅允许保留抽象戏剧机制，不复用可识别具体表达组合。",
        "tests": ["v6/artifacts/components/originality-report.schema.json", "v6/evaluations/tests/test_originality_validators.py"],
    },
    "t1.global.originality.rewrite-strategy": {
        "status": "verified", "targets": ["originality.rewrite.change-four-structural-dimensions", "originality.rewrite.forbid-rename-only"],
        "decision": "原创化重写必须同时改变关系、场景、时机与因果链，改名或少量换词明确不合格。",
        "tests": ["v6/evaluations/tests/test_originality_validators.py"],
    },
    "t1.global.originality.similarity-thresholds": {
        "status": "verified", "targets": ["originality.similarity.use-canonical-thresholds", "originality.comparison.never-fabricate-pass"],
        "decision": "严格保留 >0.72、>0.80、>0.20 三个触发条件；不可检索时只能输出 not-completed。",
        "tests": ["v6/constraints/originality.yaml", "v6/evaluations/tests/test_originality_validators.py"],
    },
    "t1.global.originality.ai-rights": {
        "status": "verified", "targets": ["originality.ai-rights.forbid-identifiable-imitation", "originality.ai-rights.require-release-label"],
        "decision": "AI 资产逐项记录类型、模仿风险、权利来源及平台/地区标识状态。",
        "tests": ["v6/artifacts/components/originality-report.schema.json", "v6/evaluations/tests/test_originality_validators.py"],
    },
    "t4.global.title_compliance.core": {
        "status": "verified", "targets": ["compliance.title.require-originality-and-honest-promise", "originality.scan.cover-six-protected-elements", "originality.comparison.never-fabricate-pass"],
        "decision": "片名冒充、受保护角色名、虚假承诺与规避审核由语义证据判定，原创性检索未完成时不得通过。",
        "tests": ["v6/artifacts/components/originality-report.schema.json", "v6/evaluations/tests/test_originality_validators.py"],
    },
    "t3.drama-compliance-guard.compliance.latest-script": {
        "status": "verified", "targets": ["compliance.fuse.block-p0-or-unresolved-p1", "originality.comparison.never-fabricate-pass"],
        "decision": "裁判只读取 latest_script 的合规与原创性评估，只决定交付许可；P0、未解决 P1 或原创性未比对均禁止通过。",
        "tests": ["v6/evaluations/tests/test_compliance_validators.py", "v6/evaluations/tests/test_originality_validators.py"],
    },
    "t1.global.concept.entry-paths": {
        "status": "verified", "targets": ["concept.entry.use-canonical-path", "concept.core.converge-to-forced-choice"],
        "decision": "五类入口进入枚举，最终统一收敛为人物、处境、压力与被迫选择四字段。",
        "tests": ["v6/artifacts/components/project-brief.schema.json", "v6/evaluations/tests/test_concept_validators.py"],
    },
    "t1.global.concept.combination-methods": {
        "status": "verified", "targets": ["concept.combination.use-canonical-method", "concept.core.keep-one-dramatic-action"],
        "decision": "五种组合方法结构化，组合完成后由确定性校验保证只保留一个核心戏剧动作。",
        "tests": ["v6/artifacts/components/project-brief.schema.json", "v6/evaluations/tests/test_concept_validators.py"],
    },
    "t1.global.concept.elevator-test": {
        "status": "verified", "targets": ["concept.elevator.require-four-elements", "concept.elevator.survive-proper-noun-removal"],
        "decision": "主角身份、急切目标、核心阻碍、差异化机制和去专名版本分别进入 Schema 字段。",
        "tests": ["v6/artifacts/components/project-brief.schema.json", "v6/evaluations/tests/test_concept_validators.py"],
    },
    "t3.drama-topic-director.project_brief.market-integrated": {
        "status": "verified", "targets": ["project-brief.market.require-integrated-judgment", "project-brief.risk.precheck-without-compliance-verdict"],
        "decision": "市场判断字段完整进入 project-brief；敏感题材只做风险预检，合规 verdict 固定为空。",
        "tests": ["v6/artifacts/components/project-brief.schema.json", "v6/evaluations/tests/test_concept_validators.py"],
    },
    "t1.global.learned_rules.lr001": {
        "status": "verified", "targets": ["learned.revenge-opening.show-oppression-within-thirty-seconds"],
        "decision": "复仇/逆袭首集受压事件以秒数定位，30 秒边界纳入确定性校验。",
        "tests": ["v6/evaluations/tests/test_learned_guardrails.py"],
    },
    "t1.global.learned_rules.lr002": {
        "status": "verified", "targets": ["learned.romance-monologue.limit-consecutive-lines", "emotion.expression.use-filmable-channel", "emotion.expression.forbid-adjective-only-interiority"],
        "decision": "甜宠/治愈连续内心独白最多三句，并复用情绪外化规则引导互动与可拍摄表达。",
        "tests": ["v6/evaluations/tests/test_learned_guardrails.py", "v6/evaluations/tests/test_emotion_system_validators.py"],
    },
    "t1.global.learned_rules.lr005": {
        "status": "verified", "targets": ["learned.identity-reveal.use-canonical-window", "learned.identity-reveal.require-ritualized-scene"],
        "decision": "S 级身份反转保留至少 5 集铺垫、前 3 集暗示、55%-75% 揭露窗口及仪式化场景要求。",
        "tests": ["v6/constraints/learned-guardrails.yaml", "v6/evaluations/tests/test_learned_guardrails.py"],
    },
    "t1.global.learned_rules.lr006": {
        "status": "verified", "targets": ["learned.progressive-beats.meet-sixty-percent", "learned.progressive-beat.change-story-state"],
        "decision": "推进节拍比例下限 60%，每个推进节拍必须改变六类故事状态之一。",
        "tests": ["v6/evaluations/tests/test_learned_guardrails.py"],
    },
    "t1.global.learned_rules.lr007": {
        "status": "verified", "targets": ["payment.first-checkpoint.use-window", "payment.card.use-canonical-type", "payment.promise.meet-payoff-deadline", "payment.hook.must-map-promise-to-payoff"],
        "decision": "首付费卡点、三类卡型、付费后最多 1 集兑现及承诺映射均由现有确定性规则闭环。",
        "tests": ["v6/evaluations/tests/test_episode_plan_validators.py", "v6/artifacts/episode-plan/2.schema.json"],
    },
    "t1.global.learned_rules.lr009": {
        "status": "verified", "targets": ["learned.breathing-episode.limit-rolling-window", "emotion.breathing-episode.do-not-repeat"],
        "decision": "滚动 10 集最多 1 个松轻喘息集，并保留禁止连续出现及必须推进支线/关系的既有规则。",
        "tests": ["v6/evaluations/tests/test_learned_guardrails.py", "v6/evaluations/tests/test_emotion_system_validators.py"],
    },
    "t1.global.learned_rules.lr010": {
        "status": "verified", "targets": ["learned.crisis-episode.require-tight-heavy", "emotion.rhythm.use-dual-track"],
        "decision": "大反转、身份揭示和决裂集确定性要求 tight-heavy 双轨节奏。",
        "tests": ["v6/evaluations/tests/test_learned_guardrails.py", "v6/artifacts/components/emotion-system.schema.json"],
    },
    "t1.global.learned_rules.lr011": {
        "status": "verified", "targets": ["learned.structured-output.require-json-object", "learned.structured-output.forbid-runtime-metadata"],
        "decision": "产物必须为 JSON 对象，禁止运行时元数据，并按各正式 Schema 的 canonical enum 拒绝同义改写。",
        "tests": ["v6/evaluations/tests/test_learned_guardrails.py", "v6/tools/validate_v6.py"],
    },
    "t1.global.series_structure.boundary": {
        "status": "verified", "targets": ["blueprint.scope.forbid-episode-scene-expansion", "blueprint.world.keep-only-actionable-rules", "world.rule.must-change-action"],
        "decision": "蓝图字段白名单禁止提前展开逐集场景；世界规则继续复用可行动性原子规则。",
        "tests": ["v6/evaluations/tests/test_architecture_validators.py", "v6/evaluations/tests/test_world_system_validators.py"],
    },
    "t1.global.rhythm_rules.hook-density": {
        "status": "verified", "targets": ["hook.opening.layered-window", "hook.first-episode.meet-minimum-count", "episode.ending.leave-open-question-or-threat", "hook.grade.use-canonical-hierarchy"],
        "decision": "首集开场窗口、钩子数量、逐集末尾未解问题和等级规范均已由现有原子规则闭环。",
        "tests": ["v6/evaluations/tests/test_episode_plan_validators.py"],
    },
    "t1.global.foreshadowing_rules.density": {
        "status": "verified", "targets": ["foreshadow.density.require-a-grade-per-ten-episodes", "foreshadow.reversal.requires-verifiable-setup", "learned.identity-reveal.use-canonical-window"],
        "decision": "每十集至少一个 A 级伏笔、禁止无铺垫硬反转及 S 级身份反转窗口分别验证。",
        "tests": ["v6/evaluations/tests/test_architecture_validators.py", "v6/evaluations/tests/test_learned_guardrails.py"],
    },
    "t1.global.philosophy.cross-section": {
        "status": "verified", "targets": ["philosophy.cross-section.start-at-maximum-tension", "philosophy.opening.define-tone-not-explain-theme", "scene.unit.define-goal-conflict-risk"],
        "decision": "首集首场从高张力横截面切入，Goal/Conflict 立即成立，并禁止用主题说明替代行动定调。",
        "tests": ["v6/evaluations/tests/test_architecture_validators.py", "v6/evaluations/tests/test_scene_system_validators.py"],
    },
    "t1.global.philosophy.mckee-value-shift": {
        "status": "verified", "targets": ["scene.unit.require-value-change", "scene.exit.leave-after-value-change"],
        "decision": "每场 value_before/value_after 必须变化，无价值转变场景由确定性校验判为无效。",
        "tests": ["v6/artifacts/components/scene-system.schema.json", "v6/evaluations/tests/test_scene_system_validators.py"],
    },
    "t2.matrix.genre_rules.from-brief": {
        "status": "verified", "targets": ["genre.matrix.consume-synthesized-rule-params", "genre.matrix.hooks-and-emotion-follow-params"],
        "decision": "四轴合成后的 reversal_density、8 节点 emotion_curve 和 hook_types 正式进入 project-brief rule_params。",
        "tests": ["v6/artifacts/components/project-brief.schema.json", "v6/evaluations/tests/test_architecture_validators.py"],
    },
    "t2.matrix.rhythm_rules.from-brief": {
        "status": "verified", "targets": ["genre.matrix.use-brief-act-ratio", "series.stage.override-only-from-project-brief"],
        "decision": "六阶段占比只能读取 project_brief.rule_params.act_ratio，缺失时返回上游合成。",
        "tests": ["v6/artifacts/components/project-brief.schema.json", "v6/evaluations/tests/test_architecture_validators.py"],
    },
    "t3.drama-episode-designer.episode_structure.episode-card": {
        "status": "verified", "targets": ["episode-plan.card.required-content", "episode-plan.scope.global-structure-readonly"],
        "decision": "分集设计卡写入正式 episode-plan schema，并由只读边界禁止重写 story_bible 主线和六阶段结构。",
        "tests": ["v6/artifacts/episode-plan/2.schema.json", "v6/evaluations/tests/test_episode_plan_validators.py"],
    },
    "t3.drama-story-bible.dual-mode.same-schema": {
        "status": "verified", "targets": ["story-bible.mode.use-one-schema", "story-bible.adaptation.record-treatment"],
        "decision": "原创与改编使用同一 story-bible Schema；改编模式额外要求原故事提取、保留/强化/改写清单和原创性报告版本。",
        "tests": ["v6/artifacts/components/story-bible.schema.json", "v6/evaluations/tests/test_story_bible_validators.py"],
    },
    "t3.drama-story-bible.character_rules.density": {
        "status": "verified", "targets": ["story-bible.compose.reference-versioned-components", "story-bible.world.require-action-power-reveal-components", "character.count.limit-protagonists", "character.arc.define-four-points", "world.rule.must-change-action", "world.power.sustain-main-conflict", "world.reveal.limit-new-layer-per-episode"],
        "decision": "story-bible 只组合版本化人物、世界、项目简报和原创性组件引用，不复制其内部规则。",
        "tests": ["v6/evaluations/tests/test_story_bible_validators.py", "v6/evaluations/tests/test_character_system_validators.py", "v6/evaluations/tests/test_world_system_validators.py"],
    },
    "t3.drama-story-bible.episode_structure.six-stage": {
        "status": "verified", "targets": ["story-bible.series.require-six-contiguous-stages", "series.stage.use-canonical-order", "series.stage.allocate-largest-remainder", "series.stage.override-only-from-project-brief"],
        "decision": "六阶段顺序、连续区间、全集覆盖、最大余数分配和 project-brief 比例覆盖均有确定性校验。",
        "tests": ["v6/evaluations/tests/test_story_bible_validators.py", "v6/evaluations/tests/test_episode_plan_validators.py"],
    },
    "t1.global.scoring.geval-framework": {
        "status": "verified", "targets": ["quality.geval.record-evidence-before-score", "quality.score.use-ssot-thresholds"],
        "decision": "逐维保存公开证据与扣分后计算分数，不记录隐藏推理；等级与返工阈值只读质量约束。",
        "tests": ["v6/artifacts/components/quality-report.schema.json", "v6/evaluations/tests/test_quality_validators.py"],
    },
    "t1.global.scoring.ten-dimensions": {
        "status": "verified", "targets": ["quality.dimensions.require-canonical-ten", "quality.preset.preserve-ten-dimension-model"],
        "decision": "十维模型逐项唯一覆盖；预设只能改变权重、通过阈值和交付资格，不能改变维度集合。",
        "tests": ["v6/artifacts/components/quality-report.schema.json", "v6/evaluations/tests/test_quality_validators.py"],
    },
    "t1.global.scoring.s-class-veto": {
        "status": "verified", "targets": ["quality.veto.cap-grade-at-b"],
        "decision": "开场冲击、至少三项明确恶行和贯穿 S/A 悬念任一缺失时封顶 B，并在报告记录否决证据。",
        "tests": ["v6/evaluations/tests/test_quality_validators.py"],
    },
    "t3.drama-revision-master.writing_requirements.revision-only": {
        "status": "verified", "targets": ["revision.scope.only-address-authorized-findings", "revision.require-passing-rescore-before-next-batch"],
        "decision": "修订只响应质量、合规或用户问题，保护 project-brief/story-bible/episode-plan；复评通过前禁止下一批。",
        "tests": ["v6/evaluations/tests/test_quality_validators.py"],
    },
    "t3.drama-script-scorer.scoring.ten-dimension": {
        "status": "verified", "targets": ["quality.judge.read-latest-script-only", "quality.dimensions.require-canonical-ten"],
        "decision": "评分能力作为无副作用独立裁判，只读取 latest_script，并要求连续性终审字段。",
        "tests": ["v6/artifacts/components/quality-report.schema.json", "v6/evaluations/tests/test_quality_validators.py"],
    },
    "t3.drama-script-scorer.scoring.evolution-proposal": {
        "status": "verified", "targets": ["evolution.log-batch-below-threshold", "evolution.propose-after-two-dimension-failures"],
        "decision": "overall_score<70 记录批次；同维度连续两批<70 才输出带目标与证据的规则升级提案。",
        "tests": ["v6/evaluations/tests/test_quality_validators.py", "v6/constraints/quality.yaml"],
    },
    "t3.drama-delivery-tool.delivery.gate": {
        "status": "verified", "targets": ["delivery.gate.require-quality-compliance-production", "delivery.gate.emit-gaps-without-marketing", "release.policy.block-unverified-or-expired", "compliance.fuse.block-p0-or-unresolved-p1"],
        "decision": "交付同时读取质量、合规、生产与预设；任一缺口只返回不可交付清单并禁止宣发物料。",
        "tests": ["v6/evaluations/tests/test_quality_validators.py", "v6/evaluations/tests/test_production_validators.py", "v6/evaluations/tests/test_compliance_validators.py"],
    },
    "t1.global.series_structure.six-stage": {
        "status": "verified",
        "targets": [
            "series.stage.use-canonical-order",
            "series.stage.allocate-largest-remainder",
            "series.stage.override-only-from-project-brief",
        ],
        "decision": "六阶段顺序、基础比例、最大余数分配和项目参数覆盖已迁移。",
        "tests": ["v6/evaluations/tests/test_episode_plan_validators.py"],
    },
}


def main() -> int:
    candidates = json.loads((ROOT / "migration" / "rule-candidates.json").read_text(encoding="utf-8"))
    mappings = []
    for candidate in candidates["candidates"]:
        item = {
            "candidate_id": candidate["candidate_id"],
            "legacy_rule_key": candidate["legacy_rule_key"],
            "source": candidate["source"],
            "status": "pending",
            "targets": [],
            "decision": "",
            "tests": [],
        }
        item.update(OVERRIDES.get(candidate["legacy_rule_key"], {}))
        mappings.append(item)

    counts = Counter(item["status"] for item in mappings)
    total = len(mappings)
    report = {
        "total": total,
        "counts": dict(sorted(counts.items())),
        "started_coverage": round((total - counts.get("pending", 0)) / max(total, 1), 6),
        "verified_coverage": round(counts.get("verified", 0) / max(total, 1), 6),
    }
    (ROOT / "migration" / "rule-mapping.json").write_text(
        json.dumps({"version": 1, "mappings": mappings}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (ROOT / "migration" / "rule-coverage-report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
