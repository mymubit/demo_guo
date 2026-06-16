/**
 * Auth.jsx — 登录 / 注册（Tab 切换）
 *
 * 对应后端：portal/auth/views.py
 * 视觉：左侧品牌叙事（实景剧照 + 一句话主张） / 右侧表单
 */
import { useState } from 'react'
import { motion } from 'framer-motion'
import { Phone, Lock, Mail, Sparkles, ShieldCheck } from 'lucide-react'
import { Button, Badge } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { cn } from '@/utils/cn'

const BG =
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cinematic%20film%20set%20at%20night%2C%20giant%20spotlight%2C%20clapperboard%20on%20a%20chair%2C%20dark%20mood%2C%20anamorphic%2C%20gold%20and%20navy%20tones%2C%20photorealistic%2C%208k&image_size=portrait_4_3'

const TABS = [
  { k: 'login', title: '登录' },
  { k: 'register', title: '注册' },
]

export default function Auth() {
  const [tab, setTab] = useState('login')
  const [method, setMethod] = useState('phone')

  return (
    <motion.div {...pageEnter} className="grid min-h-[calc(100svh-3.25rem)] grid-cols-1 lg:grid-cols-2">
      {/* ============ 左 — 品牌叙事 ============ */}
      <div className="relative hidden overflow-hidden lg:block">
        <div className="absolute inset-0 bg-cover bg-center" style={{ backgroundImage: `url(${BG})`, filter: 'brightness(.55)' }} />
        <div
          className="absolute inset-0"
          style={{
            background:
              'radial-gradient(50% 40% at 30% 60%, rgba(246,211,101,.18), transparent 70%),' +
              'linear-gradient(180deg, rgba(3,13,36,.4), rgba(3,13,36,.9))',
          }}
        />
        <div className="relative z-10 flex h-full flex-col justify-between p-12">
          <div>
            <Badge tone="gold" size="md">ScriptForge</Badge>
            <h2 className="mt-4 max-w-md font-display text-3xl font-bold leading-tight text-white">
              把每一句话创意，<br />
              变成可被拍摄的剧本。
            </h2>
            <p className="mt-3 max-w-md text-navy-200">7 节点主链 · 4 题材格式 · 数字水印 · 全流程 8–12 分钟</p>
          </div>
          <div className="space-y-2 text-sm text-navy-200">
            <div className="flex items-center gap-2">
              <ShieldCheck className={ICON.md} /> 端到端加密 · 原始数据不出端
            </div>
            <div className="flex items-center gap-2">
              <Sparkles className={ICON.md} /> 50,000+ 创作者 · 200 万集数生成
            </div>
          </div>
        </div>
      </div>

      {/* ============ 右 — 表单 ============ */}
      <div className="flex items-center justify-center p-8 md:p-12">
        <div className="w-full max-w-sm">
          {/* Tabs */}
          <div className="mb-7 flex gap-1 rounded-full border border-white/10 bg-white/5 p-1">
            {TABS.map((t) => (
              <button
                key={t.k}
                type="button"
                onClick={() => setTab(t.k)}
                className={cn(
                  'flex-1 rounded-full px-3 py-1.5 text-sm font-medium transition-colors',
                  tab === t.k ? 'bg-white/10 text-white' : 'text-slate-300 hover:text-white',
                )}
              >
                {t.title}
              </button>
            ))}
          </div>

          <h1 className="text-2xl font-bold">{tab === 'login' ? '欢迎回来' : '创建账号'}</h1>
          <p className="mt-1 text-sm text-slate-400">
            {tab === 'login' ? '登录以继续你的创作' : '注册即送 100 创作币体验'}
          </p>

          {/* 验证方式 */}
          <div className="mt-6 grid grid-cols-2 gap-2">
            <MethodBtn active={method === 'phone'} onClick={() => setMethod('phone')} icon={<Phone className={ICON.md} />}>
              手机号
            </MethodBtn>
            <MethodBtn active={method === 'email'} onClick={() => setMethod('email')} icon={<Mail className={ICON.md} />}>
              邮箱
            </MethodBtn>
          </div>

          <form className="mt-5 space-y-3">
            <Field
              icon={method === 'phone' ? <Phone className={ICON.md} /> : <Mail className={ICON.md} />}
              placeholder={method === 'phone' ? '请输入手机号' : '请输入邮箱'}
            />
            <Field icon={<Lock className={ICON.md} />} placeholder="密码（8-20 位）" type="password" />
            {tab === 'register' && (
              <Field icon={<Lock className={ICON.md} />} placeholder="确认密码" type="password" />
            )}
            <Button variant="gold" size="lg" className="w-full justify-center">
              {tab === 'login' ? '登录' : '注册'}
            </Button>
          </form>

          <div className="my-5 flex items-center gap-3 text-xs text-slate-500">
            <span className="h-px flex-1 bg-white/10" />
            其他方式
            <span className="h-px flex-1 bg-white/10" />
          </div>
          <div className="grid grid-cols-3 gap-2">
            {['微信', 'Apple', 'Google'].map((m) => (
              <Button key={m} variant="secondary" size="md" className="justify-center">
                {m}
              </Button>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  )
}

function MethodBtn({ active, onClick, icon, children }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        'flex items-center justify-center gap-2 rounded-xl border px-3 py-2 text-sm transition-colors',
        active
          ? 'border-gold-400/40 bg-gold-400/10 text-white'
          : 'border-white/10 bg-white/[0.03] text-slate-300 hover:border-white/20',
      )}
    >
      {icon}
      {children}
    </button>
  )
}

function Field({ icon, ...props }) {
  return (
    <div className="relative">
      <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-500">{icon}</span>
      <input
        {...props}
        className="h-11 w-full rounded-xl border border-white/10 bg-white/5 pl-10 pr-3 text-sm text-white placeholder:text-slate-500 focus:border-gold-400/60 focus:outline-none focus:ring-2 focus:ring-gold-400/20"
      />
    </div>
  )
}
