export type GenerationTroubleKind =
  | 'llm_disabled'
  | 'llm_misconfigured'
  | 'llm_auth'
  | 'llm_quota'
  | 'llm_timeout'
  | 'llm_network'
  | 'llm_openai_overseas'
  | 'llm_http'
  | 'schema_validation'
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
  opts?: { status?: string | null; context?: 'workbench' | 'external_review' },
): GenerationTrouble | null {
  const raw = (rawMessage ?? '').trim()
  if (!raw && opts?.status !== 'failed' && opts?.status !== 'disabled') return null

  const text = raw || '任务未成功完成'
  const lower = text.toLowerCase()
  const isExternal = opts?.context === 'external_review'
  const retryHint = isExternal
    ? '回到「外部评测」重新上传/粘贴后再次开始评测'
    : '刷新任务状态后，在工作台重新执行本阶段'

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
        isExternal
          ? '可用「探测」确认连通后，重新发起外部评测'
          : '可用「探测」确认连通后，回到工作台重新执行本阶段',
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
        isExternal ? '保存后重新发起外部评测' : '保存后回到工作台重试执行',
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

  if (/timeout|timed?\s*out|read timed out|connect timed out|等待任务进度超时/i.test(lower)) {
    return {
      kind: 'llm_timeout',
      title: '模型请求超时',
      summary: '生成时间过长或等待窗口不足（剧本蓝图等长 JSON 较常见）。',
      steps: [
        '重启后端/Celery 后再点「执行本阶段」重试（需加载最新超时与流式调用）',
        '在「模型管理」把 Max Tokens 调到 4096～8192，避免一次吐太长',
        '若环境变量仍写着旧值，将 LLM_READ_TIMEOUT 与 GENERATION_SSE_MAX_WAIT_SECONDS 提到 600+',
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

  if (/不是合法\s*json|jsondecodeerror|expecting property name|unexpected token|json\.loads/i.test(text)) {
    return {
      kind: 'schema_validation',
      title: '模型返回了无法解析的 JSON',
      summary:
        '大模型有回复，但内容不是合法 JSON（常见：尾逗号、单引号、字段名未加双引号）。产物未落库，所以侧栏仍显示「进行中」。',
      steps: [
        '直接再点一次「执行本阶段」（系统会做一次自动纠错重试）',
        '到「查看调用链」打开最近一次回复，确认是否被截断或夹杂说明文字',
        '若反复失败，可在「模型管理」换一个更稳的国内模型后再试',
      ],
      showModelHubLink: true,
      raw: text,
    }
  }

  if (/schema|校验失败|required property|不合规|未落库|is not of type/i.test(text)) {
    return {
      kind: 'schema_validation',
      title: '模型已返回，但产物结构不合规',
      summary: isExternal
        ? '模型调用其实已成功；只是当时结构校验失败没落库。可直接「用已有结果重新解析」，不必再跑一遍模型。'
        : '调用日志里的「成功」只表示大模型调用成功；落库前的 Schema 校验未通过，所以工作台没有产物。',
      steps: isExternal
        ? [
            '点击下方「用已有结果重新解析」落库（不重新调用模型）',
            '若提示缺少日志，再到「调用链」核对评分/合规两次成功回复',
            '仅当日志缺失或正文被截断时，才需要重新评测',
          ]
        : [
            '直接重试「执行本阶段」（系统会尽量自动补齐常见缺字段，如开场钩子 opening_hook）',
            '若仍失败，到「调用日志」查看模型原文，对照缺的字段（如 synopsis.short、opening_hook）',
            '确认当前模型稳定输出 JSON 后再执行',
          ],
      showModelHubLink: false,
      raw: text,
    }
  }

  if (/评分.?子任务失败|合规.?子任务失败|并行评审/i.test(text)) {
    return {
      kind: 'generic',
      title: '外部评测子任务失败',
      summary: text.length > 160 ? `${text.slice(0, 160)}…` : text,
      steps: isExternal
        ? [
            '若调用日志里评分/合规已成功，点击「用已有结果重新解析」即可落库',
            '到「调用链」确认两次调用是否都有成功回复',
            '仅当日志缺失时，才需要重新发起评测',
          ]
        : [
            '到「调用日志」按任务 ID 查看评分/合规两次调用的返回',
            '确认模型管理中当前模型可用后重试',
            retryHint,
          ],
      showModelHubLink: !isExternal,
      raw: text,
    }
  }

  return {
    kind: 'generic',
    title: opts?.status === 'disabled' ? '任务未执行' : '生成失败',
    summary: text.length > 120 ? `${text.slice(0, 120)}…` : text,
    steps: ['可先到「模型管理」确认当前模型可用', retryHint],
    showModelHubLink: /llm|model|api key|openai/i.test(text),
    raw: text,
  }
}

export function formatGenerationTroubleMessage(trouble: GenerationTrouble): string {
  const steps = trouble.steps.map((s, i) => `${i + 1}. ${s}`).join('\n')
  return `${trouble.title}\n${trouble.summary}\n${steps}`
}
