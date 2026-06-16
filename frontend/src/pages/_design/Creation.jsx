/**
 * Creation.jsx — 设计稿创作工作台
 *
 * 3 栏布局：左侧 7 节点侧栏 / 中间简报表单 / 右侧 Token 配额
 * 对应后端：creation/services/submission.py + billing/ai_field_prompt_service.py
 */
import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  ChevronRight,
  ChevronLeft,
  Lock,
  Cpu,
  Coins,
  Clock,
  Save,
  Sparkles,
} from 'lucide-react'
import { Button, Badge, Textarea, Select } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { cn } from '@/utils/cn'

// 主链节点 — 与后端 engine/node[1-7] 一致
const NODES = [
  { step: 1, name: '信息收集', meta: '✓' },
  { step: 2, name: '结构规划', meta: '✓' },
  { step: 3, name: '人设开发', meta: '✓' },
  { step: 4, name: '大纲撰写', meta: '运行中', active: true },
  { step: 5, name: '剧本创作', meta: '—' },
  { step: 6, name: '质量审查', meta: '—' },
  { step: 7, name: '输出交付', meta: '—' },
]

const FORMATS = [
  { k: 'A', n: '标准版' },
  { k: 'B', n: '行业通用版', active: true },
  { k: 'C', n: '精简版' },
  { k: 'D', n: '分镜版' },
]

// 8 题材 — 与后端 skill/config/portal/creation_form.py 一致
const THEMES = [
  { k: 'family_revenge', n: '家庭复仇' },
  { k: 'ceo_drama', n: '豪门霸总' },
  { k: 'sweet_abuse', n: '甜宠虐恋' },
  { k: 'rebirth', n: '穿越重生' },
  { k: 'urban_rising', n: '都市逆袭', active: true },
  { k: 'ancient_politics', n: '古装权谋' },
  { k: 'mystery', n: '悬疑反转' },
  { k: 'mixed', n: '混合题材' },
]

// Token 配额 — 对应后端 skill/llm/usage_log.py
const TOKEN_QUOTAS = [
  { name: '结构规划', pct: 62, cool: false },
  { name: '大纲撰写', pct: 38, cool: true },
  { name: '剧本创作', pct: 14, cool: false },
]

export default function Creation() {
  const [episodes, setEpisodes] = useState(80)

  return (
    <motion.div {...pageEnter} className="grid min-h-[calc(100svh-3.25rem)] grid-cols-1 lg:grid-cols-[320px_1fr_360px]">
      {/* ============ 左侧 — 节点 / 格式 侧栏 ============ */}
      <aside className="border-r border-white/5 bg-navy-950/60 p-5">
        <SideTitle>主链节点</SideTitle>
        <nav className="mt-2 space-y-0.5">
          {NODES.map((n) => (
            <button
              key={n.step}
              type="button"
              className={cn(
                'flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-sm transition-colors',
                n.active
                  ? 'bg-gold-400/10 text-white'
                  : 'text-navy-200 hover:bg-white/5 hover:text-white',
              )}
            >
              <span
                className={cn(
                  'grid h-5.5 w-5.5 place-items-center rounded-md border text-[11px]',
                  n.active
                    ? 'border-transparent bg-gradient-to-br from-gold-300 to-gold-500 text-navy-950'
                    : 'border-white/10 bg-white/5 text-navy-300',
                )}
                style={{ height: '22px', width: '22px' }}
              >
                {n.step}
              </span>
              {n.name}
              <span className="ml-auto text-[11px] text-navy-400">{n.meta}</span>
            </button>
          ))}
        </nav>

        <SideTitle>题材格式</SideTitle>
        <nav className="mt-2 space-y-0.5">
          {FORMATS.map((f) => (
            <button
              key={f.k}
              type="button"
              className={cn(
                'flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-sm transition-colors',
                f.active
                  ? 'bg-gold-400/10 text-white'
                  : 'text-navy-200 hover:bg-white/5 hover:text-white',
              )}
            >
              <span
                className={cn(
                  'grid h-5.5 w-5.5 place-items-center rounded-md text-[11px]',
                  f.active
                    ? 'bg-gradient-to-br from-gold-300 to-gold-500 text-navy-950'
                    : 'bg-white/5 text-navy-300',
                )}
                style={{ height: '22px', width: '22px' }}
              >
                {f.k}
              </span>
              {f.n}
            </button>
          ))}
        </nav>
      </aside>

      {/* ============ 中间 — 简报表单 ============ */}
      <main className="overflow-auto p-7 lg:p-9">
        <header className="mb-5 flex flex-wrap items-center justify-between gap-4">
          <div>
            <div className="text-sm text-navy-300">
              创作 / <b className="text-white">《逆光》</b> / 信息收集
            </div>
            <h1 className="mt-1 text-2xl font-bold">把一句话创意，变成可被拍摄的故事</h1>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" size="md" iconLeft={<Save className={ICON.md} />}>
              保存草稿
            </Button>
            <Button variant="gold" size="md" iconRight={<ChevronRight className={ICON.md} />}>
              确认项目简报
            </Button>
          </div>
        </header>

        <section className="rounded-2xl border border-white/5 bg-gradient-to-br from-navy-900/65 to-navy-950/65 p-6">
          <h2 className="m-0 text-base font-semibold">基本信息</h2>
          <p className="mt-1 mb-5 text-[13px] text-navy-300">
            题材、集数、节奏与一句话创意，决定后续 6 个节点的方向。
          </p>

          {/* 题材 */}
          <label className="mb-3 block text-xs text-navy-300">题材</label>
          <div className="mb-5 grid grid-cols-2 gap-2.5 sm:grid-cols-4">
            {THEMES.map((t) => (
              <button
                key={t.k}
                type="button"
                className={cn(
                  'rounded-xl border py-2.5 text-center text-xs transition-colors',
                  t.active
                    ? 'border-gold-400/40 bg-gold-400/10 text-white'
                    : 'border-white/10 bg-white/[0.03] text-navy-200 hover:border-white/20 hover:text-white',
                )}
              >
                {t.n}
              </button>
            ))}
          </div>

          {/* 集数 + 节奏 */}
          <div className="mb-4 grid grid-cols-1 gap-3.5 md:grid-cols-2">
            <div>
              <label className="mb-1.5 block text-xs text-navy-300">集数</label>
              <div className="flex items-center gap-3.5">
                <input
                  type="range"
                  min={20}
                  max={120}
                  value={episodes}
                  onChange={(e) => setEpisodes(Number(e.target.value))}
                  className="h-1 flex-1 cursor-pointer appearance-none rounded-full bg-white/10 accent-gold-400"
                />
                <span className="min-w-[50px] text-right font-bold text-white">{episodes} 集</span>
              </div>
            </div>
            <Select label="节奏偏好">
              <option>前慢后快（推荐）</option>
              <option>全程快节奏</option>
              <option>前快后慢</option>
            </Select>
          </div>

          {/* 一句话创意 */}
          <div className="mb-2">
            <Textarea
              label="一句话创意"
              rows={4}
              defaultValue="被前夫扫地出门的全职妈妈，靠 5 年前埋下的证据链反杀豪门，并意外发现女儿身上藏着的惊天秘密。"
              placeholder="例：被前夫扫地出门的全职妈妈，靠 5 年前埋下的证据链反杀豪门……"
            />
          </div>

          {/* AI 字段锁定提示 — 对应后端 ai_field_prompt_service 的锁定策略 */}
          <div className="mt-5 flex flex-wrap items-center gap-3 rounded-2xl border border-indigo-500/35 bg-gradient-to-r from-indigo-500/15 to-purple-500/15 p-4">
            <div className="grid h-9 w-9 place-items-center rounded-lg bg-white/10 text-white">
              <Lock className={ICON.md} />
            </div>
            <div className="min-w-0 flex-1 text-sm">
              <b className="block text-sm text-white">AI 字段提示已锁定</b>
              <span className="text-navy-200">
                后续节点将以本简报为唯一输入，<b className="text-white">不可中途替换主题</b>，确保剧本一致性。
              </span>
            </div>
            <Button variant="ghost" size="sm">查看提示词</Button>
          </div>
        </section>
      </main>

      {/* ============ 右侧 — 节点预估 / Token 配额 ============ */}
      <aside className="border-l border-white/5 bg-navy-950/60 p-5">
        <SideTitle>本节点预估</SideTitle>
        <div className="space-y-1">
          <KV k="模型" v="doubao-pro-32k" />
          <KV k="预计 Token" v="~18,200" />
          <KV k="预计耗时" v="2 分钟" />
          <KV k="消耗创作币" v="120" />
        </div>

        <SideTitle>Token 配额（本月）</SideTitle>
        <div className="space-y-2.5">
          {TOKEN_QUOTAS.map((q) => (
            <div key={q.name}>
              <div className="mb-1 flex justify-between text-[11px] text-navy-300">
                <span>{q.name}</span>
                <span>{q.pct}%</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-white/5">
                <span
                  className={cn(
                    'block h-full',
                    q.cool
                      ? 'bg-gradient-to-r from-indigo-500 to-purple-500'
                      : 'bg-gradient-to-r from-gold-300 to-gold-500',
                  )}
                  style={{ width: `${q.pct}%` }}
                />
              </div>
            </div>
          ))}
        </div>

        <SideTitle>质量门槛</SideTitle>
        <div className="space-y-1">
          <KV k="四维评分" v="≥ 70 通过" />
          <KV k="格式审查" v="正则 28 条" />
          <KV k="敏感词" v="合规清单 v2.3" />
        </div>
      </aside>
    </motion.div>
  )
}

// —— 小组件 ——
function SideTitle({ children }) {
  return (
    <h4 className="mb-2.5 mt-5 px-2 text-[11px] font-semibold uppercase tracking-[0.15em] text-navy-300 first:mt-0">
      {children}
    </h4>
  )
}

function KV({ k, v }) {
  return (
    <div className="flex items-center justify-between border-b border-dashed border-white/5 py-2 text-[13px] text-navy-200">
      <span>{k}</span>
      <b className="text-white">{v}</b>
    </div>
  )
}
