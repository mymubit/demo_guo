/**
 * 参考实现: 标准管理后台列表页 — ScriptForge 设计体系
 *
 * 本页面展示了如何按照设计规范(模块 4) 创建一个完整的管理页面：
 *
 * ┌─ 标准层级 ───────────────────────────────────────────────────┐
 * │ 1. AdminShell      — 页面壳 (title + description + actions)   │
 * │ 2. ToolbarSearch   — 搜索 + 筛选工具栏                          │
 * │ 3. KpiTile × N    — 数据概览 (标准 KPI 卡片)                    │
 * │ 4. AdminDataTable — 数据表                                     │
 * │ 5. Pagination     — 标准分页                                   │
 * └──────────────────────────────────────────────────────────────┘
 *
 * 可直接复制本文件作为其他管理页面的模板。
 */

import React, { useState, useMemo } from 'react'
import { Plus, Search, ChevronRight, Eye, Edit3, Trash2, Sparkles, TrendingUp, Users } from 'lucide-react'

import AdminShell from '@/components/admin/AdminShell.jsx'
import { ToolbarSearch, KpiTile, AdminDataTable } from '@/components/admin/AdminPrimitives.jsx'
import { Badge } from '@/components/ui/Badge.jsx'
import Button from '@/components/ui/Button.jsx'
import Pagination from '@/components/ui/Pagination.jsx'
import { useToast } from '@/hooks/useToast.js'

// ─── 示例数据 ───────────────────────────────────────────────

const MOCK_ROWS = Array.from({ length: 27 }, (_, i) => ({
  id: `skill-${i + 1}`,
  name: `短剧创作·${['创意激发', '剧本大纲', '分集创作', '台词优化', '反转设计', '分镜脚本'][i % 6]}`,
  type: ['基础能力', '业务技能', '工具能力'][i % 3],
  status: i % 4 === 0 ? 'offline' : i % 4 === 1 ? 'pending' : 'active',
  version: `v1.${i}.${Math.floor(i / 3)}`,
  usage: 120 + i * 37,
  updatedAt: `2024-12-${String(10 + (i % 20)).padStart(2, '0')}`,
  quota: Math.floor(100 + Math.random() * 2000),
}))

// ─── 组件 ─────────────────────────────────────────────────

export default function AdminSkillsPage() {
  const { success, error } = useToast()
  const [page, setPage] = useState(1)
  const [keyword, setKeyword] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')

  const pageSize = 10

  // ── 过滤与分页 ───────────────────────────────────
  const filtered = useMemo(() => {
    return MOCK_ROWS.filter((row) => {
      const matchKeyword =
        !keyword || row.name.toLowerCase().includes(keyword.toLowerCase())
      const matchStatus = statusFilter === 'all' || row.status === statusFilter
      return matchKeyword && matchStatus
    })
  }, [keyword, statusFilter])

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize))
  const paged = filtered.slice((page - 1) * pageSize, page * pageSize)

  // ── 操作 ─────────────────────────────────────────
  const handleNew = () => success('新建技能', '已进入新建技能流程')
  const handleView = (row) => success('查看技能', row.name)
  const handleEdit = (row) => success('编辑技能', row.name)
  const handleDelete = (row) => {
    success('删除技能', `已标记 ${row.name} 为待删除`)
  }

  // ── 列定义 ───────────────────────────────────────
  const columns = [
    {
      key: 'name',
      header: '技能名称',
      render: (row) => (
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-accent-300/80 to-accent-500/80 flex items-center justify-center text-[11px] font-bold text-slate-900 shrink-0">
            {row.name.slice(0, 2)}
          </div>
          <div className="min-w-0">
            <div className="font-medium text-white truncate">{row.name}</div>
            <div className="text-xs text-slate-500 mt-0.5">{row.type}</div>
          </div>
        </div>
      ),
    },
    {
      key: 'version',
      header: '版本',
      render: (row) => (
        <span className="font-mono text-xs text-slate-400">{row.version}</span>
      ),
    },
    {
      key: 'quota',
      header: '调用次数',
      align: 'right',
      render: (row) => (
        <span className="font-mono text-slate-300 tabular-nums">
          {row.quota.toLocaleString()}
        </span>
      ),
    },
    {
      key: 'status',
      header: '状态',
      render: (row) => {
        const map = {
          active: { tone: 'success', label: '已上线' },
          pending: { tone: 'warning', label: '待审核' },
          offline: { tone: 'danger', label: '已下线' },
        }
        const cfg = map[row.status]
        return <Badge tone={cfg.tone}>{cfg.label}</Badge>
      },
    },
    {
      key: 'updatedAt',
      header: '更新时间',
      render: (row) => <span className="text-slate-400 text-xs">{row.updatedAt}</span>,
    },
    {
      key: 'actions',
      header: '操作',
      align: 'right',
      render: (row) => (
        <div className="flex items-center justify-end gap-1">
          <Button size="sm" variant="ghost" iconLeft={<Eye className="w-3.5 h-3.5" />} onClick={() => handleView(row)}>
            查看
          </Button>
          <Button size="sm" variant="ghost" iconLeft={<Edit3 className="w-3.5 h-3.5" />} onClick={() => handleEdit(row)}>
            编辑
          </Button>
          <Button size="sm" variant="ghost" iconLeft={<Trash2 className="w-3.5 h-3.5" />} onClick={() => handleDelete(row)} className="text-danger-300 hover:bg-danger-500/10">
            删除
          </Button>
        </div>
      ),
    },
  ]

  // ── 渲染 ─────────────────────────────────────────

  return (
    <AdminShell
      title="技能管理"
      description="查看、创建和管理短剧创作技能。支持按状态筛选、调用量统计与版本追踪。"
      actions={
        <>
          <Button variant="secondary" iconLeft={<Search className="w-4 h-4" />}>
            高级搜索
          </Button>
          <Button
            variant="brand"
            iconLeft={<Plus className="w-4 h-4" />}
            onClick={handleNew}
          >
            新建技能
          </Button>
        </>
      }
    >
      {/* ── 工具栏：搜索 + 筛选 ────────────────────── */}
      <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-3.5 mb-6 animate-fade-in">
        <div className="flex flex-wrap items-center gap-3">
          <ToolbarSearch
            placeholder="搜索技能名称..."
            value={keyword}
            onChange={(e) => {
              setKeyword(e.target.value)
              setPage(1)
            }}
            width={280}
          />
          <div className="flex flex-wrap gap-1.5">
            {[
              { key: 'all', label: '全部' },
              { key: 'active', label: '已上线' },
              { key: 'pending', label: '待审核' },
              { key: 'offline', label: '已下线' },
            ].map((t) => (
              <button
                key={t.key}
                type="button"
                onClick={() => {
                  setStatusFilter(t.key)
                  setPage(1)
                }}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                  statusFilter === t.key
                    ? 'bg-white/10 text-white border border-white/10'
                    : 'text-slate-400 hover:text-white hover:bg-white/5 border border-transparent'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
          <div className="ml-auto text-xs text-slate-500">
            共 <span className="text-slate-300 font-medium">{filtered.length}</span> 条记录
          </div>
        </div>
      </div>

      {/* ── KPI 概览卡片 ─────────────────────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <KpiTile
          label="技能总数"
          value={MOCK_ROWS.length.toLocaleString()}
          delta="↑ 12% 较上周"
          up
          spark="0,28 15,22 30,25 45,18 60,20 75,12 90,15 105,8 120,10"
        />
        <KpiTile
          label="今日调用"
          value="8,437"
          delta="↑ 5.7% 较昨日"
          up
          gold
          spark="0,20 15,18 30,14 45,16 60,10 75,12 90,6 105,9 120,4"
        />
        <KpiTile
          label="待审核"
          value="7"
          delta="需关注"
          spark="0,15 15,18 30,12 45,14 60,18 75,10 90,14 105,8 120,16"
          hint="预计今日完成审核"
        />
        <KpiTile
          label="活跃贡献者"
          value="42"
          delta="↑ 8 本月新接入"
          up
          spark="0,22 15,18 30,20 45,14 60,12 75,10 90,14 105,8 120,6"
        />
      </div>

      {/* ── 数据表格 ────────────────────────────── */}
      <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-4.5 animate-fade-in">
        <AdminDataTable columns={columns} rows={paged} empty="没有符合条件的技能" />

        {/* ── 分页 ─────────────────────────── */}
        {totalPages > 1 && (
          <div className="mt-4 pt-4 border-t border-white/5">
            <Pagination total={filtered.length} page={page} totalPages={totalPages} onPageChange={setPage} />
          </div>
        )}
      </div>
    </AdminShell>
  )
}
