import { BeatTiptap } from '@/components/script/BeatTiptap'
import type { ScriptBeat, ScriptScene } from '@/types/v3/domain'

export type SceneListEditorProps = {
  scenes: ScriptScene[]
  onChange: (scenes: ScriptScene[]) => void
  disabled?: boolean
}

function updateScene(
  scenes: ScriptScene[],
  sceneIndex: number,
  patch: Partial<ScriptScene>,
): ScriptScene[] {
  return scenes.map((scene, index) => (index === sceneIndex ? { ...scene, ...patch } : scene))
}

function updateBeat(
  scenes: ScriptScene[],
  sceneIndex: number,
  beatIndex: number,
  patch: Partial<ScriptBeat>,
): ScriptScene[] {
  return scenes.map((scene, index) => {
    if (index !== sceneIndex) return scene
    return {
      ...scene,
      beats: scene.beats.map((beat, bi) => (bi === beatIndex ? { ...beat, ...patch } : beat)),
    }
  })
}

function beatLabel(type: string): string {
  if (type === 'dialogue') return '对白'
  if (type === 'action') return '动作'
  return type || '文本'
}

export function SceneListEditor({ scenes, onChange, disabled = false }: SceneListEditorProps) {
  const handleAddScene = () => {
    const nextId = `s${scenes.length + 1}`
    onChange([
      ...scenes,
      {
        id: nextId,
        heading: '',
        beats: [{ type: 'action', text: '' }],
      },
    ])
  }

  const handleAddBeat = (sceneIndex: number, type: 'action' | 'dialogue') => {
    const scene = scenes[sceneIndex]
    if (!scene) return
    const beat: ScriptBeat =
      type === 'dialogue' ? { type, text: '', character: '' } : { type, text: '' }
    onChange(updateScene(scenes, sceneIndex, { beats: [...scene.beats, beat] }))
  }

  if (scenes.length === 0) {
    return (
      <div className="sf-panel space-y-3 p-4">
        <p className="text-sm text-ink-muted">暂无场景，可新增一场开始编辑。</p>
        <button
          type="button"
          className="text-sm text-action underline disabled:opacity-50"
          disabled={disabled}
          onClick={handleAddScene}
        >
          新增场次
        </button>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {scenes.map((scene, sceneIndex) => (
        <article key={scene.id || `scene-${sceneIndex}`} className="sf-panel space-y-3 p-4">
          <label className="block space-y-1">
            <span className="text-xs text-ink-faint">场次标题</span>
            <input
              type="text"
              value={scene.heading}
              disabled={disabled}
              onChange={(event) =>
                onChange(updateScene(scenes, sceneIndex, { heading: event.target.value }))
              }
              className="w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink"
              placeholder="如 INT. 咖啡厅 - 日"
            />
          </label>

          <div className="space-y-3">
            {scene.beats.map((beat, beatIndex) => (
              <div key={`${scene.id}-beat-${beatIndex}`} className="space-y-1">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs text-ink-faint">{beatLabel(beat.type)}</span>
                  {beat.type === 'dialogue' ? (
                    <input
                      type="text"
                      value={beat.character ?? ''}
                      disabled={disabled}
                      onChange={(event) =>
                        onChange(
                          updateBeat(scenes, sceneIndex, beatIndex, {
                            character: event.target.value,
                          }),
                        )
                      }
                      className="w-40 rounded-md border border-border bg-surface px-2 py-1 text-xs text-ink"
                      placeholder="角色"
                      aria-label={`第 ${sceneIndex + 1} 场对白角色`}
                    />
                  ) : null}
                </div>
                <BeatTiptap
                  value={beat.text}
                  disabled={disabled}
                  onChange={(text) =>
                    onChange(updateBeat(scenes, sceneIndex, beatIndex, { text }))
                  }
                  aria-label={`${beatLabel(beat.type)}文本`}
                />
              </div>
            ))}
          </div>

          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              className="text-xs text-action underline disabled:opacity-50"
              disabled={disabled}
              onClick={() => handleAddBeat(sceneIndex, 'action')}
            >
              加动作
            </button>
            <button
              type="button"
              className="text-xs text-action underline disabled:opacity-50"
              disabled={disabled}
              onClick={() => handleAddBeat(sceneIndex, 'dialogue')}
            >
              加对白
            </button>
          </div>
        </article>
      ))}

      <button
        type="button"
        className="text-sm text-action underline disabled:opacity-50"
        disabled={disabled}
        onClick={handleAddScene}
      >
        新增场次
      </button>
    </div>
  )
}
