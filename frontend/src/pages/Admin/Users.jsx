import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { Shield, ShieldOff, KeyRound, X, FolderKanban } from 'lucide-react'
import { admin } from '@/services/api'
import { adminProjectDetailPath } from '@/utils/adminProjectRoutes'
import AdminShell from '@/components/admin/AdminShell'
import AdminDashboardHints from '@/components/admin/AdminDashboardHints'
import {
  AdminPageHeader,
  AdminPanel,
  ToolbarSearch,
  AdminTable,
  AdminPagination,
  AdminLoading,
  AdminMessage,
  AdminConfirmDialog,
  AdminBadge,
  formatDateTime,
} from '@/components/admin/AdminUI'
import { useAdminUsers } from '@/hooks/queries/useAdminUsers'

export default function UsersAdmin() {
  const queryClient = useQueryClient()
  const [searchParams] = useSearchParams()
  const [keyword, setKeyword] = useState('')
  const [filter, setFilter] = useState(() => searchParams.get('filter') || 'all')
  const [page, setPage] = useState(1)
  const [message, setMessage] = useState(null)
  const [confirm, setConfirm] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [selectedUser, setSelectedUser] = useState(null)
  const [userProjects, setUserProjects] = useState([])
  const [projectsLoading, setProjectsLoading] = useState(false)
  const navigate = useNavigate()

  const { data, isLoading, error, refetch } = useAdminUsers({ page, keyword, filter })
  const users = data?.items ?? []
  const pagination = data?.pagination ?? null
  const loading = isLoading

  const refreshUsers = useCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['adminUsers'] })
    return refetch()
  }, [queryClient, refetch])

  useEffect(() => {
    const f = searchParams.get('filter')
    if (f && ['all', 'member', 'free', 'active', 'inactive'].includes(f)) {
      setFilter(f)
      setPage(1)
    }
  }, [searchParams])

  useEffect(() => {
    if (error) {
      setMessage({ type: 'error', text: error.message || '加载用户失败' })
    }
  }, [error])

  async function openUserDrawer(user) {
    setSelectedUser(user)
    setProjectsLoading(true)
    try {
      const rows = await admin.userRecentProjects(user.user_id)
      setUserProjects(rows)
    } catch {
      setUserProjects([])
    } finally {
      setProjectsLoading(false)
    }
  }

  function closeUserDrawer() {
    setSelectedUser(null)
    setUserProjects([])
  }

  async function handleConfirm() {
    if (!confirm) return
    setActionLoading(true)
    try {
      if (confirm.type === 'toggle') {
        await admin.toggleUserActive(confirm.user.user_id)
        setMessage({ type: 'success', text: confirm.user.is_active ? '用户已禁用' : '用户已启用' })
      } else {
        const res = await admin.resetUserPassword(confirm.user.user_id)
        let copied = false
        if (res?.new_password && navigator.clipboard?.writeText) {
          try {
            await navigator.clipboard.writeText(res.new_password)
            copied = true
          } catch {
            copied = false
          }
        }
        setMessage({
          type: 'success',
          text: copied
            ? '密码已重置，新密码已复制到剪贴板，请通过安全渠道告知用户'
            : '密码已重置，请通过安全渠道告知用户',
        })
      }
      setConfirm(null)
      refreshUsers()
    } catch (err) {
      setMessage({ type: 'error', text: err.message || '操作失败' })
    } finally {
      setActionLoading(false)
    }
  }

  return (
    <AdminShell hideDescription actions={<AdminDashboardHints scope="users" />}>
      <AdminMessage message={message} onClose={() => setMessage(null)} />

      <AdminPageHeader
        crumbs={[{ label: 'Console' }, { label: '用户管理' }]}
        title={`用户 · ${pagination?.total ?? 0}`}
        subtitle="按最近活跃倒序 · 含付费 / 体验 / 企业三档"
        toolbar={
          <>
            <ToolbarSearch
              placeholder="搜索昵称、手机号…"
              value={keyword}
              onChange={(e) => {
                setKeyword(e.target.value)
                setPage(1)
              }}
            />
            <select
              value={filter}
              onChange={(e) => {
                setFilter(e.target.value)
                setPage(1)
              }}
              className="px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-sm text-white"
            >
              <option value="all">全部用户</option>
              <option value="member">有效会员</option>
              <option value="free">免费用户</option>
              <option value="active">账号正常</option>
              <option value="inactive">已禁用</option>
            </select>
            <button
              type="button"
              onClick={() => refreshUsers()}
              className="px-4 py-2 rounded-xl border border-white/10 bg-white/5 text-sm text-slate-200 hover:bg-white/10"
            >
              刷新
            </button>
          </>
        }
      />

      {loading ? (
        <AdminLoading />
      ) : (
        <AdminPanel>
          <AdminTable
            rowKey="user_id"
            rows={users}
            emptyText="没有匹配的用户"
            onRowClick={openUserDrawer}
            columns={[
              {
                key: 'user',
                title: '用户',
                render: (r) => (
                  <div>
                    <div className="text-white font-medium">{r.nickname || '未设置昵称'}</div>
                    <div className="text-xs text-navy-300 font-mono">{r.phone || r.email || '—'}</div>
                  </div>
                ),
              },
              {
                key: 'member',
                title: '会员',
                render: (r) =>
                  r.is_member && r.current_plan ? (
                    <div>
                      <AdminBadge tone="gold">{r.current_plan}</AdminBadge>
                      {r.membership_expires_at && (
                        <div className="text-[11px] text-navy-400 mt-1">
                          至 {formatDateTime(r.membership_expires_at)}
                        </div>
                      )}
                    </div>
                  ) : (
                    <AdminBadge>免费用户</AdminBadge>
                  ),
              },
              {
                key: 'wallet_balance',
                title: '创作币',
                render: (r) => <span className="text-gold-300">{r.wallet_balance ?? 0}</span>,
              },
              {
                key: 'is_active',
                title: '账号',
                render: (r) => (
                  <AdminBadge tone={r.is_active ? 'success' : 'danger'}>
                    {r.is_active ? '正常' : '已禁用'}
                  </AdminBadge>
                ),
              },
              { key: 'order_count', title: '订单' },
              { key: 'created_at', title: '注册', render: (r) => formatDateTime(r.created_at) },
              {
                key: 'actions',
                title: '操作',
                render: (r) => (
                  <div className="flex flex-wrap items-center gap-2">
                    <button
                      type="button"
                      disabled={r.is_superuser}
                      onClick={() =>
                        setConfirm({
                          type: 'toggle',
                          user: r,
                          title: r.is_active ? '禁用用户' : '启用用户',
                          message: `确认${r.is_active ? '禁用' : '启用'}用户 ${r.nickname || r.phone}？`,
                        })
                      }
                      className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-navy-200 hover:bg-white/[0.06] disabled:opacity-40"
                    >
                      {r.is_active ? <ShieldOff className="w-3.5 h-3.5" /> : <Shield className="w-3.5 h-3.5" />}
                      {r.is_active ? '禁用' : '启用'}
                    </button>
                    <button
                      type="button"
                      onClick={() =>
                        setConfirm({
                          type: 'reset',
                          user: r,
                          title: '重置密码',
                          message: `将为 ${r.nickname || r.phone} 生成新的随机密码，请妥善告知用户。`,
                        })
                      }
                      className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-gold-400 hover:bg-white/[0.06]"
                    >
                      <KeyRound className="w-3.5 h-3.5" />
                      重置密码
                    </button>
                  </div>
                ),
              },
            ]}
          />
          <div className="mt-4">
            <AdminPagination
              page={pagination?.page || page}
              totalPages={pagination?.total_pages || 1}
              total={pagination?.total || 0}
              onPageChange={setPage}
            />
          </div>
        </AdminPanel>
      )}

      <AdminConfirmDialog
        open={!!confirm}
        title={confirm?.title}
        message={confirm?.message}
        loading={actionLoading}
        onCancel={() => setConfirm(null)}
        onConfirm={handleConfirm}
      />

      {selectedUser ? (
        <div className="fixed inset-0 z-[80] flex justify-end bg-black/50">
          <div className="w-full max-w-md h-full sf-console-panel border-l border-white/10 p-5 overflow-y-auto shadow-2xl">
            <div className="flex items-start justify-between gap-3 mb-4">
              <div>
                <h3 className="text-lg font-semibold text-white">{selectedUser.nickname || '用户'}</h3>
                <p className="text-xs text-navy-400 font-mono mt-1">{selectedUser.phone || selectedUser.email}</p>
              </div>
              <button type="button" onClick={closeUserDrawer} className="text-navy-400 hover:text-white p-1">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="rounded-xl border border-white/5 bg-slate-900/40 p-4 mb-4 text-sm space-y-2">
              <p className="text-navy-400">创作币 <span className="text-gold-300">{selectedUser.wallet_balance ?? 0}</span></p>
              <p className="text-navy-400">订单 {selectedUser.order_count ?? 0} · 注册 {formatDateTime(selectedUser.created_at)}</p>
            </div>
            <h4 className="text-sm font-medium text-white flex items-center gap-2 mb-3">
              <FolderKanban className="w-4 h-4 text-gold-400" />
              该用户的创作项目
            </h4>
            {projectsLoading ? (
              <p className="text-sm text-navy-400">加载中…</p>
            ) : userProjects.length ? (
              <ul className="space-y-2">
                {userProjects.map((row) => (
                  <li key={row.project_id}>
                    <button
                      type="button"
                      onClick={() => {
                        closeUserDrawer()
                        navigate(adminProjectDetailPath(row.project_id, 'basic'))
                      }}
                      className="w-full text-left rounded-xl border border-white/5 bg-slate-900/40 px-3 py-2.5 hover:bg-white/[0.04]"
                    >
                      <p className="text-sm text-white truncate">{row.title}</p>
                      <p className="text-xs text-navy-400 mt-0.5">{row.status_text || row.status}</p>
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-navy-400">暂无创作项目</p>
            )}
          </div>
        </div>
      ) : null}
    </AdminShell>
  )
}
