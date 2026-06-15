import { useCallback, useState } from 'react'

export function useFormErrors() {
  const [errors, setErrors] = useState({})

  const setFieldError = useCallback((name, message) => {
    setErrors((prev) => ({ ...prev, [name]: message }))
  }, [])

  const clearFieldError = useCallback((name) => {
    setErrors((prev) => ({ ...prev, [name]: '' }))
  }, [])

  const applyErrors = useCallback((nextErrors) => {
    const normalizedErrors = nextErrors || {}
    setErrors(normalizedErrors)
    return Object.values(normalizedErrors).every((value) => !value)
  }, [])

  return { errors, setErrors, setFieldError, clearFieldError, applyErrors }
}
