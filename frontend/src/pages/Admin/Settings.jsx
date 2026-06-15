import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Database, RefreshCw, Server, Mail, Clock, Shield } from 'lucide-react'
import { admin } from '@/services/api'
import { AdminMessage, AdminLoading, AdminBadge } from '@/components/admin/AdminUI'

export default function AdminSettings() {
  const [loading, setLoading] = useState(true)
  const [clearing, setClearing] = useState(false)
  const [message, setMessage] = useState(null)
  const [settings, setSettings] = useState(null)

  useEffect(() => {
    ;(async () => {
      try {
        const data = await admin.getSystemSettings()
        setSettings(data || null)
      } catch (err) {
        setMessage({ type: 'error', text: err.message || '加载失败' })
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  async function handleClearCache() {
    if (!window.confirm('确定清除仪表盘与运营配置缓存？不会影响用户登录态。')) return
    setClearing(true)
    try {
      const res = await admin.clearCache()
      setMessage({
        type: 'success',
        text: res?.message || `缓存已清除（${res?.cleared_keys ?? 0} 项）`,
      })
    } catch (err) {
      setMessage({ type: 'error', text: err.message || '清除失败' })
    } finally {
      setClearing(false)
    }
  }

  if (loading) return <AdminLoading />

  const rows = [
    { icon: Server, label: '站点名称', value: settings?.site_name || '—' },
    { icon: Mail, label: '支持邮箱', value: settings?.support_email || '—' },
    { icon: Clock, label: '时区', value: settings?.time_zone || '—' },
    { icon: Database, label: '缓存后端', value: settings?.cache_backend || '—' },
    {
      icon: Shield,
      label: '调试模式',
      value: settings?.debug_mode ? '开启' : '关闭',
      badge: settings?.debug_mode ? 'danger' : 'success',
    },
    {
      icon: Shield,
      label: 'API 限流',
      value: `${settings?.api_rate_limit_per_hour ?? '—'} / 小时`,
    },
  ]

  return (
    <div className="space-y-6">
      <AdminMessage message={message} onClose={() => setMessage(null)} />

      <div className="glass-card rounded-2xl p-5 border border-blue-500/15 bg-blue-500/5">
        <p className="text-sm text-navy-200 leading-relaxed">
          <span className="text-white font-medium">此处为部署环境只读快照</span>
          （站点名、时区、DEBUG 等需改服务器配置，后台不能在线改）。
          运营可编辑项：币种与
          <Link to="/admin/commerce/settings" className="text-gold-400 hover:underline mx-1">
            注册赠送
          </Link>
          、
          <Link to="/admin/commerce/settings" className="text-gold-400 hover:underline mx-1">
            充值档位
          </Link>
          、
          <Link to="/admin/members/plans" className="text-gold-400 hover:underline mx-1">
            会员与卡密
          </Link>
          。
        </p>
      </div>

      <div className="glass-card rounded-2xl p-6 space-y-4">
        {rows.map((row) => (
          <div
            key={row.label}
            className="flex items-center justify-between gap-4 py-3 border-b border-navy-700/30 last:border-0"
          >
            <div className="flex items-center gap-3 text-navy-200">
              <row.icon className="w-5 h-5 text-gold-400" />
              <span>{row.label}</span>
            </div>
            <div className="text-right">
              {row.badge ? (
                <AdminBadge tone={row.badge}>{row.value}</AdminBadge>
              ) : (
                <span className="text-white text-sm break-all">{row.value}</span>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="glass-card rounded-2xl p-6">
        <h3 className="text-lg font-semibold text-white mb-2">缓存维护</h3>
        <p className="text-sm text-navy-300 mb-4">
          清除仪表盘统计与运营配置缓存。修改 LLM / Agent 参数后若未生效，可尝试此操作。
        </p>
        <button
          type="button"
          disabled={clearing}
          onClick={handleClearCache}
          className="inline-flex items-center gap-2 px-5 py-3 rounded-xl btn-gold disabled:opacity-60"
        >
          <RefreshCw className={`w-4 h-4 ${clearing ? 'animate-spin' : ''}`} />
          {clearing ? '清除中…' : '清除缓存'}
        </button>
      </div>
    </div>
  )
}
