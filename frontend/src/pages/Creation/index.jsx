import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Sparkles,
  Check,
  ArrowLeft,
  ArrowRight,
  Film,
  Users,
  BookOpen,
  Clock,
  FileText,
  Compass,
  Users as UsersIcon,
  LayoutList,
} from 'lucide-react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'
import { creation, billing, membership as membershipApi, useConfig } from '@/services/api'
import CreationEntryHub from '@/components/creation/CreationEntryHub'
import ProjectWorkspace from '@/components/creation/ProjectWorkspace'
import CreationFormShell from '@/components/creation/CreationFormShell'
import SkillPipelineShowcase from '@/components/creation/SkillPipelineShowcase'
import EntryFormHeader from '@/components/creation/EntryFormHeader'
import NovelAdaptationPanel from '@/components/creation/NovelAdaptationPanel'
import StoryBriefFields from '@/components/creation/StoryBriefFields'
import AudienceProfileField, { AudienceProfileSummary } from '@/components/creation/AudienceProfileField'
import FormatVariantPicker from '@/components/creation/FormatVariantPicker'
import { AiGenerateLockProvider } from '@/components/creation/AiGenerateLockContext'
import { normalizeAudienceProfile } from '@/utils/audienceProfile'
import { formatVariantLabel, themeDisplayName } from '@/config/fusion'
import { useFusionCatalog } from '@/hooks/useFusionCatalog'
import {
  resolveEntryProfile,
  validateEntryForm,
  buildSubmitPayload,
  getEntryPipelineHints,
  getEntryFormStepIndex,
  getRequiredFieldMinLength,
} from '@/utils/creationEntry'
import { getEntryMeta } from '@/utils/creationEntryMeta'
import { mergeThemeWithCatalog } from '@/constants/themeMeta'
import ThemeBadge from '@/components/ui/ThemeBadge'
import { Badge, Button, Card, Textarea } from '@/components/ui'
import { PageContainer } from '@/components/shared/ConsumerSection'
import { storyBriefContext } from '@/utils/storyBrief'
import { filterCreationPipelineNodes } from '@/utils/pipelineNodes'
import { cn } from '@/utils/cn'
import { ICON } from '@/constants/iconSizes'
import { renderLucideIcon } from '@/utils/renderLucideIcon'
import { pageEnter } from '@/constants/motion'
import { useSubmitGuard } from '@/hooks/useSubmitGuard'

const INITIAL_EPISODE_COUNT = 80
const creationDraftKey = (entry) => `creation:draft:${entry || 'from-scratch'}`

// ============ 主组件 ============
export default function Creation() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const {
    catalog,
    pipelineNodes,
    executionPlan,
    loading: catalogLoading,
    error: catalogError,
    selectedPipelineId,
  } = useFusionCatalog()
  const defaultEpisodeCount = useConfig('creation.default_episode_count', INITIAL_EPISODE_COUNT)
  const maxOutlineChars = useConfig('creation.max_outline_chars', 8000)
  const aiFieldFallbackCost = useConfig('creation.ai_field_fallback_cost', 10)
  const themes = (catalog.themes || [])
    .filter((t) => t.enabled !== false)
    .map((t) => mergeThemeWithCatalog(t))
  const [stage, setStage] = useState(0)
  const [projectId, setProjectId] = useState('')
  const [submitError, setSubmitError] = useState('')
  const { isSubmitting, runSubmit } = useSubmitGuard({
    minInterval: 1200,
    onError: () => {},
    shouldThrow: true,
  })
  const [formData, setFormData] = useState({
    theme: '',
    idea: '',
    coreConflict: '',
    emotionalTone: '',
    openingHooks: '',
    episodes: defaultEpisodeCount,
    format: 'B',
    targetPlatform: 'douyin',
    budgetLevel: 'medium',
    creationEntry: 'from-scratch',
    outline: '',
    novelText: '',
    referenceWork: '',
    ipSequelMode: 'sequel',
    ipKeepRules: '',
    audience: '',
    audienceProfile: { ageRange: '', preferences: [], note: '' },
  })
  const [pipelineMode] = useState('workspace')
  const [fieldActions, setFieldActions] = useState([])
  const [currencyName, setCurrencyName] = useState('创作币')
  const [billingCatalog, setBillingCatalog] = useState(null)
  const [billingError, setBillingError] = useState('')
  const [billingLoaded, setBillingLoaded] = useState(false)
  const [membershipActive, setMembershipActive] = useState(false)
  const [membershipLoaded, setMembershipLoaded] = useState(false)
  const [membershipError, setMembershipError] = useState('')

  useEffect(() => {
    if (selectedPipelineId) {
      setFormData((prev) => ({ ...prev, pipelinePackId: selectedPipelineId }))
    }
  }, [selectedPipelineId])

  useEffect(() => {
    billing.catalog().then((data) => {
      setBillingCatalog(data)
      setFieldActions(data?.field_actions || [])
      setCurrencyName(data?.currency_name || '创作币')
      setBillingError('')
    }).catch((e) => {
      const msg = e.message || '计费配置加载失败'
      setBillingError(msg)
      toast.error(msg)
    }).finally(() => {
      setBillingLoaded(true)
    })
    membershipApi.summary().then((data) => {
      setMembershipActive(!!data?.is_active)
      setMembershipError('')
    }).catch((e) => {
      const msg = e.message || '会员状态加载失败'
      setMembershipError(msg)
      toast.error(msg)
    }).finally(() => {
      setMembershipLoaded(true)
    })
  }, [])

  useEffect(() => {
    const pid = searchParams.get('project')
    if (pid) {
      setProjectId(pid)
      setStage(3)
      return
    }
    const entryFromUrl = searchParams.get('entry')
    if (!entryFromUrl || catalogLoading) return
    const valid = (catalog.creationEntries || []).some((e) => e.key === entryFromUrl)
    if (valid) {
      setFormData((prev) => ({ ...prev, creationEntry: entryFromUrl }))
      setStage(1)
    }
  }, [searchParams, catalog.creationEntries, catalogLoading])

  function selectCreationEntry(entryKey) {
    setFormData((prev) => ({ ...prev, creationEntry: entryKey }))
    setSearchParams({ entry: entryKey }, { replace: true })
    setStage(1)
  }

  function backToHub() {
    setSearchParams({}, { replace: true })
    setStage(0)
  }

  const entryMeta = getEntryMeta(
    formData.creationEntry,
    (catalog.creationEntries || []).find((e) => e.key === formData.creationEntry),
    catalog
  )

  useEffect(() => {
    setFormData((prev) =>
      prev.episodes === INITIAL_EPISODE_COUNT && defaultEpisodeCount !== INITIAL_EPISODE_COUNT
        ? { ...prev, episodes: defaultEpisodeCount }
        : prev
    )
  }, [defaultEpisodeCount])

  useEffect(() => {
    if (stage === 3) return
    const draft = sessionStorage.getItem(creationDraftKey(formData.creationEntry))
    if (!draft) return
    try {
      const parsed = JSON.parse(draft)
      setFormData((prev) => ({ ...prev, ...parsed, creationEntry: prev.creationEntry }))
    } catch {
      sessionStorage.removeItem(creationDraftKey(formData.creationEntry))
    }
  }, [formData.creationEntry, stage])

  useEffect(() => {
    if (stage < 1 || stage > 2) return
    sessionStorage.setItem(creationDraftKey(formData.creationEntry), JSON.stringify(formData))
  }, [formData, stage])

  const actionCost = (key, fallback = aiFieldFallbackCost) =>
    fieldActions.find((a) => a.action_key === key)?.coin_cost ?? fallback

  const actionRequiresMember = (key) =>
    !!fieldActions.find((a) => a.action_key === key)?.member_only

  const aiContext = () => storyBriefContext(formData)

  const goToBrief = () => {
    setSubmitError('')
    setStage(2)
  }

  const handleConfirmStart = async () => {
    setSubmitError('')
    try {
      await runSubmit(async () => {
        const entryProfile = resolveEntryProfile(catalog, formData.creationEntry)
        const res = await creation.submit(buildSubmitPayload(formData, pipelineMode, entryProfile))
        const tid = res.project_id
        setProjectId(tid)
        sessionStorage.removeItem(creationDraftKey(formData.creationEntry))
        setSearchParams({ project: tid }, { replace: true })
        setStage(3)
        // 【运营 F1】埋点：创作提交成功（前端双保险，后端也会写）
        try {
          const { trackCreationSubmitted } = await import('@/utils/behaviorTracker')
          trackCreationSubmitted({
            projectId: tid,
            theme: formData?.theme,
            episodeCount: formData?.episodeCount,
            pipelineMode,
          })
        } catch (_) {
          /* ignore */
        }
      })
    } catch (e) {
      const msg = e.message || '提交失败，请检查登录与会员状态'
      setSubmitError(msg)
      toast.error(msg)
      if (msg.includes('会员') || msg.includes('次数')) {
        toast('请先开通会员或购买创作次数', { action: { label: '去会员中心', onClick: () => navigate('/member') } })
      }
    }
  }

  const getThemeName = (key) => themeDisplayName(catalog, key) || '未选择'
  const getFormatName = (key) => formatVariantLabel(catalog, key)

  const visiblePipelineNodes = filterCreationPipelineNodes(pipelineNodes)

  if (stage === 1 || stage === 2) {
    return (
      <div className="relative min-h-screen bg-navy-950">
        <CreationFormShell
          main={
            <>
              {(billingError || membershipError) && (
                <Card variant="flat" padding="sm" className="mb-6 border-amber-500/30 bg-amber-500/10 text-sm text-amber-200">
                  {billingError || membershipError}。计费或会员状态可能暂不可用，请刷新后重试。
                </Card>
              )}
              <StageIndicator stage={stage} />
              <AnimatePresence mode="wait">
                {stage === 1 && (
                  <StageInputForm
                    key="stage1"
                    formData={formData}
                    setFormData={setFormData}
                    catalog={catalog}
                    themes={themes}
                    pipelineNodes={pipelineNodes}
                    entryMeta={entryMeta}
                    onSubmit={goToBrief}
                    onBackToHub={backToHub}
                    fieldActions={fieldActions}
                    currencyName={currencyName}
                    actionCost={actionCost}
                    actionRequiresMember={actionRequiresMember}
                    membershipActive={membershipActive}
                    membershipLoaded={membershipLoaded}
                    aiContext={aiContext}
                    defaultEpisodeCount={defaultEpisodeCount}
                    maxOutlineChars={maxOutlineChars}
                  />
                )}
                {stage === 2 && (
                  <StageBrief
                    key="stage2"
                    formData={formData}
                    themes={themes}
                    entryMeta={entryMeta}
                    catalog={catalog}
                    getThemeName={getThemeName}
                    getFormatName={getFormatName}
                    submitError={submitError}
                    isSubmitting={isSubmitting}
                    billingCatalog={billingCatalog}
                    billingLoaded={billingLoaded}
                    billingError={billingError}
                    pipelineNodes={visiblePipelineNodes}
                    executionPlan={executionPlan}
                    currencyName={currencyName}
                    onBack={() => setStage(1)}
                    onConfirm={handleConfirmStart}
                  />
                )}
              </AnimatePresence>
            </>
          }
        />
      </div>
    )
  }

  return (
    <div className={cn('relative min-h-screen bg-navy-950', stage === 3 ? 'py-5 md:py-6' : 'py-10 md:py-12')}>
      <PageContainer
        width={stage === 3 ? 'full' : '5xl'}
        className={cn(stage === 3 && 'px-3 sm:px-4 lg:px-6')}
      >
        <motion.div {...pageEnter} className={cn('text-center', stage === 3 ? 'mb-4' : 'mb-12')}>
          <Badge tone="gold" size="md" className="mb-4">
            <Sparkles className={ICON.md} />
            {stage === 0 ? 'Agent 驱动 · AI 创作引擎' : `${entryMeta.tag} · Agent 工作台`}
          </Badge>
          <h1 className={cn('font-bold tracking-tight text-white', stage === 3 ? 'text-2xl md:text-3xl mb-3' : 'text-4xl md:text-5xl mb-4')}>
            {stage === 0 ? (
              <>5 个创作 Agent · 从<span className="gradient-text">创意到专业级剧本</span></>
            ) : (
              <>
                {entryMeta.name}
                <span className="block text-2xl md:text-3xl mt-2 font-semibold text-navy-200">Agent 工作台</span>
              </>
            )}
          </h1>
          <p className={stage === 3 ? 'text-sm text-navy-400' : 'text-lg text-navy-200'}>
            {stage === 0
              ? '先选创作方式，再填写该方式专属信息；确认后进入 Agent 工作台'
              : '五个创作 Agent 独立生成，随时切换查看与下载'}
          </p>
        </motion.div>

        {catalogError && (
          <Card variant="flat" padding="sm" className="mb-6 border-danger-500/30 bg-danger-500/10 text-sm text-danger-300">
            {/限流|429|过于频繁/.test(catalogError) ? (
              <>请求过于频繁：{catalogError}。请等待片刻后点击刷新，或关闭其他正在轮询的页面标签。</>
            ) : (
              <>Agent 目录加载失败：{catalogError}。请刷新或联系管理员检查 FUSION_SKILL_ROOT。</>
            )}
          </Card>
        )}
        {catalogLoading && !catalogError && (
          <div className="mb-6 text-center text-navy-400 text-sm">加载 Agent 配置…</div>
        )}

        <AnimatePresence mode="wait">
          {stage === 0 && !catalogLoading && (
            <CreationEntryHub
              key="hub"
              catalog={catalog}
              onSelectEntry={selectCreationEntry}
            />
          )}

          {stage === 3 && projectId && (
            <ProjectWorkspace
              key="workspace"
              projectId={projectId}
              currencyName={currencyName}
              onBack={() => navigate('/works')}
              onRestart={() => {
                setSearchParams({}, { replace: true })
                backToHub()
                setProjectId('')
              }}
            />
          )}
        </AnimatePresence>
      </PageContainer>
    </div>
  )
}

// ============ 阶段指示器 ============
function StageIndicator({ stage }) {
  const stages = [
    { id: 1, label: '创意输入' },
    { id: 2, label: '项目确认' },
    { id: 3, label: 'Agent 工作台' },
  ]
  return (
    <Card className="mb-6" padding="md">
      <div className="flex items-center justify-between">
        {stages.map((s, idx) => {
          const active = stage === s.id
          const passed = stage > s.id
          return (
            <div key={s.id} className="flex items-center flex-1 last:flex-none">
              <div className="flex flex-col items-center">
                <motion.div
                  animate={{ scale: active ? 1.1 : 1 }}
                  className={cn(
                    'w-10 h-10 rounded-full flex items-center justify-center font-bold text-sm transition-all',
                    passed && 'bg-gradient-to-br from-gold-400 to-gold-600 text-navy-950',
                    active && 'bg-gradient-to-br from-gold-400 to-gold-600 text-navy-950 node-active',
                    !active && !passed && 'bg-white/[0.05] text-navy-300 border border-white/10',
                  )}
                >
                  {passed ? <Check className={ICON.lg} /> : s.id}
                </motion.div>
                <div className={cn('text-xs mt-2', active ? 'text-gold-400 font-semibold' : passed ? 'text-white' : 'text-navy-400')}>
                  {s.label}
                </div>
              </div>
              {idx < stages.length - 1 && (
                <div className="flex-1 mx-2 h-0.5 relative overflow-hidden bg-white/10">
                  <motion.div
                    initial={{ width: '0%' }}
                    animate={{ width: passed ? '100%' : active ? '50%' : '0%' }}
                    transition={{ duration: 0.5 }}
                    className="absolute inset-y-0 left-0 bg-gradient-to-r from-gold-400 to-gold-600"
                  />
                </div>
              )}
            </div>
          )
        })}
      </div>
    </Card>
  )
}

// ============ 阶段1：创意输入表单 ============
function OptionTile({ active, title, description, onClick, className = '' }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'rounded-2xl text-left transition-all border p-4 sf-focus-ring',
        active
          ? 'border-gold-400/50 bg-gold-400/10 ring-1 ring-gold-400/40'
          : 'border-white/10 bg-white/[0.03] hover:bg-white/[0.06]',
        className,
      )}
    >
      <div className={cn('text-sm font-semibold', active ? 'text-gold-300' : 'text-white')}>{title}</div>
      {description ? <p className="text-xs text-navy-400 mt-1.5 leading-relaxed">{description}</p> : null}
    </button>
  )
}

function StageInputForm({
  formData,
  setFormData,
  catalog,
  themes,
  pipelineNodes,
  entryMeta,
  onSubmit,
  onBackToHub,
  actionCost,
  actionRequiresMember,
  membershipActive,
  membershipLoaded = true,
  aiContext,
  currencyName,
  defaultEpisodeCount = 80,
  maxOutlineChars = 8000,
}) {
  const entryProfile = resolveEntryProfile(catalog, formData.creationEntry)
  const show = entryProfile.show || {}
  const entrySteps = entryMeta?.steps || []
  const formStepIndex = getEntryFormStepIndex(formData, entryProfile, entrySteps.length)
  const validation = validateEntryForm(formData, entryProfile)
  const canSubmit = validation.ok
  const sections = catalog.sections || {}
  const epCfg = catalog.episodeSettings || {}
  const epMin = epCfg.min ?? 20
  const epMax = epCfg.max ?? 200
  const epStep = epCfg.step ?? 10
  const epPresets = epCfg.presets?.length ? epCfg.presets : [20, 40, 60, 80, 100, 120, 150, 200]
  const epDuration = epCfg.durationMinutes ?? 2
  const totalMinutes = formData.episodes * epDuration
  const EntryIcon = entryMeta?.icon || Compass
  const isNovelEntry = Boolean(show.novel)
  const novelMinLength = getRequiredFieldMinLength(entryProfile, 'novel_text', 200)
  const novelReady = !isNovelEntry || (formData.novelText || '').trim().length >= novelMinLength
  const storyFormReady =
    (show.theme === false || Boolean(formData.theme)) && novelReady
  const budgetLevels = catalog.budgetLevels || []
  const fieldMeta = (block, fallbackTitle, fallbackSubtitle) => ({
    title: block?.title || fallbackTitle,
    subtitle: block?.subtitle || fallbackSubtitle,
    placeholder: block?.placeholder || '',
  })

  const update = (key, value) => setFormData((prev) => ({ ...prev, [key]: value }))
  const ctx = () => (typeof aiContext === 'function' ? aiContext() : {})
  const sectionMeta = (key, fallbackTitle, fallbackSubtitle) => ({
    title: sections[key]?.title || fallbackTitle,
    subtitle: sections[key]?.subtitle || fallbackSubtitle,
  })

  useEffect(() => {
    const def = catalog.episodeSettings?.default
    const nextDefault = typeof def === 'number' ? def : defaultEpisodeCount
    setFormData((prev) =>
      prev.episodes === 80 && nextDefault !== 80 ? { ...prev, episodes: nextDefault } : prev
    )
  }, [catalog.episodeSettings?.default, defaultEpisodeCount, setFormData])

  return (
    <AiGenerateLockProvider>
    <motion.div
      initial={{ opacity: 0, x: 30 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -30 }}
      transition={{ duration: 0.4 }}
      className="space-y-6"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Button
          variant="ghost"
          size="sm"
          iconLeft={<ArrowLeft className={ICON.md} />}
          onClick={onBackToHub}
          className="border-transparent bg-transparent px-0 text-navy-300 hover:bg-transparent hover:text-gold-400"
        >
          切换创作方式
        </Button>
        <div className="flex items-center gap-2 text-sm text-navy-400">
          <EntryIcon className={`${ICON.md} text-gold-400`} />
          <span className="text-white font-medium">{entryMeta?.name}</span>
        </div>
      </div>

      <EntryFormHeader entryMeta={entryMeta} currentStepIndex={formStepIndex} />

      {show.novel && (
        <NovelAdaptationPanel
          novelText={formData.novelText}
          onChange={(text) => update('novelText', text)}
          minLength={novelMinLength}
        />
      )}

      {isNovelEntry && novelReady && (
        <p className="text-xs text-navy-400 -mt-4 px-1">
          小说已就绪，请继续选择改编参数（题材、集数、格式等）
        </p>
      )}

      {show.outline && (
      <SectionCard
        title={fieldMeta(entryProfile.outline, '分集大纲', '粘贴已有大纲').title}
        subtitle={fieldMeta(entryProfile.outline, '', '').subtitle}
        icon={LayoutList}
      >
        <Textarea
          value={formData.outline}
          onChange={(e) => update('outline', e.target.value.slice(0, maxOutlineChars))}
          placeholder={fieldMeta(entryProfile.outline, '', '第1集：…\n第2集：…').placeholder}
          rows={8}
          textareaClassName="min-h-48 rounded-2xl p-5"
        />
        <p className="text-xs text-navy-400 mt-2">{formData.outline.length} / {maxOutlineChars} 字</p>
      </SectionCard>
      )}

      {show.ipSequel && (
      <SectionCard title="IP 续作设置" subtitle="声明须保持的 IP 约束" icon={UsersIcon}>
        <div className="flex flex-wrap gap-2 mb-4">
          {[
            { key: 'sequel', label: '续作' },
            { key: 'prequel', label: '前传' },
            { key: 'spin-off', label: '衍生' },
          ].map((m) => (
            <button
              key={m.key}
              type="button"
              onClick={() => update('ipSequelMode', m.key)}
              className={`px-4 py-2 rounded-xl text-sm transition-colors sf-focus-ring ${
                formData.ipSequelMode === m.key
                  ? 'bg-gold-400/20 text-gold-400 ring-1 ring-gold-400/50'
                  : 'bg-white/[0.03] text-navy-300'
              }`}
            >
              {m.label}
            </button>
          ))}
        </div>
        <Textarea
          value={formData.ipKeepRules}
          onChange={(e) => update('ipKeepRules', e.target.value.slice(0, 2000))}
          placeholder={fieldMeta(entryProfile.ipSequel, '', '须保持的角色名、世界观规则…').placeholder}
          rows={5}
          textareaClassName="min-h-32 rounded-2xl"
        />
      </SectionCard>
      )}

      {/* 题材选择 — 网文改编需先上传小说再配置 */}
      {show.theme !== false && novelReady && (
      <SectionCard
        title={sectionMeta('theme', '选择题材', '选择最契合你创意的热门题材（单选）').title}
        subtitle={sectionMeta('theme', '选择题材', '选择最契合你创意的热门题材（单选）').subtitle}
        icon={Film}
      >
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {(themes || []).map((theme) => {
            const active = formData.theme === theme.key
            return (
              <motion.button
                key={theme.key}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => update('theme', theme.key)}
                className={`p-4 rounded-2xl text-left transition-all relative overflow-hidden ${
                  active
                    ? 'ring-2 ring-gold-400 bg-gold-400/10 shadow-gold'
                    : 'border border-white/10 bg-white/[0.02] hover:border-white/20 hover:bg-white/[0.04]'
                }`}
                style={active ? { borderColor: theme.color + '60' } : {}}
              >
                <ThemeBadge theme={theme} size="lg" showName active={active} className="!bg-transparent !p-0" />
                {active && (
                  <motion.div
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="absolute top-2 right-2 w-6 h-6 rounded-full flex items-center justify-center"
                    style={{ background: theme.color }}
                  >
                    <Check className="w-3.5 h-3.5 text-white" />
                  </motion.div>
                )}
              </motion.button>
            )
          })}
        </div>
      </SectionCard>
      )}

      {storyFormReady && (show.coreIdea || show.audience) && (
        <div className="flex items-center gap-3 px-1">
          <div className="h-px flex-1 bg-slate-700/50" />
          <span className="text-sm font-medium text-gold-300">故事策划</span>
          <div className="h-px flex-1 bg-slate-700/50" />
        </div>
      )}

      {!storyFormReady && show.coreIdea && (
        <div className="rounded-xl border border-dashed border-white/10 px-4 py-3 text-sm text-navy-400 text-center">
          {isNovelEntry && !novelReady
            ? '请先上传小说正文，再选择题材与填写故事策划'
            : '请先选择题材，再填写故事策划'}
        </div>
      )}

      {storyFormReady && show.audience && (
        <SectionCard title="目标受众" subtitle="可选：标签 + 画像描述" icon={Users}>
          <AudienceProfileField
            profile={normalizeAudienceProfile(formData.audienceProfile, formData.audience)}
            onChange={(audienceProfile, audience) =>
              setFormData((prev) => ({ ...prev, audienceProfile, audience }))
            }
            currencyName={currencyName}
            actionCost={actionCost}
            actionRequiresMember={actionRequiresMember}
            membershipActive={membershipLoaded && membershipActive}
            aiContext={ctx}
            disabled={!membershipLoaded}
          />
        </SectionCard>
      )}

      {show.coreIdea && storyFormReady && (
      <SectionCard
        title={fieldMeta(entryProfile.coreIdea, '故事策划', '根据上方题材与项目参数生成').title}
        subtitle={fieldMeta(entryProfile.coreIdea, '故事策划', '一句话梗概 + 核心冲突 + 情绪基调 + 前三集钩子').subtitle}
        icon={Sparkles}
      >
        <StoryBriefFields
          formData={formData}
          onChange={(key, value) => {
            if (key === 'batch') {
              setFormData((prev) => ({ ...prev, ...value }))
            } else {
              update(key, value)
            }
          }}
          currencyName={currencyName}
          actionCost={actionCost}
          actionRequiresMember={actionRequiresMember}
          membershipActive={membershipLoaded && membershipActive}
          aiContext={ctx}
          disabled={!membershipLoaded}
        />
      </SectionCard>
      )}

      {show.referenceBlock && show.referenceBlock !== 'hidden' && storyFormReady && (
      <SectionCard
        title={fieldMeta(entryProfile.reference, '参考作品', '仅学习风格、节奏与类型经验，不复制剧情和台词').title}
        subtitle={fieldMeta(entryProfile.reference, '', '对标热门短剧的叙事节奏与情绪曲线，不复制剧情和台词').subtitle}
        icon={Film}
      >
        <Textarea
          value={formData.referenceWork}
          onChange={(e) => update('referenceWork', e.target.value.slice(0, 2000))}
          placeholder={fieldMeta(entryProfile.reference, '', '例：《某某短剧》的台词节奏 + 《某某剧》的反转密度…').placeholder}
          rows={5}
          textareaClassName="min-h-32 rounded-2xl"
        />
        <p className="text-xs text-navy-400 mt-2">
          {show.referenceBlock === 'required' ? '必填' : '可选'} · {formData.referenceWork.length} / 2000 字
        </p>
      </SectionCard>
      )}

      {show.projectParams !== false && novelReady && (
      <>
      {/* 项目参数 */}
      <div className="space-y-6">
        <div className="flex items-center gap-3 px-1">
          <div className="h-px flex-1 bg-slate-700/50" />
          <span className="text-sm font-medium text-navy-300">项目参数</span>
          <div className="h-px flex-1 bg-slate-700/50" />
        </div>

      <SectionCard
        title={sectionMeta('targetPlatform', '目标平台', '选择剧本主要投放的平台').title}
        subtitle={sectionMeta('targetPlatform', '目标平台', '选择剧本主要投放的平台，影响节奏与审查侧重').subtitle}
        icon={Compass}
      >
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {(catalog.platforms || []).map((p) => {
            const active = formData.targetPlatform === p.key
            return (
              <OptionTile
                key={p.key}
                active={active}
                title={p.name}
                description={p.description}
                onClick={() => update('targetPlatform', p.key)}
              />
            )
          })}
        </div>
      </SectionCard>

      {budgetLevels.length > 0 && (
        <SectionCard
          title={sectionMeta('budgetLevel', '预算档位', '选择本项目的制作预算倾向').title}
          subtitle={sectionMeta('budgetLevel', '预算档位', '用于影响场景规模、角色数量和制作复杂度').subtitle}
          icon={LayoutList}
        >
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {budgetLevels.map((item) => {
              const key = item.key || item.value || item.name
              return (
                <OptionTile
                  key={key}
                  active={formData.budgetLevel === key}
                  title={item.name || item.label || key}
                  description={item.description}
                  onClick={() => update('budgetLevel', key)}
                />
              )
            })}
          </div>
        </SectionCard>
      )}

      <SectionCard
        title={sectionMeta('episodes', '集数设置', '选择剧本总集数').title}
        subtitle={`${sectionMeta('episodes', '集数设置', '选择剧本总集数').subtitle}（每集约 ${epDuration} 分钟 · 全剧约 ${totalMinutes} 分钟）`}
        icon={Clock}
      >
        <div className="flex items-center gap-6">
          <div className="flex-1">
            <input
              type="range"
              min={epMin}
              max={epMax}
              step={epStep}
              value={formData.episodes}
              onChange={(e) => update('episodes', parseInt(e.target.value, 10))}
              className="w-full h-2 rounded-full bg-slate-700/50 appearance-none cursor-pointer accent-gold-400"
              style={{
                background: `linear-gradient(to right, #f6d365 0%, #fda085 ${
                  ((formData.episodes - epMin) / Math.max(epMax - epMin, 1)) * 100
                }%, rgba(30, 58, 138, 0.5) ${((formData.episodes - epMin) / Math.max(epMax - epMin, 1)) * 100}%, rgba(30, 58, 138, 0.5) 100%)`,
              }}
            />
            <div className="flex justify-between mt-2 text-xs text-navy-400">
              <span>{epMin}集</span>
              <span>{Math.round((epMin + epMax) / 2)}集</span>
              <span>{epMax}集</span>
            </div>
          </div>
          <motion.div
            key={formData.episodes}
            initial={{ scale: 0.9 }}
            animate={{ scale: 1 }}
            className="flex h-24 w-24 flex-col items-center justify-center rounded-2xl border border-gold-400/40 bg-gold-400/10 shadow-gold"
          >
            <span className="text-3xl font-bold gradient-text">{formData.episodes}</span>
            <span className="text-xs text-navy-300 mt-1">集</span>
          </motion.div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {epPresets.map((n) => (
            <button
              key={n}
              type="button"
              onClick={() => update('episodes', n)}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all ${
                formData.episodes === n
                  ? 'bg-gold-400/20 text-gold-400 border border-gold-400/40'
                  : 'bg-white/[0.05] text-navy-300 hover:bg-white/[0.06] border border-transparent'
              }`}
            >
              {n}集
            </button>
          ))}
        </div>
      </SectionCard>

      <SectionCard
        title={sectionMeta('formatVariant', '格式变体', '选择剧本输出格式').title}
        subtitle={sectionMeta('formatVariant', '格式变体', '对比场景/台词/动作写法，选择最适合落地的格式').subtitle}
        icon={FileText}
      >
        <FormatVariantPicker
          variants={catalog.formatVariants || []}
          value={formData.format}
          onChange={(key) => update('format', key)}
        />
      </SectionCard>
      </div>
      </>
      )}

      {/* 提交按钮 */}
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }}>
        <Button
          onClick={onSubmit}
          disabled={!canSubmit}
          variant={canSubmit ? 'gold' : 'secondary'}
          size="lg"
          iconLeft={<Sparkles className={ICON.lg} />}
          iconRight={canSubmit ? <ArrowRight className={ICON.lg} /> : null}
          className="w-full rounded-2xl py-5 text-lg"
        >
          {canSubmit ? '生成项目简报，开始创作' : validation.message}
        </Button>
      </motion.div>
    </motion.div>
    </AiGenerateLockProvider>
  )
}

// ============ 阶段2：项目简报确认 ============
function StageBrief({
  formData,
  themes,
  entryMeta,
  catalog,
  getThemeName,
  getFormatName,
  onBack,
  onConfirm,
  submitError,
  isSubmitting,
  billingCatalog,
  billingLoaded = true,
  billingError = '',
  pipelineNodes: fusionPipelineNodes = [],
  executionPlan = null,
  currencyName = '创作币',
}) {
  const entryProfile = resolveEntryProfile(catalog, formData.creationEntry)
  const show = entryProfile.show || {}
  const pipelineHints = getEntryPipelineHints(formData.creationEntry, entryProfile)
  const autoCost = billingCatalog?.estimated_auto_cost ?? 0
  const submitCost = billingCatalog?.submit_cost ?? 0
  const pipelineNodes = fusionPipelineNodes.length
    ? fusionPipelineNodes
    : filterCreationPipelineNodes(billingCatalog?.pipeline_nodes || [])
  const theme = themes?.find((t) => t.key === formData.theme)
  const budgetLevel = (catalog.budgetLevels || []).find((item) => {
    const key = item.key || item.value || item.name
    return key === formData.budgetLevel
  })
  return (
    <motion.div
      initial={{ opacity: 0, x: 30 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -30 }}
      transition={{ duration: 0.4 }}
    >
      <Card variant="glass" padding="xl" className="rounded-3xl md:p-10">
        <div className="text-center mb-8">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', delay: 0.1 }}
            className="w-20 h-20 rounded-3xl mx-auto mb-4 flex items-center justify-center"
            style={{
              background: 'linear-gradient(135deg, rgba(246, 211, 101, 0.2) 0%, rgba(253, 160, 133, 0.2) 100%)',
              border: '1px solid rgba(244, 183, 25, 0.3)',
            }}
          >
            <FileText className="w-9 h-9 text-gold-400" />
          </motion.div>
          <h2 className="text-3xl font-bold mb-2">项目简报</h2>
          <p className="text-navy-300">
            {entryMeta?.name || '创作项目'} · {entryProfile.summary || '请确认以下创作参数'}
          </p>
        </div>

        <div className="space-y-4 mb-10">
          <BriefRow icon={Compass} label="创作方式">
            <span className="font-semibold text-white">{entryMeta?.name || formData.creationEntry}</span>
          </BriefRow>

          {show.novel && (formData.novelText || '').trim() && (
            <BriefRow icon={BookOpen} label="小说原文">
              <p className="text-navy-100 text-sm leading-relaxed line-clamp-4 whitespace-pre-wrap">
                {(formData.novelText || '').trim().slice(0, 400)}
                {(formData.novelText || '').length > 400 ? '…' : ''}
              </p>
              <p className="text-xs text-navy-400 mt-1">共 {(formData.novelText || '').length} 字</p>
            </BriefRow>
          )}

          {show.outline && (formData.outline || '').trim() && (
            <BriefRow icon={LayoutList} label="分集大纲">
              <p className="text-navy-100 text-sm leading-relaxed whitespace-pre-wrap line-clamp-6">
                {formData.outline}
              </p>
            </BriefRow>
          )}

          {show.ipSequel && (formData.ipKeepRules || '').trim() && (
            <BriefRow icon={UsersIcon} label="IP 约束">
              <p className="text-navy-100 text-sm">
                模式：{formData.ipSequelMode === 'prequel' ? '前传' : formData.ipSequelMode === 'spin-off' ? '衍生' : '续作'}
              </p>
              <p className="text-navy-100 text-sm leading-relaxed mt-2 whitespace-pre-wrap">{formData.ipKeepRules}</p>
            </BriefRow>
          )}

          {show.theme !== false && (
          <BriefRow icon={Film} label="选择题材">
            <div className="flex items-center gap-2">
              <span className="text-2xl">{theme?.emoji}</span>
              <span className="font-semibold text-white">{getThemeName(formData.theme)}</span>
            </div>
          </BriefRow>
          )}

          {(show.audience &&
            (formData.audienceProfile?.ageRange ||
            formData.audienceProfile?.preferences?.length ||
            formData.audienceProfile?.note ||
            formData.audience)) && (
            <BriefRow icon={Users} label="目标受众">
              <AudienceProfileSummary
                profile={formData.audienceProfile}
                fallbackText={formData.audience}
              />
            </BriefRow>
          )}

          {show.coreIdea && (formData.idea || formData.coreConflict || formData.emotionalTone || formData.openingHooks) && (
          <BriefRow icon={Sparkles} label="故事策划">
            <div className="rounded-2xl border border-white/5 bg-slate-900/40 p-5 space-y-3 text-sm">
              {formData.idea && (
                <div>
                  <div className="text-navy-400 text-xs mb-1">一句话梗概</div>
                  <p className="text-navy-100 leading-relaxed">{formData.idea}</p>
                </div>
              )}
              {formData.coreConflict && (
                <div>
                  <div className="text-navy-400 text-xs mb-1">核心冲突</div>
                  <p className="text-navy-100 leading-relaxed">{formData.coreConflict}</p>
                </div>
              )}
              {formData.emotionalTone && (
                <div>
                  <div className="text-navy-400 text-xs mb-1">情绪基调</div>
                  <p className="text-navy-100">{formData.emotionalTone}</p>
                </div>
              )}
              {formData.openingHooks && (
                <div>
                  <div className="text-navy-400 text-xs mb-1">前三集钩子</div>
                  <p className="text-navy-100 leading-relaxed whitespace-pre-wrap">{formData.openingHooks}</p>
                </div>
              )}
            </div>
          </BriefRow>
          )}

          <BriefRow icon={Clock} label="集数设置">
            <span className="text-2xl font-bold gradient-text">{formData.episodes}</span>
            <span className="text-navy-300 ml-1">集</span>
          </BriefRow>

          {budgetLevel && (
            <BriefRow icon={LayoutList} label="预算档位">
              <span className="font-semibold text-white">
                {budgetLevel.name || budgetLevel.label || formData.budgetLevel}
              </span>
            </BriefRow>
          )}

          <BriefRow icon={FileText} label="输出格式">
            <span className="font-semibold text-white">{getFormatName(formData.format)}</span>
          </BriefRow>

        </div>

        {pipelineNodes.length > 0 && (
          <div className="mb-8">
            <SkillPipelineShowcase
              nodes={filterCreationPipelineNodes(pipelineNodes)}
              currencyName={currencyName}
              compact
              prefilledSteps={pipelineHints.prefilledSteps}
              executionPlan={executionPlan}
            />
            {pipelineHints.caption ? (
              <p className="text-xs text-navy-400 mt-2 px-1">{pipelineHints.caption}</p>
            ) : null}
          </div>
        )}

        {/* 预估信息 */}
        <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-5 mb-8 space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="text-navy-300">预估扣费</span>
            <span className="text-gold-400 font-semibold">
              {autoCost ? `约 ${autoCost + submitCost} ${currencyName}` : `发起 ${submitCost} ${currencyName} + 各节点`}
            </span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <div className="flex items-center gap-2 text-navy-300">
              <Clock className={ICON.md} />
              <span>预计创作时间</span>
            </div>
            <span className="text-gold-400 font-semibold">约 3-5 分钟</span>
          </div>
          <div className="flex items-center justify-between text-sm">
            <span className="text-navy-300">当前余额</span>
            <span className="text-white font-semibold">
              {billingLoaded && !billingError ? `${billingCatalog?.balance ?? 0} ${currencyName}` : '加载失败'}
            </span>
          </div>
          {pipelineNodes.length > 0 && (
            <div className="pt-2 border-t border-white/5">
              <div className="text-xs text-navy-400 mb-2">主链节点币价（启用项）</div>
              <div className="flex flex-wrap gap-2">
                {pipelineNodes.map((node) => (
                  <span
                    key={node.step || node.index || node.name}
                    className="text-xs px-2 py-1 rounded-lg rounded-lg border border-white/10 bg-white/[0.03] text-navy-200"
                  >
                    {node.name} · {node.coinCost ?? node.coin_cost ?? '—'} {currencyName}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        {submitError && (
          <p className="text-red-400 text-sm text-center mb-4">{submitError}</p>
        )}
        {billingError && (
          <p className="text-amber-300 text-sm text-center mb-4">计费配置未加载成功，请刷新后再提交。</p>
        )}

        {/* 按钮 */}
        <div className="flex flex-col md:flex-row gap-3">
          <Button
            onClick={onBack}
            disabled={isSubmitting}
            variant="secondary"
            size="lg"
            iconLeft={<ArrowLeft className={ICON.md} />}
            className="flex-1 rounded-2xl py-4"
          >
            返回修改
          </Button>
          <Button
            onClick={onConfirm}
            disabled={isSubmitting || !billingLoaded || Boolean(billingError)}
            isLoading={isSubmitting}
            variant="gold"
            size="lg"
            iconLeft={<Sparkles className={ICON.lg} />}
            iconRight={!isSubmitting ? <ArrowRight className={ICON.md} /> : null}
            className="flex-1 rounded-2xl py-4"
          >
            {isSubmitting
              ? '提交中…'
              : `进入 Agent 工作台 · 发起 ${submitCost} ${currencyName}`}
          </Button>
        </div>
      </Card>
    </motion.div>
  )
}

function BriefRow({ icon, label, children }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.1 }}
      className="flex items-start gap-4 py-4 border-b border-white/5 last:border-0"
    >
      <div className="w-10 h-10 rounded-xl flex flex-shrink-0 items-center justify-center bg-white/[0.05]">
        {renderLucideIcon(icon, `${ICON.lg} text-gold-400`)}
      </div>
      <div className="flex-1">
        <div className="text-xs text-navy-400 mb-1.5 uppercase tracking-wider">{label}</div>
        <div className="text-white">{children}</div>
      </div>
    </motion.div>
  )
}

// ============ 通用：分区卡片 ============
function SectionCard({ title, subtitle, icon, children }) {
  return (
    <Card
      as={motion.div}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      variant="glass"
      padding="lg"
      className="rounded-3xl md:p-7"
    >
      <div className="flex items-start gap-3 mb-5">
        {icon ? (
          <div className="w-10 h-10 rounded-xl bg-gold-400/15 flex items-center justify-center flex-shrink-0">
            {renderLucideIcon(icon, `${ICON.lg} text-gold-400`)}
          </div>
        ) : null}
        <div>
          <h3 className="text-lg font-bold text-white">{title}</h3>
          {subtitle && <p className="text-sm text-navy-300 mt-1">{subtitle}</p>}
        </div>
      </div>
      {children}
    </Card>
  )
}
