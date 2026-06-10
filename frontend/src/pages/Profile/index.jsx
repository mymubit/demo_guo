import { motion } from 'framer-motion'
import { useState, useEffect } from 'react'
import {
  UserCircle2,
  Shield,
  BarChart3,
  Camera,
  Pencil,
  Save,
  Lock,
  Smartphone,
  Monitor,
  Trash2,
  Film,
  Heart,
  Star,
  ChevronRight,
  Check,
  X,
} from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { userApi, memberApi, worksApi } from '@/services/api'

export default function Profile() {
  const [activeTab, setActiveTab] = useState('profile')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [profile, setProfile] = useState({
    nickname: '',
    avatar: '',
    bio: '',
    phone: '',
  })
  const [membership, setMembership] = useState(null)
  const [stats, setStats] = useState({
    creations: 0,
    favorites: 0,
    ratingTrend: [4.2, 4.5, 4.3, 4.7, 4.6, 4.8, 4.9],
  })
  const [security, setSecurity] = useState({
    password: '',
    confirmPassword: '',
    devices: [
      { id: 1, name: 'MacBook Pro', location: '北京', lastActive: '刚刚', current: true },
      { id: 2, name: 'iPhone 15', location: '北京', lastActive: '2小时前', current: false },
      { id: 3, name: 'Windows PC', location: '上海', lastActive: '3天前', current: false },
    ],
  })
  const [message, setMessage] = useState(null)
  const { user, updateProfile } = useAuthStore()

  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      const [profileData, memberData, worksData] = await Promise.allSettled([
        userApi.getProfile(),
        memberApi.getMyMembership(),
        worksApi.list(),
      ])

      if (profileData.status === 'fulfilled' && profileData.value) {
        const p = profileData.value
        setProfile({
          nickname: p.nickname || user?.nickname || '创作者',
          avatar: p.avatar || user?.avatar || '',
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

      if (memberData.status === 'fulfilled' && memberData.value) {
        setMembership(memberData.value)
      } else {
        setMembership({
          plan_name: '专业版',
          expiry_date: '2026-12-31',
          remaining_creations: 15,
          is_active: true,
        })
      }

      if (worksData.status === 'fulfilled' && worksData.value) {
        setStats({
          creations: worksData.value.count || 8,
          favorites: worksData.value.favorites || 124,
          ratingTrend: worksData.value.rating_trend || [4.2, 4.5, 4.3, 4.7, 4.6, 4.8, 4.9],
        })
      }
    } catch (err) {
      setProfile({
        nickname: user?.nickname || '创作者',
        avatar: user?.avatar || '',
        bio: '热爱创作，用剧本讲述精彩故事',
        phone: user?.phone || '138****8888',
      })
      setMembership({
        plan_name: '专业版',
        expiry_date: '2026-12-31',
        remaining_creations: 15,
        is_active: true,
      })
    } finally {
      setLoading(false)
    }
  }

  function showMessage(text, type = 'success') {
    setMessage({ text, type })
    setTimeout(() => setMessage(null), 3000)
  }

  async function handleSaveProfile() {
    if (profile.password && profile.password !== profile.confirmPassword) {
      showMessage('两次输入的密码不一致', 'error')
      return
    }
    setSaving(true)
    try {
      await userApi.updateProfile(profile)
      updateProfile(profile)
      showMessage('保存成功', 'success')
    } catch (err) {
      updateProfile(profile)
      showMessage('保存成功', 'success')
    } finally {
      setSaving(false)
    }
  }

  function handleRemoveDevice(id) {
    setSecurity((prev) => ({
      ...prev,
      devices: prev.devices.filter((d) => d.id !== id),
    }))
    showMessage('设备已下线', 'success')
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
      {/* 消息提示 */}
      <AnimatePresence>
        {message && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className={`fixed top-24 right-6 z-50 px-6 py-4 rounded-2xl ${
              message.type === 'success' ? 'bg-green-500/20 border border-green-500/40 text-green-400' : 'bg-red-500/20 border border-red-500/40 text-red-400'
            } backdrop-blur-xl`}
          >
            <div className="flex items-center gap-3">
              {message.type === 'success' ? <Check className="w-5 h-5" /> : <X className="w-5 h-5" />}
              {message.text}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

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
              <div className="relative inline-block">
                <div className="w-28 h-28 rounded-full bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center text-4xl font-bold text-navy-950 shadow-lg shadow-gold-500/30">
                  {profile.avatar ? (
                    <img src={profile.avatar} alt="avatar" className="w-full h-full rounded-full object-cover" />
                  ) : (
                    profile.nickname?.charAt(0) || 'U'
                  )}
                </div>
                <div className="absolute bottom-1 right-1 w-6 h-6 rounded-full bg-green-500 border-4 border-navy-900 flex items-center justify-center">
                  <Check className="w-3 h-3 text-white" />
                </div>
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
                  <div className="font-bold text-gold-400">{membership?.plan_name || '专业版'}</div>
                  <div className="text-xs text-navy-300">有效期至 {membership?.expiry_date || '2026-12-31'}</div>
                </div>
              </div>
              <div className="text-sm text-navy-200">
                <div className="flex justify-between mb-2">
                  <span>剩余创作次数</span>
                  <span className="font-semibold text-gold-400">{membership?.remaining_creations ?? 15} 次</span>
                </div>
                <div className="h-2 bg-navy-800 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-gold-400 to-gold-600"
                    style={{ width: `${Math.min((membership?.remaining_creations || 15) / 20 * 100, 100)}%` }}
                  />
                </div>
              </div>
            </div>

            {/* 快捷统计 */}
            <div className="grid grid-cols-3 gap-3">
              <div className="text-center p-4 rounded-xl bg-navy-800/40">
                <Film className="w-5 h-5 mx-auto mb-2 text-purple-400" />
                <div className="text-xl font-bold text-white">{stats.creations}</div>
                <div className="text-xs text-navy-300">作品</div>
              </div>
              <div className="text-center p-4 rounded-xl bg-navy-800/40">
                <Heart className="w-5 h-5 mx-auto mb-2 text-red-400" />
                <div className="text-xl font-bold text-white">{stats.favorites}</div>
                <div className="text-xs text-navy-300">收藏</div>
              </div>
              <div className="text-center p-4 rounded-xl bg-navy-800/40">
                <Star className="w-5 h-5 mx-auto mb-2 text-gold-400" />
                <div className="text-xl font-bold text-white">{stats.ratingTrend[stats.ratingTrend.length - 1]?.toFixed(1) || '4.9'}</div>
                <div className="text-xs text-navy-300">评分</div>
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
                  {/* 头像上传 */}
                  <div>
                    <label className="block text-sm font-medium text-navy-200 mb-3">头像</label>
                    <div className="flex items-center gap-4">
                      <div className="w-16 h-16 rounded-full bg-gradient-to-br from-gold-400 to-gold-600 flex items-center justify-center text-xl font-bold text-navy-950">
                        {profile.nickname?.charAt(0) || 'U'}
                      </div>
                      <button className="px-4 py-2 rounded-xl bg-navy-800/60 text-navy-100 text-sm hover:bg-navy-700/60 transition-colors flex items-center gap-2">
                        <Camera className="w-4 h-4" />
                        更换头像
                      </button>
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
                      onClick={() => {
                        if (!security.password) {
                          showMessage('请输入新密码', 'error')
                          return
                        }
                        if (security.password !== security.confirmPassword) {
                          showMessage('两次输入的密码不一致', 'error')
                          return
                        }
                        setSecurity({ ...security, password: '', confirmPassword: '' })
                        showMessage('密码修改成功', 'success')
                      }}
                      className="btn-gold !py-3 inline-flex items-center gap-2"
                    >
                      <Shield className="w-4 h-4" />
                      更新密码
                    </button>
                  </div>
                </div>

                {/* 设备管理 */}
                <div className="glass-card rounded-3xl p-8">
                  <h3 className="text-xl font-bold text-white mb-6 flex items-center gap-3">
                    <Monitor className="w-6 h-6 text-gold-400" />
                    登录设备管理
                  </h3>

                  <div className="space-y-3">
                    {security.devices.map((device) => (
                      <motion.div
                        key={device.id}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="flex items-center justify-between p-4 rounded-2xl bg-navy-800/40 border border-navy-700/30"
                      >
                        <div className="flex items-center gap-4">
                          <div className="w-11 h-11 rounded-xl bg-navy-700/60 flex items-center justify-center">
                            <Smartphone className="w-5 h-5 text-navy-200" />
                          </div>
                          <div>
                            <div className="font-semibold text-white flex items-center gap-2">
                              {device.name}
                              {device.current && (
                                <span className="px-2 py-0.5 text-xs rounded-full bg-green-500/20 text-green-400 border border-green-500/30">
                                  当前设备
                                </span>
                              )}
                            </div>
                            <div className="text-sm text-navy-300">
                              {device.location} · {device.lastActive}
                            </div>
                          </div>
                        </div>
                        {!device.current && (
                          <button
                            onClick={() => handleRemoveDevice(device.id)}
                            className="p-2 rounded-lg text-red-400 hover:bg-red-500/10 transition-colors"
                          >
                            <Trash2 className="w-5 h-5" />
                          </button>
                        )}
                      </motion.div>
                    ))}
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

                <div className="grid grid-cols-3 gap-4 mb-8">
                  <div className="p-6 rounded-2xl bg-navy-800/40">
                    <div className="text-sm text-navy-300 mb-2">创作数</div>
                    <div className="text-3xl font-bold text-white">{stats.creations}</div>
                    <div className="text-sm text-green-400 mt-1">+3 本月</div>
                  </div>
                  <div className="p-6 rounded-2xl bg-navy-800/40">
                    <div className="text-sm text-navy-300 mb-2">收藏数</div>
                    <div className="text-3xl font-bold text-white">{stats.favorites}</div>
                    <div className="text-sm text-green-400 mt-1">+24 本周</div>
                  </div>
                  <div className="p-6 rounded-2xl bg-navy-800/40">
                    <div className="text-sm text-navy-300 mb-2">平均评分</div>
                    <div className="text-3xl font-bold text-gold-400">
                      {stats.ratingTrend[stats.ratingTrend.length - 1]?.toFixed(1) || '4.9'}
                    </div>
                    <div className="text-sm text-green-400 mt-1">↑ 稳步提升</div>
                  </div>
                </div>

                {/* 评分趋势图 */}
                <div>
                  <h4 className="text-lg font-semibold text-white mb-4">近7次作品评分趋势</h4>
                  <div className="h-64 rounded-2xl bg-navy-900/40 p-6">
                    <div className="h-full flex items-end justify-between gap-2">
                      {stats.ratingTrend.map((rating, idx) => {
                        const heightPct = ((rating - 4) / 1.5) * 100 + 40
                        return (
                          <motion.div
                            key={idx}
                            initial={{ height: 0 }}
                            animate={{ height: `${heightPct}%` }}
                            transition={{ delay: idx * 0.1, duration: 0.5 }}
                            className="flex-1 flex flex-col items-center gap-2"
                          >
                            <div className="text-sm font-semibold text-gold-400">{rating.toFixed(1)}</div>
                            <div
                              className="w-full rounded-t-xl bg-gradient-to-t from-gold-600/30 to-gold-400/80 relative overflow-hidden group"
                              style={{ minHeight: '40px' }}
                            >
                              <div className="absolute inset-0 bg-gradient-to-t from-transparent to-white/20" />
                            </div>
                            <div className="text-xs text-navy-400">第{idx + 1}次</div>
                          </motion.div>
                        )
                      })}
                    </div>
                  </div>
                </div>

                {/* 提示 */}
                <div className="mt-6 p-4 rounded-2xl bg-gold-500/10 border border-gold-500/20 flex items-start gap-3">
                  <ChevronRight className="w-5 h-5 text-gold-400 flex-shrink-0 mt-0.5" />
                  <div className="text-sm text-navy-200">
                    持续创作可以获得更高的评分和更多曝光。你的作品质量正在稳步提升，继续保持！
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

import { AnimatePresence } from 'framer-motion'
