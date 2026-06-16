import BillingAdmin from '@/pages/Admin/billing'

/** 填表 Agent 配置 — 从配置中心迁入 Agent 中心 */
export default function FormFieldAgentPanel() {
  return <BillingAdmin forcedTab="ai-prompts" />
}
