import type { ProjectSettings } from '@/types/domain'
import type { WorkbenchDefinition, WorkbenchFormApiResponse } from '@/types/workbench'
import { normalizeWorkbenchDefinition } from '@/utils/workbenchDefinition'

/** Minimal project settings fixture for tests — not a business-default catalog. */
export function testProjectSettings(partial?: Partial<ProjectSettings>): ProjectSettings {
  return {
    schema_version: 'project-settings.v1',
    entry_type: 'original_track',
    episode_count: 80,
    target_platform: 'generic',
    core_idea: '',
    production_context: {
      target_band: 'standard',
    },
    creation_preferences: {
      batch_episode_max: 5,
      outline_mode: 'full',
      scoring_preset: 'standard',
      compliance_check_mode: 'standard',
      enable_delivery: false,
      deliverables: ['storyboard', 'visual', 'marketing', 'budget'],
    },
    flavor_tags: [],
    reference_dramas: [],
    audit: {
      revision: 1,
      updated_at: new Date().toISOString(),
      updated_by: 'user',
    },
    ...partial,
  }
}

/** Compact API-shaped fixture used by dynamic contract tests. */
export function testWorkbenchFormApi(
  overrides?: Partial<WorkbenchFormApiResponse>,
): WorkbenchFormApiResponse {
  const base: WorkbenchFormApiResponse = {
    schema_version: 'workbench-form.v1',
    skills_bundle_version: '5.0.0',
    project_settings: {
      groups: {
        entry: {
          label_zh: '创作入口',
          fields: ['entry_type', 'core_idea', 'external_story', 'adapt_notes'],
        },
        theme: {
          label_zh: '题材与平台',
          fields: ['genre_matrix', 'flavor_tags', 'preset_theme_code', 'target_platform'],
        },
        delivery: {
          label_zh: '交付偏好',
          fields: ['enable_delivery', 'deliverables'],
        },
      },
      fields: {
        entry_type: {
          type: 'string',
          persist_path: 'entry_type',
          required: true,
          enum: ['original_track', 'story_adapt'],
          default: 'original_track',
          options: [
            { value: 'original_track', label: '原创通道' },
            { value: 'story_adapt', label: '故事改编通道' },
          ],
        },
        core_idea: {
          type: 'string',
          persist_path: 'core_idea',
          ui_widget: 'textarea',
          visible_when: "entry_type == 'original_track'",
        },
        external_story: {
          type: 'string',
          persist_path: 'external_story',
          ui_widget: 'textarea',
          visible_when: "entry_type == 'story_adapt'",
          required_when: "entry_type == 'story_adapt'",
        },
        adapt_notes: {
          type: 'object',
          persist_path: 'adapt_notes',
          visible_when: "entry_type == 'story_adapt'",
        },
        genre_matrix: {
          type: 'object',
          persist_path: 'genre_matrix',
          fields: {
            emotion: {
              label: '情感轴',
              required: true,
              options: [
                { value: 'revenge', label: '复仇爽感' },
                { value: 'love', label: '爱情甜虐' },
              ],
            },
            identity: {
              label: '身份轴',
              required: true,
              options: [
                { value: 'underdog', label: '弱势逆袭' },
                { value: 'reborn', label: '重生穿越' },
              ],
            },
            conflict: {
              label: '冲突轴',
              required: true,
              options: [
                { value: 'family', label: '家族伦理' },
                { value: 'workplace', label: '职场商战' },
              ],
            },
            world: {
              label: '世界观轴',
              required: true,
              options: [
                { value: 'urban', label: '都市现实' },
                { value: 'period', label: '古装年代' },
              ],
            },
          },
        },
        flavor_tags: {
          type: 'array',
          persist_path: 'flavor_tags',
          max_items: 5,
          options: [
            { value: 'wuxia', label: '武侠江湖' },
            { value: 'xianxia', label: '修仙玄幻' },
          ],
        },
        preset_theme_code: {
          type: 'string',
          persist_path: 'preset_theme_code',
          options: [{ value: 'family-revenge', label: '家庭伦理复仇' }],
        },
        target_platform: {
          type: 'string',
          persist_path: 'target_platform',
          default: 'generic',
          options: [
            { value: 'generic', label: '通用' },
            { value: 'douyin', label: '抖音' },
          ],
        },
        enable_delivery: {
          type: 'boolean',
          persist_path: 'creation_preferences.enable_delivery',
          default: false,
        },
        deliverables: {
          type: 'array',
          persist_path: 'creation_preferences.deliverables',
          visible_when: 'enable_delivery == true',
          items_enum: ['storyboard', 'visual', 'marketing', 'interactive', 'budget', 'release'],
          default: ['storyboard', 'visual'],
        },
      },
    },
    stages: [
      {
        id: 'strategy',
        orchestration_phase: 'strategy',
        stage_kind: 'main',
        role: 'drama.topic-director',
        role_label: '选题定调官',
        artifact: 'project_brief',
        label_zh: '立项简报',
        visible_when: "entry_type == 'original_track'",
      },
      {
        id: 'blueprint',
        orchestration_phase: 'blueprint',
        stage_kind: 'main',
        role: 'drama.story-bible',
        role_label: '剧本蓝图官',
        artifact: 'story_bible',
        label_zh: '故事蓝图',
        approval_required: true,
      },
      {
        id: 'episode_design',
        orchestration_phase: 'episode_design',
        stage_kind: 'main',
        role: 'drama.episode-designer',
        role_label: '分集设计官',
        artifact: 'narrative_plan',
        label_zh: '分集设计',
      },
      {
        id: 'writing',
        orchestration_phase: 'writing',
        stage_kind: 'main',
        role: 'drama.script-writer',
        role_label: '剧本正文官',
        artifact: 'episode_scripts',
        label_zh: '分集剧本',
        batch_field: 'episode_range',
      },
      {
        id: 'quality_score',
        stage_kind: 'quality_loop',
        role: 'drama.script-scorer',
        role_label: '剧本评分官',
        artifact: 'quality_report',
        label_zh: '质量评分报告',
        parallel_group: 'quality',
      },
      {
        id: 'compliance',
        stage_kind: 'quality_loop',
        role: 'drama.compliance-guard',
        role_label: '合规审查官',
        artifact: 'compliance_report',
        label_zh: '合规审查报告',
        parallel_group: 'quality',
      },
      {
        id: 'revision',
        stage_kind: 'quality_loop',
        role: 'drama.revision-master',
        role_label: '剧本修复官',
        artifact: 'polished_script',
        label_zh: '修复稿',
        conditional: true,
      },
      {
        id: 'delivery',
        stage_kind: 'optional',
        role: 'drama.delivery-tool',
        role_label: '宣发交付工具',
        artifact: 'production_package',
        label_zh: '制作发行交付包',
        optional: true,
        visible_when: 'enable_delivery == true',
      },
    ],
    module_catalog: {
      'concept-development': {
        label_zh: '核心概念形成',
        domain: 'concept',
        kind: 'core',
        lifecycle: 'active',
        target_roles: ['drama.topic-director'],
        workbench_visible: true,
      },
      'character-system': {
        label_zh: '人物系统',
        domain: 'character',
        kind: 'core',
        lifecycle: 'active',
        target_roles: ['drama.story-bible'],
        workbench_visible: true,
      },
      'adaptation-originality': {
        label_zh: '改编原创化',
        domain: 'concept',
        kind: 'core',
        lifecycle: 'active',
        target_roles: ['drama.story-bible'],
        workbench_visible: true,
        enable_when: "entry_type == 'story_adapt'",
      },
      'storyboard-9col': {
        label_zh: '九列分镜',
        domain: 'production',
        kind: 'extension',
        lifecycle: 'active',
        target_roles: ['drama.delivery-tool'],
        workbench_visible: true,
        enable_when: "deliverables contains 'storyboard'",
      },
    },
    admin_settings: {
      sections: [
        { id: 'model_routing', source: 'foundation/constraints/agent-runtime.yaml' },
        { id: 'script_format', source: 'foundation/constraints/script-format.yaml' },
      ],
    },
  }

  return {
    ...base,
    ...overrides,
    project_settings: {
      ...base.project_settings,
      ...overrides?.project_settings,
      groups: overrides?.project_settings?.groups ?? base.project_settings.groups,
      fields: {
        ...base.project_settings.fields,
        ...overrides?.project_settings?.fields,
      },
    },
    stages: overrides?.stages ?? base.stages,
    module_catalog: overrides?.module_catalog ?? base.module_catalog,
  }
}

export function testWorkbenchDefinition(
  overrides?: Partial<WorkbenchFormApiResponse>,
): WorkbenchDefinition {
  return normalizeWorkbenchDefinition(testWorkbenchFormApi(overrides))
}
