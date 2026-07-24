import { Button } from '@/components/ui/Button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

interface DeleteConfirmDialogProps {
  open: boolean
  busy?: boolean
  projectTitle?: string
  errorMessage?: string | null
  onOpenChange: (open: boolean) => void
  onConfirm: () => void
}

export function DeleteConfirmDialog({
  open,
  busy = false,
  projectTitle,
  errorMessage,
  onOpenChange,
  onConfirm,
}: DeleteConfirmDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>确认删除</DialogTitle>
          <DialogDescription>
            {projectTitle
              ? `将永久删除「${projectTitle}」及其产物与任务记录，此操作不可恢复。`
              : '将永久删除该项目及其产物与任务记录，此操作不可恢复。'}
          </DialogDescription>
        </DialogHeader>
        {errorMessage ? <p className="text-sm text-danger">{errorMessage}</p> : null}
        <DialogFooter>
          <Button type="button" variant="secondary" disabled={busy} onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button type="button" variant="danger" loading={busy} onClick={onConfirm}>
            确认删除
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
