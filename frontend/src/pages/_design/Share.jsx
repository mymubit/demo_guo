/**
 * Share.jsx — 公开分享落地页
 *
 * 对应后端：creation/services/share_download.py
 * 视觉：极简可分享海报 + 一次性链接倒计时 + 水印提示
 */
import { motion } from 'framer-motion'
import { Clock, Download, ShieldCheck, Lock } from 'lucide-react'
import { Badge, Button } from '@/components/ui'
import { ICON } from '@/constants/iconSizes'
import { pageEnter } from '@/constants/motion'

const COVER =
  'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=cinematic%20poster%20of%20a%20chinese%20short%20drama%20manuscript%20on%20a%20dark%20mahogany%20desk%2C%20golden%20spotlight%2C%20shallow%20depth%20of%20field%2C%20film%20noir%2C%20photorealistic&image_size=portrait_4_3'

export default function Share() {
  return (
    <motion.div {...pageEnter} className="min-h-[calc(100svh-3.25rem)] bg-navy-950 text-white">
      {/* 顶部 — 一次性链接提示 */}
      <div className="border-b border-white/5 bg-slate-900/60">
        <div className="mx-auto flex max-w-5xl flex-wrap items-center justify-between gap-3 px-6 py-3 text-sm">
          <div className="flex items-center gap-2 text-slate-300">
            <ShieldCheck className={ICON.md} />
            一次性分享链接
            <Badge tone="warning" size="sm" className="ml-1">
              <Clock className={ICON.xs} /> 剩余 23:46:12
            </Badge>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-500">
            <Lock className={ICON.xs} /> 已植入数字水印 · 访问 IP 138****8821
          </div>
        </div>
      </div>

      <div className="mx-auto grid max-w-5xl grid-cols-1 gap-8 px-6 py-10 lg:grid-cols-[1fr_320px]">
        {/* 左侧 — 海报 + 简介 */}
        <div>
          <div className="overflow-hidden rounded-3xl border border-white/5">
            <div className="aspect-[4/3] bg-cover bg-center" style={{ backgroundImage: `url(${COVER})` }} />
          </div>
          <h1 className="mt-5 font-display text-3xl font-bold">《逆光》</h1>
          <div className="mt-1 text-sm text-slate-400">都市逆袭 · 80 集 · 由 ScriptForge AI 生成</div>
          <p className="mt-4 max-w-2xl leading-relaxed text-navy-200">
            被前夫扫地出门的全职妈妈，靠 5 年前埋下的证据链反杀豪门，
            并意外发现女儿身上藏着的惊天秘密。
            这是一部关于「反击、救赎与母爱」的 80 集短剧。
          </p>
          <div className="mt-5 flex flex-wrap gap-2">
            <Badge tone="gold">评分 86</Badge>
            <Badge tone="info">已分享 12 次</Badge>
            <Badge tone="success">已审核</Badge>
          </div>
        </div>

        {/* 右侧 — 下载 / 操作 */}
        <aside className="space-y-3.5">
          <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-4.5">
            <h3 className="m-0 mb-2 text-sm font-semibold text-white">下载剧本</h3>
            <p className="m-0 mb-3 text-xs text-slate-500">下载文件将携带您的水印，请勿二次传播</p>
            <Button variant="gold" size="lg" className="w-full justify-center" iconLeft={<Download className={ICON.md} />}>
              下载 4.6 MB ZIP
            </Button>
            <div className="mt-2 grid grid-cols-4 gap-1.5 text-[10px]">
              {['标准版', '行业版', '精简版', '分镜版'].map((f) => (
                <button key={f} className="rounded-md border border-white/10 bg-white/[0.03] py-1.5 text-slate-300 hover:border-gold-400/40 hover:text-white">
                  {f}
                </button>
              ))}
            </div>
          </div>
          <div className="rounded-2xl border border-white/5 bg-slate-900/60 p-4.5 text-xs text-slate-400">
            <b className="text-slate-200">访问统计</b>
            <div className="mt-2 grid grid-cols-2 gap-2">
              <div className="rounded-lg border border-white/5 bg-white/[0.02] p-2">
                <div className="text-[10px] text-slate-500">浏览</div>
                <div className="text-lg font-bold text-white">238</div>
              </div>
              <div className="rounded-lg border border-white/5 bg-white/[0.02] p-2">
                <div className="text-[10px] text-slate-500">下载</div>
                <div className="text-lg font-bold text-white">12</div>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </motion.div>
  )
}
