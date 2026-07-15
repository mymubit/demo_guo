import { useQuery, useQueryClient } from '@tanstack/react-query'
import { dramaApi } from '@/services/drama'
import { formatApiError } from '@/services/errors'
import { ErrorBanner, LoadingBlock } from '@/components/ui/Tabs'
import {
  normalizeWorkbenchDefinition,
  workbenchFormQueryKey,
} from '@/utils/workbenchDefinition'
import type { WorkbenchDefinition } from '@/types/workbench'
import {
  createContext,
  useContext,
  type ReactNode,
} from 'react'

type WorkbenchDefinitionContextValue = {
  definition: WorkbenchDefinition
  skillsBundleVersion: string
  refetch: () => void
}

const WorkbenchDefinitionContext = createContext<WorkbenchDefinitionContextValue | null>(
  null,
)

async function fetchWorkbenchDefinition(): Promise<WorkbenchDefinition> {
  const raw = await dramaApi.getWorkbenchForm()
  return normalizeWorkbenchDefinition(raw)
}

/** TanStack Query for workbench-form; cache partitioned by skills bundle version. */
export function useWorkbenchDefinitionQuery() {
  const qc = useQueryClient()

  return useQuery({
    queryKey: workbenchFormQueryKey(),
    queryFn: async () => {
      const definition = await fetchWorkbenchDefinition()
      qc.setQueryData(workbenchFormQueryKey(definition.skills_bundle_version), definition)
      return definition
    },
    staleTime: Infinity,
    gcTime: 1000 * 60 * 60,
    retry: false,
    refetchOnWindowFocus: false,
  })
}

export function WorkbenchDefinitionProvider({ children }: { children: ReactNode }) {
  const query = useWorkbenchDefinitionQuery()

  if (query.isLoading || (query.isFetching && !query.data)) {
    return <LoadingBlock label="加载工作台定义…" />
  }

  if (query.isError || !query.data) {
    return (
      <div className="p-8">
        <ErrorBanner
          message={formatApiError(query.error ?? new Error('工作台定义不可用'))}
          onRetry={() => {
            void query.refetch()
          }}
        />
      </div>
    )
  }

  const value: WorkbenchDefinitionContextValue = {
    definition: query.data,
    skillsBundleVersion: query.data.skills_bundle_version,
    refetch: () => {
      void query.refetch()
    },
  }

  return (
    <WorkbenchDefinitionContext.Provider value={value}>
      {children}
    </WorkbenchDefinitionContext.Provider>
  )
}

/** Requires WorkbenchDefinitionProvider. Throws if used outside (no silent fallback). */
export function useWorkbenchDefinition(): WorkbenchDefinitionContextValue {
  const ctx = useContext(WorkbenchDefinitionContext)
  if (!ctx) {
    throw new Error('useWorkbenchDefinition 必须在 WorkbenchDefinitionProvider 内使用')
  }
  return ctx
}

export function useWorkbenchDefinitionOptional(): WorkbenchDefinitionContextValue | null {
  return useContext(WorkbenchDefinitionContext)
}

/** Test-only provider that injects a normalized definition without hitting the network. */
export function WorkbenchDefinitionTestProvider({
  definition,
  children,
}: {
  definition: WorkbenchDefinition
  children: ReactNode
}) {
  return (
    <WorkbenchDefinitionContext.Provider
      value={{
        definition,
        skillsBundleVersion: definition.skills_bundle_version,
        refetch: () => undefined,
      }}
    >
      {children}
    </WorkbenchDefinitionContext.Provider>
  )
}
