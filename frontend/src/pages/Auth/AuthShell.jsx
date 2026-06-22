import { Link } from 'react-router-dom'
import { ShieldCheck, Sparkles } from 'lucide-react'
import { Badge } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { cn } from '@/utils/cn'

const AUTH_BG =
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cinematic%20film%20set%20at%20night%2C%20giant%20spotlight%2C%20clapperboard%20on%20a%20chair%2C%20dark%20mood%2C%20anamorphic%2C%20gold%20and%20navy%20tones%2C%20photorealistic%2C%208k&image_size=portrait_4_3'

const TABS = [
  { key: 'login', label: '登录', to: '/login' },
  { key: 'register', label: '注册', to: '/register' },
]

export default function AuthShell({ activeTab, title, subtitle, children }) {
  return (
    <div className="relative min-h-[calc(100vh-4.25rem)] grid grid-cols-1 bg-gray-50 lg:grid-cols-2">
      <div className="relative hidden overflow-hidden lg:block bg-brand-600">
        <div
          className="absolute inset-0 bg-cover bg-center opacity-30"
          style={{ backgroundImage: `url(${AUTH_BG})` }}
        />
        <div className="absolute inset-0 bg-gradient-to-br from-brand-700/90 to-brand-900/95" />
        <div className="relative z-10 flex h-full flex-col justify-between p-12 text-white">
          <div>
            <Badge tone="gold" size="md">
              ScriptForge
            </Badge>
            <h2 className="mt-4 max-w-md font-display text-3xl font-bold leading-tight">
              把每一句话创意，
              <br />
              变成可被拍摄的剧本。
            </h2>
            <p className="mt-3 max-w-md text-brand-100">
              7 节点主链 · 4 题材格式 · 数字水印 · 全流程 8–12 分钟
            </p>
          </div>
          <div className="space-y-2 text-sm text-brand-100">
            <div className="flex items-center gap-2">
              <ShieldCheck className={ICON.md} /> 端到端加密 · 原始数据不出端
            </div>
            <div className="flex items-center gap-2">
              <Sparkles className={ICON.md} /> 50,000+ 创作者 · 200 万集数生成
            </div>
          </div>
        </div>
      </div>

      <div className="relative z-10 flex items-center justify-center bg-white p-8 md:p-12">
        <div className="w-full max-w-sm">
          <div className="mb-7 flex gap-1 rounded-full border border-gray-200 bg-gray-50 p-1">
            {TABS.map((tab) => (
              <Link
                key={tab.key}
                to={tab.to}
                className={cn(
                  'flex-1 rounded-full px-3 py-1.5 text-center text-sm font-medium transition-colors',
                  activeTab === tab.key ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-900',
                )}
              >
                {tab.label}
              </Link>
            ))}
          </div>

          <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
          {subtitle ? <p className="mt-1 text-sm text-gray-500">{subtitle}</p> : null}

          <div className="mt-6">{children}</div>
        </div>
      </div>
    </div>
  )
}
