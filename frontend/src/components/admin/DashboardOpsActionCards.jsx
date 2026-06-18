import { Link } from 'react-router-dom'
import { AlertTriangle, MessageSquare, Bell } from 'lucide-react'
import { Card } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { adminProjectDetailPath } from '@/utils/adminProjectRoutes'

/** Dashboard 顶部运营动作卡片（可穿透） */
export default function DashboardOpsActionCards({ opsAlerts = {}, failedProjects = [] }) {
  const cards = [
    {
      key: 'failed',
      label: '待处理失败项目',
      value: opsAlerts.failed ?? opsAlerts.has_failed_run ?? 0,
      hint: '融合状态为需修改或有失败 run',
      tone: 'text-red-300',
      border: 'border-red-500/25 bg-red-500/5',
      icon: AlertTriangle,
      to: '/admin/creation/projects?status=blocked',
    },
    {
      key: 'feedback',
      label: '待回复反馈',
      value: opsAlerts.feedback_open ?? 0,
      hint: '近 30 天 open 状态反馈',
      tone: 'text-amber-300',
      border: 'border-amber-500/25 bg-amber-500/5',
      icon: MessageSquare,
      to: '/admin/operations/feedback?status=open',
    },
    {
      key: 'alerts',
      label: '今日异常告警',
      value: opsAlerts.alert_open ?? 0,
      hint: '未关闭运营告警事件',
      tone: 'text-violet-300',
      border: 'border-violet-500/25 bg-violet-500/5',
      icon: Bell,
      to: '/admin/operations/alerts',
    },
  ]

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {cards.map((card) => {
          const Icon = card.icon
          return (
            <Link key={card.key} to={card.to} className="block group">
              <Card
                padding="sm"
                className={`${card.border} hover:ring-1 hover:ring-gold-500/20 transition`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="text-xs text-navy-400">{card.label}</p>
                    <p className={`text-3xl font-bold mt-1 ${card.tone}`}>{card.value}</p>
                    <p className="text-[10px] text-navy-500 mt-1">{card.hint}</p>
                  </div>
                  <Icon className={`${ICON.lg} ${card.tone} opacity-70 group-hover:opacity-100`} />
                </div>
              </Card>
            </Link>
          )
        })}
      </div>

      {(failedProjects?.length ?? 0) > 0 ? (
        <Card padding="sm" className="border-white/5">
          <div className="flex items-center justify-between gap-3 mb-3">
            <h3 className="text-sm font-semibold text-white">失败项目快捷入口</h3>
            <Link to="/admin/creation/projects?failed_run=1" className="text-xs text-gold-400 hover:text-gold-300">
              查看全部 →
            </Link>
          </div>
          <ul className="space-y-2">
            {failedProjects.slice(0, 6).map((row) => (
              <li key={row.project_id}>
                <Link
                  to={adminProjectDetailPath(row.project_id, 'runs')}
                  className="flex flex-wrap items-center justify-between gap-2 rounded-lg border border-white/5 bg-slate-900/40 px-3 py-2 text-sm hover:bg-white/[0.04]"
                >
                  <span className="text-white truncate">{row.title || '未命名'}</span>
                  <span className="text-xs text-red-300/90 shrink-0">
                    {row.execution_failed_count ? `失败 ${row.execution_failed_count} 次` : row.status_text || row.status}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      ) : null}
    </div>
  )
}
