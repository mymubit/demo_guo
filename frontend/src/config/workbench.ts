/**
 * Frontend-only UI constants. Business enums / stages / modules / field defaults
 * come from GET /api/v1/drama/meta/workbench-form/ at runtime — do not re-copy them here.
 */

/** PC workbench minimum width (dynamic layout 1280–2560). */
export const PC_MIN_WIDTH = 1280

/** Workflow user-decision button labels (UI mapping only; values come from workflow state). */
export const USER_DECISION_OPTIONS = [
  { value: 'accept_current' as const, label: '接受当前批次' },
  { value: 'manual_revision' as const, label: '手动修复' },
  { value: 'abandon_batch' as const, label: '放弃本批' },
]

/** Map parameter contract type (+ hints) → settings form widget. No business enums/defaults. */
export function resolveUiWidget(field: {
  type?: string
  ui_widget?: string
  enum?: string[]
  options?: unknown[]
  items_enum?: string[]
  enum_items?: string[]
  fields?: unknown
}): string {
  if (field.ui_widget) return field.ui_widget
  if (field.type === 'boolean') return 'switch'
  if (field.type === 'integer') return 'number'
  if (field.fields && typeof field.fields === 'object') return 'matrix'
  if (field.items_enum || field.enum_items) return 'checklist'
  if (field.type === 'array') return 'tags'
  if (field.enum?.length || (field.options && field.options.length > 0)) return 'select'
  if (field.type === 'object') return 'object'
  return 'text'
}
