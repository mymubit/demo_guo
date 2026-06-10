import { create } from 'zustand'

// 会员套餐数据
const MEMBERSHIP_PLANS = [
  {
    id: 'basic',
    name: '体验版',
    price: 99,
    originalPrice: 199,
    validity: 30,
    creation_quota: 3,
    features: [
      '3次完整剧本创作',
      '8大题材模板',
      'Markdown 格式导出',
      '基础质量审查',
      '7天作品保存',
    ],
    recommended: false,
    color: 'navy',
  },
  {
    id: 'pro',
    name: '专业版',
    price: 299,
    originalPrice: 599,
    validity: 30,
    creation_quota: 20,
    features: [
      '20次完整剧本创作',
      '所有题材模板',
      '4种格式变体',
      '高级质量审查评分',
      '30天作品保存',
      '优先创作队列',
      '作品分享链接',
    ],
    recommended: true,
    color: 'gold',
  },
  {
    id: 'ultimate',
    name: '旗舰版',
    price: 999,
    originalPrice: 1999,
    validity: 365,
    creation_quota: -1, // 无限
    features: [
      '无限次剧本创作',
      '所有题材 + 定制模板',
      '完整格式 + PDF + DOCX 导出',
      'S级质量审查与优化建议',
      '永久作品保存',
      '最高优先级队列',
      '高级分享与水印',
      '专属客服支持',
      '团队协作功能',
    ],
    recommended: false,
    color: 'purple',
  },
]

export const useMemberStore = create((set, get) => ({
  plans: MEMBERSHIP_PLANS,
  currentMembership: null,
  selectedPlan: null,

  setSelectedPlan: (planId) => {
    const plan = MEMBERSHIP_PLANS.find(p => p.id === planId)
    set({ selectedPlan: plan })
  },

  setCurrentMembership: (membership) => {
    set({ currentMembership: membership })
  },
}))
