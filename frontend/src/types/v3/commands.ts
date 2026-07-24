export const PRODUCT_COMMAND_TYPES = [
  'create_project',
  'generate_topic_brief',
  'confirm_topic_brief',
  'generate_blueprint',
  'confirm_blueprint',
  'generate_episode_plan',
  'confirm_episode_plan',
  'revise_episode_plan',
  'write_episode_batch',
  'confirm_script_candidate',
  'score_quality',
  'check_compliance',
  'accept_findings',
  'revise_from_findings',
  'prepare_delivery',
  'test_model_provider',
] as const

export type ProductCommandType = (typeof PRODUCT_COMMAND_TYPES)[number]
