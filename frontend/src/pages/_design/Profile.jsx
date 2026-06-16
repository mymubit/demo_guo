/**
 * Profile.jsx — 个人中心
 *
 * 对应后端：portal/users/views.py
 * 视觉：左侧 profile 卡 / 右侧 Tab（资料 / 安全 / 设备 / 通知）
 */
import { useState } from 'react'
import { motion } from 'framer-motion'
import { User, Shield, Smartphone, Bell, Camera, Check } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { cn } from '@/utils/cn'

const TABS = [
  { k: 'profile', n: '基本资料', icon: User },
  { k: 'security', n: '安全设置', icon: Shield },
  { k: 'devices', n: '登录设备', icon: Smartphone },
  { k: 'notify', n: '消息通知', icon: Bell },
]

const DEVICES = [
  { d: 'MacBook Pro · Chrome 124', loc: '上海 · 本机', ip: '192.168.1.4', last: '当前会话', current: true },
  { d: 'iPhone 15 · Safari', loc: '上海', ip: '10.0.0.18', last: '2 小时前' },
  { d: 'iPad · App', loc: '北京', ip: '36.1.2.41', last: '昨天 18:24' },
]

export default function Profile() {
  const [tab, setTab] = useState('profile')

  return (
    <motion.div {...pageEnter} className="mx-auto max-w-6xl px-6 py-10">
      <div className="grid grid-cols-1 gap-6 md:grid-cols-[280px_1fr]">
        {/* 左侧 — profile + 导航 */}
        <aside className="space-y-3.5">
          <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-5 text-center">
            <div className="relative mx-auto h-20 w-20">
              <div className="grid h-20 w-20 place-items-center rounded-full bg-gradient-to-br from-gold-300 to-gold-500 text-2xl font-bold text-navy-950">
                陈
              </div>
              <button className="absolute bottom-0 right-0 grid h-7 w-7 place-items-center rounded-full border border-white/20 bg-slate-900 text-slate-200 hover:bg-slate-800">
                <Camera className={ICON.sm} />
              </button>
            </div>
            <h2 className="mt-3 text-base font-semibold text-white">陈导</h2>
            <div className="mt-1 text-xs text-slate-500">138****8821 · 加入 2025-03</div>
            <div className="mt-3 flex flex-wrap justify-center gap-1.5">
              <Badge tone="gold">Pro 会员</Badge>
              <Badge tone="info">创作者</Badge>
            </div>
          </div>

          <nav className="rounded-2xl border border-white/5 bg-slate-900/60 p-2">
            {TABS.map((t) => (
              <button
                key={t.k}
                type="button"
                onClick={() => setTab(t.k)}
                className={cn(
                  'flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-sm transition-colors',
                  tab === t.k ? 'bg-gold-400/10 text-white' : 'text-slate-300 hover:bg-white/5 hover:text-white',
                )}
              >
                <t.icon className={cn(ICON.md, tab === t.k ? 'text-gold-400' : 'text-slate-400')} />
                {t.n}
              </button>
            ))}
          </nav>
        </aside>

        {/* 右侧 — 内容 */}
        <main className="rounded-2xl border border-white/5 bg-slate-900/60 p-5">
          {tab === 'profile' && <ProfileForm />}
          {tab === 'security' && <SecurityForm />}
          {tab === 'devices' && <DevicesTable />}
          {tab === 'notify' && <NotifyForm />}
        </main>
      </div>
    </motion.div>
  )
}

function ProfileForm() {
  return (
    <div>
      <h2 className="m-0 mb-4 text-base font-semibold">基本资料</h2>
      <div className="grid grid-cols-1 gap-3.5 md:grid-cols-2">
        <Field label="昵称" defaultValue="陈导" />
        <Field label="邮箱" defaultValue="chen@studio.cn" />
        <Field label="手机" defaultValue="138****8821" right="已验证" tone="success" />
        <Field label="所在城市" defaultValue="上海" />
        <Field label="团队/公司" defaultValue="逆光工作室" full />
        <Field label="个人简介" defaultValue="短剧导演 · 8 年从业经验 · 擅长都市情感题材" full textarea />
      </div>
      <div className="mt-5 flex justify-end gap-2">
        <Button variant="secondary" size="md">取消</Button>
        <Button variant="gold" size="md" iconLeft={<Check className={ICON.md} />}>保存修改</Button>
      </div>
    </div>
  )
}

function SecurityForm() {
  const rows = [
    { k: '登录密码', v: '上次修改 2025-08-12', cta: '修改密码' },
    { k: '手机绑定', v: '138****8821 · 已验证', cta: '更换' },
    { k: '邮箱绑定', v: 'chen@studio.cn · 已验证', cta: '更换' },
    { k: '两步验证', v: '未开启', cta: '开启', tone: 'warning' },
    { k: 'API 密钥', v: '已生成 2 个', cta: '管理' },
  ]
  return (
    <div>
      <h2 className="m-0 mb-4 text-base font-semibold">安全设置</h2>
      <ul className="m-0 space-y-1 p-0">
        {rows.map((r) => (
          <li key={r.k} className="flex items-center justify-between border-b border-white/5 py-3 last:border-b-0">
            <div>
              <div className="text-sm text-white">{r.k}</div>
              <div className="mt-0.5 text-xs text-slate-500">{r.v}</div>
            </div>
            <Button variant={r.tone === 'warning' ? 'gold' : 'secondary'} size="sm">{r.cta}</Button>
          </li>
        ))}
      </ul>
    </div>
  )
}

function DevicesTable() {
  return (
    <div>
      <h2 className="m-0 mb-4 text-base font-semibold">登录设备</h2>
      <table className="w-full border-collapse text-[13px]">
        <thead>
          <tr className="text-[11px] uppercase tracking-wider text-slate-500">
            <th className="py-2 text-left">设备</th>
            <th className="py-2 text-left">位置</th>
            <th className="py-2 text-left">最近活跃</th>
            <th className="py-2 text-right">操作</th>
          </tr>
        </thead>
        <tbody>
          {DEVICES.map((d, i) => (
            <tr key={i} className="border-t border-white/5">
              <td className="py-3 text-white">{d.d} {d.current && <Badge tone="success" size="sm" className="ml-1.5">当前</Badge>}</td>
              <td className="py-3 text-slate-300">{d.loc} · {d.ip}</td>
              <td className="py-3 text-slate-400">{d.last}</td>
              <td className="py-3 text-right">
                {!d.current && <button className="text-xs text-danger-300 hover:underline">登出</button>}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function NotifyForm() {
  const items = ['创作完成', '评论与回复', '会员到期', '系统公告', '营销推送']
  return (
    <div>
      <h2 className="m-0 mb-4 text-base font-semibold">消息通知</h2>
      <ul className="m-0 space-y-2 p-0">
        {items.map((k) => (
          <li key={k} className="flex items-center justify-between rounded-xl border border-white/5 bg-white/[0.02] p-3">
            <span className="text-sm text-white">{k}</span>
            <div className="flex gap-2 text-[11px] text-slate-400">
              {['站内', '邮件', '短信'].map((c) => (
                <label key={c} className="flex items-center gap-1.5">
                  <input type="checkbox" defaultChecked className="accent-gold-400" />
                  {c}
                </label>
              ))}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}

function Field({ label, right, tone, full, textarea, ...props }) {
  return (
    <label className={cn('block', full && 'md:col-span-2')}>
      <div className="mb-1.5 flex items-center justify-between text-xs text-slate-400">
        <span>{label}</span>
        {right && <Badge tone={tone} size="sm">{right}</Badge>}
      </div>
      {textarea ? (
        <textarea
          rows={3}
          {...props}
          className="w-full rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white placeholder:text-slate-500 focus:border-gold-400/60 focus:outline-none focus:ring-2 focus:ring-gold-400/20"
        />
      ) : (
        <input
          {...props}
          className="h-10 w-full rounded-xl border border-white/10 bg-white/5 px-3 text-sm text-white placeholder:text-slate-500 focus:border-gold-400/60 focus:outline-none focus:ring-2 focus:ring-gold-400/20"
        />
      )}
    </label>
  )
}
