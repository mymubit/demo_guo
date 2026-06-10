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
    }),
    {
      name: 'scriptforge-auth',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        refreshToken: state.refreshToken,
      }),
    }
  )
)
