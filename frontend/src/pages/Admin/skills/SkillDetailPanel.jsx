import { useState } from 'react'
import { Pencil, Save } from 'lucide-react'
import AdminEvolution from '@/pages/Admin/evolution/AdminEvolution'
import {
  AdminDetailHeader,
  AdminField,
  AdminJsonDrawer,
  AdminKvGrid,
  AdminLifecycleBadge,
  AdminTextPreview,
  adminBtnPrimary,
  adminBtnDanger,
  adminBtnSecondary,
} from '@/components/admin/workbench/AdminWorkbenchKit'
import { AdminInspectorSection, AdminPanel } from '@/components/admin/AdminUI'
import { LAYER_LABEL } from './skillFormUtils'

function SchemaCard({ title, value, onEdit }) {
  return (
    <AdminPanel title={title}>
      <AdminTextPreview text={value} maxLines={8} />
      <button type="button" onClick={onEdit} className={`${adminBtnSecondary()} mt-3 text-xs`}>
        <Pencil className="h-3.5 w-3.5" />
        编辑 JSON
      </button>
    </AdminPanel>
  )
}

export default function SkillDetailPanel({
  selected,
  form,
  setForm,
  detailTab,
  skillStats,
  skillVersions,
  isNew,
  saving,
  onSave,
  onPublish,
  onRollback,
  onDelete,
  onMessage,
}) {
  const [drawer, setDrawer] = useState(null)

  function patchForm(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  function openDrawer(key, title) {
    setDrawer({ key, title, value: form[key] })
  }

  function closeDrawer() {
    setDrawer(null)
  }

  function saveDrawer() {
    if (drawer?.key) patchForm(drawer.key, drawer.value)
    closeDrawer()
  }

  if (isNew) {
    return (
      <div className="space-y-4">
        <AdminDetailHeader title="新增技能" subtitle="创建后可发布上线" />
        <AdminInspectorSection title="基础信息">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <AdminField label="技能 ID *">
              <input className="sf-control" value={form.skill_id} onChange={(e) => patchForm('skill_id', e.target.value)} placeholder="如 brief.character_extract" />
            </AdminField>
            <AdminField label="技能名称 *">
              <input className="sf-control" value={form.name} onChange={(e) => patchForm('name', e.target.value)} />
            </AdminField>
            <AdminField label="技能层级">
              <select className="sf-control" value={form.skill_layer} onChange={(e) => patchForm('skill_layer', e.target.value)}>
                <option value="">未分类</option>
                <option value="foundation">基础能力层</option>
                <option value="business">业务技能层</option>
                <option value="tool">工具能力层</option>
              </select>
            </AdminField>
            <AdminField label="版本号">
              <input className="sf-control" value={form.version} onChange={(e) => patchForm('version', e.target.value)} />
            </AdminField>
          </div>
        </AdminInspectorSection>
        <div className="flex justify-end">
          <button type="button" disabled={saving} onClick={onSave} className={adminBtnPrimary()}>
            <Save className="h-4 w-4" />
            {saving ? '创建中…' : '创建技能'}
          </button>
        </div>
      </div>
    )
  }

  if (!selected) return null

  const headerActions = (
    <>
      {selected.lifecycle_status !== 'deprecated' ? (
        <>
          <button type="button" onClick={onPublish} className={adminBtnSecondary()}>发布/灰度</button>
          <button type="button" onClick={onRollback} className={adminBtnSecondary()}>回滚</button>
          <button type="button" onClick={onDelete} className={adminBtnDanger()}>废弃</button>
        </>
      ) : null}
      <button type="button" disabled={saving} onClick={onSave} className={adminBtnPrimary()}>
        <Save className="h-4 w-4" />
        {saving ? '保存中…' : '保存'}
      </button>
    </>
  )

  return (
    <>
      <AdminDetailHeader
        title={form.name || selected.name || selected.skill_id}
        subtitle={selected.skill_id}
        meta={`${LAYER_LABEL[form.skill_layer] || form.skill_layer || '未分类'}${form.sub_category ? ` · ${form.sub_category}` : ''} · v${form.version}`}
        badges={[<AdminLifecycleBadge key="s" status={selected.lifecycle_status} grayWeight={selected.gray_weight} />]}
        actions={headerActions}
      />

      {detailTab === 'overview' ? (
        <div className="space-y-4">
          <AdminInspectorSection title="基础配置">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <AdminField label="技能名称">
                <input className="sf-control" value={form.name} onChange={(e) => patchForm('name', e.target.value)} />
              </AdminField>
              <AdminField label="版本号">
                <input className="sf-control" value={form.version} onChange={(e) => patchForm('version', e.target.value)} />
              </AdminField>
              <AdminField label="技能层级">
                <select className="sf-control" value={form.skill_layer} onChange={(e) => patchForm('skill_layer', e.target.value)}>
                  <option value="">未分类</option>
                  <option value="foundation">基础能力层</option>
                  <option value="business">业务技能层</option>
                  <option value="tool">工具能力层</option>
                </select>
              </AdminField>
              <AdminField label="子分类">
                <input className="sf-control" value={form.sub_category} onChange={(e) => patchForm('sub_category', e.target.value)} />
              </AdminField>
              <AdminField label="超时（秒）">
                <input type="number" className="sf-control" min={5} max={600} value={form.timeout_seconds} onChange={(e) => patchForm('timeout_seconds', e.target.value)} />
              </AdminField>
              <AdminField label="配额消耗">
                <input type="number" className="sf-control" min={0} step={0.1} value={form.quota_cost} onChange={(e) => patchForm('quota_cost', e.target.value)} />
              </AdminField>
              <AdminField label="降级技能 ID" className="md:col-span-2">
                <input className="sf-control" value={form.fallback_skill_id} onChange={(e) => patchForm('fallback_skill_id', e.target.value)} placeholder="主技能失败时的 fallback skill_id" />
              </AdminField>
            </div>
          </AdminInspectorSection>
          <AdminInspectorSection title="重试策略">
            <AdminTextPreview text={form.retry_policy} maxLines={4} />
            <button type="button" onClick={() => openDrawer('retry_policy', '重试策略 JSON')} className={`${adminBtnSecondary()} mt-2 text-xs`}>
              <Pencil className="h-3.5 w-3.5" /> 编辑
            </button>
          </AdminInspectorSection>
        </div>
      ) : null}

      {detailTab === 'prompt' ? (
        <div className="space-y-4">
          <AdminPanel title="System Hint（LLM 系统提示词）">
            <AdminTextPreview text={form.system_hint} maxLines={6} />
            <button type="button" onClick={() => openDrawer('system_hint', 'System Hint')} className={`${adminBtnSecondary()} mt-3 text-xs`}>
              <Pencil className="h-3.5 w-3.5" /> 全屏编辑
            </button>
          </AdminPanel>
          <AdminPanel title="技能内容（Markdown）">
            <AdminTextPreview text={form.content} maxLines={8} />
            <button type="button" onClick={() => openDrawer('content', '技能 Markdown')} className={`${adminBtnSecondary()} mt-3 text-xs`}>
              <Pencil className="h-3.5 w-3.5" /> 全屏编辑
            </button>
          </AdminPanel>
        </div>
      ) : null}

      {detailTab === 'schema' ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SchemaCard title="入参 Schema" value={form.input_schema} onEdit={() => openDrawer('input_schema', '入参 Schema')} />
          <SchemaCard title="出参 Schema" value={form.output_schema} onEdit={() => openDrawer('output_schema', '出参 Schema')} />
        </div>
      ) : null}

      {detailTab === 'versions' ? (
        <AdminPanel title="版本历史">
          {skillVersions?.length ? (
            <ul className="space-y-2">
              {skillVersions.map((ver) => (
                <li key={ver.id} className="flex items-center justify-between rounded-lg border border-white/10 px-3 py-2 text-sm">
                  <span className="text-white font-mono">v{ver.version}</span>
                  <AdminLifecycleBadge status={ver.lifecycle_status} />
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-navy-400">暂无其他版本</p>
          )}
        </AdminPanel>
      ) : null}

      {detailTab === 'stats' ? (
        <AdminPanel title="近 7 日调用统计">
          {skillStats ? (
            <AdminKvGrid
              rows={[
                { label: '调用量', value: skillStats.total_calls ?? 0 },
                { label: '成功率', value: `${((skillStats.success_rate ?? 0) * 100).toFixed(1)}%` },
                { label: '开放缺陷', value: skillStats.open_defects ?? 0 },
                {
                  label: '平均耗时',
                  value: skillStats.avg_duration_ms != null ? `${skillStats.avg_duration_ms} ms` : '—',
                },
              ]}
            />
          ) : (
            <p className="text-sm text-navy-400">暂无统计数据</p>
          )}
        </AdminPanel>
      ) : null}

      {detailTab === 'evolution' ? (
        <AdminEvolution embedded filterSkillId={selected.skill_id} />
      ) : null}

      <AdminJsonDrawer
        open={!!drawer}
        title={drawer?.title || ''}
        value={drawer?.value ?? ''}
        onChange={(v) => setDrawer((d) => (d ? { ...d, value: v } : d))}
        onClose={closeDrawer}
        onSave={saveDrawer}
        language={drawer?.key?.includes('schema') || drawer?.key === 'retry_policy' ? 'json' : 'text'}
      />
    </>
  )
}
