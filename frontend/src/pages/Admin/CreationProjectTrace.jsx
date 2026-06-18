import { Link, useParams, useSearchParams } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import AdminShell from '@/components/admin/AdminShell'
import { ProjectAgentTraceView } from '@/components/admin/ProjectAgentTrace'

/** 单项目的 Agent 执行轨迹 — 从创作项目列表进入 */
export default function CreationProjectTracePage() {
  const { projectId } = useParams()
  const [searchParams, setSearchParams] = useSearchParams()
  const tab = searchParams.get('tab') || 'basic'

  const setTab = (key) => {
    setSearchParams({ tab: key }, { replace: true })
  }

  return (
    <AdminShell
      title="项目详情"
      description="基本信息、执行记录、AI 产物与质量缺陷一站式排查"
      actions={
        <div className="flex flex-wrap items-center gap-3 text-sm">
          <Link
            to="/admin/creation/projects"
            className="text-gold-400 hover:text-gold-300 inline-flex items-center gap-1.5"
          >
            <ArrowLeft className="w-4 h-4" />
            项目列表
          </Link>
          {tab !== 'basic' ? (
            <button
              type="button"
              onClick={() => setTab('basic')}
              className="text-navy-400 hover:text-navy-200"
            >
              回到概览
            </button>
          ) : null}
        </div>
      }
    >
      <ProjectAgentTraceView
        projectId={projectId}
        activeTab={tab}
        onTabChange={setTab}
        showSummary
      />
    </AdminShell>
  )
}
