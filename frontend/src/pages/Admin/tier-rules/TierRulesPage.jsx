import { useCallback, useState } from 'react'
import AiConfigShell from '@/components/admin/ai-config/AiConfigShell'
import { AdminMessage } from '@/components/admin/AdminUI'
import SkillRulesPanel from './SkillRulesPanel'

export default function TierRulesPage() {
  const [message, setMessage] = useState(null)

  const showMsg = useCallback((text, type = 'success') => {
    setMessage({ type, text })
  }, [])

  return (
    <AiConfigShell sectionId="tier-rules">
      <AdminMessage message={message} onClose={() => setMessage(null)} />
      <SkillRulesPanel onMessage={showMsg} />
    </AiConfigShell>
  )
}
