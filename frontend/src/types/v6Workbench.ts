import type { GenerationJob } from '@/types/domain'
import type { OperationInputField, V6Capability, V6Persona } from '@/types/workbench'

export type V6OperationStatus = 'blocked' | 'ready' | 'running' | 'failed' | 'stale' | 'complete'

export type V6WorkbenchOperation = {
  id: string
  label_zh: string
  group: string
  order: number
  intent: string
  dependencies: string[]
  invalidates: string[]
  result_view: string
  utility?: boolean
  quality_lane?: 'score' | 'compliance' | 'revision'
  declaration: {
    version: number
    user_inputs: string[]
    reads: string[]
    writes: string[]
    required_params?: string[]
    validation?: string[]
    constraints?: { readonly?: string[]; write_scope?: string; user_levels?: string[] }
    stages: string[]
  }
  persona: V6Persona
  capabilities: V6Capability[]
  input_fields: OperationInputField[]
  input_defaults: Record<string, unknown>
  state: {
    status: V6OperationStatus
    missing_dependencies: string[]
    stale_dependencies: string[]
    readiness_failures: Array<{ path: string; expected: unknown; actual: unknown }>
    output_versions: Record<string, number>
    latest_call: GenerationJob | null
  }
}

export type V6WorkbenchSnapshot = {
  schema_version: 'v6-workbench.v1'
  workbench_id: string
  workbench_version: number
  skills_version: string
  project: {
    id: string
    title: string
    settings_revision: number
    workbench_revision: number
    entry_ready: boolean
    entry_issues: string[]
  }
  groups: Array<{ id: string; label_zh: string; order: number }>
  operations: V6WorkbenchOperation[]
  artifacts: Record<string, { label_zh?: string; version: number; schema_version: number; created_at: string; stale: boolean }>
  quality_join: {
    status: 'waiting' | 'stale' | 'complete'
    lanes: string[]
    revision: string
    script_version: number | null
    quality_version: number | null
    compliance_version: number | null
  }
  transaction_view: { stages: string[]; terminal_statuses: string[] }
}
