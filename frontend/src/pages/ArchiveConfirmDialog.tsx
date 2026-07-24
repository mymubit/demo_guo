import { Button } from '@/components/ui/Button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'

interface ArchiveConfirmDialogProps {
  open: boolean
  busy?: boolean
  projectTitle?: string
  errorMessage?: string | null
  onOpenChange: (open: boolean) => void
  onConfirm: () => void
}

export function ArchiveConfirmDialog({
  open,
  busy = false,
  projectTitle,
  errorMessage,
  onOpenChange,
  onConfirm,
}: ArchiveConfirmDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>确认归档</DialogTitle>
          <DialogDescription>
            {projectTitle
              ? `归档后「${projectTitle}」将从默认列表中隐藏，可随时通过「显示已归档」查看。`
              : '归档后该项目将从默认列表中隐藏，可随时通过「显示已归档」查看。'}
          </DialogDescription>
        </DialogHeader>
        {errorMessage ? <p className="text-sm text-danger">{errorMessage}</p> : null}
        <DialogFooter>
          <Button type="button" variant="secondary" disabled={busy} onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button type="button" variant="danger" loading={busy} onClick={onConfirm}>
            确认归档
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
