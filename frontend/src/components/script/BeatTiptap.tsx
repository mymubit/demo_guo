import { EditorContent, useEditor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import { useEffect } from 'react'

export type BeatTiptapProps = {
  value: string
  onChange: (plainText: string) => void
  disabled?: boolean
  'aria-label'?: string
}

function insertPlainTextFromClipboard(event: ClipboardEvent): string | null {
  const text = event.clipboardData?.getData('text/plain')
  if (text == null) return null
  return text
}

export function BeatTiptap({
  value,
  onChange,
  disabled = false,
  'aria-label': ariaLabel = '节拍正文',
}: BeatTiptapProps) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: { levels: [2] },
      }),
    ],
    content: value,
    editable: !disabled,
    editorProps: {
      attributes: {
        'aria-label': ariaLabel,
        role: 'textbox',
        class: 'min-h-[6rem] px-3 py-2 text-sm text-ink outline-none',
      },
      handlePaste: (view, event) => {
        const plain = insertPlainTextFromClipboard(event)
        if (plain == null) return false
        event.preventDefault()
        view.dispatch(view.state.tr.insertText(plain))
        return true
      },
    },
    onUpdate: ({ editor: current }) => {
      onChange(current.getText())
    },
  })

  useEffect(() => {
    if (!editor) return
    editor.setEditable(!disabled)
  }, [disabled, editor])

  useEffect(() => {
    if (!editor) return
    const current = editor.getText()
    if (value === current) return
    editor.commands.setContent(value, false)
  }, [value, editor])

  if (!editor) {
    return null
  }

  const toolbarBtnClass =
    'rounded border border-border bg-surface px-2 py-1 text-xs text-ink hover:bg-canvas-muted disabled:cursor-not-allowed disabled:opacity-50'

  return (
    <div className="space-y-2 rounded border border-border bg-surface">
      <div className="flex flex-wrap gap-1 border-b border-border px-2 py-1.5" role="toolbar" aria-label="格式工具栏">
        <button
          type="button"
          className={toolbarBtnClass}
          disabled={disabled}
          aria-pressed={editor.isActive('bold')}
          onClick={() => editor.chain().focus().toggleBold().run()}
        >
          粗体
        </button>
        <button
          type="button"
          className={toolbarBtnClass}
          disabled={disabled}
          aria-pressed={editor.isActive('italic')}
          onClick={() => editor.chain().focus().toggleItalic().run()}
        >
          斜体
        </button>
        <button
          type="button"
          className={toolbarBtnClass}
          disabled={disabled}
          aria-pressed={editor.isActive('heading', { level: 2 })}
          onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
        >
          标题
        </button>
        <button
          type="button"
          className={toolbarBtnClass}
          disabled={disabled}
          aria-pressed={editor.isActive('bulletList')}
          onClick={() => editor.chain().focus().toggleBulletList().run()}
        >
          列表
        </button>
        <button
          type="button"
          className={toolbarBtnClass}
          disabled={disabled}
          aria-pressed={editor.isActive('orderedList')}
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
        >
          有序列表
        </button>
      </div>
      <EditorContent editor={editor} />
    </div>
  )
}
