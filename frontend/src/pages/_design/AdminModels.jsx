/**
 * AdminModels.jsx — LLM Provider / 模型目录 / 路由限流
 *
 * 对应后端：console/model/views.py
 */
import { motion } from 'framer-motion'
import { Cpu, Plus, Wifi, AlertTriangle, Settings } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { PageHeader, Panel } from './components'

const PROVIDERS = [
  { k: 'volcengine', n: '火山引擎', mk: 'doubao-pro-32k', models: 7, calls: '12,840', cost: '¥ 642', fail: 0.4, state: 'live' },
  { k: 'deepseek', n: 'DeepSeek', mk: 'deepseek-v3', models: 2, calls: '4,210', cost: '¥ 312', fail: 0.7, state: 'live' },
  { k: 'openai', n: 'OpenAI', mk: 'gpt-4o-mini', models: 1, calls: '1,884', cost: '¥ 188', fail: 2.1, state: 'limit' },
  { k: 'zhipu', n: '智谱', mk: 'glm-4-plus', models: 2, calls: '0', cost: '¥ 0', fail: 0, state: 'expired' },
  { k: 'qwen', n: '通义千问', mk: 'qwen-long', models: 3, calls: '920', cost: '¥ 96', fail: 0.2, state: 'live' },
]

const stateBadge = {
  live: <Badge tone="success">在线</Badge>,
  limit: <Badge tone="warning">限流</Badge>,
  expired: <Badge tone="danger">凭证过期</Badge>,
}

const CATALOG = [
  { p: '火山引擎', m: 'doubao-pro-32k', c: 0.008, ctx: '32K', tags: ['推荐'] },
  { p: '火山引擎', m: 'doubao-pro-128k', c: 0.024, ctx: '128K', tags: ['长文本'] },
  { p: 'DeepSeek', m: 'deepseek-v3', c: 0.002, ctx: '64K', tags: ['性价比'] },
  { p: 'OpenAI', m: 'gpt-4o-mini', c: 0.015, ctx: '128K', tags: [] },
  { p: '通义千问', m: 'qwen-long', c: 0.004, ctx: '1M', tags: ['超长'] },
  { p: '智谱', m: 'glm-4-plus', c: 0.05, ctx: '128K', tags: [] },
  { p: 'Anthropic', m: 'claude-3.5-sonnet', c: 0.018, ctx: '200K', tags: ['海外'] },
]

export default function AdminModels() {
  return (
    <motion.div {...pageEnter} className="space-y-5">
      <PageHeader
        crumbs={[{ label: 'Console' }, { label: '模型中心' }]}
        title="LLM Provider · 模型目录 · 路由"
        subtitle="5 个 Provider · 15 个模型 · 同步官方价目"
        toolbar={
          <>
            <Button variant="secondary" size="md" iconLeft={<Settings className={ICON.md} />}>同步官方价目</Button>
            <Button variant="primary" size="md" iconLeft={<Plus className={ICON.md} />}>新建 Provider</Button>
          </>
        }
      />

      <div className="grid grid-cols-1 gap-3.5 md:grid-cols-2">
        {PROVIDERS.map((p) => (
          <div key={p.k} className="rounded-2xl border border-white/5 bg-slate-900/60 p-4.5">
            <div className="flex items-start gap-3">
              <div className="grid h-9 w-9 place-items-center rounded-lg bg-gradient-to-br from-indigo-500 to-purple-500 text-sm font-bold text-white">
                {p.n[0]}
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h3 className="m-0 text-sm font-semibold text-white">{p.n}</h3>
                  {stateBadge[p.state]}
                </div>
                <div className="mt-0.5 text-[11px] text-slate-500">主推：{p.mk} · {p.models} 模型</div>
              </div>
            </div>
            <div className="mt-3 grid grid-cols-3 gap-2">
              <div className="rounded-lg border border-white/5 bg-white/[0.03] p-2">
                <div className="text-[10px] text-slate-500">24h 调用</div>
                <div className="mt-0.5 text-sm font-bold text-white">{p.calls}</div>
              </div>
              <div className="rounded-lg border border-white/5 bg-white/[0.03] p-2">
                <div className="text-[10px] text-slate-500">24h 成本</div>
                <div className="mt-0.5 text-sm font-bold text-white">{p.cost}</div>
              </div>
              <div className="rounded-lg border border-white/5 bg-white/[0.03] p-2">
                <div className="text-[10px] text-slate-500">失败率</div>
                <div className={`mt-0.5 text-sm font-bold ${p.fail > 1.5 ? 'text-warning-300' : 'text-white'}`}>{p.fail}%</div>
              </div>
            </div>
            <div className="mt-3 flex flex-wrap gap-1.5">
              <Button variant="secondary" size="sm" iconLeft={<Wifi className={ICON.sm} />}>连接测试</Button>
              <Button variant="ghost" size="sm">查看路由</Button>
              <Button variant="primary" size="sm">编辑凭证</Button>
            </div>
          </div>
        ))}
      </div>

      <Panel title="模型目录" sub="按 Provider 分类 · 支持按上下文 / 价格筛选">
        <table className="w-full border-collapse text-[13px]">
          <thead>
            <tr className="text-[11px] uppercase tracking-wider text-slate-500">
              <th className="border-b border-white/5 py-2 text-left">Provider</th>
              <th className="border-b border-white/5 py-2 text-left">模型</th>
              <th className="border-b border-white/5 py-2 text-right">¥ / 1K tok</th>
              <th className="border-b border-white/5 py-2 text-left">上下文</th>
              <th className="border-b border-white/5 py-2 text-left">标签</th>
            </tr>
          </thead>
          <tbody>
            {CATALOG.map((c) => (
              <tr key={c.p + c.m} className="border-t border-white/5">
                <td className="py-2.5 text-slate-300">{c.p}</td>
                <td className="py-2.5 text-white">{c.m}</td>
                <td className="py-2.5 text-right text-slate-300 tabular-nums">¥ {c.c.toFixed(3)}</td>
                <td className="py-2.5 text-slate-300">{c.ctx}</td>
                <td className="py-2.5">
                  <div className="flex flex-wrap gap-1">
                    {c.tags.map((t) => <Badge key={t} tone="gold">{t}</Badge>)}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </motion.div>
  )
}
