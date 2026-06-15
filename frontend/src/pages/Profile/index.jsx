import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { toast } from 'sonner'
import UserAvatar from '@/components/ui/UserAvatar'
import {
  UserCircle2,
  Shield,
  BarChart3,
  Pencil,
  Save,
  Lock,
  Film,
  Star,
  ChevronRight,
  Check,
  Loader2,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useWalletStore } from '@/store/walletStore'
import { users, membership as membershipApi, works as worksApi } from '@/services/api'
import { formatDate, mergeMembershipState } from '@/utils/date'

export default function Profile() {
  const [activeTab, setActiveTab] = useState('profile')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [securitySaving, setSecuritySaving] = useState(false)
  const [profile, setProfile] = useState({
    nickname: '',
    avatar: '',
    bio: '',
    phone: '',
  })
  const [membershipInfo, setMembershipInfo] = useState(null)
  const [stats, setStats] = useState({
    total: 0,
    completed: 0,
    running: 0,
    failed: 0,
  })
  const [security, setSecurity] = useState({
    oldPassword: '',
    password: '',
    confirmPassword: '',
  })
  const { user, updateProfile } = useAuthStore()
  const { wallet, fetchWallet } = useWalletStore()

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      const [profileData, memberData, summaryData, statsData] = await Promise.allSettled([
        users.me(),
        membershipApi.myMembership(),
        membershipApi.summary(),
        worksApi.stats(),
        fetchWallet(),
      ])

      if (profileData.status === 'fulfilled' && profileData.value) {
        const p = profileData.value
        setProfile({
          nickname: p.nickname || user?.nickname || '创作者',
          avatar: p.avatar_url || user?.avatar || '',
          bio: p.bio || '热爱创作，用剧本讲述精彩故事',
          phone: p.phone || user?.phone || '',
        })
      } else {
        setProfile({
          nickname: user?.nickname || '创作者',
          avatar: user?.avatar || '',
          bio: '热爱创作，用剧本讲述精彩故事',
          phone: user?.phone || '138****8888',
        })
      }

      const memberRaw = memberData.status === 'fulfilled' ? memberData.value : null
      const summaryRaw = summaryData.status === 'fulfilled' ? summaryData.value : null
      setMembershipInfo(
        mergeMembershipState(memberRaw, summaryRaw, {
          plan_name: '免费用户',
          end_at: null,
          remaining_creations: 0,
          is_active: false,
          wallet: { balance: 0, currency_name: '创作币' },
        })
      )

      if (statsData.status === 'fulfilled' && statsData.value) {
        const s = statsData.value
        setStats({
          total: s.total || 0,
          completed: s.completed || 0,
          running: s.running || 0,
          failed: s.failed || 0,
        })
      }
    } catch (err) {
      setProfile({
        nickname: user?.nickname || '创作者',
        avatar: user?.avatar || '',
        bio: '热爱创作，用剧本讲述精彩故事',
        phone: user?.phone || '',
      })
      setMembershipInfo({
        plan_name: '免费用户',
        end_at: null,
        remaining_creations: 0,
        is_active: false,
      })
    } finally {
      setLoading(false)
    }
  }

  async function handleSaveProfile() {
    if (saving) return
    setSaving(true)
    try {
      await users.updateProfile(profile)
      updateProfile(profile)
      toast.success('保存成功')
    } catch (err) {
      toast.error(err.message || '保存失败')
    } finally {
      setSaving(false)
    }
  }

  async function handleChangePassword() {
    if (securitySaving) return
    if (!security.oldPassword) {
      toast.error('请输入当前密码')
      return
    }
    if (!security.password) {
      toast.error('请输入新密码')
      return
    }
    if (security.password.length < 8) {
      toast.error('新密码至少 8 位')
      return
    }
    if (security.password !== security.confirmPassword) {
      toast.error('两次输入的密码不一致')
      return
    }
    setSecuritySaving(true)
    try {
      await users.changePassword({
        old_password: security.oldPassword,
        new_password: security.password,
        new_password_confirm: security.confirmPassword,
      })
      setSecurity({ oldPassword: '', password: '', confirmPassword: '' })
      toast.success('密码修改成功')
    } catch (err) {
      toast.error(err.message || '密码修改失败')
    } finally {
      setSecuritySaving(false)
    }
  }

  const tabs = [
    { key: 'profile', label: '资料修改', icon: Pencil },
    { key: 'security', label: '安全设置', icon: Shield },
    { key: 'stats', label: '作品统计', icon: BarChart3 },
  ]

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="animate-pulse space-y-6">
          <div className="h-32 glass-card rounded-3xl" />
          <div className="h-96 glass-card rounded-3xl" />
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-12">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* 左侧 - 用户信息卡片 */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="lg:col-span-4"
        >
          <div className="glass-card rounded-3xl p-8 sticky top-24">
            {/* 头像 */}
            <div className="text-center mb-8">
              <div className="inline-block">
                <UserAvatar src={profile.avatar} name={profile.nickname} size="lg" />
              </div>
              <h2 className="text-2xl font-bold text-white mt-4">{profile.nickname}</h2>
              <p className="text-navy-300 text-sm mt-1">{profile.phone}</p>
            </div>

            {/* 会员信息 */}
            <div className="p-6 rounded-2xl bg-gradient-to-br from-gold-500/10 to-gold-600/5 border border-gold-500/20 mb-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-gold-500/20 flex items-center justify-center">
                  <Star className="w-5 h-5 text-gold-400 fill-gold-400" />
                </div>
                <div>
                  <div className="font-bold text-gold-400">
                    {membershipInfo?.is_active
                      ? membershipInfo?.plan_name || '会员'
                      : membershipInfo?.plan_name || '免费用户'}
                  </div>
                  <div className="text-xs text-navy-300">
                    有效期至{' '}
                    {membershipInfo?.is_active && membershipInfo?.end_at
                      ? formatDate(membershipInfo.end_at)
                      : '未开通'}
                  </div>
                </div>
              </div>
              <div className="text-sm text-navy-200">
                <div className="flex justify-between mb-2">
                  <span>{wallet?.currency_name || membershipInfo?.wallet?.currency_name || '创作币'}余额</span>
                  <span className="font-semibold text-gold-400">
                    {wallet?.balance ?? membershipInfo?.wallet?.balance ?? 0}
                  </span>
                </div>
                <div className="text-xs text-navy-400 mb-3">
                  创作按节点扣费，开通会员赠送创作币
                </div>
                <Link
                  to="/wallet"
                  className="inline-flex items-center gap-1 text-sm text-gold-400 hover:underline"
                >
                  去充值 →
                </Link>
              </div>
            </div>

            {/* 快捷统计 */}
            <div className="grid grid-cols-3 gap-3">
              <div className="text-center p-4 rounded-xl bg-navy-800/40">
                <Film className="w-5 h-5 mx-auto mb-2 text-purple-400" />
                <div className="text-xl font-bold text-white">{stats.total}</div>
                <div className="text-xs text-navy-300">作品</div>
              </div>
              <div className="text-center p-4 rounded-xl bg-navy-800/40">
                <Check className="w-5 h-5 mx-auto mb-2 text-green-400" />
                <div className="text-xl font-bold text-white">{stats.completed}</div>
                <div className="text-xs text-navy-300">已完成</div>
              </div>
              <div className="text-center p-4 rounded-xl bg-navy-800/40">
                <Loader2 className="w-5 h-5 mx-auto mb-2 text-gold-400" />
                <div className="text-xl font-bold text-white">{stats.running}</div>
                <div className="text-xs text-navy-300">进行中</div>
              </div>
            </div>
          </div>
        </motion.div>

        {/* 右侧 - Tab 内容 */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="lg:col-span-8"
        >
          {/* Tab 切换 */}
          <div className="flex gap-2 mb-6 p-1 glass-card rounded-2xl">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-medium transition-all ${
                  activeTab === tab.key
                    ? 'bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 shadow-lg shadow-gold-500/30'
                    : 'text-navy-200 hover:bg-navy-800/50'
                }`}
              >
                <tab.icon className="w-4 h-4" />
                {tab.label}
              </button>
            ))}
          </div>

          {/* 资料修改 */}
          <AnimatePresence mode="wait">
            {activeTab === 'profile' && (
              <motion.div
                key="profile"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="glass-card rounded-3xl p-8"
              >
                <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                  <UserCircle2 className="w-6 h-6 text-gold-400" />
                  个人资料
                </h3>

                <div className="space-y-6">
                  {/* 头像 */}
                  <div>
                    <label className="block text-sm font-medium text-navy-200 mb-3">头像 URL</label>
                    <div className="flex items-center gap-4">
                      <UserAvatar src={profile.avatar} name={profile.nickname} size="md" />
                      <input
                        type="url"
                        value={profile.avatar}
                        onChange={(e) => setProfile({ ...profile, avatar: e.target.value })}
                        className="flex-1 px-4 py-3 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white focus:outline-none focus:border-gold-500/60 transition-colors"
                        placeholder="https://example.com/avatar.png"
                      />
                    </div>
                  </div>

                  {/* 昵称 */}
                  <div>
                    <label className="block text-sm font-medium text-navy-200 mb-3">昵称</label>
                    <input
                      type="text"
                      value={profile.nickname}
                      onChange={(e) => setProfile({ ...profile, nickname: e.target.value })}
                      className="w-full px-4 py-3 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white focus:outline-none focus:border-gold-500/60 transition-colors"
                      placeholder="请输入昵称"
                    />
                  </div>

                  {/* 手机号（只读） */}
                  <div>
                    <label className="block text-sm font-medium text-navy-200 mb-3">手机号</label>
                    <div className="w-full px-4 py-3 rounded-xl bg-navy-900/40 border border-navy-700/20 text-navy-300">
                      {profile.phone}
                    </div>
                  </div>

                  {/* 个人简介 */}
                  <div>
                    <label className="block text-sm font-medium text-navy-200 mb-3">个人简介</label>
                    <textarea
                      value={profile.bio}
                      onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
                      rows={4}
                      className="w-full px-4 py-3 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white focus:outline-none focus:border-gold-500/60 transition-colors resize-none"
                      placeholder="介绍一下你自己..."
                    />
                  </div>

                  <div className="pt-4">
                    <button
                      onClick={handleSaveProfile}
                      disabled={saving}
                      className="btn-gold !py-3 inline-flex items-center gap-2 disabled:opacity-60"
                    >
                      {saving ? (
                        <>
                          <div className="w-4 h-4 border-2 border-navy-950/30 border-t-navy-950 rounded-full animate-spin" />
                          保存中...
                        </>
                      ) : (
                        <>
                          <Save className="w-4 h-4" />
                          保存修改
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </motion.div>
            )}

            {/* 安全设置 */}
            {activeTab === 'security' && (
              <motion.div
                key="security"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-6"
              >
                {/* 修改密码 */}
                <div className="glass-card rounded-3xl p-8">
                  <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                    <Lock className="w-6 h-6 text-gold-400" />
                    修改密码
                  </h3>

                  <div className="space-y-5">
                    <div>
                      <label className="block text-sm font-medium text-navy-200 mb-3">当前密码</label>
                      <input
                        type="password"
                        value={security.oldPassword}
                        onChange={(e) => setSecurity({ ...security, oldPassword: e.target.value })}
                        className="w-full px-4 py-3 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white focus:outline-none focus:border-gold-500/60 transition-colors"
                        placeholder="请输入当前密码"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-navy-200 mb-3">新密码</label>
                      <input
                        type="password"
                        value={security.password}
                        onChange={(e) => setSecurity({ ...security, password: e.target.value })}
                        className="w-full px-4 py-3 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white focus:outline-none focus:border-gold-500/60 transition-colors"
                        placeholder="至少8位，包含大小写字母和数字"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-navy-200 mb-3">确认新密码</label>
                      <input
                        type="password"
                        value={security.confirmPassword}
                        onChange={(e) => setSecurity({ ...security, confirmPassword: e.target.value })}
                        className="w-full px-4 py-3 rounded-xl bg-navy-800/60 border border-navy-700/40 text-white focus:outline-none focus:border-gold-500/60 transition-colors"
                        placeholder="再次输入新密码"
                      />
                    </div>
                    <button
                      onClick={handleChangePassword}
                      disabled={securitySaving}
                      className="btn-gold !py-3 inline-flex items-center gap-2 disabled:opacity-60"
                    >
                      {securitySaving ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          更新中…
                        </>
                      ) : (
                        <>
                          <Shield className="w-4 h-4" />
                          更新密码
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </motion.div>
            )}

            {/* 作品统计 */}
            {activeTab === 'stats' && (
              <motion.div
                key="stats"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="glass-card rounded-3xl p-8"
              >
                <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                  <BarChart3 className="w-6 h-6 text-gold-400" />
                  作品统计
                </h3>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                  <div className="p-6 rounded-2xl bg-navy-800/40">
                    <div className="text-sm text-navy-300 mb-2">作品总数</div>
                    <div className="text-3xl font-bold text-white">{stats.total}</div>
                  </div>
                  <div className="p-6 rounded-2xl bg-navy-800/40">
                    <div className="text-sm text-navy-300 mb-2">已完成</div>
                    <div className="text-3xl font-bold text-green-400">{stats.completed}</div>
                  </div>
                  <div className="p-6 rounded-2xl bg-navy-800/40">
                    <div className="text-sm text-navy-300 mb-2">进行中</div>
                    <div className="text-3xl font-bold text-gold-400">{stats.running}</div>
                  </div>
                  <div className="p-6 rounded-2xl bg-navy-800/40">
                    <div className="text-sm text-navy-300 mb-2">失败</div>
                    <div className="text-3xl font-bold text-red-400">{stats.failed}</div>
                  </div>
                </div>

                <div className="p-4 rounded-2xl bg-gold-500/10 border border-gold-500/20 flex items-start gap-3">
                  <ChevronRight className="w-5 h-5 text-gold-400 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-navy-200">
                    数据来自你的创作项目。可在「我的作品」查看详情与下载剧本。
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </div>
    </div>
  )
}
