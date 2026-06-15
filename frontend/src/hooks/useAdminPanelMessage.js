import { createElement, useState } from 'react'
import { AdminMessage } from '@/components/admin/AdminUI'
import { formatUserError } from '@/utils/userError'

function formatAdminError(text, type = 'success') {
  if (!text || type !== 'error') return text || ''
  return formatUserError(text, '操作失败，请稍后重试')
}

export { formatAdminError }

export function useAdminPanelMessage() {
  const [message, setMessage] = useState(null)

  function showMessage(text, type = 'success') {
    setMessage({ text: formatAdminError(text, type), type })
    setTimeout(() => setMessage(null), type === 'error' ? 8000 : 3000)
  }

  function MessageBanner() {
    return createElement(AdminMessage, { message, onClose: () => setMessage(null) })
  }

  return { message, showMessage, MessageBanner }
}

