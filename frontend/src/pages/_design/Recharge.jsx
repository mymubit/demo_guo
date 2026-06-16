/**
 * Recharge.jsx — 充值
 *
 * 对应后端：portal/billing/views.py (RechargePackage)
 * 视觉：充值包 + 支付方式 + 订单确认
 */
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Coins, Check, ShieldCheck, Wallet } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { cn } from '@/utils/cn'

const PACKAGES = [
  { coins: 100, price: 19 },
  { coins: 500, price: 89, tag: '热门' },
  { coins: 1000, price: 168, tag: '推荐', off: 12 },
  { coins: 3000, price: 478, tag: '专业', off: 16 },
  { coins: 10000, price: 1498, tag: '旗舰', off: 22 },
]

const PAYMENTS = [
  { k: 'wechat', n: '微信支付' },
  { k: 'alipay', n: '支付宝' },
  { k: 'enterprise', n: '企业对公' },
]

export default function Recharge() {
  const [pkg, setPkg] = useState(1000)
  const [pay, setPay] = useState('wechat')
  const sel = PACKAGES.find((p) => p.coins === pkg)

  return (
    <motion.div {...pageEnter} className="mx-auto max-w-6xl px-6 py-10">
      <header className="mb-6">
        <div className="text-xs uppercase tracking-wider text-gold-400 before:mr-2 before:inline-block before:h-px before:w-6 before:align-middle before:bg-gold-400">
          充值创作币
        </div>
        <h1 className="mt-2 text-3xl font-bold">充值创作币 · 解锁更多主链节点</h1>
        <p className="mt-2 max-w-2xl text-slate-400">会员 9 折 · 旗舰版用户额外赠送 5% · 支持企业对公转账</p>
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_360px]">
        {/* 左 — 充值包 + 支付方式 */}
        <div className="space-y-5">
          <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-5">
            <h3 className="m-0 mb-3 text-sm font-semibold text-white">选择充值包</h3>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
              {PACKAGES.map((p) => (
                <button
                  key={p.coins}
                  type="button"
                  onClick={() => setPkg(p.coins)}
                  className={cn(
                    'relative flex flex-col rounded-2xl border p-4 text-left transition-all',
                    pkg === p.coins
                      ? 'border-gold-400/60 bg-gold-400/10 shadow-gold'
                      : 'border-white/10 bg-white/[0.03] hover:border-white/20',
                  )}
                >
                  {p.tag && (
                    <span className="absolute right-3 top-3 rounded-full bg-gradient-to-r from-gold-300 to-gold-500 px-2 py-0.5 text-[10px] font-bold text-navy-950">
                      {p.tag}
                    </span>
                  )}
                  {pkg === p.coins && (
                    <span className="absolute left-3 top-3 grid h-5 w-5 place-items-center rounded-full bg-gradient-to-br from-gold-300 to-gold-500">
                      <Check className="h-3 w-3 text-navy-950" />
                    </span>
                  )}
                  <div className="mt-5 flex items-center gap-1.5 text-gold-400">
                    <Coins className={ICON.md} />
                    <span className="text-2xl font-bold text-white">{p.coins.toLocaleString()}</span>
                  </div>
                  <div className="text-xs text-slate-400">创作币</div>
                  <div className="mt-3 flex items-baseline gap-2">
                    <span className="text-xl font-bold text-white">¥ {p.price}</span>
                    {p.off && <span className="text-xs text-success-300">省 {p.off}%</span>}
                  </div>
                </button>
              ))}
            </div>
          </div>

          <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-5">
            <h3 className="m-0 mb-3 text-sm font-semibold text-white">支付方式</h3>
            <div className="grid grid-cols-3 gap-3">
              {PAYMENTS.map((p) => (
                <button
                  key={p.k}
                  type="button"
                  onClick={() => setPay(p.k)}
                  className={cn(
                    'flex items-center justify-center gap-2 rounded-xl border px-3 py-3 text-sm transition-colors',
                    pay === p.k
                      ? 'border-gold-400/60 bg-gold-400/10 text-white'
                      : 'border-white/10 bg-white/[0.03] text-slate-300 hover:border-white/20',
                  )}
                >
                  <Wallet className={ICON.md} />
                  {p.n}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* 右 — 订单确认 */}
        <aside className="rounded-2xl border border-white/5 bg-slate-900/60 p-5">
          <h3 className="m-0 mb-3 text-sm font-semibold text-white">订单确认</h3>
          <div className="rounded-xl border border-white/5 bg-white/[0.02] p-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-slate-300">{sel.coins.toLocaleString()} 创作币</span>
              <span className="text-base font-bold text-white">¥ {sel.price}</span>
            </div>
            {sel.off && (
              <div className="mt-2 flex items-center justify-between text-xs text-slate-400">
                <span>优惠</span>
                <span className="text-success-300">-{sel.off}%</span>
              </div>
            )}
            <div className="my-3 h-px bg-white/5" />
            <div className="flex items-center justify-between text-base font-bold">
              <span>实付</span>
              <span className="text-gold-400">¥ {sel.price}</span>
            </div>
          </div>
          <Button variant="gold" size="lg" className="mt-4 w-full justify-center">
            立即支付
          </Button>
          <div className="mt-3 flex items-start gap-2 text-[11px] text-slate-400">
            <ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <span>支付完成后创作币将即时到账，本平台不存储任何支付凭证，仅依赖第三方支付通道</span>
          </div>
        </aside>
      </div>
    </motion.div>
  )
}
