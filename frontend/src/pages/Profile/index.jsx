import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import UserAvatar from '@/components/ui/UserAvatar'
import { Badge } from '@/components/ui'
import { SectionEyebrow } from '@/components/shared/ConsumerSection'
import { pageEnter } from '@/constants/motion'
import { cn } from '@/utils/cn'
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
          <div className="h-32 rounded-2xl border border-white/5 bg-slate-900/60 animate-pulse" />
          <div className="h-96 rounded-2xl border border-white/5 bg-slate-900/60 animate-pulse" />
        </div>
      </div>
    )
  }

  return (
    <motion.div {...pageEnter} className="mx-auto max-w-6xl px-6 py-10">
      <header className="mb-8">
        <SectionEyebrow>个人中心</SectionEyebrow>
        <h1 className="mt-3 text-3xl font-bold text-white">账号与创作概览</h1>
      </header>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-[280px_1fr]">
        <aside className="space-y-3.5">
          <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-5 text-center sticky top-24">
            <div className="inline-block">
              <UserAvatar src={profile.avatar} name={profile.nickname} size="lg" />
            </div>
            <h2 className="mt-3 text-base font-semibold text-white">{profile.nickname}</h2>
            <p className="mt-1 text-xs text-slate-500">{profile.phone}</p>
            <div className="mt-3 flex flex-wrap justify-center gap-1.5">
              <Badge tone={membershipInfo?.is_active ? 'gold' : 'default'}>
                {membershipInfo?.is_active ? membershipInfo?.plan_name || '会员' : membershipInfo?.plan_name || '免费用户'}
              </Badge>
              <Badge tone="info">创作者</Badge>
            </div>

            <div className="mt-5 rounded-xl border border-gold-400/20 bg-gold-400/5 p-4 text-left text-sm">
              <div className="flex justify-between text-navy-200">
                <span>{wallet?.currency_name || '创作币'}余额</span>
                <span className="font-semibold text-gold-400">{wallet?.balance ?? 0}</span>
              </div>
              <div className="mt-3 flex flex-wrap gap-x-3 gap-y-1 text-xs">
                <Link to="/wallet" className="text-gold-400 hover:underline">
                  去充值 →
                </Link>
                <Link to="/orders" className="text-navy-300 hover:text-white hover:underline">
                  我的订单
                </Link>
                <Link to="/member" className="text-navy-300 hover:text-white hover:underline">
                  会员中心
                </Link>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-3 gap-2 text-center">
              <div className="rounded-lg border border-white/5 bg-white/[0.02] p-2">
                <div className="text-lg font-bold text-white">{stats.total}</div>
                <div className="text-[10px] text-slate-500">作品</div>
              </div>
              <div className="rounded-lg border border-white/5 bg-white/[0.02] p-2">
                <div className="text-lg font-bold text-white">{stats.completed}</div>
                <div className="text-[10px] text-slate-500">完成</div>
              </div>
              <div className="rounded-lg border border-white/5 bg-white/[0.02] p-2">
                <div className="text-lg font-bold text-white">{stats.running}</div>
                <div className="text-[10px] text-slate-500">进行中</div>
              </div>
            </div>
          </div>

          <nav className="rounded-2xl border border-white/5 bg-slate-900/60 p-2">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                type="button"
                onClick={() => setActiveTab(tab.key)}
                className={cn(
                  'flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-sm transition-colors',
                  activeTab === tab.key
                    ? 'bg-gold-400/10 text-white'
                    : 'text-slate-300 hover:bg-white/5 hover:text-white',
                )}
              >
                <tab.icon className={cn('w-4 h-4', activeTab === tab.key ? 'text-gold-400' : 'text-slate-400')} />
                {tab.label}
              </button>
            ))}
          </nav>
        </aside>

        <main className="rounded-2xl border border-white/5 bg-slate-900/60 p-5 md:p-6">
          <AnimatePresence mode="wait">
            {activeTab === 'profile' && (
              <motion.div
                key="profile"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-6"
              >
                <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                  <UserCircle2 className="w-6 h-6 text-gold-400" />
                  个人资料
                </h3>

                <div className="space-y-6">
                  {/* 头像 */}
                  <div>
                    <label className="sf-label">头像 URL</label>
                    <div className="flex items-center gap-4">
                      <UserAvatar src={profile.avatar} name={profile.nickname} size="md" />
                      <input
                        type="url"
                        value={profile.avatar}
                        onChange={(e) => setProfile({ ...profile, avatar: e.target.value })}
                        className="sf-control flex-1"
                        placeholder="https://example.com/avatar.png"
                      />
                    </div>
                  </div>

                  {/* 昵称 */}
                  <div>
                    <label className="sf-label">昵称</label>
                    <input
                      type="text"
                      value={profile.nickname}
                      onChange={(e) => setProfile({ ...profile, nickname: e.target.value })}
                      className="sf-control"
                      placeholder="请输入昵称"
                    />
                  </div>

                  {/* 手机号（只读） */}
                  <div>
                    <label className="sf-label">手机号</label>
                    <div className="w-full px-4 py-3 rounded-xl bg-slate-900/40 border border-white/10 text-navy-300">
                      {profile.phone}
                    </div>
                  </div>

                  {/* 个人简介 */}
                  <div>
                    <label className="sf-label">个人简介</label>
                    <textarea
                      value={profile.bio}
                      onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
                      rows={4}
                      className="sf-control resize-none"
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
                <div>
                  <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                    <Lock className="w-6 h-6 text-gold-400" />
                    修改密码
                  </h3>

                  <div className="space-y-5">
                    <div>
                      <label className="sf-label">当前密码</label>
                      <input
                        type="password"
                        value={security.oldPassword}
                        onChange={(e) => setSecurity({ ...security, oldPassword: e.target.value })}
                        className="sf-control"
                        placeholder="请输入当前密码"
                      />
                    </div>
                    <div>
                      <label className="sf-label">新密码</label>
                      <input
                        type="password"
                        value={security.password}
                        onChange={(e) => setSecurity({ ...security, password: e.target.value })}
                        className="sf-control"
                        placeholder="至少8位，包含大小写字母和数字"
                      />
                    </div>
                    <div>
                      <label className="sf-label">确认新密码</label>
                      <input
                        type="password"
                        value={security.confirmPassword}
                        onChange={(e) => setSecurity({ ...security, confirmPassword: e.target.value })}
                        className="sf-control"
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
                className="space-y-6"
              >
                <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                  <BarChart3 className="w-6 h-6 text-gold-400" />
                  作品统计
                </h3>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                  <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
                    <div className="text-sm text-slate-400 mb-2">作品总数</div>
                    <div className="text-3xl font-bold text-white">{stats.total}</div>
                  </div>
                  <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
                    <div className="text-sm text-slate-400 mb-2">已完成</div>
                    <div className="text-3xl font-bold text-green-400">{stats.completed}</div>
                  </div>
                  <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
                    <div className="text-sm text-slate-400 mb-2">进行中</div>
                    <div className="text-3xl font-bold text-gold-400">{stats.running}</div>
                  </div>
                  <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-6">
                    <div className="text-sm text-slate-400 mb-2">失败</div>
                    <div className="text-3xl font-bold text-red-400">{stats.failed}</div>
                  </div>
                </div>

                <div className="flex flex-wrap items-start gap-3 rounded-2xl border border-gold-400/20 bg-gold-400/5 p-4">
                  <ChevronRight className="w-5 h-5 text-gold-400 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-navy-200">
                    数据来自你的创作项目。
                    <Link to="/works" className="ml-1 text-gold-400 hover:underline">我的作品</Link>
                    <span className="text-navy-400 mx-1">·</span>
                    <Link to="/orders" className="text-gold-400 hover:underline">我的订单</Link>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>
    </motion.div>
  )
}
