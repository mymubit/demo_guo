/**
 * AdminSystem.jsx — 系统配置 / 监控 / 缓存
 *
 * 对应后端：console/system/views.py
 * 视觉：3 段（KPI 监控 / 系统配置 / 缓存管理）
 */
import { motion } from 'framer-motion'
import { Server, Database, Cloud, HardDrive, RefreshCcw, Save, AlertCircle } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { PageHeader, Panel, KpiTile } from './components'

const CONFIGS = [
  { k: '站点名称', v: 'ScriptForge', type: 'string', env: '—' },
  { k: '主链超时', v: '600s', type: 'number', env: 'PROD' },
  { k: '水印前缀', v: 'wm_', type: 'string', env: 'PROD' },
  { k: '最大集数', v: '120', type: 'number', env: '—' },
  { k: '签名密钥', v: 'sk_live_****c1d2', type: 'secret', env: 'PROD' },
  { k: '每月免费额度', v: '3 次', type: 'number', env: '—' },
]

const CACHES = [
  { k: 'llm_routes', hit: 96.4, size: '2.1 MB', ttl: '5m' },
  { k: 'theme_cards', hit: 92.0, size: '1.6 MB', ttl: '10m' },
  { k: 'plan_matrix', hit: 88.2, size: '420 KB', ttl: '30m' },
  { k: 'skill_defs', hit: 99.1, size: '880 KB', ttl: '1h' },
]

export default function AdminSystem() {
  return (
    <motion.div {...pageEnter} className="space-y-5">
      <PageHeader
        crumbs={[{ label: 'Console' }, { label: '系统设置' }]}
        title="系统配置 · 监控 · 缓存"
        subtitle="6 项配置 · 4 个缓存 · 1 套监控告警"
      />

      {/* 监控 */}
      <div className="grid grid-cols-1 gap-3.5 sm:grid-cols-2 lg:grid-cols-4">
        <KpiTile label="CPU 使用率" value="42%" delta="正常" up />
        <KpiTile label="内存使用" value="68%" delta="正常" up />
        <KpiTile label="磁盘空间" value="412 GB" delta="可用 68%" up gold />
        <KpiTile label="API 响应 P95" value="186ms" delta="+12ms" up danger />
      </div>

      {/* 配置表 */}
      <Panel
        title="系统配置"
        sub="支持按环境覆盖（DEV / STAGING / PROD）"
        action={<Button variant="primary" size="sm" iconLeft={<Save className={ICON.sm} />}>保存全部</Button>}
      >
        <table className="w-full border-collapse text-[13px]">
          <thead>
            <tr className="text-[11px] uppercase tracking-wider text-slate-500">
              <th className="border-b border-white/5 py-2 text-left">键</th>
              <th className="border-b border-white/5 py-2 text-left">值</th>
              <th className="border-b border-white/5 py-2 text-left">类型</th>
              <th className="border-b border-white/5 py-2 text-left">环境</th>
            </tr>
          </thead>
          <tbody>
            {CONFIGS.map((c) => (
              <tr key={c.k} className="border-t border-white/5">
                <td className="py-2.5 text-slate-300">{c.k}</td>
                <td className="py-2.5 text-white">
                  {c.type === 'secret' ? (
                    <span className="font-mono text-slate-400">•••••••</span>
                  ) : (
                    <span className="rounded-md border border-white/10 bg-white/5 px-2 py-0.5">{c.v}</span>
                  )}
                </td>
                <td className="py-2.5 text-slate-400">{c.type}</td>
                <td className="py-2.5">
                  {c.env === 'PROD' ? <Badge tone="warning">PROD</Badge> : <Badge tone="default">—</Badge>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>

      {/* 缓存 */}
      <Panel
        title="缓存管理"
        sub="命中率 < 80% 将触发告警"
        action={<Button variant="secondary" size="sm" iconLeft={<RefreshCcw className={ICON.sm} />}>清空全部</Button>}
      >
        <div className="grid grid-cols-1 gap-3.5 md:grid-cols-2 lg:grid-cols-4">
          {CACHES.map((c) => (
            <div key={c.k} className="rounded-2xl border border-white/5 bg-white/[0.03] p-3.5">
              <div className="text-xs text-slate-400">{c.k}</div>
              <div className="mt-1 flex items-baseline gap-1">
                <span className={`text-2xl font-bold ${c.hit >= 90 ? 'text-success-300' : c.hit >= 80 ? 'text-white' : 'text-warning-300'}`}>{c.hit}%</span>
                <span className="text-[10px] text-slate-500">命中率</span>
              </div>
              <div className="mt-1 flex justify-between text-[10px] text-slate-500">
                <span>{c.size}</span>
                <span>TTL {c.ttl}</span>
              </div>
              <div className="mt-2 h-1 overflow-hidden rounded-full bg-white/5">
                <span className="block h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500" style={{ width: `${c.hit}%` }} />
              </div>
            </div>
          ))}
        </div>
      </Panel>
    </motion.div>
  )
}
