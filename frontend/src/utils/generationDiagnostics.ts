export type GenerationTroubleKind =
  | 'llm_disabled'
  | 'llm_misconfigured'
  | 'llm_auth'
  | 'llm_quota'
  | 'llm_timeout'
  | 'llm_network'
  | 'llm_openai_overseas'
  | 'llm_http'
  | 'workflow_gate'
  | 'generic'

export type GenerationTrouble = {
  kind: GenerationTroubleKind
  title: string
  summary: string
  steps: string[]
  /** 建议跳转：模型管理 */
  showModelHubLink: boolean
  /** 原始错误（折叠展示） */
  raw?: string
}

/**
 * 将生成任务/LLM 原始错误翻译为可操作的中文排障说明。
 * 仅做前端文案映射，不改变后端契约。
 */
export function diagnoseGenerationFailure(
  rawMessage: string | null | undefined,
  opts?: { status?: string | null },
): GenerationTrouble | null {
  const raw = (rawMessage ?? '').trim()
  if (!raw && opts?.status !== 'failed' && opts?.status !== 'disabled') return null

  const text = raw || '任务未成功完成'
  const lower = text.toLowerCase()

  if (
    /llm\s*已禁用|llm_enabled\s*=?\s*false|llm\s*不可用\s*\(?\s*disabled/i.test(text) ||
    (opts?.status === 'disabled' && /llm/i.test(text))
  ) {
    return {
      kind: 'llm_disabled',
      title: '模型未启用',
      summary: '当前环境没有可用的大模型接入，生成任务已跳过。',
      steps: [
        '打开「模型管理」，选用国内厂商预设（DeepSeek / 通义 / 智谱等）',
        '填写有效 API Key，保存并设为「当前使用」',
        '可用「探测」确认连通后，回到工作台重新执行本阶段',
      ],
      showModelHubLink: true,
      raw: text,
    }
  }

  if (/配置不完整|misconfigured|缺少.?api.?key|未配置.?api.?key|base url.*api key|api key.*base url/i.test(text)) {
    return {
      kind: 'llm_misconfigured',
      title: '模型配置不完整',
      summary: '接口地址或 API Key 缺失，无法调用大模型。',
      steps: [
        '进入「模型管理」补全 Base URL 与 API Key',
        '确认配置已启用且标记为「当前」',
        '保存后回到工作台重试执行',
      ],
      showModelHubLink: true,
      raw: text,
    }
  }

  if (
    /http\s*401|unauthorized|invalid.?api.?key|incorrect.?api.?key|authentication/i.test(
      lower,
    )
  ) {
    return {
      kind: 'llm_auth',
      title: 'API Key 无效或未授权',
      summary: '模型服务拒绝了当前密钥，请检查 Key 是否正确、是否过期。',
      steps: [
        '在「模型管理」重新粘贴厂商控制台中的 API Key',
        '确认所选模型名与 Key 权限匹配',
        '探测连通成功后再执行阶段',
      ],
      showModelHubLink: true,
      raw: text,
    }
  }

  if (/http\s*403|permission|forbidden/i.test(lower) && /llm|model|openai|api/i.test(lower)) {
    return {
      kind: 'llm_auth',
      title: '模型接口无权限',
      summary: '当前 Key 无权调用该模型或接口。',
      steps: ['在厂商控制台开通对应模型权限', '或更换有权限的模型名后重试'],
      showModelHubLink: true,
      raw: text,
    }
  }

  if (/http\s*429|rate.?limit|quota|insufficient.?quota|余额|额度/i.test(lower)) {
    return {
      kind: 'llm_quota',
      title: '调用超限或额度不足',
      summary: '模型服务限流或账户额度不足。',
      steps: ['稍后再试，或检查厂商账户余额/套餐', '必要时更换其他国内模型配置'],
      showModelHubLink: true,
      raw: text,
    }
  }

  if (/timeout|timed?\s*out|read timed out|connect timed out/i.test(lower)) {
    return {
      kind: 'llm_timeout',
      title: '模型请求超时',
      summary: '连接或读取超时，常见于网络不稳或海外接口不可达。',
      steps: [
        '若当前指向 api.openai.com，请改用国内厂商接口',
        '检查本机/服务器出口网络后重试',
      ],
      showModelHubLink: true,
      raw: text,
    }
  }

  if (
    /openai\.com|api\.openai\.com/i.test(lower) ||
    (/connection|name or service not known|failed to establish|max retries|network/i.test(
      lower,
    ) &&
      /llm|openai|http/i.test(lower))
  ) {
    const isOverseas = /openai\.com/i.test(lower)
    return {
      kind: isOverseas ? 'llm_openai_overseas' : 'llm_network',
      title: isOverseas ? '海外 OpenAI 接口可能不可达' : '模型网络连接失败',
      summary: isOverseas
        ? '当前错误疑似访问 OpenAI 官方地址失败，国内环境通常需要改用国内模型。'
        : '无法连接到模型服务，请检查接口地址与网络。',
      steps: [
        '打开「模型管理」，清理演示/海外 OpenAI 配置',
        '选用 DeepSeek / 通义 / 智谱等国内预设并填写 Key',
        '设为当前使用后，回到工作台重新执行',
      ],
      showModelHubLink: true,
      raw: text,
    }
  }

  if (/llm\s*http\s*\d{3}/i.test(text) || /llm http/i.test(lower)) {
    return {
      kind: 'llm_http',
      title: '模型服务返回错误',
      summary: '大模型接口调用失败，请根据状态码与下方原文排查。',
      steps: [
        '到「模型管理」对当前配置执行「探测」',
        '确认模型名、Base URL 与 Key 正确后重试',
      ],
      showModelHubLink: true,
      raw: text,
    }
  }

  if (/门禁|gate|workflow/i.test(text)) {
    return {
      kind: 'workflow_gate',
      title: '流程门禁未通过',
      summary: '当前阶段尚不可执行，请先完成前置步骤。',
      steps: ['查看工作台流水线中已解锁的阶段', '按顺序执行，或先处理审批/质检决策'],
      showModelHubLink: false,
      raw: text,
    }
  }

  return {
    kind: 'generic',
    title: opts?.status === 'disabled' ? '任务未执行' : '生成失败',
    summary: text.length > 120 ? `${text.slice(0, 120)}…` : text,
    steps: [
      '可先到「模型管理」确认当前模型可用',
      '刷新任务状态后，在工作台重新执行本阶段',
    ],
    showModelHubLink: /llm|model|api key|openai/i.test(text),
    raw: text,
  }
}

export function formatGenerationTroubleMessage(trouble: GenerationTrouble): string {
  const steps = trouble.steps.map((s, i) => `${i + 1}. ${s}`).join('\n')
  return `${trouble.title}\n${trouble.summary}\n${steps}`
}
