export type ProjectEntryType = 'original' | 'adapt'
export type ProjectStage = 'topic' | 'blueprint' | 'episodes' | 'writing' | 'quality' | 'delivery'
export type CommandRunStatus = 'queued' | 'running' | 'succeeded' | 'failed' | 'unsupported'

export interface ProjectSummary {
  id: string
  title: string
  entry_type: ProjectEntryType
  stage: ProjectStage
  progress_percent?: number
  archived_at?: string | null
  updated_at: string
}

export interface CommandRunSummary {
  id: string
  command_type: string
  status: CommandRunStatus
  project_id: string | null
  error_message: string
  result_payload: Record<string, unknown>
  created_at: string
  updated_at: string
}

export interface CreateProjectRequest {
  title: string
  entry_type: ProjectEntryType
  /** 自定义模板 UUID（与 theme_code 互斥） */
  template_id?: string | null
  /** 内置主题码（与 template_id 互斥） */
  theme_code?: string
}

export type ArtifactStatus = 'draft' | 'candidate' | 'committed' | 'superseded'

export interface ArtifactVersion {
  id: string
  artifact_key: string
  version: number
  schema_version: number
  status: ArtifactStatus
  payload: Record<string, unknown>
  created_at: string
}

/** P3-W3 可回滚主链产物 key */
export type RollbackArtifactKey =
  | 'project_brief'
  | 'story_bible'
  | 'character_system'
  | 'world_system'
  | 'emotion_system'
  | 'originality_report'
  | 'episode_plan'
  | 'episode_scripts'

export interface ArtifactVersionList {
  items: ArtifactVersion[]
}

export interface ArtifactRollbackRequest {
  artifact_key: RollbackArtifactKey
  source_version: number
}

export interface TopicState {
  stage: ProjectStage
  committed: ArtifactVersion | null
  candidate: ArtifactVersion | null
  draft: ArtifactVersion | null
  latest_run: CommandRunSummary | null
}

/** 蓝图五产物按 artifact_key 聚合 */
export type BlueprintBundle = Partial<Record<string, ArtifactVersion>>

export interface BlueprintState {
  committed: BlueprintBundle | null
  candidate: BlueprintBundle | null
  latest_run: CommandRunSummary | null
}

export interface EpisodesState {
  stage: ProjectStage
  committed: ArtifactVersion | null
  candidate: ArtifactVersion | null
  latest_run: CommandRunSummary | null
}

/** 正文草稿 beats：对白 / 动作等 */
export interface ScriptBeat {
  type: string
  text: string
  character?: string
}

export interface ScriptScene {
  id: string
  heading: string
  beats: ScriptBeat[]
}

export interface ScriptDraftPayload {
  scenes: ScriptScene[]
}

export interface ScriptDraft {
  episode_number: number
  payload: ScriptDraftPayload | Record<string, unknown>
  updated_at: string | null
}

export interface ScriptsState {
  committed: ArtifactVersion | null
  candidate: ArtifactVersion | null
  drafts: ScriptDraft[]
  latest_run: CommandRunSummary | null
}

export interface ScriptEpisodeState {
  episode_number: number
  committed: Record<string, unknown> | null
  candidate: Record<string, unknown> | null
  draft: ScriptDraft | null
}

/** 套餐 id：basic | pro | team（只读壳，无支付） */
export interface BillingPlan {
  id: string
  name: string
  price_label: string
  features: string[]
}

/** 质检 / 合规问题来源 */
export type QualityFindingSource = 'quality' | 'compliance'

/** 问题处理状态 */
export type QualityFindingStatus = 'open' | 'accepted' | 'resolved'

export interface QualityFinding {
  id: string
  source: QualityFindingSource
  finding_key: string
  title: string
  severity: string
  status: QualityFindingStatus
  report_artifact_id?: string | null
  created_at: string
  updated_at: string
}

/** GET /projects/:id/quality/ */
export interface QualityState {
  stage: ProjectStage
  quality_report: ArtifactVersion | null
  compliance_report: ArtifactVersion | null
  findings: QualityFinding[]
  quality_is_stale: boolean
  compliance_is_stale: boolean
  latest_quality_run: CommandRunSummary | null
  latest_compliance_run: CommandRunSummary | null
}

export interface DeliveryGateSnapshot {
  passed: boolean
  blockers: string[]
}

/** GET /projects/:id/delivery/ */
export interface DeliveryState {
  stage: ProjectStage
  gate: DeliveryGateSnapshot
  package: ArtifactVersion | null
  latest_run: CommandRunSummary | null
}

/** 系统配置 overlay 允许键（W5 最小集） */
export type TargetPlatform = 'generic' | 'douyin' | 'kuaishou' | 'wechat_miniprogram'
export type ScoringPreset = 'standard' | 'strict' | 'relaxed' | 'rhythm_first'

export interface SystemConfigOverlay {
  target_platform?: TargetPlatform
  scoring_preset?: ScoringPreset
  /** null 表示显式清除覆盖项；省略则保留上一 revision */
  quality_pass_threshold?: number | null
  /** 日费用预警阈值（元）；null 表示清除 */
  daily_cost_alert_cny?: number | null
}

export interface SystemConfigEffective {
  target_platform: TargetPlatform
  scoring_preset: ScoringPreset
  pass_threshold: number
  platform_label_zh: string
  /** 未配置时为 null（预警关闭） */
  daily_cost_alert_cny: number | null
}

/** GET/PUT /system/config/ */
export interface SystemConfigState {
  revision: number
  overlay: SystemConfigOverlay
  effective: SystemConfigEffective
}

export interface SystemConfigPutRequest {
  overlay: SystemConfigOverlay
  change_reason?: string
}

/** 角色→provider 映射键（与 recipe role 对齐） */
export const ROLE_MODEL_KEYS = [
  'drama-topic-director',
  'drama-story-bible',
  'drama-episode-designer',
  'drama-script-writer',
  'drama-script-scorer',
  'drama-compliance-guard',
  'drama-revision-master',
  'drama-delivery-tool',
] as const

export type RoleModelKey = (typeof ROLE_MODEL_KEYS)[number]

/** GET/POST /models/providers/ — 响应永不含 api_key 明文 */
export interface ModelProvider {
  id: string
  name: string
  base_url: string
  model_name: string
  temperature: number
  max_tokens: number
  is_enabled: boolean
  is_active: boolean
  api_key_set: boolean
  remark: string
  updated_at: string
  created_at?: string
}

/** 创建/更新供应商；api_key write_only，空串表示不覆盖密文 */
export interface ModelProviderWrite {
  name?: string
  base_url?: string
  model_name?: string
  api_key?: string
  temperature?: number
  max_tokens?: number
  is_enabled?: boolean
  is_active?: boolean
  remark?: string
}

/** GET/POST /models/providers/{id}/keys/ — 响应永不含 api_key 明文 */
export interface ProviderKey {
  id: string
  provider_id: string
  label: string
  sort_order: number
  is_enabled: boolean
  api_key_set: boolean
  created_at?: string | null
  updated_at?: string | null
}

export interface ProviderKeyWrite {
  label: string
  api_key?: string
  sort_order?: number
  is_enabled?: boolean
}

export interface ProviderKeyList {
  items: ProviderKey[]
}

/** GET/PUT /models/role-mappings/ */
export interface RoleModelMapping {
  role_key: RoleModelKey | string
  provider_id: string
  backup_provider_ids?: string[]
  temperature?: number | null
  max_tokens?: number | null
  updated_at?: string
}

export interface RoleModelMappingTable {
  items: RoleModelMapping[]
}

/** GET/PUT /models/prices/ */
export interface ModelPrice {
  id: number
  provider_id: string
  provider_name: string
  model_name: string
  price_in_per_1k: number
  price_out_per_1k: number
  /** 缓存命中输入单价；null/缺省表示按输入单价计 */
  price_cache_in_per_1k?: number | null
  currency: string
}

export interface ModelPriceTable {
  items: ModelPrice[]
}

export interface ModelPriceItemWrite {
  provider_id: string
  model_name: string
  price_in_per_1k: number
  price_out_per_1k: number
  price_cache_in_per_1k?: number | null
  currency?: string
}

export interface ModelPriceTableWrite {
  items: ModelPriceItemWrite[]
}

/** GET /usage/summary/ — 分组维度 */
export type UsageGroupBy = 'day' | 'model' | 'command_type'

/** GET /usage/summary/ — 单行/合计度量 */
export interface UsageMetrics {
  prompt_tokens: number
  cached_prompt_tokens?: number
  completion_tokens: number
  total_tokens: number
  call_count: number
  success_count: number
  estimated_cost: string
  unpriced_call_count: number
}

export interface UsageSummaryRow extends UsageMetrics {
  key: string
  /** 按模型分组时：供应商展示名（避免 ep-… 接入点 ID） */
  label?: string
}

/** GET /usage/summary/ 查询参数 */
export interface UsageSummaryQuery {
  project_id?: string
  date_from?: string
  date_to?: string
  group_by?: UsageGroupBy
  live?: 0 | 1 | '0' | '1'
}

/** GET /usage/summary/ 响应 data */
export interface UsageSummary {
  timezone: 'Asia/Shanghai' | string
  date_from: string
  date_to: string
  group_by: UsageGroupBy
  rows: UsageSummaryRow[]
  totals: UsageMetrics
}

/** POST /models/providers/{id}/test/ — 连通性试连结果（无 api_key） */
export interface ProviderTestResult {
  ok: boolean
  provider_id: string
  message: string
  status_code?: number
  latency_ms?: number
}

export type LlmCallStatus = 'success' | 'error'

/** GET /logs/calls/{id}/ — 单次调用快照（脱敏，无 api_key） */
export interface LogCall {
  id: string
  role: string
  purpose: string
  status: LlmCallStatus
  model_name: string
  /** 供应商展示名；无配置时回退 model_name */
  model_label?: string
  base_url?: string
  latency_ms: number
  prompt_tokens?: number | null
  completion_tokens?: number | null
  total_tokens?: number | null
  system_prompt: string
  user_prompt: string
  response_text: string
  error_message?: string
  http_status?: number | null
  v3_command_run_id?: string | null
  v3_project_id?: string | null
  created_at: string
  /** 列表截断预览（详情可省略） */
  system_prompt_preview?: string
  user_prompt_preview?: string
  response_preview?: string
}

/** GET /logs/runs/{id}/ — 主备切换尝试 */
export type FailoverAttemptStatus =
  | 'succeeded'
  | 'failed_switchable'
  | 'failed_terminal'
  | 'skipped'

export interface FailoverAttempt {
  id: string
  attempt_index: number
  provider_id: string
  provider_name: string
  status: FailoverAttemptStatus
  error_code: string
  error_message: string
  llm_call_log_id: string | null
  created_at: string
}

/** GET /logs/runs/{id}/ — run + 关联 LLM calls + failover attempts */
export interface LogRun extends CommandRunSummary {
  calls: LogCall[]
  failover_attempts: FailoverAttempt[]
}

/** GET /logs/runs/ 分页列表 */
export interface LogRunList {
  items: CommandRunSummary[]
  total?: number
  limit?: number
  offset?: number
}

/** GET /api/v3/templates/ — 内置模板 */
export interface BuiltinTemplate {
  theme_code: string
  label_zh: string
  dims: Record<string, unknown>
  kind: 'builtin'
}

/** GET /api/v3/templates/ — 自定义模板 */
export interface CustomTemplate {
  id: string
  name: string
  theme_code: string
  label_zh: string
  dims: Record<string, unknown>
  description?: string
  created_by?: string | null
  created_at?: string | null
  updated_at?: string | null
  kind: 'custom'
}

export interface TemplateList {
  builtin: BuiltinTemplate[]
  custom: CustomTemplate[]
}

export interface CustomTemplateWrite {
  name: string
  theme_code: string
  label_zh: string
  dims?: Record<string, unknown>
  description?: string
}

/** GET /api/v3/knowledge/ — 文件索引项 */
export interface KnowledgeDocSummary {
  path: string
  title: string
  section: string
  excerpt: string
}

export interface KnowledgeList {
  items: KnowledgeDocSummary[]
}

/** GET /api/v3/knowledge/doc/ — markdown 正文 */
export interface KnowledgeDoc {
  path: string
  title: string
  content: string
}

/** 独立剧本评审 */
export type ScriptReviewSourceType = 'paste' | 'upload'
export type ScriptReviewRunKind = 'quality' | 'compliance'
export type ScriptReviewRunStatus = 'queued' | 'running' | 'succeeded' | 'failed'

export interface ScriptReviewRun {
  id: string
  kind: ScriptReviewRunKind
  status: ScriptReviewRunStatus
  command_run_id: string | null
  report_payload: Record<string, unknown>
  error_message: string
  created_at: string | null
  finished_at: string | null
}

export interface ScriptReviewSummary {
  id: string
  title: string
  source_type: ScriptReviewSourceType
  source_filename: string
  project_id: string | null
  project_title: string | null
  script_preview?: string
  script_char_count?: number
  latest_quality_score: number | null
  latest_quality_grade: string | null
  latest_compliance_result: string | null
  created_at: string | null
  updated_at: string | null
}

export interface ScriptReviewDetail extends ScriptReviewSummary {
  script_text: string
  runs: ScriptReviewRun[]
}

export interface ScriptReviewList {
  items: ScriptReviewSummary[]
}

export interface ScriptReviewCompareSide {
  run_id: string
  created_at: string | null
  finished_at?: string | null
  summary: Record<string, unknown>
  dimensions: Array<{ key: string; score?: unknown; weight?: unknown }>
  top_defects: unknown[]
}

export interface ScriptReviewCompare {
  kind: ScriptReviewRunKind
  left: ScriptReviewCompareSide
  right: ScriptReviewCompareSide
  deltas: Record<string, number>
}
