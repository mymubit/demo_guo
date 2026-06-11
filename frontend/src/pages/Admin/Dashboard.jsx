import { motion } from 'framer-motion'
import { useState, useEffect } from 'react'
import {
  Users,
  UserPlus,
  Crown,
  DollarSign,
  Sparkles,
  Film,
  TrendingUp,
  TrendingDown,
  Calendar,
  ArrowUpRight,
  ShoppingCart,
  CheckCircle2,
  Clock,
} from 'lucide-react'
import { admin } from '@/services/api'

export default function Dashboard() {
  const [stats, setStats] = useState({
    totalUsers: 12847,
    todayNew: 128,
    totalMembers: 3456,
    todayRevenue: 28999,
    totalCreations: 56892,
  })
  const [loading, setLoading] = useState(true)

  // 模拟数据
  const userGrowthData = [120, 150, 180, 160, 200, 220, 250, 230, 280, 300, 270, 320, 350, 340, 380, 400, 390, 420, 450, 480, 460, 500, 520, 550, 530, 580, 600, 620, 640, 680]
  const memberDistribution = [
    { name: '体验版', value: 45, color: '#667eea' },
    { name: '专业版', value: 35, color: '#f6ad55' },
    { name: '旗舰版', value: 15, color: '#9f7aea' },
    { name: '企业版', value: 5, color: '#48bb78' },
  ]
  const creationData = [420, 380, 520, 610, 480, 550, 620]
  const recentOrders = [
    { id: 'ORD20260610001', user: '陈思远', plan: '专业版-月付', amount: 299, status: '已支付', time: '10分钟前' },
    { id: 'ORD20260610002', user: '林小雨', plan: '旗舰版-年付', amount: 999, status: '已支付', time: '25分钟前' },
    { id: 'ORD20260610003', user: '王建国', plan: '体验版-月付', amount: 99, status: '待支付', time: '1小时前' },
    { id: 'ORD20260610004', user: '张晓萌', plan: '专业版-季付', amount: 799, status: '已支付', time: '2小时前' },
    { id: 'ORD20260610005', user: '李明', plan: '专业版-月付', amount: 299, status: '已退款', time: '3小时前' },
  ]

  useEffect(() => {
    async function loadData() {
      try {
        const data = await admin.getDashboard()
        if (data) setStats({ ...stats, ...data })
      } catch (err) {
        // 回退到 mock 数据
      } finally {
        setLoading(false)
      }
    }
    const timer = setTimeout(loadData, 500)
    return () => clearTimeout(timer)
  }, [])

  // 计算折线图路径
  const maxGrowth = Math.max(...userGrowthData)
  const minGrowth = Math.min(...userGrowthData)

  // 柱状图最大
  const maxCreation = Math.max(...creationData)

  // 饼图计算
  let cumulativePercent = 0
  const pieSegments = memberDistribution.map((seg) => {
    const start = cumulativePercent
    cumulativePercent += seg.value
    return {
      ...seg,
      startPercent: start,
      endPercent: cumulativePercent,
    }
  })

  function getCoordsForPercent(percent) {
    const angle = percent * 3.6 - 90
    const angleRad = (angle * Math.PI) / 180
    return { x: 50 + 40 * Math.cos(angleRad), y: 50 + 40 * Math.sin(angleRad) }
  }

  return (
    <div className="space-y-6">
      {/* 页面标题 */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white mb-1">仪表盘</h1>
          <p className="text-navy-300 text-sm">ScriptForge 平台运营数据总览</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-navy-400">
          <Calendar className="w-4 h-4" />
          <span>2026年6月10日</span>
        </div>
      </div>

      {/* 指标卡片 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {[
          { label: '总用户数', value: stats.totalUsers.toLocaleString(), change: '+12.5%', up: true, icon: Users, color: '#667eea' },
          { label: '今日新增', value: `+${stats.todayNew}`, change: '+8.3%', up: true, icon: UserPlus, color: '#48bb78' },
          { label: '会员总数', value: stats.totalMembers.toLocaleString(), change: '+15.2%', up: true, icon: Crown, color: '#f6ad55' },
          { label: '今日营收', value: `¥${stats.todayRevenue.toLocaleString()}`, change: '+22.1%', up: true, icon: DollarSign, color: '#9f7aea' },
          { label: '创作数', value: stats.totalCreations.toLocaleString(), change: '+5.8%', up: true, icon: Sparkles, color: '#ed64a6' },
        ].map((card, idx) => (
          <motion.div
            key={card.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.05 }}
            className="glass-card rounded-2xl p-5 relative overflow-hidden group hover:shadow-lg transition-shadow"
          >
            <div
              className="absolute top-0 right-0 w-24 h-24 rounded-full opacity-10 group-hover:opacity-20 transition-opacity"
              style={{ background: card.color, transform: 'translate(40%, -40%)' }}
            />
            <div
              className="w-10 h-10 rounded-xl flex items-center justify-center mb-3"
              style={{ background: `${card.color}30` }}
            >
              <card.icon className="w-5 h-5" style={{ color: card.color }} />
            </div>
            <div className="text-sm text-navy-300 mb-1">{card.label}</div>
            <div className="text-2xl font-bold text-white mb-2">{card.value}</div>
            <div className={`text-xs flex items-center gap-1 ${card.up ? 'text-green-400' : 'text-red-400'}`}>
              {card.up ? <ArrowUpRight className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
              {card.change} <span className="text-navy-500 ml-1">较昨日</span>
            </div>
          </motion.div>
        ))}
      </div>

      {/* 图表区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 折线图 - 近30天用户增长 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="lg:col-span-2 glass-card rounded-2xl p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-bold text-white">近30天用户增长趋势</h3>
              <p className="text-sm text-navy-300 mt-1">每日新增注册用户</p>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <span className="flex items-center gap-1.5 text-navy-300">
                <span className="w-2 h-2 rounded-full bg-gold-400" />
                新增用户
              </span>
            </div>
          </div>

          {/* 简易折线图 - 用 div 实现 */}
          <div className="relative h-64">
            {/* 背景网格线 */}
            <div className="absolute inset-0 flex flex-col justify-between">
              {[0, 1, 2, 3, 4].map((i) => (
                <div key={i} className="border-t border-navy-700/30 border-dashed" />
              ))}
            </div>

            {/* Y轴标签 */}
            <div className="absolute left-0 top-0 bottom-0 flex flex-col justify-between text-xs text-navy-500 -translate-x-1">
              <span>{maxGrowth}</span>
              <span>{Math.round((maxGrowth + minGrowth) / 2)}</span>
              <span>{minGrowth}</span>
            </div>

            {/* 折线图区域 */}
            <div className="pl-10 h-full relative">
              {/* 面积填充 */}
              <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none" viewBox="0 0 100 100">
                <defs>
                  <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#f6d365" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#f6d365" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <path
                  d={`
                    M 0 ${100 - ((userGrowthData[0] - minGrowth) / (maxGrowth - minGrowth)) * 100}
                    ${userGrowthData.map((v, i) => {
                      const x = (i / (userGrowthData.length - 1)) * 100
                      const y = 100 - ((v - minGrowth) / (maxGrowth - minGrowth)) * 100
                      return `L ${x} ${y}`
                    }).join(' ')}
                    L 100 100 L 0 100 Z
                  `}
                  fill="url(#areaGradient)"
                />
                <path
                  d={`
                    M 0 ${100 - ((userGrowthData[0] - minGrowth) / (maxGrowth - minGrowth)) * 100}
                    ${userGrowthData.map((v, i) => {
                      const x = (i / (userGrowthData.length - 1)) * 100
                      const y = 100 - ((v - minGrowth) / (maxGrowth - minGrowth)) * 100
                      return `L ${x} ${y}`
                    }).join(' ')}
                  `}
                  fill="none"
                  stroke="#f6ad55"
                  strokeWidth="0.8"
                  vectorEffect="non-scaling-stroke"
                />
              </svg>

              {/* 数据点 */}
              <div className="absolute inset-0 flex items-end justify-between">
                {userGrowthData.map((value, idx) => {
                  const heightPct = ((value - minGrowth) / (maxGrowth - minGrowth)) * 100
                  return (
                    <div key={idx} className="flex-1 relative h-full" style={{ minWidth: '6px' }}>
                      {idx % 5 === 0 && (
                        <>
                          <motion.div
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            transition={{ delay: 0.3 + idx * 0.01 }}
                            className="absolute w-2 h-2 rounded-full bg-gold-400 border-2 border-navy-900 -translate-x-1/2"
                            style={{ left: '50%', bottom: `${heightPct}%` }}
                          />
                          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-xs text-navy-500 translate-y-5">
                            {idx + 1}
                          </div>
                        </>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </motion.div>

        {/* 饼图 - 会员套餐分布 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="glass-card rounded-2xl p-6"
        >
          <h3 className="text-lg font-bold text-white mb-2">会员套餐分布</h3>
          <p className="text-sm text-navy-300 mb-6">当前会员套餐占比</p>

          {/* SVG 饼图 */}
          <div className="w-40 h-40 mx-auto mb-6 relative">
            <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
              {pieSegments.map((seg, idx) => {
                const start = getCoordsForPercent(seg.startPercent / 100)
                const end = getCoordsForPercent(seg.endPercent / 100)
                const largeArc = seg.value > 50 ? 1 : 0
                return (
                  <path
                    key={idx}
                    d={`M 50 50 L ${start.x} ${start.y} A 40 40 0 ${largeArc} 1 ${end.x} ${end.y} Z`}
                    fill={seg.color}
                    opacity="0.85"
                    stroke="#030d24"
                    strokeWidth="1"
                  />
                )
              })}
              {/* 中心孔 - 圆环效果 */}
              <circle cx="50" cy="50" r="22" fill="#030d24" />
            </svg>
            {/* 中心文字 */}
            <div className="absolute inset-0 flex items-center justify-center flex-col">
              <div className="text-xl font-bold text-white">{stats.totalMembers.toLocaleString()}</div>
              <div className="text-xs text-navy-400">总会员</div>
            </div>
          </div>

          {/* 图例 */}
          <div className="space-y-2">
            {memberDistribution.map((seg, idx) => (
              <div key={idx} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span className="w-3 h-3 rounded-sm" style={{ background: seg.color }} />
                  <span className="text-navy-200">{seg.name}</span>
                </div>
                <span className="font-semibold text-white">{seg.value}%</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* 第二排图表 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 柱状图 - 近7天创作数 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="glass-card rounded-2xl p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-bold text-white">近7天创作数</h3>
              <p className="text-sm text-navy-300 mt-1">每日生成剧本数量统计</p>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-white">{creationData.reduce((a, b) => a + b, 0).toLocaleString()}</div>
              <div className="text-xs text-green-400">7日总计</div>
            </div>
          </div>

          {/* 柱状图 */}
          <div className="h-56 flex items-end justify-between gap-2 pt-4">
            {creationData.map((value, idx) => {
              const heightPct = (value / maxCreation) * 100
              const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
              return (
                <div key={idx} className="flex-1 flex flex-col items-center gap-2">
                  <div className="text-xs font-semibold text-gold-400">{value}</div>
                  <motion.div
                    initial={{ height: 0 }}
                    animate={{ height: `${heightPct}%` }}
                    transition={{ delay: 0.3 + idx * 0.08, duration: 0.5 }}
                    className="w-full rounded-t-xl bg-gradient-to-t from-gold-600/40 to-gold-400 relative group"
                    style={{ minHeight: '20px' }}
                  >
                    <div className="absolute inset-0 bg-gradient-to-t from-transparent to-white/20 rounded-t-xl opacity-0 group-hover:opacity-100 transition-opacity" />
                  </motion.div>
                  <div className="text-xs text-navy-400">{days[idx]}</div>
                </div>
              )
            })}
          </div>
        </motion.div>

        {/* 最近订单 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.35 }}
          className="glass-card rounded-2xl p-6"
        >
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-lg font-bold text-white">最近订单</h3>
              <p className="text-sm text-navy-300 mt-1">最新支付订单动态</p>
            </div>
            <button className="text-sm text-gold-400 hover:text-gold-300 transition-colors">
              查看全部 →
            </button>
          </div>

          <div className="space-y-3">
            {recentOrders.map((order, idx) => (
              <div
                key={order.id}
                className="flex items-center justify-between p-3 rounded-xl bg-navy-800/40 border border-navy-700/30 hover:border-navy-600/40 transition-colors"
              >
                <div className="flex items-center gap-3 min-w-0">
                  <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0 ${
                    order.status === '已支付' ? 'bg-green-500/20' :
                    order.status === '待支付' ? 'bg-yellow-500/20' : 'bg-red-500/20'
                  }`}>
                    {order.status === '已支付' ? <CheckCircle2 className="w-4 h-4 text-green-400" /> :
                     order.status === '待支付' ? <Clock className="w-4 h-4 text-yellow-400" /> :
                     <ShoppingCart className="w-4 h-4 text-red-400" />}
                  </div>
                  <div className="min-w-0">
                    <div className="text-sm font-medium text-white truncate">{order.user}</div>
                    <div className="text-xs text-navy-400 truncate">{order.plan}</div>
                  </div>
                </div>
                <div className="text-right flex-shrink-0 ml-2">
                  <div className="text-sm font-semibold text-white">¥{order.amount}</div>
                  <div className="text-xs text-navy-400">{order.time}</div>
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}
