import { create } from 'zustand'

export const useRequestUiStore = create((set) => ({
  pendingCount: 0,
  start: () => set((state) => ({ pendingCount: state.pendingCount + 1 })),
  finish: () => set((state) => ({ pendingCount: Math.max(0, state.pendingCount - 1) })),
}))
