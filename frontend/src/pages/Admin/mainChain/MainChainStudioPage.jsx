import { Navigate } from 'react-router-dom'

/** 主链工作室已并入调度中心流程编排；UI 见 OrchestrationFlowPage */
export default function MainChainStudioPage() {
  return <Navigate to="/admin/orchestration?tab=flow" replace />
}
