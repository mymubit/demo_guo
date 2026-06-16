// 参考页面: 标准管理后台页面示例
// 此文件展示了如何按照设计规范 (模块4) 创建一个完整的管理页面
//
// 标准布局:
// 1. AdminShell — 页面壳 (title + description + breadcrumbs + actions)
// 2. AdminToolbar — 顶部筛选工具栏
// 3. AdminKpiCard — 数据概览
// 4. AdminTable — 数据表
// 5. AdminPagination — 分页
//
// 注: 本文件作为设计规范参考实现, 可直接复用为其他页面模板

import React, { useState } from 'react'
import {
  Plus, Search, Trash2, Edit3, Eye, ChevronRight, Sparkles, TrendingUp, Users } from 'lucide-react'

import AdminShell, {
  AdminToolbar,
  AdminTable,
  AdminPagination,
  AdminKpiCard,
} from '@/components/admin/AdminShell.jsx'
import { Badge } from '@/components/ui/Badge.jsx'
import Button from '@/components/ui/Button.jsx'
import { useToast } from '@/hooks/useToast.js'

// 示例数据
const mockRows = Array.from({ length: 12 }, (_, i) => ({
  id: `skill-${i + 1}`,
  name: `短剧创作·${['创意激发', '剧本大纲', '分集创作', '台词优化', '反转设计', '分镜脚本'][i % 6]}`,
  type: ['基础能力', '业务技能', '工具能力'][i % 3],
  status: i % 4 === 0 ? 'offline' : i % 4 === 1 ? 'pending' : 'active',
  version: `v1.${i}.${Math.floor(i / 3)}`,
  usage: 120 + i * 37,
  updatedAt: `2024-12-${String(10 + i).padStart(2, '0')}`,
  quota: Math.floor(Math.random() * 2000),
}))

export default function AdminStandardSkillsPage() {
  const { success } = useToast()
  const [page, setPage] = useState(1)
  const [keyword, setKeyword] = useState('')

  const filtered = mockRows.filter(
    row => !keyword || row.name.toLowerCase().includes(keyword.toLowerCase()),
  )

  const pageSize = 8
  const paged = filtered.slice((page - 1) * pageSize, page * pageSize)

  const handleNew = () => {
    success('新建技能', '已进入新建技能')
  }

  const tableColumns = [
    { key: 'name', title: '技能名称', render: row => (
        <div className="flex items-center gap-2">
          <span className="font-medium text-white">{row.name}</span>
          <Badge tone="default" size="sm">
            {row.type}
          </Badge>
        </div>
      )},
    { key: 'version', title: '版本' },
    { key: 'quota', title: '调用次数', align: 'right', render: row => (
        <span className="font-mono text-slate-300">{row.quota.toLocaleString()}</span>
      ) },
    { key: 'status', title: '状态', render: row => (
        <Badge
          tone={
            row.status === 'active' ? 'success' : row.status === 'pending' ? 'warning' : 'danger'}
        >
          {row.status === 'active' ? '已上线' : row.status === 'pending' ? '待审核' : '已下线'}
        </Badge>
      )},
    { key: 'updatedAt', title: '更新时间' },
    {
      key: 'actions',
      title: '操作',
      align: 'right',
      render: row => (
        <div className="flex items-center gap-1 justify-end">
          <Button size="xs" variant="ghost" iconOnly icon={<Eye className="w-3.5 h-3.5" />}>
            查看
          </Button>
          <Button size="xs" variant="ghost" icon={<Edit3 className="w-3.5 h-3.5" />}>
            编辑
          </Button>
          <Button
            size="xs"
            variant="ghost"
            icon={<Trash2 className="w-3.5 h-3.5 text-danger-300" />}
            onClick={() => success('删除成功')}
          >
            删除
          </Button>
        </div>
      ),
    },
  ]

  return (
    <AdminShell
      title="技能管理"
      description="管理短剧创作平台的全部技能。支持版本管理、上下线操作和使用统计"
      breadcrumbs={[{ label: '创作中心', href: '/admin/creation' }]}
      actions={
        <Button
          variant="brand"
          iconLeft={<Plus className="w-4 h-4" />}
          onClick={handleNew}
        >
          新建技能
        </Button>
      }
      toolbar={
        <AdminToolbar>
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400" />
              <input
                value={keyword}
                onChange={e => setKeyword(e.target.value)}
                placeholder="搜索技能..."
                className="w-64 h-9 pl-9 pr-3 rounded-lg bg-slate-800/60 border border-white/5 text-slate-200 text-sm placeholder:text-slate-500 focus:outline-none focus:border-brand-400/40 focus:bg-slate-800"
              />
            </div>
            <Button size="sm" variant="secondary">
              已上线
            </Button>
            <Button size="sm" variant="secondary">
              待审核
            </Button>
            <Button size="sm" variant="secondary">
              已下线
            </Button>
          </div>
          <Button size="sm" variant="secondary">
            批量操作
          </Button>
        </AdminToolbar>
      }
    >
      {/* KPI 数据卡片 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <AdminKpiCard
          title="技能总数"
          value={mockRows.length}
          trend={12}
          icon={<Sparkles className="w-5 h-5" />}
          variant="brand"
        />
        <AdminKpiCard
          title="已上线"
          value={mockRows.filter(r => r.status === 'active').length}
          trend={8}
          icon={<TrendingUp className="w-5 h-5" />}
          variant="success"
        />
        <AdminKpiCard
          title="本周调用"
          value={'12,480'}
          trend={15}
          icon={<TrendingUp className="w-5 h-5" />}
          variant="accent"
        />
        <AdminKpiCard
          title="活跃用户"
          value={'3,214'}
          trend={-3}
          icon={<Users className="w-5 h-5" />}
          variant="default"
        />
      </div>

      {/* 数据表 */}
      <AdminTable
        columns={tableColumns}
        rows={paged}
        rowKey="id"
        onRowClick={row => console.log('row click:', row)}
      />
      <AdminPagination
        page={page}
        pageSize={pageSize}
        total={filtered.length}
        onChange={setPage}
      />
    </AdminShell>
  )
}
