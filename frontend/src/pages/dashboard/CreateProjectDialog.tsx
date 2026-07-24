import { useState } from 'react'
import { Button } from '@/components/ui/Button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import type { CreateProjectRequest, ProjectEntryType } from '@/types/v3/domain'

interface CreateProjectDialogProps {
  open: boolean
  busy?: boolean
  errorMessage?: string | null
  /** 用模板建项：theme_code 或 template_id（互斥） */
  seed?: { theme_code?: string; template_id?: string } | null
  onOpenChange: (open: boolean) => void
  onSubmit: (body: CreateProjectRequest) => void
}

export function CreateProjectDialog({
  open,
  busy = false,
  errorMessage,
  seed = null,
  onOpenChange,
  onSubmit,
}: CreateProjectDialogProps) {
  const [title, setTitle] = useState('')
  const [entryType, setEntryType] = useState<ProjectEntryType>('original')

  const handleOpenChange = (next: boolean) => {
    if (!next) {
      setTitle('')
      setEntryType('original')
    }
    onOpenChange(next)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>新建项目</DialogTitle>
          <DialogDescription>
            {seed?.theme_code || seed?.template_id
              ? '将使用所选模板预填选题草稿；创建后自动开始选题定调。'
              : '填写标题并选择创作来源；创建后自动开始选题定调。'}
          </DialogDescription>
        </DialogHeader>
        <form
          className="space-y-4"
          onSubmit={(event) => {
            event.preventDefault()
            const trimmed = title.trim()
            if (!trimmed || busy) return
            const body: CreateProjectRequest = { title: trimmed, entry_type: entryType }
            if (seed?.template_id) {
              body.template_id = seed.template_id
            } else if (seed?.theme_code) {
              body.theme_code = seed.theme_code
            }
            onSubmit(body)
          }}
        >
          <label className="block space-y-1.5 text-sm font-medium text-ink">
            项目标题
            <Input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="例如：重生之逆袭人生"
              required
              autoFocus
              disabled={busy}
            />
          </label>
          <label className="block space-y-1.5 text-sm font-medium text-ink">
            创作来源
            <select
              value={entryType}
              onChange={(event) => setEntryType(event.target.value as ProjectEntryType)}
              disabled={busy}
              className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value="original">原创</option>
              <option value="adapt">改编</option>
            </select>
          </label>
          {errorMessage ? <p className="text-sm text-danger">{errorMessage}</p> : null}
          <DialogFooter>
            <Button type="button" variant="secondary" disabled={busy} onClick={() => handleOpenChange(false)}>
              取消
            </Button>
            <Button type="submit" loading={busy}>
              创建并进入
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
