import { http } from '@/services/http'
import type { KnowledgeDoc, KnowledgeList } from '@/types/v3/domain'

const KNOWLEDGE_BASE = '/api/v3/knowledge/'
const KNOWLEDGE_DOC_PATH = `${KNOWLEDGE_BASE}doc/`

export type ListKnowledgeParams = {
  q?: string
  section?: string
}

export async function listKnowledge(params?: ListKnowledgeParams): Promise<KnowledgeList> {
  const query: Record<string, string> = {}
  const q = params?.q?.trim()
  const section = params?.section?.trim()
  if (q) query.q = q
  if (section) query.section = section
  const options = Object.keys(query).length > 0 ? { params: query } : undefined
  return http.get<KnowledgeList>(KNOWLEDGE_BASE, options)
}

export async function getKnowledgeDoc(path: string): Promise<KnowledgeDoc> {
  return http.get<KnowledgeDoc>(KNOWLEDGE_DOC_PATH, { params: { path } })
}
