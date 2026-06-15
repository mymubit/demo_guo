import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      refreshToken: null,
      isAuthenticated: false,

      login: (userData, token, refreshToken) => {
        set({
          user: userData,
          token,
          refreshToken,
          isAuthenticated: true,
        })
      },

      setUser: (userData) => set({ user: userData }),

      logout: () => {
        set({
          user: null,
          token: null,
          refreshToken: null,
          isAuthenticated: false,
        })
      },

      updateProfile: (profile) => {
        set({ user: { ...get().user, ...profile } })
      },

      setToken: (token) => set({ token }),
      setTokens: ({ token, refreshToken }) =>
        set((state) => ({
          token: token ?? state.token,
          refreshToken: refreshToken ?? state.refreshToken,
          isAuthenticated: Boolean(token ?? state.token),
        })),
      hasAdminAccess: () => {
        const user = get().user || {}
        return Boolean(user.is_staff || user.is_superuser)
      },
    }),
    {
      name: 'scriptforge-auth',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        if (state?.token && !state.isAuthenticated) {
          state.isAuthenticated = true
        }
      },
    }
  )
)
