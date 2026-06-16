/**
 * AdminMembers.jsx — 会员 / 套餐管理
 *
 * 对应后端：console/commerce/membership_views.py
 * 视觉：左 — 套餐矩阵 / 右 — 权益编辑
 */
import { motion } from 'framer-motion'
import { Edit3, Plus, Sparkles } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { PageHeader, Panel } from './components'

const PLANS = [
  { k: 'free', n: '体验版', p: '¥0', u: '永久', c: '12,403', tone: 'default' },
  { k: 'pro', n: '专业版', p: '¥299', u: '月', c: '6,841', tone: 'gold', featured: true },
  { k: 'enterprise', n: '旗舰版', p: '¥2,880', u: '月', c: '1,224', tone: 'info' },
]

const FEATURES = [
  '主链创作次数', '单次最大集数', '题材模板', '输出格式', '数字水印', '分享链接', '质量审查', 'API 接入', '团队协作',
]
const MATRIX = {
  free:       ['1 次 / 月', '20 集', '3', '1', '—', '—', '—', '—', '—'],
  pro:        ['30 次 / 月', '120 集', '8', '4', '✓', '✓', '✓', '—', '—'],
  enterprise: ['不限', '120 集', '8 + 私有', '4 + 私有', '✓', '✓ 短链', '✓ + 优先', '✓', '✓'],
}

export default function AdminMembers() {
  return (
    <motion.div {...pageEnter} className="space-y-5">
      <PageHeader
        crumbs={[{ label: 'Console' }, { label: '会员 / 套餐' }]}
        title="会员套餐"
        subtitle="3 个主套餐 + 私有模板 · 总用户 20,468"
        toolbar={
          <Button variant="primary" size="md" iconLeft={<Plus className={ICON.md} />}>新建套餐</Button>
        }
      />

      <div className="grid grid-cols-1 gap-3.5 md:grid-cols-3">
        {PLANS.map((p) => (
          <div key={p.k} className={`rounded-2xl border border-white/5 bg-slate-900/60 p-4.5 ${p.featured ? 'border-gold-400/40 shadow-gold' : ''}`}>
            <div className="flex items-center justify-between">
              <Badge tone={p.tone} size="md">{p.n}</Badge>
              {p.featured && <Sparkles className={ICON.md + ' text-gold-400'} />}
            </div>
            <div className="mt-3 flex items-baseline gap-1">
              <span className="text-2xl font-bold text-white">{p.p}</span>
              <span className="text-slate-400">/ {p.u}</span>
            </div>
            <div className="mt-1 text-xs text-slate-500">当前 {p.c} 订阅</div>
            <div className="mt-3 flex gap-2">
              <Button variant="secondary" size="sm" iconLeft={<Edit3 className={ICON.sm} />}>编辑</Button>
              <Button variant="ghost" size="sm">订阅用户</Button>
            </div>
          </div>
        ))}
      </div>

      <Panel title="权益矩阵" sub="点击单元格可编辑具体权益值">
        <table className="w-full border-collapse text-[13px]">
          <thead>
            <tr className="text-[11px] uppercase tracking-wider text-slate-500">
              <th className="border-b border-white/5 py-2 text-left">权益</th>
              {PLANS.map((p) => (
                <th key={p.k} className="border-b border-white/5 py-2 text-left">{p.n}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {FEATURES.map((f, i) => (
              <tr key={f} className="border-t border-white/5">
                <td className="py-3 text-slate-300">{f}</td>
                {PLANS.map((p) => (
                  <td key={p.k} className="py-3 text-white">{MATRIX[p.k][i]}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </motion.div>
  )
}
