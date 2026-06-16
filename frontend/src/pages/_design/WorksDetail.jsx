/**
 * WorksDetail.jsx — 单本剧本详情
 *
 * 对应后端：portal/creation/works_views.py
 * 视觉：左侧剧本正文（带 Tab 切换 4 种格式） / 右侧元信息 + 操作
 */
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Download, Share2, Edit3, FileText, AlignLeft, Eye } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { cn } from '@/utils/cn'

const FORMATS = [
  { k: 'A', n: '标准版' },
  { k: 'B', n: '行业通用版' },
  { k: 'C', n: '精简版' },
  { k: 'D', n: '分镜版' },
]

const COVER =
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cinematic%20city%20rooftop%20at%20dusk%2C%20a%20woman%20in%20a%20red%20coat%20looking%20at%20the%20skyline%2C%20dark%20mood%2C%20anamorphic%2C%20photorealistic&image_size=landscape_16_9'

const META = [
  { k: '题材', v: '都市逆袭' },
  { k: '集数', v: '80 集 · 完整本' },
  { k: '评分', v: '86 / 100' },
  { k: '耗时', v: '08m 02s' },
  { k: '模型', v: 'doubao-pro-32k' },
  { k: 'Token', v: '182,310' },
  { k: '字数', v: '128,420' },
  { k: '文件', v: '4.6 MB · ZIP' },
]

// 极简示意剧本内容
const SCRIPT_PREVIEW = `第 17 集 · 「公司门口的真相」

场景 A · 写字楼外 · 日
雨后的街道反着光。苏敏撑着一把黑伞站在「长河集团」楼下，
她抬头看着那面曾经属于她的工位所在的玻璃幕墙。
    苏敏（旁白）：五年前，我被从这里扫地出门；
    今天，我要亲手把它烧回原形。

场景 B · 18 楼会议室 · 日
李明远正在和客户签合同。助理慌张推门进来。
    助理：李总，外面有人……她手里有一份 5 年前的审计原件。
李明远的钢笔停在半空。

[冲突点 1]  苏敏进入会议室，将证据链摊在会议桌上。
[反转 1]    审计原件的笔迹鉴定日期比合同签订日早 7 天。
[钩子]      苏敏微微一笑：「这只是第一份。」`

export default function WorksDetail() {
  const [fmt, setFmt] = useState('B')

  return (
    <motion.div {...pageEnter} className="mx-auto max-w-7xl space-y-5 px-6 py-8">
      {/* 顶 — 标题 + 操作 */}
      <div className="overflow-hidden rounded-3xl border border-white/5">
        <div className="relative h-48 bg-cover bg-center" style={{ backgroundImage: `url(${COVER})` }}>
          <div className="absolute inset-0 bg-gradient-to-t from-navy-950 via-navy-950/70 to-transparent" />
        </div>
        <div className="flex flex-wrap items-end justify-between gap-4 bg-navy-950 px-7 pb-6 pt-0">
          <div className="-mt-12">
            <Badge tone="gold">评分 86</Badge>
            <h1 className="mt-2 text-3xl font-bold">《逆光》</h1>
            <div className="mt-1 text-sm text-slate-400">都市逆袭 · 80 集 · 4.6 MB · 2026-06-15 生成</div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" size="md" iconLeft={<Edit3 className={ICON.md} />}>续写</Button>
            <Button variant="secondary" size="md" iconLeft={<Share2 className={ICON.md} />}>分享</Button>
            <Button variant="gold" size="md" iconLeft={<Download className={ICON.md} />}>下载剧本</Button>
          </div>
        </div>
      </div>

      {/* 主体 — 2 栏 */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-[1fr_320px]">
        {/* 左 — 剧本 */}
        <section className="rounded-2xl border border-white/5 bg-slate-900/40 p-5">
          {/* 格式切换 */}
          <div className="mb-4 flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 p-1">
            {FORMATS.map((f) => (
              <button
                key={f.k}
                type="button"
                onClick={() => setFmt(f.k)}
                className={cn(
                  'flex flex-1 items-center justify-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium transition-colors',
                  fmt === f.k ? 'bg-gold-400/15 text-white' : 'text-slate-300 hover:text-white',
                )}
              >
                <span className={cn('rounded-md px-1.5 py-0.5 text-[10px]', fmt === f.k ? 'bg-gradient-to-r from-gold-300 to-gold-500 text-navy-950' : 'bg-white/10')}>
                  {f.k}
                </span>
                {f.n}
              </button>
            ))}
          </div>
          <div className="flex items-center justify-between text-xs text-slate-500">
            <span>Variant-{fmt} · 第 17 集 / 共 80 集</span>
            <span className="flex items-center gap-3">
              <span className="flex items-center gap-1"><Eye className={ICON.xs} /> 已被阅读 12 次</span>
              <span className="flex items-center gap-1"><FileText className={ICON.xs} /> 数字水印：wm_138****8821</span>
            </span>
          </div>
          <pre className="mt-4 whitespace-pre-wrap rounded-xl border border-white/5 bg-navy-950/60 p-5 font-mono text-[13px] leading-7 text-navy-100">
            {SCRIPT_PREVIEW}
          </pre>
        </section>

        {/* 右 — 元信息 */}
        <aside className="space-y-3.5">
          <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-4.5">
            <h3 className="m-0 mb-3 text-sm font-semibold text-white">剧本信息</h3>
            <dl className="space-y-2 text-[13px]">
              {META.map((m) => (
                <div key={m.k} className="flex justify-between border-b border-dashed border-white/5 pb-2 last:border-b-0 last:pb-0">
                  <dt className="text-slate-400">{m.k}</dt>
                  <dd className="text-white">{m.v}</dd>
                </div>
              ))}
            </dl>
          </div>
          <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-4.5">
            <h3 className="m-0 mb-3 text-sm font-semibold text-white">质量评分</h3>
            <ScoreRow label="格式" v={92} />
            <ScoreRow label="节奏" v={84} />
            <ScoreRow label="内容" v={86} />
            <ScoreRow label="制作" v={80} />
          </div>
        </aside>
      </div>
    </motion.div>
  )
}

function ScoreRow({ label, v }) {
  return (
    <div className="mb-2 last:mb-0">
      <div className="mb-1 flex justify-between text-[11px] text-slate-400">
        <span>{label}</span>
        <span className="font-bold text-white">{v}</span>
      </div>
      <div className="h-1 overflow-hidden rounded-full bg-white/5">
        <span className="block h-full rounded-full bg-gradient-to-r from-gold-300 to-gold-500" style={{ width: `${v}%` }} />
      </div>
    </div>
  )
}
