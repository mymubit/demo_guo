import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Coins, Loader2 } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useWalletStore } from '@/store/walletStore'

export default function WalletBadge({ className = '', compact = false }) {
  const { isAuthenticated } = useAuthStore()
  const { wallet, loading, fetchWallet, clearWallet } = useWalletStore()

  useEffect(() => {
    if (!isAuthenticated) {
      clearWallet()
      return
    }
    fetchWallet()
  }, [isAuthenticated, fetchWallet, clearWallet])

  if (!isAuthenticated) return null

  const currency = wallet?.currency_name || '创作币'
  const balance = wallet?.balance ?? 0

  return (
    <Link
      to="/wallet"
      className={`inline-flex items-center gap-2 rounded-lg border border-accent-300/40 bg-accent-50 text-accent-700 hover:bg-accent-100 transition-colors ${
        compact ? 'px-3 py-1.5 text-sm' : 'px-4 py-2 text-sm'
      } ${className}`}
      title="查看余额与充值"
    >
      <Coins className="w-4 h-4 text-accent-600" />
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <span>
          {compact ? balance : `${balance} ${currency}`}
        </span>
      )}
      {!compact && <span className="text-accent-600/80 text-xs">充值</span>}
    </Link>
  )
}
