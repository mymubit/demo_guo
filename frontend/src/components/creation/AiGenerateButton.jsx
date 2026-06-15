import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2, Sparkles } from 'lucide-react'
import { toast } from 'sonner'
import { creation } from '@/services/api'
import { useAiGenerateLock } from '@/components/creation/AiGenerateLockContext'
import { useWalletStore } from '@/store/walletStore'

export default function AiGenerateButton({
  actionKey,
  coinCost = 0,
  currencyName = '创作币',
  label = 'AI 生成',
  memberOnly = false,
  membershipActive = true,
  disabled,
  context,
  onGenerated,
  className = '',
}) {
  const navigate = useNavigate()
  const lock = useAiGenerateLock()
  const fetchWallet = useWalletStore((s) => s.fetchWallet)
  const patchWalletBalance = useWalletStore((s) => s.setWallet)
  const [loading, setLoading] = useState(false)
  const globalBusy = lock?.busy && !loading
  const needsMembership = memberOnly && !membershipActive

  function promptMembership() {
    toast.error(`${label}为会员专享，请先开通会员（开通后仍按创作币扣费）`, {
      action: {
        label: '去开通',
        onClick: () => navigate('/member'),
      },
    })
  }

  async function handleClick() {
    if (needsMembership) {
      promptMembership()
      return
    }

    const execute = async () => {
      setLoading(true)
      try {
        const data = await creation.aiGenerate(actionKey, context || {})
        onGenerated?.(data.text || '', data)
        if (typeof data.balance_after === 'number') {
          const prev = useWalletStore.getState().wallet || {}
          patchWalletBalance({
            ...prev,
            balance: data.balance_after,
            currency_name: data.currency_name || prev.currency_name || currencyName,
          })
        } else {
          fetchWallet()
        }
        if ((data.text || '').trim() || data.reference_items?.length) {
          toast.success(`已生成，消耗 ${data.coin_cost ?? coinCost} ${currencyName}`)
        } else {
          toast.error('AI 未返回有效内容，请重试')
        }
      } catch (err) {
        const msg = err.message || '生成失败'
        if (msg.includes('不足') || msg.includes('余额')) {
          toast.error(msg)
          navigate('/wallet')
        } else if (msg.includes('会员')) {
          toast.error(msg, {
            action: {
              label: '去开通',
              onClick: () => navigate('/member'),
            },
          })
        } else {
          toast.error(msg)
        }
      } finally {
        setLoading(false)
      }
    }

    if (lock?.runLocked) {
      await lock.runLocked(execute)
    } else {
      await execute()
    }
  }

  return (
    <button
      type="button"
      disabled={disabled || loading || globalBusy}
      onClick={handleClick}
      title={needsMembership ? '会员专享功能' : undefined}
      className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium bg-gradient-to-r from-purple-500/25 to-pink-500/20 text-purple-100 border border-purple-400/40 hover:border-purple-400/60 hover:from-purple-500/35 disabled:opacity-50 shadow-sm ${className}`}
    >
      {loading ? (
        <Loader2 className="w-3.5 h-3.5 animate-spin" />
      ) : (
        <Sparkles className="w-3.5 h-3.5" />
      )}
      {label}
      {memberOnly ? ' · 会员' : ''} · {coinCost} {currencyName}
    </button>
  )
}
