import { useMemo } from 'react'
import { EChart, buildCharacterRelationGraphOption } from '@/components/charts'
import { resolveRelationshipList } from '@/utils/relationshipResolve'
import EmptyState from '@/components/ui/EmptyState'

export default function CharacterRelationshipGraph({ characters = [], relationships = [], onSelectCharacter }) {
  const resolvedRelationships = useMemo(
    () => resolveRelationshipList(relationships, characters),
    [relationships, characters],
  )

  const hasBidirectional = useMemo(
    () => resolvedRelationships.some((r) => r.perspectiveA && r.perspectiveB),
    [resolvedRelationships],
  )

  const option = useMemo(
    () => buildCharacterRelationGraphOption({ characters, relationships: resolvedRelationships }),
    [characters, resolvedRelationships],
  )

  const events = useMemo(
    () =>
      onSelectCharacter
        ? {
            click: (params) => {
              if (params.dataType === 'node' && params.data?.id) {
                onSelectCharacter(params.data.id)
              }
            },
          }
        : undefined,
    [onSelectCharacter],
  )

  if (!option) {
    return (
      <EmptyState
        compact
        title="暂无人物关系数据"
        description="生成人物小传后将展示角色关系图谱。"
        className="mb-4"
      />
    )
  }

  return (
    <div className="rounded-xl bg-navy-950/40 border border-navy-700/30 p-3 mb-4">
      <div className="flex flex-wrap items-center justify-between gap-2 mb-2">
        <div className="text-xs text-navy-500">关系图谱 · 悬停连线查看详情 · 可拖拽缩放</div>
        {hasBidirectional ? (
          <span className="text-[10px] text-cyan-400/80">双箭头 = 双方视角</span>
        ) : null}
      </div>
      <EChart option={option} height={360} onEvents={events} />
    </div>
  )
}
