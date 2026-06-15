import { useEffect } from 'react'
import { useConfigStore } from './configStore'

export function useConfig(key, defaultValue) {
  const value = useConfigStore((state) =>
    Object.prototype.hasOwnProperty.call(state.values, key) ? state.values[key] : defaultValue
  )
  const fetchPublicConfigs = useConfigStore((state) => state.fetchPublicConfigs)

  useEffect(() => {
    fetchPublicConfigs()
  }, [fetchPublicConfigs])

  return value
}

export function useConfigs(keys = []) {
  const values = useConfigStore((state) => state.values)
  const fetchPublicConfigs = useConfigStore((state) => state.fetchPublicConfigs)

  useEffect(() => {
    fetchPublicConfigs()
  }, [fetchPublicConfigs])

  return keys.reduce((acc, key) => {
    acc[key] = Object.prototype.hasOwnProperty.call(values, key) ? values[key] : undefined
    return acc
  }, {})
}

export function useConfigReady() {
  return useConfigStore((state) => ({
    loading: state.loading,
    loaded: Boolean(state.loadedAt),
    error: state.error,
    version: state.version,
  }))
}
