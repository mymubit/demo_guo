import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Coins, Loader2 } from 'lucide-react'
import { useAuthStore } from '@/store/authStore'
import { useWalletStore } from '@/store/walletStore'

export default function WalletBadge({ className = '', compact = false }) {
  const { isAuthenticated } = useAuthStore()
  const location = useLocation()
  const { wallet, loading, fetchWallet, clearWallet } = useWalletStore()

  useEffect(() => {
    if (!isAuthenticated) {
      clearWallet()
      return
    }
    fetchWallet()
  }, [isAuthenticated, location.pathname, fetchWallet, clearWallet])

  if (!isAuthenticated) return null

  const currency = wallet?.currency_name || '创作币'
  const balance = wallet?.balance ?? 0

  return (
    <Link
      to="/wallet"
      className={`inline-flex items-center gap-2 rounded-xl border border-gold-500/25 bg-gold-500/10 text-gold-200 hover:bg-gold-500/15 transition-colors ${
        compact ? 'px-3 py-1.5 text-sm' : 'px-4 py-2 text-sm'
      } ${className}`}
      title="查看余额与充值"
    >
      <Coins className="w-4 h-4 text-gold-400" />
      {loading ? (
        <Loader2 className="w-4 h-4 animate-spin" />
      ) : (
        <span>
          {compact ? balance : `${balance} ${currency}`}
        </span>
      )}
      {!compact && <span className="text-gold-400/80 text-xs">充值</span>}
    </Link>
  )
}
