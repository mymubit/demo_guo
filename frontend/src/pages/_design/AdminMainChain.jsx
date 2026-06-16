/**
 * AdminMainChain.jsx — 主链蓝图 / 步骤编辑 / Fusion 节点包
 *
 * 对应后端：console/main_chain/views.py
 * 视觉：横向 7 节点蓝图（点击编辑）+ Fusion 节点包列表
 */
import { motion } from 'framer-motion'
import { Settings, Layers, Plus, Save, GitBranch } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'
import { PageHeader, Panel, DataTable } from './components'

const NODES = [
  { step: 1, name: '信息收集', skill: 'brief.collect', model: 'doubao-pro-32k', state: 'idle' },
  { step: 2, name: '结构规划', skill: 'structure.beat', model: 'deepseek-v3', state: 'idle' },
  { step: 3, name: '人设开发', skill: 'character.profile', model: 'gpt-4o-mini', state: 'draft' },
  { step: 4, name: '大纲撰写', skill: 'outline.episode', model: 'doubao-pro-32k', state: 'active' },
  { step: 5, name: '剧本创作', skill: 'script.scene', model: 'doubao-pro-128k', state: 'idle' },
  { step: 6, name: '质量审查', skill: 'review.gate', model: 'qwen-long', state: 'defect' },
  { step: 7, name: '输出交付', skill: 'final.deliver', model: '—', state: 'idle' },
]

const PACKS = [
  { k: 'fusion-pack-01', n: '都市逆袭 · 标准', steps: 7, skills: 7, by: '林老师', time: '2 天前' },
  { k: 'fusion-pack-02', n: '古装权谋 · 行业通用', steps: 7, skills: 9, by: '陈老师', time: '1 周前' },
  { k: 'fusion-pack-03', n: '甜宠虐恋 · 精简', steps: 5, skills: 5, by: '王老师', time: '2 周前' },
  { k: 'fusion-pack-04', n: '混合题材 · 实验', steps: 7, skills: 11, by: '李总', time: '1 个月前' },
]

const stateTone = { idle: 'default', active: 'info', draft: 'warning', defect: 'danger' }
const stateText = { idle: '运行中', active: '推荐', draft: '草稿', defect: '缺陷' }

const packCols = [
  { key: 'k', header: '包编号', render: (r) => <b className="text-white">{r.k}</b> },
  { key: 'n', header: '名称' },
  { key: 'steps', header: '步骤数', align: 'right' },
  { key: 'skills', header: '技能数', align: 'right' },
  { key: 'by', header: '编辑人' },
  { key: 'time', header: '最近修改' },
  {
    key: 'actions', header: '操作', align: 'right', render: () => (
      <span className="flex justify-end gap-1.5 text-xs">
        <button className="text-indigo-300 hover:underline">编辑</button>
        <span className="text-slate-600">·</span>
        <button className="text-gold-300 hover:underline">回灌</button>
      </span>
    ),
  },
]

export default function AdminMainChain() {
  return (
    <motion.div {...pageEnter} className="space-y-5">
      <PageHeader
        crumbs={[{ label: 'Console' }, { label: '主链工作室' }]}
        title="主链蓝图 · Fusion 节点包"
        subtitle="7 节点主链 · 4 个 Fusion Pack · 与 SKILL.md 同步"
        toolbar={
          <>
            <Button variant="secondary" size="md" iconLeft={<GitBranch className={ICON.md} />}>拉取 SKILL.md</Button>
            <Button variant="primary" size="md" iconLeft={<Save className={ICON.md} />}>同步到生产</Button>
          </>
        }
      />

      <Panel title="主链蓝图" sub="点击节点可编辑技能 / 模型 / 提示词">
        <div className="grid grid-cols-7 gap-2">
          {NODES.map((n) => (
            <button
              key={n.step}
              type="button"
              className={`flex flex-col items-start gap-1.5 rounded-2xl border p-3 text-left transition-colors ${
                n.state === 'active'
                  ? 'border-gold-400/40 bg-gold-400/10 text-white'
                  : 'border-white/10 bg-white/[0.03] text-slate-300 hover:border-white/20'
              }`}
            >
              <div className="flex w-full items-center justify-between">
                <span className="text-[10px] text-slate-500">STEP {n.step}</span>
                <Badge tone={stateTone[n.state]} size="sm">{stateText[n.state]}</Badge>
              </div>
              <div className="text-sm font-semibold text-white">{n.name}</div>
              <div className="text-[10px] text-slate-400">{n.skill}</div>
              <div className="mt-1 text-[10px] text-slate-500">{n.model}</div>
              <div className="mt-1 flex w-full items-center justify-end">
                <Settings className={ICON.xs + ' text-slate-500'} />
              </div>
            </button>
          ))}
        </div>
      </Panel>

      <Panel
        title="Fusion 节点包"
        sub="按题材封装的 7 节点参数包 · 支持回灌到生产"
        action={<Button variant="primary" size="sm" iconLeft={<Plus className={ICON.sm} />}>新建 Pack</Button>}
      >
        <DataTable columns={packCols} rows={PACKS} />
      </Panel>
    </motion.div>
  )
}
