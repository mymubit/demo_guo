/** 国内主流大模型预设（OpenAI 兼容），优先于海外厂商展示。 */

export type LlmVendorPreset = {
  id: string
  vendor: string
  vendorLabel: string
  name: string
  base_url: string
  model_name: string
  temperature: number
  max_tokens: number
  apiKeyHint: string
  apiKeyUrl: string
  remark?: string
}

/** 国内优先：DeepSeek → 通义 → 智谱 → 月之暗面 → 豆包/火山；OpenAI 放最后 */
export const LLM_VENDOR_PRESETS: LlmVendorPreset[] = [
  {
    id: 'deepseek-chat',
    vendor: 'deepseek',
    vendorLabel: 'DeepSeek',
    name: 'DeepSeek Chat',
    base_url: 'https://api.deepseek.com',
    model_name: 'deepseek-chat',
    temperature: 0.7,
    max_tokens: 8192,
    apiKeyHint: 'DeepSeek 开放平台 API Key',
    apiKeyUrl: 'https://platform.deepseek.com/api_keys',
    remark: '国内高性价比，OpenAI 兼容',
  },
  {
    id: 'deepseek-reasoner',
    vendor: 'deepseek',
    vendorLabel: 'DeepSeek',
    name: 'DeepSeek Reasoner',
    base_url: 'https://api.deepseek.com',
    model_name: 'deepseek-reasoner',
    temperature: 0.6,
    max_tokens: 8192,
    apiKeyHint: 'DeepSeek 开放平台 API Key',
    apiKeyUrl: 'https://platform.deepseek.com/api_keys',
  },
  {
    id: 'qwen-plus',
    vendor: 'qwen',
    vendorLabel: '通义千问',
    name: '通义千问 Plus',
    base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    model_name: 'qwen-plus',
    temperature: 0.7,
    max_tokens: 8192,
    apiKeyHint: '阿里云百炼 / DashScope API Key',
    apiKeyUrl: 'https://bailian.console.aliyun.com/',
    remark: 'DashScope OpenAI 兼容模式',
  },
  {
    id: 'qwen-max',
    vendor: 'qwen',
    vendorLabel: '通义千问',
    name: '通义千问 Max',
    base_url: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    model_name: 'qwen-max',
    temperature: 0.7,
    max_tokens: 8192,
    apiKeyHint: '阿里云百炼 / DashScope API Key',
    apiKeyUrl: 'https://bailian.console.aliyun.com/',
  },
  {
    id: 'glm-4-plus',
    vendor: 'zhipu',
    vendorLabel: '智谱 AI',
    name: '智谱 GLM-4-Plus',
    base_url: 'https://open.bigmodel.cn/api/paas/v4',
    model_name: 'glm-4-plus',
    temperature: 0.7,
    max_tokens: 8192,
    apiKeyHint: '智谱开放平台 API Key',
    apiKeyUrl: 'https://open.bigmodel.cn/usercenter/apikeys',
  },
  {
    id: 'glm-4-flash',
    vendor: 'zhipu',
    vendorLabel: '智谱 AI',
    name: '智谱 GLM-4-Flash',
    base_url: 'https://open.bigmodel.cn/api/paas/v4',
    model_name: 'glm-4-flash',
    temperature: 0.7,
    max_tokens: 8192,
    apiKeyHint: '智谱开放平台 API Key',
    apiKeyUrl: 'https://open.bigmodel.cn/usercenter/apikeys',
    remark: '高速低价',
  },
  {
    id: 'kimi-k2.5',
    vendor: 'moonshot',
    vendorLabel: '月之暗面',
    name: 'Kimi K2.5',
    base_url: 'https://api.moonshot.cn/v1',
    model_name: 'kimi-k2.5',
    temperature: 0.6,
    max_tokens: 8192,
    apiKeyHint: 'Moonshot 开放平台 API Key',
    apiKeyUrl: 'https://platform.moonshot.cn/console/api-keys',
  },
  {
    id: 'doubao-seed',
    vendor: 'volcengine',
    vendorLabel: '豆包 / 火山方舟',
    name: '豆包 Seed（火山）',
    base_url: 'https://ark.cn-beijing.volces.com/api/v3',
    model_name: 'doubao-seed-1-6-250615',
    temperature: 0.7,
    max_tokens: 8192,
    apiKeyHint: '火山方舟 API Key；按量付费可将模型改为 ep-xxx 接入点',
    apiKeyUrl: 'https://console.volcengine.com/ark/region:ark+cn-beijing/apiKey',
    remark: '推荐在控制台创建推理接入点后填入 ep-xxx',
  },
  {
    id: 'openai-gpt-4o-mini',
    vendor: 'openai',
    vendorLabel: 'OpenAI（海外）',
    name: 'GPT-4o mini',
    base_url: 'https://api.openai.com/v1',
    model_name: 'gpt-4o-mini',
    temperature: 0.7,
    max_tokens: 8192,
    apiKeyHint: 'OpenAI API Key',
    apiKeyUrl: 'https://platform.openai.com/api-keys',
    remark: '需要可访问 OpenAI 的网络环境',
  },
]

export const DEFAULT_LLM_FORM = {
  name: '',
  base_url: '',
  model_name: 'deepseek-chat',
  api_key: '',
  temperature: 0.7,
  max_tokens: 8192,
  is_enabled: true,
  is_active: false,
  remark: '',
}

export function groupPresetsByVendor(presets: LlmVendorPreset[] = LLM_VENDOR_PRESETS) {
  const map = new Map<string, { vendor: string; vendorLabel: string; items: LlmVendorPreset[] }>()
  for (const p of presets) {
    const cur = map.get(p.vendor)
    if (cur) cur.items.push(p)
    else map.set(p.vendor, { vendor: p.vendor, vendorLabel: p.vendorLabel, items: [p] })
  }
  return [...map.values()]
}
