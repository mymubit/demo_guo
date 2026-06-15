import {
  Search,
  LayoutList,
  Users,
  PenTool,
  FileText,
  ClipboardCheck,
  BarChart3,
} from 'lucide-react'

/** 仅 UI 图标映射；业务枚举一律从 GET /api/creation/fusion/catalog/ 加载 */
export const PIPELINE_NODE_ICONS = [
  Search,
  LayoutList,
  Users,
  PenTool,
  FileText,
  ClipboardCheck,
  BarChart3,
]

export function formatVariantLabel(catalog, key) {
  const item = (catalog?.formatVariants || []).find((f) => f.key === key)
  return item?.name || key
}

export function themeDisplayName(catalog, key) {
  const item = (catalog?.themes || []).find((t) => t.key === key)
  return item?.displayName || key
}
