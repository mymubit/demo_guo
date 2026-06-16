/**
 * AdminUsers.jsx — 用户管理
 *
 * 对应后端：console/identity/user_views.py
 */
import { motion } from 'framer-motion'
import { Plus, Download, Shield, ShieldOff } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { PageHeader, ToolbarSearch, Panel, DataTable } from './components'

const USERS = [
  { id: 'U-10248', name: '陈导', phone: '138****8821', role: 'enterprise', plan: '旗舰版 · 至 2027-03', coins: '1,280 币', works: 42, last: '10 分钟前' },
  { id: 'U-10241', name: '林编剧', phone: '139****0032', role: 'paid', plan: '专业版 · 至 2026-08', coins: '420 币', works: 18, last: '1 小时前' },
  { id: 'U-10220', name: '王老师', phone: '186****7741', role: 'free', plan: '—', coins: '0 币', works: 1, last: '昨天' },
  { id: 'U-10211', name: '张同学', phone: '177****2098', role: 'paid', plan: '专业版 · 至 2026-07', coins: '86 币', works: 6, last: '3 天前' },
  { id: 'U-10198', name: '李总', phone: '151****6620', role: 'enterprise', plan: '旗舰版 · 至 2027-01', coins: '8,200 币', works: 122, last: '5 小时前' },
]

const roleTone = { enterprise: 'info', paid: 'gold', free: 'default' }
const roleText = { enterprise: '企业', paid: '付费', free: '体验' }

const cols = [
  {
    key: 'name',
    header: '用户',
    render: (r) => (
      <span className="flex items-center gap-2.5">
        <span className="grid h-7 w-7 place-items-center rounded-full bg-gradient-to-br from-indigo-500 to-purple-500 text-xs font-bold text-white">
          {r.name[0]}
        </span>
        <span><b className="text-white">{r.name}</b> <span className="text-slate-500">· {r.phone}</span></span>
      </span>
    ),
  },
  { key: 'role', header: '角色', render: (r) => <Badge tone={roleTone[r.role]}>{roleText[r.role]}</Badge> },
  { key: 'plan', header: '会员' },
  { key: 'coins', header: '余额', align: 'right' },
  { key: 'works', header: '作品数', align: 'right' },
  { key: 'last', header: '最近活跃' },
  {
    key: 'actions',
    header: '操作',
    align: 'right',
    render: () => (
      <span className="flex justify-end gap-1.5 text-xs">
        <button className="text-indigo-300 hover:underline">详情</button>
        <span className="text-slate-600">·</span>
        <button className="inline-flex items-center gap-1 text-danger-300 hover:underline">
          <ShieldOff className={ICON.xs} /> 冻结
        </button>
      </span>
    ),
  },
]

export default function AdminUsers() {
  return (
    <motion.div {...pageEnter} className="space-y-5">
      <PageHeader
        crumbs={[{ label: 'Console' }, { label: '用户管理' }]}
        title="用户 · 9,238"
        subtitle="按最近活跃倒序 · 含付费 / 体验 / 企业三档"
        toolbar={
          <>
            <ToolbarSearch placeholder="手机号 / 昵称 / ID" width={240} />
            <Button variant="secondary" size="md" iconLeft={<Download className={ICON.md} />}>导出</Button>
            <Button variant="primary" size="md" iconLeft={<Plus className={ICON.md} />}>新建用户</Button>
          </>
        }
      />
      <Panel>
        <DataTable columns={cols} rows={USERS} />
      </Panel>
    </motion.div>
  )
}
