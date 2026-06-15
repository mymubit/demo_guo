import { create } from 'zustand'
import { billing } from '@/services/api'

/** 创作币余额 — 全站单一数据源（/api/billing/wallet/） */
export const useWalletStore = create((set, get) => ({
  wallet: null,
  loading: false,
  error: null,

  fetchWallet: async () => {
    set({ loading: true, error: null })
    try {
      const data = await billing.wallet()
      set({ wallet: data, loading: false })
      return data
    } catch (err) {
      set({ loading: false, error: err?.message || '加载失败' })
      return null
    }
  },

  setWallet: (wallet) => set({ wallet }),

  clearWallet: () => set({ wallet: null, loading: false, error: null }),
}))
