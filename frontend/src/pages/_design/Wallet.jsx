/**
 * Wallet.jsx — 创作币（钱包）
 *
 * 对应后端：portal/billing/views.py + billing/recharge_grant.py
 * 视觉：左侧余额大卡 + 右侧充值包选购 + 下方流水
 */
import { motion } from 'framer-motion'
import { Coins, ArrowUpRight, ArrowDownRight, Gift, Plus, History } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { Panel, DataTable } from './components'

const PACKAGES = [
  { coins: 100, price: 19, tag: '体验' },
  { coins: 500, price: 89, tag: '热门' },
  { coins: 1000, price: 168, tag: '推荐', off: 12 },
  { coins: 3000, price: 478, tag: '专业', off: 16 },
  { coins: 10000, price: 1498, tag: '旗舰', off: 22 },
]

const LEDGER = [
  { time: '06-16 10:24', type: '消费', item: '大纲撰写 · 节点 4', delta: -120, balance: 1280, tone: 'down' },
  { time: '06-15 14:02', type: '充值', item: '1000 币 充值包', delta: 1000, balance: 1400, tone: 'up' },
  { time: '06-15 14:00', type: '赠送', item: 'Pro 会员 · 月度奖励', delta: 200, balance: 400, tone: 'up' },
  { time: '06-14 09:18', type: '消费', item: 'script.scene · 节点 5', delta: -380, balance: 200, tone: 'down' },
  { time: '06-13 21:46', type: '退款', item: '订单 SF-2026-0613-007', delta: 168, balance: 580, tone: 'up' },
]

const cols = [
  { key: 'time', header: '时间' },
  { key: 'type', header: '类型', render: (r) => <Badge tone={r.tone === 'up' ? 'success' : 'danger'}>{r.type}</Badge> },
  { key: 'item', header: '说明' },
  { key: 'delta', header: '变动', align: 'right', render: (r) => (r.delta > 0 ? `+${r.delta}` : r.delta) },
  { key: 'balance', header: '余额', align: 'right' },
]

export default function Wallet() {
  return (
    <motion.div {...pageEnter} className="mx-auto max-w-7xl space-y-5 px-6 py-12">
      {/* ============ 顶部 — 余额大卡 ============ */}
      <div className="relative overflow-hidden rounded-3xl border border-white/5 bg-gradient-to-br from-navy-900 to-navy-950 p-8">
        <div
          className="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full opacity-30 blur-3xl"
          style={{ background: 'radial-gradient(closest-side, #f6d365, transparent)' }}
        />
        <div className="relative flex flex-wrap items-end justify-between gap-6">
          <div>
            <div className="text-xs uppercase tracking-wider text-gold-400">创作币余额</div>
            <div className="mt-1 flex items-baseline gap-2">
              <span className="font-display text-5xl font-bold text-white">1,280</span>
              <span className="text-slate-400">币 · ≈ ¥ 215</span>
            </div>
            <div className="mt-3 flex flex-wrap items-center gap-2 text-sm text-slate-300">
              <Badge tone="gold">Pro 会员 · 至 2026-08</Badge>
              <Badge tone="info">本月已节省 ¥ 86</Badge>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="secondary" size="md" iconLeft={<History className={ICON.md} />}>充值记录</Button>
            <Button variant="gold" size="md" iconLeft={<Plus className={ICON.md} />}>立即充值</Button>
          </div>
        </div>
      </div>

      {/* ============ 充值包选购 ============ */}
      <Panel title="充值包" sub="会员 9 折 · 旗舰版用户额外赠送 5%">
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {PACKAGES.map((p) => (
            <button
              key={p.coins}
              type="button"
              className="group relative flex flex-col rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left transition-all hover:border-gold-400/40 hover:bg-gold-400/5"
            >
              {p.tag && (
                <span className="absolute right-3 top-3 rounded-full bg-gradient-to-r from-gold-300 to-gold-500 px-2 py-0.5 text-[10px] font-bold text-navy-950">
                  {p.tag}
                </span>
              )}
              <div className="flex items-center gap-1.5 text-gold-400">
                <Coins className={ICON.md} />
                <span className="text-xl font-bold text-white">{p.coins.toLocaleString()}</span>
              </div>
              <div className="mt-1 text-xs text-slate-400">创作币</div>
              <div className="mt-3 flex items-baseline gap-1">
                <span className="text-lg font-bold text-white">¥ {p.price}</span>
                {p.off && <span className="text-xs text-slate-500">省 {p.off}%</span>}
              </div>
            </button>
          ))}
        </div>
        <div className="mt-3 text-xs text-slate-500">
          提示：充值 500 币起，企业客户可申请 <a className="text-gold-400">对公转账</a>。
        </div>
      </Panel>

      {/* ============ 卡密兑换 + 流水 ============ */}
      <div className="grid grid-cols-1 gap-3.5 lg:grid-cols-[1fr_2fr]">
        <Panel title="卡密兑换" sub="输入 16 位卡密激活创作币或会员">
          <div className="flex gap-2">
            <input
              placeholder="XXXX-XXXX-XXXX-XXXX"
              className="h-10 flex-1 rounded-xl border border-white/10 bg-white/5 px-3 text-sm text-white placeholder:text-slate-500 focus:border-gold-400/60 focus:outline-none"
            />
            <Button variant="gold" size="md">兑换</Button>
          </div>
          <div className="mt-3 flex items-center gap-2 text-xs text-slate-400">
            <Gift className={ICON.sm} /> 兑换成功后即时到账，可在「充值记录」中查询
          </div>
        </Panel>

        <Panel title="最近流水" sub="按时间倒序 · 仅显示最近 30 天">
          <DataTable columns={cols} rows={LEDGER} />
        </Panel>
      </div>
    </motion.div>
  )
}
