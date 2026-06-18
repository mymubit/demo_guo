import SkillEditorPanel from './workspace/SkillEditorPanel'

export default function ArtifactPreviewPanel({ editorView }) {
  if (!editorView) {
    return <p className="text-sm text-navy-400">暂无预览内容。</p>
  }

  if (editorView.mode === 'json') {
    return (
      <pre className="max-h-[520px] overflow-auto whitespace-pre-wrap text-xs leading-relaxed text-navy-100">
        {JSON.stringify(editorView.payload, null, 2)}
      </pre>
    )
  }

  return (
    <div className="max-h-[520px] overflow-auto">
      <SkillEditorPanel
        skill={{ index: 0 }}
        editor={editorView}
        editMode={false}
      />
    </div>
  )
}
