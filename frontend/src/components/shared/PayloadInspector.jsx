import { useEffect, useMemo, useState } from 'react'

/** 各字段说明（排查时对照） */
export const LLM_TRACE_FIELD_META = {
  system_prompt: {
    key: 'system_prompt',
    shortLabel: 'System',
    title: 'LLM System Prompt',
    hint: '模型 system 角色：铁律、输出格式、子技能职责、手册摘要',
    debug: '规则写错/过严 → 看这里',
  },
  user_prompt: {
    key: 'user_prompt',
    shortLabel: 'User',
    title: 'LLM User Prompt',
    hint: '模型 user 消息：裁剪后的 upstream JSON + 本步任务描述',
    debug: '排查首选：模型实际看到的完整输入',
    recommended: true,
  },
  upstream: {
    key: 'upstream',
    shortLabel: 'Upstream',
    title: 'LLM Upstream 摘要',
    hint: '传入上下文的键名与规模摘要，非 artifact 全文',
    debug: '速览本步调用了哪些产物；全文在 User Prompt',
  },
  raw_content: {
    key: 'raw_content',
    shortLabel: '原始响应',
    title: 'LLM 原始响应',
    hint: 'API 返回的原始文本，解析前',
    debug: 'JSON 截断、markdown 包裹、空内容 → 看这里',
  },
  parsed: {
    key: 'parsed',
    shortLabel: '解析 JSON',
    title: 'LLM 解析结果 (JSON)',
    hint: '对原始响应 parse 后的结构化对象',
    debug: '字段缺失、类型不对、schema 不满足 → 看这里',
    recommended: true,
  },
  input_payload: {
    key: 'input_payload',
    shortLabel: '输入',
    title: '输入 upstream / payload',
    hint: '本 sub_skill 写入 DB 的入参摘要（与 Upstream 摘要同源）',
    debug: '与 User Prompt 对照，确认裁剪是否合理',
  },
  output_payload: {
    key: 'output_payload',
    shortLabel: '输出',
    title: '输出 payload',
    hint: '本步最终产出，会 merge 进 artifact 传给下游',
    debug: '这步生成了什么、下游能不能用 → 看这里',
  },
}

const TRACE_TAB_ORDER = [
  'user_prompt',
  'parsed',
  'system_prompt',
  'upstream',
  'raw_content',
  'input_payload',
  'output_payload',
]

export function formatPayloadText(data) {
  if (data == null) return { text: '', empty: true, truncated: false }
  const isEmpty = typeof data === 'object' && !Array.isArray(data) && Object.keys(data).length === 0
  if (isEmpty) return { text: '', empty: true, truncated: false }

  let text = ''
  if (typeof data === 'string') {
    text = data
  } else if (data?.text != null) {
    text = String(data.text)
  } else {
    try {
      text = JSON.stringify(data, null, 2)
    } catch {
      text = String(data)
    }
  }
  return {
    text: text.trim(),
    empty: !text.trim(),
    truncated: Boolean(data?.truncated),
    length: data?.length,
  }
}

function TraceTabBar({ tabs, active, onChange }) {
  if (!tabs.length) return null
  return (
    <div
      className="flex flex-wrap gap-1 rounded-lg border border-white/5 bg-black/20 p-1"
      role="tablist"
    >
      {tabs.map((tab) => {
        const isActive = active === tab.key
        return (
          <button
            key={tab.key}
            type="button"
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(tab.key)}
            title={tab.meta.title}
            className={`rounded-md px-2.5 py-1 text-[11px] font-medium transition-colors ${
              isActive
                ? 'bg-gold-500/20 text-gold-200 ring-1 ring-gold-500/30'
                : 'text-navy-400 hover:bg-white/[0.06] hover:text-navy-200'
            }`}
          >
            {tab.meta.shortLabel}
            {tab.meta.recommended ? (
              <span className="ml-0.5 text-[9px] text-gold-400/70">★</span>
            ) : null}
          </button>
        )
      })}
    </div>
  )
}

function TraceTabPanel({ meta, data }) {
  const formatted = formatPayloadText(data)
  if (formatted.empty) {
    return <p className="text-xs text-navy-500 py-4 text-center">此项无数据</p>
  }
  return (
    <div className="mt-2">
      <p className="text-[10px] text-navy-500 leading-relaxed mb-2">
        {meta.hint}
        {formatted.truncated ? (
          <span className="text-amber-400/80 ml-2">（已截断，原始长度 {formatted.length}）</span>
        ) : null}
      </p>
      {meta.debug ? (
        <p className="text-[10px] text-gold-400/70 mb-2">排查提示：{meta.debug}</p>
      ) : null}
      <pre className="max-h-[420px] overflow-auto whitespace-pre-wrap break-words rounded-lg border border-white/5 bg-black/30 p-3 text-[11px] leading-relaxed text-navy-100 font-mono">
        {formatted.text}
      </pre>
    </div>
  )
}

export function subSkillStepId(step) {
  return String(step?.skill_id || step?.id || '')
}

function SubSkillChooserNav({ steps, active, onChange }) {
  if (!steps?.length) return null
  return (
    <nav
      className="flex w-[11.5rem] shrink-0 flex-col gap-0.5 rounded-lg border border-gold-500/20 bg-black/25 p-1 max-h-[min(560px,70vh)] overflow-y-auto"
      role="tablist"
      aria-orientation="vertical"
      aria-label="子技能"
    >
      {steps.map((step) => {
        const id = subSkillStepId(step)
        const isActive = active === id
        const failed = step.status === 'failed'
        const isLlm = hasLlmIo(step)
        return (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(id)}
            title={`${id} · ${subSkillTypeLabel(step)} · ${step.status}`}
            className={`w-full text-left rounded-md px-2.5 py-2 transition-colors border-l-2 ${
              isActive
                ? isLlm
                  ? 'border-gold-400 bg-gold-500/20 text-gold-100'
                  : 'border-white/40 bg-white/10 text-white'
                : failed
                  ? 'border-transparent text-red-300/90 hover:bg-red-500/10'
                  : 'border-transparent text-navy-300 hover:bg-white/[0.06] hover:text-white'
            }`}
          >
            <span className="block text-[11px] font-medium leading-snug break-all">{id}</span>
            <span className="mt-0.5 block text-[9px] leading-tight text-navy-500">
              {subSkillTypeLabel(step)}
              {isLlm ? <span className="text-gold-400/80"> · LLM</span> : null}
              {failed ? <span className="text-red-400"> · 失败</span> : null}
            </span>
          </button>
        )
      })}
    </nav>
  )
}

function mergeTraceSteps(subSkills, executionTrace) {
  const fromDb = subSkills || []
  if (!executionTrace?.length) return fromDb
  const byId = new Map(fromDb.map((s) => [subSkillStepId(s), s]))
  return executionTrace.map((entry) => {
    const id = String(entry?.id || entry?.skill_id || '')
    if (!id) return null
    const db = byId.get(id)
    if (db) return db
    return {
      skill_id: id,
      id,
      status: entry.status,
      type: entry.type,
      skill_type: entry.type,
      message: entry.message,
      error_message: entry.message,
    }
  }).filter(Boolean)
}

function NonLlmStepDetail({ step }) {
  const msg = step.message || step.error_message
  const hasTabs = hasDebugPayload(step) && !hasLlmIo(step)
  return (
    <>
      <p className="text-[10px] text-navy-500 mb-2">
        {subSkillTypeLabel(step)} · {step.status}
        <span className="ml-2 text-navy-600">未调用大模型</span>
      </p>
      <p className="text-xs text-navy-400 leading-relaxed mb-2">
        此步骤为检索 / CLI 校验 / 规则占位等，无 System / User Prompt。若失败请看下方 message。
      </p>
      {msg ? <p className="text-xs text-red-300/90 mb-2">{msg}</p> : null}
      {hasTabs ? (
        <SubSkillTraceTabs step={step} defaultTab="input_payload" />
      ) : (
        <SummaryFallback step={step} />
      )}
    </>
  )
}

function SummaryFallback({ step }) {
  const inSum = step.input_summary
  const outSum = step.output_summary
  if (!inSum && !outSum) {
    return <p className="text-xs text-navy-500 py-2">暂无详细 I/O 记录</p>
  }
  return (
    <div className="space-y-2 text-[11px]">
      {inSum && Object.keys(inSum).length ? (
        <pre className="rounded border border-white/5 bg-black/30 p-2 text-navy-300 overflow-auto">
          {JSON.stringify(inSum, null, 2)}
        </pre>
      ) : null}
      {outSum && Object.keys(outSum).length ? (
        <pre className="rounded border border-white/5 bg-black/30 p-2 text-navy-300 overflow-auto">
          {JSON.stringify(outSum, null, 2)}
        </pre>
      ) : null}
    </div>
  )
}

/** 一次 run 内全部 sub_skill：外层 Tab 与上方步骤条对齐，内层 Tab 看 LLM I/O */
export function LlmRunTracePanel({ subSkills = [], executionTrace = null }) {
  const allSteps = useMemo(
    () => mergeTraceSteps(subSkills, executionTrace),
    [subSkills, executionTrace],
  )
  const llmCount = useMemo(() => allSteps.filter(hasLlmIo).length, [allSteps])

  const firstId = subSkillStepId(allSteps[0])
  const [activeSkillId, setActiveSkillId] = useState(firstId)

  useEffect(() => {
    if (!allSteps.length) return
    if (!allSteps.some((s) => subSkillStepId(s) === activeSkillId)) {
      setActiveSkillId(subSkillStepId(allSteps[0]))
    }
  }, [allSteps, activeSkillId])

  const activeStep = allSteps.find((s) => subSkillStepId(s) === activeSkillId) || allSteps[0]

  if (!allSteps.length) return null

  return (
    <div>
      <div className="mb-3">
        <p className="text-[10px] text-gold-400/80 uppercase tracking-wide">子技能轨迹（调试）</p>
        <p className="text-[10px] text-navy-500 mt-1">
          左侧选子技能（共 {allSteps.length} 步，{llmCount} 步调 LLM），右侧看详情；内层 Tab 查看
          Prompt / 响应，★ 为排查优先。
        </p>
      </div>

      <div className="flex gap-3 items-start">
        <SubSkillChooserNav
          steps={allSteps}
          active={subSkillStepId(activeStep)}
          onChange={setActiveSkillId}
        />

        {activeStep ? (
          <div
            className={`flex-1 min-w-0 rounded-lg border p-3 ${
              hasLlmIo(activeStep) ? 'border-gold-500/15 bg-black/20' : 'border-white/5 bg-black/15'
            }`}
            role="tabpanel"
          >
            {hasLlmIo(activeStep) ? (
              <>
                <p className="text-[10px] text-navy-500 mb-2">
                  {subSkillTypeLabel(activeStep)} · {activeStep.status}
                  <span className="ml-2 text-gold-400/80">含 LLM 调用</span>
                </p>
                <SubSkillTraceTabs
                  key={subSkillStepId(activeStep)}
                  step={activeStep}
                  defaultTab="user_prompt"
                />
              </>
            ) : (
              <NonLlmStepDetail key={subSkillStepId(activeStep)} step={activeStep} />
            )}
          </div>
        ) : null}
      </div>
    </div>
  )
}

/** 单 sub_skill 全量轨迹：Tab 切换（替代多层折叠） */
export function SubSkillTraceTabs({ step, defaultTab = 'user_prompt' }) {
  const llmIo = step?.llm_io || {}
  const req = llmIo.request || {}
  const res = llmIo.response || {}

  const dataByKey = useMemo(
    () => ({
      system_prompt: req.system_prompt,
      user_prompt: req.user_prompt,
      upstream: req.upstream,
      raw_content: res.raw_content,
      parsed: res.parsed,
      input_payload: step?.input_payload,
      output_payload: step?.output_payload,
    }),
    [req, res, step],
  )

  const tabs = useMemo(
    () =>
      TRACE_TAB_ORDER.map((key) => ({
        key,
        meta: LLM_TRACE_FIELD_META[key],
        data: dataByKey[key],
      })).filter((tab) => !formatPayloadText(tab.data).empty),
    [dataByKey],
  )

  const initialTab = tabs.some((t) => t.key === defaultTab)
    ? defaultTab
    : tabs.find((t) => t.meta.recommended)?.key || tabs[0]?.key || ''

  const [active, setActive] = useState(initialTab)

  const activeTab = tabs.find((t) => t.key === active) || tabs[0]

  if (!tabs.length) return null

  return (
    <div className="mt-2">
      <TraceTabBar tabs={tabs} active={activeTab?.key} onChange={setActive} />
      {activeTab ? (
        <div role="tabpanel">
          <TraceTabPanel meta={activeTab.meta} data={activeTab.data} />
        </div>
      ) : null}
      {res.error ? <p className="text-xs text-red-300/90 mt-2">错误：{res.error}</p> : null}
    </div>
  )
}

/** @deprecated 保留兼容；新 UI 请用 SubSkillTraceTabs */
export function PayloadInspector({
  title,
  data,
  defaultOpen = false,
  className = '',
  hint = '',
  debug = '',
}) {
  const formatted = formatPayloadText(data)
  if (formatted.empty) return null

  return (
    <details className={`mt-2 ${className}`} open={defaultOpen}>
      <summary className="text-xs text-gold-400/90 cursor-pointer hover:text-gold-300 select-none">
        <span>{title}</span>
        {hint ? <span className="text-navy-500 font-normal ml-1.5">— {hint}</span> : null}
        {formatted.truncated ? (
          <span className="text-amber-400/80 ml-2">（已截断，原始长度 {formatted.length}）</span>
        ) : null}
      </summary>
      {debug ? (
        <p className="mt-1 text-[10px] text-navy-500 leading-relaxed pl-0.5">排查提示：{debug}</p>
      ) : null}
      <pre className="mt-1 max-h-[420px] overflow-auto whitespace-pre-wrap break-words rounded-lg border border-white/5 bg-black/30 p-3 text-[11px] leading-relaxed text-navy-100 font-mono">
        {formatted.text}
      </pre>
    </details>
  )
}

/** @deprecated 保留兼容；新 UI 请用 SubSkillTraceTabs */
export function LlmIoInspector({ llmIo, defaultOpen = false }) {
  if (!llmIo || !Object.keys(llmIo).length) return null
  const req = llmIo.request || {}
  const res = llmIo.response || {}
  const hasRequest = req.system_prompt || req.user_prompt || req.upstream
  const hasResponse = res.raw_content || res.parsed || res.error
  if (!hasRequest && !hasResponse) return null

  const m = LLM_TRACE_FIELD_META
  return (
    <div className="space-y-1">
      <PayloadInspector
        title={m.system_prompt.title}
        hint={m.system_prompt.hint}
        debug={m.system_prompt.debug}
        data={req.system_prompt}
        defaultOpen={defaultOpen}
      />
      <PayloadInspector
        title={m.user_prompt.title}
        hint={m.user_prompt.hint}
        debug={m.user_prompt.debug}
        data={req.user_prompt}
        defaultOpen={defaultOpen}
      />
      <PayloadInspector
        title={m.upstream.title}
        hint={m.upstream.hint}
        debug={m.upstream.debug}
        data={req.upstream}
      />
      <PayloadInspector
        title={m.raw_content.title}
        hint={m.raw_content.hint}
        debug={m.raw_content.debug}
        data={res.raw_content}
      />
      <PayloadInspector
        title={m.parsed.title}
        hint={m.parsed.hint}
        debug={m.parsed.debug}
        data={res.parsed}
        defaultOpen={defaultOpen}
      />
      {res.error ? <p className="text-xs text-red-300/90 mt-1">错误：{res.error}</p> : null}
    </div>
  )
}

export function hasLlmIo(step) {
  const io = step?.llm_io
  if (!io || !Object.keys(io).length) return false
  const req = io.request || {}
  const res = io.response || {}
  return Boolean(req.system_prompt || req.user_prompt || req.upstream || res.raw_content || res.parsed || res.error)
}

export function hasDebugPayload(step) {
  if (hasLlmIo(step)) return true
  const inP = step?.input_payload
  const outP = step?.output_payload
  const inOk = inP && typeof inP === 'object' && Object.keys(inP).length > 0
  const outOk = outP && typeof outP === 'object' && Object.keys(outP).length > 0
  return inOk || outOk
}

const SUB_SKILL_TYPE_LABEL = {
  llm: '大模型',
  retrieval: '检索',
  cli: 'CLI 校验',
  script: '脚本',
}

export function subSkillTypeLabel(step) {
  const t = step?.type || step?.skill_type || ''
  return SUB_SKILL_TYPE_LABEL[t] || t || '步骤'
}
