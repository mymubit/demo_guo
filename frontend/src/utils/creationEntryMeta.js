import { BookOpen, Compass, FileText, Film, PenTool, Sparkles, Users } from 'lucide-react'
import { resolveEntryProfile } from './creationEntry'

export const ENTRY_ICON_MAP = {
  sparkles: Sparkles,
  bookOpen: BookOpen,
  fileText: FileText,
  film: Film,
  users: Users,
  penTool: PenTool,
}

function resolveIcon(iconKey, fallbackIcon) {
  if (iconKey && ENTRY_ICON_MAP[iconKey]) return ENTRY_ICON_MAP[iconKey]
  return fallbackIcon || PenTool
}

export function getEntryMeta(key, catalogEntry, catalog = null) {
  const profile = catalog ? resolveEntryProfile(catalog, key) : null
  const fallback = {
    iconKey: 'penTool',
    tag: '创作',
    headline: catalogEntry?.name || key,
    description: catalogEntry?.description || '按技能流水线生成剧本',
    steps: ['填写信息', '确认简报', '技能流水线'],
  }

  const iconKey = profile?.iconKey || fallback.iconKey
  const steps = Array.isArray(profile?.steps) && profile.steps.length ? profile.steps : fallback.steps

  return {
    key,
    icon: resolveIcon(iconKey, fallback.icon),
    tag: profile?.tag || fallback.tag,
    headline: profile?.headline || catalogEntry?.name || fallback.headline,
    name: catalogEntry?.name || profile?.headline || fallback.headline,
    description: profile?.description || profile?.summary || fallback.description,
    steps,
  }
}
