import { http } from '@/services/http'
import type {
  CustomTemplate,
  CustomTemplateWrite,
  TemplateList,
} from '@/types/v3/domain'

const TEMPLATES_BASE = '/api/v3/templates/'
const CUSTOM_BASE = `${TEMPLATES_BASE}custom/`

export async function listTemplates(): Promise<TemplateList> {
  return http.get<TemplateList>(TEMPLATES_BASE)
}

export async function createCustomTemplate(body: CustomTemplateWrite): Promise<CustomTemplate> {
  return http.post<CustomTemplate>(CUSTOM_BASE, body)
}

export async function updateCustomTemplate(
  id: string,
  body: Partial<CustomTemplateWrite>,
): Promise<CustomTemplate> {
  return http.patch<CustomTemplate>(`${CUSTOM_BASE}${id}/`, body)
}

export async function deleteCustomTemplate(id: string): Promise<null> {
  return http.delete<null>(`${CUSTOM_BASE}${id}/`)
}
