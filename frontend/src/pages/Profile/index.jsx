import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { toast } from 'sonner'
import UserAvatar from '@/components/ui/UserAvatar'
import { Badge, Button } from '@/components/ui'
import { cn } from '@/utils/cn'
import { renderLucideIcon } from '@/utils/renderLucideIcon'
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
  Coins,
  Receipt,
  Crown,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useWalletStore } from '@/store/walletStore'
import { users, membership as membershipApi, works as worksApi } from '@/services/api'
import { mergeMembershipState } from '@/utils/date'
import PageShell from '@/components/layout/PageShell'

const inputClass = 'w-full px-4 py-3 rounded-xl bg-white/5 border border-white/10 text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-gold-500/50 focus:ring-2 focus:ring-gold-500/20 transition-all'
const labelClass = 'block text-sm font-medium text-slate-300 mb-2'

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
          phone: user?.phone || '',
        })
        if (profileData.status === 'rejected') {
          toast.error('资料加载失败，请稍后刷新')
        }
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
      toast.error(err?.message || '加载资料失败')
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
      <PageShell title="" showBack={false}>
        <div className="min-h-[60vh] flex items-center justify-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
            className="w-12 h-12 rounded-full border-4 border-gold-400 border-t-transparent"
          />
        </div>
      </PageShell>
    )
  }

  return (
    <PageShell
      title="个人中心"
      description="管理你的账号信息、密码安全，查看创作统计"
      backTo="/"
      maxWidth="4xl"
    >
      <div className="grid grid-cols-1 gap-6 md:grid-cols-[260px_1fr]">
        <aside className="space-y-4">
          <div className="rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-sm p-5 text-center">
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

            <div className="mt-5 rounded-xl border border-gold-500/20 bg-gold-500/5 p-4 text-left text-sm">
              <div className="flex justify-between text-slate-300">
                <span className="flex items-center gap-1.5">
                  <Coins className="w-4 h-4 text-gold-400" />
                  {wallet?.currency_name || '创作币'}
                </span>
                <span className="font-semibold text-gold-400">{wallet?.balance ?? 0}</span>
              </div>
              <div className="mt-3 flex flex-wrap gap-x-3 gap-y-2 text-xs">
                <Link to="/wallet" className="text-gold-400 hover:text-gold-300 transition-colors flex items-center gap-1">
                  <Coins className="w-3 h-3" /> 去充值
                </Link>
                <Link to="/orders" className="text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1">
                  <Receipt className="w-3 h-3" /> 订单
                </Link>
                <Link to="/member" className="text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1">
                  <Crown className="w-3 h-3" /> 会员
                </Link>
              </div>
            </div>

            <div className="mt-4 grid grid-cols-3 gap-2 text-center">
              <div className="rounded-lg border border-white/5 bg-white/[0.02] p-2">
                <div className="text-lg font-bold text-white">{stats.total}</div>
                <div className="text-[10px] text-slate-500">作品</div>
              </div>
              <div className="rounded-lg border border-white/5 bg-white/[0.02] p-2">
                <div className="text-lg font-bold text-emerald-400">{stats.completed}</div>
                <div className="text-[10px] text-slate-500">完成</div>
              </div>
              <div className="rounded-lg border border-white/5 bg-white/[0.02] p-2">
                <div className="text-lg font-bold text-gold-400">{stats.running}</div>
                <div className="text-[10px] text-slate-500">进行中</div>
              </div>
            </div>
          </div>

          <nav className="rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-sm p-2">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                type="button"
                onClick={() => setActiveTab(tab.key)}
                className={cn(
                  'flex w-full items-center gap-2.5 rounded-xl px-3 py-2.5 text-left text-sm transition-all',
                  activeTab === tab.key
                    ? 'bg-gold-500/10 text-white'
                    : 'text-slate-400 hover:bg-white/5 hover:text-slate-200',
                )}
              >
                {renderLucideIcon(tab.icon, cn('w-4 h-4', activeTab === tab.key ? 'text-gold-400' : 'text-slate-500'))}
                {tab.label}
              </button>
            ))}
          </nav>
        </aside>

        <main className="rounded-2xl border border-white/10 bg-white/[0.03] backdrop-blur-sm p-5 md:p-6">
          <AnimatePresence mode="wait">
            {activeTab === 'profile' && (
              <motion.div
                key="profile"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-6"
              >
                <h3 className="text-xl font-bold text-white flex items-center gap-3">
                  <UserCircle2 className="w-6 h-6 text-gold-400" />
                  个人资料
                </h3>

                <div className="space-y-6">
                  <div>
                    <label className={labelClass}>头像 URL</label>
                    <div className="flex items-center gap-4">
                      <UserAvatar src={profile.avatar} name={profile.nickname} size="md" />
                      <input
                        type="url"
                        value={profile.avatar}
                        onChange={(e) => setProfile({ ...profile, avatar: e.target.value })}
                        className={inputClass}
                        placeholder="https://example.com/avatar.png"
                      />
                    </div>
                  </div>

                  <div>
                    <label className={labelClass}>昵称</label>
                    <input
                      type="text"
                      value={profile.nickname}
                      onChange={(e) => setProfile({ ...profile, nickname: e.target.value })}
                      className={inputClass}
                      placeholder="请输入昵称"
                    />
                  </div>

                  <div>
                    <label className={labelClass}>手机号</label>
                    <div className="w-full px-4 py-3 rounded-xl bg-white/[0.02] border border-white/5 text-slate-500">
                      {profile.phone || '未绑定手机号'}
                    </div>
                  </div>

                  <div>
                    <label className={labelClass}>个人简介</label>
                    <textarea
                      value={profile.bio}
                      onChange={(e) => setProfile({ ...profile, bio: e.target.value })}
                      rows={4}
                      className={cn(inputClass, 'resize-none')}
                      placeholder="介绍一下你自己..."
                    />
                  </div>

                  <div className="pt-4">
                    <Button
                      variant="gold"
                      size="lg"
                      onClick={handleSaveProfile}
                      disabled={saving}
                      isLoading={saving}
                      iconLeft={!saving && <Save className="w-4 h-4" />}
                    >
                      {saving ? '保存中...' : '保存修改'}
                    </Button>
                  </div>
                </div>
              </motion.div>
            )}

            {activeTab === 'security' && (
              <motion.div
                key="security"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-6"
              >
                <h3 className="text-xl font-bold text-white flex items-center gap-3">
                  <Lock className="w-6 h-6 text-gold-400" />
                  修改密码
                </h3>

                <div className="space-y-5">
                  <div>
                    <label className={labelClass}>当前密码</label>
                    <input
                      type="password"
                      value={security.oldPassword}
                      onChange={(e) => setSecurity({ ...security, oldPassword: e.target.value })}
                      className={inputClass}
                      placeholder="请输入当前密码"
                    />
                  </div>
                  <div>
                    <label className={labelClass}>新密码</label>
                    <input
                      type="password"
                      value={security.password}
                      onChange={(e) => setSecurity({ ...security, password: e.target.value })}
                      className={inputClass}
                      placeholder="至少8位，包含大小写字母和数字"
                    />
                  </div>
                  <div>
                    <label className={labelClass}>确认新密码</label>
                    <input
                      type="password"
                      value={security.confirmPassword}
                      onChange={(e) => setSecurity({ ...security, confirmPassword: e.target.value })}
                      className={inputClass}
                      placeholder="再次输入新密码"
                    />
                  </div>
                  <Button
                    variant="gold"
                    size="lg"
                    onClick={handleChangePassword}
                    disabled={securitySaving}
                    isLoading={securitySaving}
                    iconLeft={!securitySaving && <Shield className="w-4 h-4" />}
                  >
                    {securitySaving ? '更新中…' : '更新密码'}
                  </Button>
                </div>
              </motion.div>
            )}

            {activeTab === 'stats' && (
              <motion.div
                key="stats"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="space-y-6"
              >
                <h3 className="text-xl font-bold text-white flex items-center gap-3">
                  <BarChart3 className="w-6 h-6 text-gold-400" />
                  作品统计
                </h3>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5">
                    <div className="text-sm text-slate-400 mb-2">作品总数</div>
                    <div className="text-2xl font-bold text-white">{stats.total}</div>
                  </div>
                  <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5">
                    <div className="text-sm text-slate-400 mb-2">已完成</div>
                    <div className="text-2xl font-bold text-emerald-400">{stats.completed}</div>
                  </div>
                  <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5">
                    <div className="text-sm text-slate-400 mb-2">进行中</div>
                    <div className="text-2xl font-bold text-gold-400">{stats.running}</div>
                  </div>
                  <div className="rounded-xl border border-white/10 bg-white/[0.03] p-5">
                    <div className="text-sm text-slate-400 mb-2">失败</div>
                    <div className="text-2xl font-bold text-red-400">{stats.failed}</div>
                  </div>
                </div>

                <div className="flex flex-wrap items-start gap-3 rounded-xl border border-gold-500/20 bg-gold-500/5 p-4">
                  <ChevronRight className="w-5 h-5 text-gold-400 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-slate-400">
                    数据来自你的创作项目。
                    <Link to="/works" className="ml-1 text-gold-400 hover:text-gold-300 transition-colors">我的作品</Link>
                    <span className="text-slate-600 mx-1">·</span>
                    <Link to="/orders" className="text-gold-400 hover:text-gold-300 transition-colors">我的订单</Link>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>
    </PageShell>
  )
}
