import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle } from 'lucide-react'
import { admin } from '@/services/api'

function fmtYuan(v) {
  return `¥${Number(v || 0).toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`
}

/**
 * 用户/订单/会员/创作页与 Dashboard 待办联动
 * @param {'users'|'orders'|'members'|'creation'} scope
 */
export default function AdminDashboardHints({ scope = 'users' }) {
  const [dash, setDash] = useState(null)

  useEffect(() => {
    admin.getDashboard().then(setDash).catch(() => {})
  }, [])

  if (!dash) return null

  const summary = dash.summary || {}
  const commerce = dash.commerce_alerts || {}
  const chips = []

  if (scope === 'users') {
    if ((summary.today_new_users ?? 0) > 0) {
      chips.push({
        key: 'new-users',
        label: '今日新注册',
        value: summary.today_new_users,
        to: '/admin/dashboard?tab=commerce',
      })
    }
    if ((commerce.inactive_users ?? 0) > 0) {
      chips.push({
        key: 'inactive',
        label: '已禁用账号',
        value: commerce.inactive_users,
        to: '/admin/users?filter=inactive',
        warn: true,
      })
    }
    chips.push({
      key: 'dashboard',
      label: '数据概览',
      hint: '商业 Tab',
      to: '/admin/dashboard?tab=commerce',
    })
  }

  if (scope === 'orders') {
    if ((commerce.pending_orders ?? 0) > 0) {
      chips.push({
        key: 'pending',
        label: '待支付',
        value: commerce.pending_orders,
        to: '/admin/orders?status=pending',
        warn: true,
      })
    }
    if (Number(summary.today_revenue ?? 0) > 0) {
      chips.push({
        key: 'revenue',
        label: '今日人民币收入',
        value: fmtYuan(summary.today_revenue),
        to: '/admin/dashboard?tab=commerce',
      })
    }
    chips.push({ key: 'recharge', label: '充值档位', to: '/admin/commerce/settings' })
    chips.push({ key: 'plans', label: '会员与卡密', to: '/admin/members/plans' })
  }

  if (scope === 'members') {
    if ((summary.total_members ?? 0) > 0) {
      chips.push({
        key: 'members',
        label: '有效会员',
        value: summary.total_members,
        to: '/admin/dashboard?tab=commerce',
      })
    }
    if (Number(summary.today_membership_yuan ?? 0) > 0) {
      chips.push({
        key: 'member-revenue',
        label: '今日会员收入',
        value: fmtYuan(summary.today_membership_yuan),
        to: '/admin/dashboard?tab=commerce',
      })
    }
    chips.push({ key: 'dashboard', label: '商业概览', hint: 'Dashboard', to: '/admin/dashboard?tab=commerce' })
    chips.push({ key: 'orders', label: '会员订单', to: '/admin/orders' })
  }

  if (scope === 'creation') {
    const ops = dash.ops_alerts || {}
    if ((ops.failed ?? 0) > 0) {
      chips.push({
        key: 'failed',
        label: '失败项目',
        value: ops.failed,
        to: '/admin/creation/projects?status=failed',
        warn: true,
      })
    }
    if ((ops.has_failed_run ?? 0) > 0) {
      chips.push({
        key: 'failed-run',
        label: '失败 run',
        value: ops.has_failed_run,
        to: '/admin/creation/projects?failed_run=1',
        warn: true,
      })
    }
    if ((ops.running ?? 0) > 0) {
      chips.push({
        key: 'running',
        label: '创作中',
        value: ops.running,
        to: '/admin/creation/projects?status=running',
      })
    }
    if ((ops.awaiting ?? 0) > 0) {
      chips.push({
        key: 'awaiting',
        label: '待确认',
        value: ops.awaiting,
        to: '/admin/creation/projects?status=awaiting',
      })
    }
    chips.push({ key: 'agents', label: '调度监控', to: '/admin/orchestration?view=overview' })
  }

  if (!chips.length) return null

  return (
    <div className="flex flex-wrap gap-1.5">
      {chips.map((chip) => (
        <Link
          key={chip.key}
          to={chip.to}
          className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition ${
            chip.warn
              ? 'bg-amber-500/10 text-amber-200 hover:bg-amber-500/15'
              : 'bg-slate-800/50 text-navy-300 hover:bg-slate-800 hover:text-white'
          }`}
        >
          {chip.warn ? <AlertTriangle className="w-3 h-3 shrink-0 opacity-80" /> : null}
          <span>{chip.label}</span>
          {chip.value != null ? <span className="font-semibold tabular-nums">{chip.value}</span> : null}
        </Link>
      ))}
    </div>
  )
}
