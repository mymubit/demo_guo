import { useCallback, useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { Shield, ShieldOff, KeyRound } from 'lucide-react'
import { admin } from '@/services/api'
import AdminShell from '@/components/admin/AdminShell'
import AdminDashboardHints from '@/components/admin/AdminDashboardHints'
import {
  AdminToolbar,
  AdminSearchInput,
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
    <AdminShell actions={<AdminDashboardHints scope="users" />}>
      <AdminMessage message={message} onClose={() => setMessage(null)} />

      <AdminToolbar>
        <AdminSearchInput
          value={keyword}
          onChange={(v) => {
            setKeyword(v)
            setPage(1)
          }}
          placeholder="搜索昵称、手机号…"
        />
        <select
          value={filter}
          onChange={(e) => {
            setFilter(e.target.value)
            setPage(1)
          }}
          className="px-4 py-3 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white"
        >
          <option value="all">全部用户</option>
          <option value="member">有效会员</option>
          <option value="free">免费用户</option>
          <option value="active">账号正常</option>
          <option value="inactive">已禁用</option>
        </select>
        <button type="button" onClick={() => refreshUsers()} className="px-4 py-3 rounded-xl bg-navy-800/60 text-navy-200 hover:bg-navy-700/60">
          刷新
        </button>
      </AdminToolbar>

      {loading ? (
        <AdminLoading />
      ) : (
        <>
          <AdminTable
            rowKey="user_id"
            rows={users}
            emptyText="没有匹配的用户"
            columns={[
              {
                key: 'user',
                title: '用户',
                render: (r) => (
                  <div>
                    <div className="text-white font-medium">{r.nickname || '未设置昵称'}</div>
                    <div className="text-xs text-navy-500 font-mono">{r.phone || r.email || '—'}</div>
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
                        <div className="text-[11px] text-navy-500 mt-1">
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
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs bg-navy-800/60 hover:bg-navy-700/60 text-navy-200 disabled:opacity-40"
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
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs bg-navy-800/60 hover:bg-navy-700/60 text-gold-400"
                    >
                      <KeyRound className="w-3.5 h-3.5" />
                      重置密码
                    </button>
                  </div>
                ),
              },
            ]}
          />
          <AdminPagination
            page={pagination?.page || page}
            totalPages={pagination?.total_pages || 1}
            total={pagination?.total || 0}
            onPageChange={setPage}
          />
        </>
      )}

      <AdminConfirmDialog
        open={!!confirm}
        title={confirm?.title}
        message={confirm?.message}
        loading={actionLoading}
        onCancel={() => setConfirm(null)}
        onConfirm={handleConfirm}
      />
    </AdminShell>
  )
}
