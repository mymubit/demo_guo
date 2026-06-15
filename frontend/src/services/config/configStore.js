import { create } from 'zustand'
import { systemConfig } from './systemConfig'
import { configureMonitor } from '@/utils/monitor/client'
import { resolveMonitorSampleRate } from '@/utils/monitor/config'

function syncMonitorFromValues(values) {
  const sampleRate = resolveMonitorSampleRate(values?.['monitoring.frontend_sample_rate'])
  configureMonitor({ sampleRate })
}

export const useConfigStore = create((set, get) => ({
  values: {},
  items: [],
  version: 0,
  loadedAt: null,
  loading: false,
  error: '',

  fetchPublicConfigs: async ({ force = false } = {}) => {
    const state = get()
    if (state.loading) return state.values
    if (!force && state.loadedAt && Date.now() - state.loadedAt < 5 * 60 * 1000) {
      return state.values
    }

    set({ loading: true, error: '' })
    try {
      const data = await systemConfig.publicAll()
      const values = data?.values || {}
      syncMonitorFromValues(values)
      set({
        values,
        items: data.items,
        version: data?.version || state.version,
        loadedAt: Date.now(),
        loading: false,
        error: '',
      })
      return values
    } catch (error) {
      set({ loading: false, error: error?.message || '配置加载失败' })
      return state.values
    }
  },

  setValues: (values, version) => {
    set((state) => {
      const merged = { ...state.values, ...(values || {}) }
      syncMonitorFromValues(merged)
      return {
        values: merged,
        version: version || state.version,
        loadedAt: Date.now(),
      }
    })
  },

  getValue: (key, defaultValue) => {
    const values = get().values || {}
    return Object.prototype.hasOwnProperty.call(values, key) ? values[key] : defaultValue
  },

  clear: () => set({ values: {}, items: [], version: 0, loadedAt: null, loading: false, error: '' }),
}))

export function getConfigValue(key, defaultValue) {
  return useConfigStore.getState().getValue(key, defaultValue)
}
