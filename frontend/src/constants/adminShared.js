export const EMPTY_LLM_PROVIDER = {
  catalog_id: '',
  name: '',
  api_key: '',
  base_url: '',
  model_name: 'gpt-4o-mini',
  volcano_key_type: '',
  vendor: '',
  temperature: 0.7,
  max_tokens: 4096,
  context_window_input: '',
  context_window_output: '',
  tool_call_rounds: '',
  supports_multimodal: false,
  is_enabled: true,
  remark: '',
}

export const VOLCANO_PAYG_URL = 'https://ark.cn-beijing.volces.com/api/v3'
export const VOLCANO_CODING_URL = 'https://ark.cn-beijing.volces.com/api/coding/v3'

export function inferVolcanoKeyType(baseUrl) {
  const url = String(baseUrl || '')
  if (url.includes('/api/coding')) return 'coding_plan'
  if (url.includes('volces.com') || url.includes('volcengine')) return 'payg'
  return ''
}

export function volcanoBaseUrlForKeyType(keyType) {
  if (keyType === 'coding_plan') return VOLCANO_CODING_URL
  if (keyType === 'payg') return VOLCANO_PAYG_URL
  return ''
}
