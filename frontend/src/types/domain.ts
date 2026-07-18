/** API envelope & shared domain types */

export type ApiEnvelope<T> = {
  code: number
  message: string
  data: T | null
}

export type EntryType = 'original_track' | 'story_adapt'

export type GenreMatrix = {
  emotion: string
  identity: string
  conflict: string
  world: string
}

export type AdaptNotes = {
  retained: string[]
  enhanced: string[]
  rewritten: string[]
}

export type ProductionContext = {
  target_band: 'lean' | 'standard' | 'complex'
  region?: string
  currency?: string
  pricing_version?: string
  excluded_items?: string[]
}

export type DeliveryItem =
  | 'storyboard'
  | 'visual'
  | 'marketing'
  | 'interactive'
  | 'budget'
  | 'release'

export type CreationPreferences = {
  batch_episode_max: number
  outline_mode: 'full' | 'structure_only'
  scoring_preset: string
  compliance_check_mode: 'standard' | 'values-risk' | 'full'
  enable_delivery: boolean
  delivery_items?: DeliveryItem[]
}

export type ProjectSettingsAudit = {
  revision: number
  created_at?: string
  updated_at: string
  updated_by: string
}

export type ProjectSettings = {
  schema_version: 'project-settings.v1'
  project_id?: string
  skills_version?: string
  skills_git_ref?: string
  entry_type: EntryType
  title?: string
  core_idea?: string
  synopsis?: string
  external_story?: string
  adapt_notes?: AdaptNotes
  audience_channel?: string
  genre_matrix?: GenreMatrix
  protagonist_structure?: string | null
  flavor_tags?: string[]
  preset_theme_code?: string | null
  episode_count: number
  target_platform: string
  reference_dramas?: string[]
  production_context: ProductionContext
  creation_preferences: CreationPreferences
  platform_policy?: {
    policy_version?: string | null
    policy_source?: string | null
    verified_at?: string | null
  }
  derived?: {
    matrix_key?: string
    rule_params_ref?: string
  }
  audit: ProjectSettingsAudit
}

export type WorkflowStatus =
  | 'active'
  | 'waiting_approval'
  | 'waiting_quality'
  | 'waiting_user'
  | 'completed'
  | 'blocked'

export type WorkflowPhase =
  | 'strategy'
  | 'blueprint'
  | 'blueprint_approval'
  | 'episode_design'
  | 'writing'
  | 'quality'
  | 'revision'
  | 'delivery'
  | 'completed'

export type UserDecisionOption = 'accept_current' | 'manual_revision' | 'abandon_batch'

export type WorkflowState = {
  schema_version: 'workflow-state.v1'
  project_id: string
  version: number
  entry_type: EntryType
  status: WorkflowStatus
  current_phase: WorkflowPhase
  approvals: Record<string, unknown>
  batch_cursor: number
  revision_round: number
  score_history: number[]
  quality_results: Record<string, unknown>
  artifacts: Record<string, unknown>
  processed_commands: string[]
  blocked_reason?: string | null
  pending_user_options?: string[]
}

export type WorkflowCommandRequest = {
  command_id: string
  event: string
  expected_version: number
  payload?: Record<string, unknown>
}

export type ApprovalDecision = 'approve' | 'reject'

export type StoryBibleApprovalRequest = {
  command_id: string
  decision: ApprovalDecision
  expected_version: number
}

/** Artifact API wrapper — schema_version is numeric (artifacts contract), not legacy *.v1 strings */
export type ArtifactRecord<T = unknown> = {
  artifact_key: string
  version: number | null
  schema_version?: number
  payload: T | null
}

export type DramaProjectSummary = {
  id: string
  title: string
  entry_type: EntryType
  status?: string
  episode_count?: number
  updated_at?: string
  created_at?: string
}

export type CreateProjectRequest = {
  title: string
  entry_type: EntryType
  episode_count?: number
  core_idea?: string
  external_story?: string
}

export type GenerationJobStatus =
  | 'pending'
  | 'queued'
  | 'running'
  | 'completed'
  | 'failed'
  | 'disabled'

export type GenerationStartRequest = {
  command_id: string
  expected_version: number
  role: string
  input?: Record<string, unknown>
}

export type GenerationJob = {
  job_id: string
  project_id: string | null
  job_type?: string
  status: GenerationJobStatus
  role?: string
  command_id?: string
  artifact_key?: string | null
  workflow_version?: number | null
  progress?: number
  message?: string
  error?: string | null
  result?: unknown
  /** 外部评测列表展示名（文件名 / 剧本名 / 正文首行） */
  title?: string | null
  source_filename?: string | null
  created_at?: string
  updated_at?: string
}

export type SseJobEvent = {
  type:
    | 'status'
    | 'progress'
    | 'log'
    | 'artifact'
    | 'error'
    | 'done'
    | 'timeout'
    | 'heartbeat'
    | 'warning'
    | 'message'
  job_id: string
  status?: GenerationJobStatus
  progress?: number
  message?: string | null
  done?: boolean
  data?: unknown
}

export type OpsConfigOverlay = {
  schema_version: 'ops-config-overlay.v1'
  tenant_id: string
  skills_version: string
  effective_at?: string
  overrides: Record<string, Record<string, unknown>>
  audit: {
    revision: number
    updated_by: string
    updated_at: string
    change_reason: string
  }
}

export type ConfigRollbackRequest = {
  target_revision: number
  change_reason: string
}

export type ExternalScriptReviewRequest = {
  command_id: string
  scoring_preset: string
  check_mode: 'standard' | 'values-risk' | 'full'
  script_content?: string
  content?: string
  source_filename?: string
  filename?: string
  script_title?: string
  project_id?: string
}

export type AuthTokens = {
  access: string
  refresh: string
}

export type AuthUser = {
  id: string
  nickname?: string
  username?: string
  email?: string
}

export type LoginResponse = {
  access: string
  refresh: string
  user?: AuthUser
}
