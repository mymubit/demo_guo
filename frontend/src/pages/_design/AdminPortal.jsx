/**
 * AdminPortal.jsx — 门户题材 / 钩子 / 创作表单
 *
 * 对应后端：console/portal/portal_views.py
 * 视觉：3 段（题材模板 / 钩子库 / 创作表单）
 */
import { motion } from 'framer-motion'
import { Plus, Edit3, FileText, Image as ImageIcon, Hash } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { PageHeader, Panel, DataTable } from './components'

const THEMES = [
  { k: 'urban_rising', n: '都市逆袭', c: '12,403', order: 1, state: 'online' },
  { k: 'family_revenge', n: '家庭复仇', c: '9,210', order: 2, state: 'online' },
  { k: 'ceo_drama', n: '豪门霸总', c: '8,402', order: 3, state: 'online' },
  { k: 'rebirth', n: '穿越重生', c: '6,820', order: 4, state: 'online' },
  { k: 'sweet_abuse', n: '甜宠虐恋', c: '5,910', order: 5, state: 'online' },
  { k: 'ancient_politics', n: '古装权谋', c: '3,420', order: 6, state: 'online' },
  { k: 'mystery', n: '悬疑反转', c: '2,840', order: 7, state: 'draft' },
]

const HOOKS = [
  { k: 'H-001', t: '被前夫扫地出门，却意外继承 50 亿', tag: '都市', hot: 1240 },
  { k: 'H-002', t: '穿越 90 年代成了我爸的班主任', tag: '穿越', hot: 980 },
  { k: 'H-003', t: '我给财阀儿子当了 7 年替身', tag: '豪门', hot: 820 },
  { k: 'H-004', t: '她从火场抱出孩子那天，警察找上门', tag: '悬疑', hot: 720 },
]

const themeCols = [
  { key: 'k', header: '代码', render: (r) => <code className="rounded bg-white/5 px-1.5 py-0.5 text-xs text-slate-300">{r.k}</code> },
  { key: 'n', header: '题材', render: (r) => <b className="text-white">{r.n}</b> },
  { key: 'c', header: '使用次数', align: 'right' },
  { key: 'order', header: '排序', align: 'right' },
  { key: 'state', header: '状态', render: (r) => <Badge tone={r.state === 'online' ? 'success' : 'warning'}>{r.state === 'online' ? '已上线' : '草稿'}</Badge> },
]
const hookCols = [
  { key: 'k', header: '编号' },
  { key: 't', header: '钩子文案' },
  { key: 'tag', header: '题材', render: (r) => <Badge tone="gold">{r.tag}</Badge> },
  { key: 'hot', header: '使用量', align: 'right' },
]

export default function AdminPortal() {
  return (
    <motion.div {...pageEnter} className="space-y-5">
      <PageHeader
        crumbs={[{ label: 'Console' }, { label: '门户内容' }]}
        title="门户题材 · 钩子库 · 创作表单"
        subtitle="7 个题材 · 4 条钩子 · 1 套表单"
        toolbar={<Button variant="primary" size="md" iconLeft={<Plus className={ICON.md} />}>新建题材</Button>}
      />

      <Panel title="题材模板" sub="门户首页「题材」Tab 内容 · 支持拖拽排序">
        <DataTable columns={themeCols} rows={THEMES} />
      </Panel>

      <div className="grid grid-cols-1 gap-3.5 lg:grid-cols-2">
        <Panel
          title="钩子库"
          sub="点击文案可一键应用到创作表单"
          action={<Button variant="secondary" size="sm" iconLeft={<Plus className={ICON.sm} />}>添加</Button>}
        >
          <DataTable columns={hookCols} rows={HOOKS} />
        </Panel>

        <Panel title="创作表单" sub="portal/creation_form.py · 字段按主链节点分组">
          <ul className="m-0 space-y-1.5 p-0 text-[13px]">
            {[
              { node: '信息收集', fields: ['题材', '集数', '节奏', '一句话创意'] },
              { node: '结构规划', fields: ['节拍密度', '冲突等级'] },
              { node: '人设开发', fields: ['人物数量', '主配角'] },
              { node: '大纲撰写', fields: ['钩子模板', '反转密度'] },
            ].map((g) => (
              <li key={g.node} className="rounded-lg border border-white/5 bg-white/[0.02] p-3">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-white">{g.node}</span>
                  <span className="text-slate-500">{g.fields.length} 个字段</span>
                </div>
                <div className="mt-1.5 flex flex-wrap gap-1">
                  {g.fields.map((f) => <span key={f} className="rounded-md border border-white/10 bg-white/[0.03] px-1.5 py-0.5 text-[10px] text-slate-300">{f}</span>)}
                </div>
              </li>
            ))}
          </ul>
        </Panel>
      </div>
    </motion.div>
  )
}
