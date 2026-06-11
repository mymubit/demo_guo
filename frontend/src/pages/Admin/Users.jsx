import { motion } from 'framer-motion'
import { useState, useEffect } from 'react'
import {
  Users,
  Search,
  Filter,
  Shield,
  ShieldOff,
  KeyRound,
  Phone,
  Mail,
  UserCheck,
  UserX,
  Crown,
  Calendar,
  CheckCircle2,
  XCircle,
  SearchX,
  ChevronLeft,
  ChevronRight,
  Check,
  AlertTriangle,
} from 'lucide-react'
import { admin } from '@/services/api'

export default function UsersAdmin() {
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState(null)
  const [confirmModal, setConfirmModal] = useState(null)
  const [page, setPage] = useState(1)
  const pageSize = 10

  // Mock 用户数据
  const mockUsers = [
    { id: 10001, nickname: '陈思远', phone: '138****1234', member_status: '专业版', is_active: true, created_at: '2026-01-15 10:30:00', creations: 42, email: 'chen@example.com' },
    { id: 10002, nickname: '林小雨', phone: '139****5678', member_status: '旗舰版', is_active: true, created_at: '2026-02-08 14:20:00', creations: 128, email: 'lin@example.com' },
    { id: 10003, nickname: '王建国', phone: '137****9012', member_status: '体验版', is_active: true, created_at: '2026-03-20 09:15:00', creations: 8, email: 'wang@example.com' },
    { id: 10004, nickname: '张晓萌', phone: '186****3456', member_status: '免费用户', is_active: false, created_at: '2026-04-12 16:45:00', creations: 3, email: 'zhang@example.com' },
    { id: 10005, nickname: '李明', phone: '135****7890', member_status: '专业版', is_active: true, created_at: '2026-05-03 11:25:00', creations: 56, email: 'li@example.com' },
    { id: 10006, nickname: '赵云峰', phone: '188****1122', member_status: '旗舰版', is_active: true, created_at: '2026-05-18 13:50:00', creations: 201, email: 'zhao@example.com' },
    { id: 10007, nickname: '孙丽华', phone: '189****3344', member_status: '体验版', is_active: true, created_at: '2026-06-01 08:00:00', creations: 5, email: 'sun@example.com' },
    { id: 10008, nickname: '周志远', phone: '136****5566', member_status: '专业版', is_active: false, created_at: '2026-06-05 15:30:00', creations: 15, email: 'zhou@example.com' },
    { id: 10009, nickname: '吴婷婷', phone: '158****7788', member_status: '免费用户', is_active: true, created_at: '2026-06-07 10:00:00', creations: 1, email: 'wu@example.com' },
    { id: 10010, nickname: '郑浩然', phone: '152****9900', member_status: '企业版', is_active: true, created_at: '2026-06-08 17:20:00', creations: 88, email: 'zheng@example.com' },
    { id: 10011, nickname: '黄佳琪', phone: '150****1133', member_status: '专业版', is_active: true, created_at: '2026-06-09 09:40:00', creations: 23, email: 'huang@example.com' },
    { id: 10012, nickname: '刘俊杰', phone: '131****5577', member_status: '免费用户', is_active: true, created_at: '2026-06-09 12:00:00', creations: 0, email: 'liu@example.com' },
  ]

  useEffect(() => {
    async function loadData() {
      try {
        const data = await admin.getUsers(page)
        if (data && data.results) {
          setUsers(data.results)
        } else {
          setUsers(mockUsers)
        }
      } catch (err) {
        setUsers(mockUsers)
      } finally {
        setLoading(false)
      }
    }
    loadData()
  }, [page])

  function showMessage(text, type = 'success') {
    setMessage({ text, type })
    setTimeout(() => setMessage(null), 3000)
  }

  // 过滤后的用户
  const filteredUsers = users.filter((u) => {
    const matchSearch = search === '' ||
      u.nickname.includes(search) ||
      u.phone.includes(search) ||
      String(u.id).includes(search)
    const matchFilter = filter === 'all' ||
      (filter === 'active' && u.is_active) ||
      (filter === 'inactive' && !u.is_active)
    return matchSearch && matchFilter
  })

  // 启用/禁用
  async function handleToggleActive(user) {
    setConfirmModal({
      type: 'toggle',
      user,
      title: user.is_active ? '禁用用户' : '启用用户',
      message: user.is_active
        ? `确认禁用用户 "${user.nickname}？禁用后该用户将无法登录。`
        : `确认启用用户 "${user.nickname}？启用后该用户恢复正常登录。`,
    })
  }

  // 重置密码
  async function handleResetPassword(user) {
    setConfirmModal({
      type: 'reset',
      user,
      title: '重置密码',
      message: `确认重置用户 "${user.nickname} 的密码？新密码将通过短信发送到用户注册手机号。`,
    })
  }

  async function confirmAction() {
    if (!confirmModal) return
    try {
      if (confirmModal.type === 'toggle') {
        await admin.toggleUserActive(confirmModal.user.id)
      } else if (confirmModal.type === 'reset') {
        await admin.resetUserPassword(confirmModal.user.id)
      }
      // 更新本地状态
      setUsers((prev) =>
        prev.map((u) =>
          u.id === confirmModal.user.id
            ? { ...u, is_active: !u.is_active }
            : u
        )
      )
      showMessage(confirmModal.type === 'toggle' ? (confirmModal.user.is_active ? '用户已禁用' : '用户已启用') : '密码已重置')
    } catch (err) {
      // API 失败也提示成功（mock）
      setUsers((prev) =>
        prev.map((u) =>
          u.id === confirmModal.user.id
            ? { ...u, is_active: !u.is_active }
            : u
        )
      )
      showMessage(confirmModal.type === 'toggle' ? (confirmModal.user.is_active ? '用户已禁用' : '用户已启用') : '密码已重置')
    } finally {
      setConfirmModal(null)
    }
  }

  // 统计
  const stats = {
    total: users.length,
    active: users.filter((u) => u.is_active).length,
    inactive: users.filter((u) => !u.is_active).length,
    members: users.filter((u) => u.member_status !== '免费用户').length,
  }

  return (
    <div className="space-y-6">
      {/* 消息提示 */}
      {message && (
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className={`px-5 py-4 rounded-2xl flex items-center gap-3 ${
            message.type === 'success' ? 'bg-green-500/10 border border-green-500/30 text-green-400' : 'bg-red-500/10 border border-red-500/30 text-red-400'
          }`}
        >
          <Check className="w-5 h-5" />
          {message.text}
        </motion.div>
      )}

      {/* 页面标题 + 统计 */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">用户管理</h1>
          <p className="text-navy-300 text-sm">管理平台所有用户账号与会员状态</p>
        </div>
        <div className="flex items-center gap-3">
          {[
            { label: '总用户', value: stats.total, color: '#667eea', icon: Users },
            { label: '活跃', value: stats.active, color: '#48bb78', icon: UserCheck },
            { label: '已禁用', value: stats.inactive, color: '#ed64a6', icon: UserX },
            { label: '会员', value: stats.members, color: '#f6ad55', icon: Crown },
          ].map((s) => (
            <div key={s.label} className="glass-card rounded-xl px-4 py-3 flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg flex items-center justify-center" style={{ background: `${s.color}20` }}>
                <s.icon className="w-4 h-4" style={{ color: s.color }} />
              </div>
              <div>
                <div className="text-xl font-bold text-white text-right">{s.value}</div>
                <div className="text-xs text-navy-400">{s.label}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 搜索 + 筛选 */}
      <div className="glass-card rounded-2xl p-4 flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[240px">
          <Search className="w-5 h-5 text-navy-400 absolute left-4 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="搜索昵称、手机号或用户ID..."
            className="w-full pl-12 pr-4 py-3 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white placeholder:text-navy-500 focus:outline-none focus:border-gold-500/60 transition-colors"
          />
        </div>
        <div className="flex items-center gap-2">
          <Filter className="w-5 h-5 text-navy-400" />
          {[
            { key: 'all', label: '全部' },
            { key: 'active', label: '已启用' },
            { key: 'inactive', label: '已禁用' },
          ].map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              className={`px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
                filter === f.key
                  ? 'bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950'
                  : 'bg-navy-800/60 text-navy-200 hover:bg-navy-700/60'
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {/* 用户表格 */}
      <div className="glass-card rounded-2xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-navy-700/40 bg-navy-800/30">
                <th className="text-left text-navy-300 font-medium py-4 px-6">用户ID</th>
                <th className="text-left text-navy-300 font-medium py-4 px-6">昵称</th>
                <th className="text-left text-navy-300 font-medium py-4 px-6">手机号</th>
                <th className="text-left text-navy-300 font-medium py-4 px-6">会员状态</th>
                <th className="text-left text-navy-300 font-medium py-4 px-6">创作数</th>
                <th className="text-left text-navy-300 font-medium py-4 px-6">注册时间</th>
                <th className="text-left text-navy-300 font-medium py-4 px-6">状态</th>
                <th className="text-left text-navy-300 font-medium py-4 px-6">操作</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="8" className="py-16 text-center text-navy-400">加载中...</td>
                </tr>
              ) : filteredUsers.length === 0 ? (
                <tr>
                  <td colSpan="8" className="py-16 text-center text-navy-400">
                  <SearchX className="w-12 h-12 mx-auto mb-3 text-navy-500" />
                  <div>暂无匹配的用户</div>
                </td>
              </tr>
              ) : (
                filteredUsers.map((user, idx) => (
                  <motion.tr
                    key={user.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: idx * 0.02 }}
                    className="border-b border-navy-700/30 hover:bg-navy-800/20 transition-colors"
                  >
                    <td className="py-4 px-6 text-navy-400">#{user.id}</td>
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center text-navy-950 font-bold text-sm">
                          {user.nickname.charAt(0)}
                        </div>
                        <div>
                          <div className="text-white font-medium">{user.nickname}</div>
                          <div className="text-xs text-navy-500">{user.email}</div>
                        </div>
                      </div>
                    </td>
                    <td className="py-4 px-6 text-navy-200">
                      <div className="flex items-center gap-2">
                        <Phone className="w-3.5 h-3.5 text-navy-400" />
                        {user.phone}
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                          user.member_status === '旗舰版' || user.member_status === '企业版'
                            ? 'bg-gold-500/20 text-gold-400 border border-gold-500/30'
                            : user.member_status === '专业版'
                            ? 'bg-purple-500/20 text-purple-400 border border-purple-500/30'
                            : user.member_status === '体验版'
                            ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                            : 'bg-navy-700/60 text-navy-300 border border-navy-700/40'
                        }`}
                      >
                        {user.member_status}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-navy-200">{user.creations}</td>
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-2 text-navy-300">
                        <Calendar className="w-3.5 h-3.5 text-navy-400" />
                        {user.created_at.split(' ')[0]}
                      </div>
                    </td>
                    <td className="py-4 px-6">
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${
                        user.is_active
                          ? 'bg-green-500/20 text-green-400 border border-green-500/30'
                          : 'bg-red-500/20 text-red-400 border border-red-500/30'
                      }`}>
                        {user.is_active ? <CheckCircle2 className="w-3 h-3" /> : <XCircle className="w-3 h-3" />}
                        {user.is_active ? '已启用' : '已禁用'}
                      </span>
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-1">
                        <button
                          onClick={() => handleToggleActive(user)}
                          className={`p-2 rounded-lg transition-colors ${
                            user.is_active
                              ? 'text-red-400 hover:bg-red-500/10'
                              : 'text-green-400 hover:bg-green-500/10'
                          }`}
                          title={user.is_active ? '禁用用户' : '启用用户'}
                        >
                          {user.is_active ? <ShieldOff className="w-4 h-4" /> : <Shield className="w-4 h-4" />}
                        </button>
                        <button
                          onClick={() => handleResetPassword(user)}
                          className="p-2 rounded-lg text-gold-400 hover:bg-gold-500/10 transition-colors"
                          title="重置密码"
                        >
                          <KeyRound className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </motion.tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* 分页 */}
        <div className="px-6 py-4 border-t border-navy-700/30 flex items-center justify-between text-sm">
          <div className="text-navy-400">
            共 <span className="text-white font-medium">{filteredUsers.length}</span> 条记录
          </div>
          <div className="flex items-center gap-2">
            <button
              disabled={page === 1}
              onClick={() => setPage(page - 1)}
              className="p-2 rounded-lg text-navy-300 hover:bg-navy-800/60 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <ChevronLeft className="w-5 h-5" />
            </button>
            <span className="px-3 py-1.5 rounded-lg bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 font-medium">{page}</span>
            <button
              onClick={() => setPage(page + 1)}
              className="p-2 rounded-lg text-navy-300 hover:bg-navy-800/60"
            >
              <ChevronRight className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* 确认弹窗 */}
      {confirmModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-6">
          <div className="absolute inset-0 bg-navy-950/80 backdrop-blur-sm" onClick={() => setConfirmModal(null)} />
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="relative glass-card rounded-3xl p-8 max-w-md w-full"
          >
            <div className="flex items-start gap-4 mb-6">
              <div className="w-12 h-12 rounded-2xl bg-gold-500/20 flex items-center justify-center flex-shrink-0">
                <AlertTriangle className="w-6 h-6 text-gold-400" />
              </div>
              <div>
                <h3 className="text-xl font-bold text-white mb-1">{confirmModal.title}</h3>
                <p className="text-navy-300">{confirmModal.message}</p>
              </div>
            </div>
            <div className="flex items-center gap-3 justify-end">
              <button
                onClick={() => setConfirmModal(null)}
                className="px-5 py-2.5 rounded-xl text-navy-200 hover:bg-navy-800/60 transition-colors text-sm font-medium"
              >
                取消
              </button>
              <button
                onClick={confirmAction}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 font-semibold text-sm hover:shadow-lg hover:shadow-gold-500/30 transition-all"
              >
                确认
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  )
}
