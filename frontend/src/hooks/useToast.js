// 统一的消息提示封装 — 基于 sonner
//
// 设计原则:
// 1. 统一规范 — 全站所有消息提示都通过这里
// 2. 克制使用 — 成功操作最多2500ms显示,失败最多5000ms
// 3. 语义统一 — 文案遵循模块5规范

import { toast } from 'sonner'

const DURATION = {
  SUCCESS: 2500,
  ERROR: 5000,
  WARNING: 4000,
  INFO: 3000,
}

export function useToast() {
  return {
    // 操作成功
    success(message = '操作成功', description) {
      return toast.success(message, {
      description,
      duration: DURATION.SUCCESS,
    })
  },

    // 操作失败
    error(message = '操作失败', description) {
      return toast.error(message, {
        description,
        duration: DURATION.ERROR,
      })
    },

    // 警告
    warning(message = '请注意', description) {
      return toast.warning(message, {
        description,
        duration: DURATION.WARNING,
      })
    },

    // 信息
    info(message, description) {
      return toast(message, {
        description,
        duration: DURATION.INFO,
      })
    },

    // 加载中 — 返回 toast id，用于后续 dismiss/update
    loading(message = '处理中...') {
      return toast.loading(message)
    },

    // 异步操作的一体式消息 — 自动管理 loading/success/error
    promise(promise, messages) {
      return toast.promise(promise, {
        loading: messages.loading || '处理中...',
        success: messages.success,
        error: messages.error || '操作失败',
      })
    },

    // 手动关闭
    dismiss(toastId) {
      if (toastId !== undefined) {
        toast.dismiss(toastId)
      } else {
        toast.dismiss()
      }
    },
  }
}

// 便捷函数 — 无需在组件hook时直接调用
const globalToast = {
  success: (m, d) => toast.success(m, { description: d, duration: DURATION.SUCCESS }),
  error: (m, d) => toast.error(m, { description: d, duration: DURATION.ERROR }),
  warning: (m, d) => toast.warning(m, { description: d, duration: DURATION.WARNING }),
  info: (m, d) => toast(m, { description: d, duration: DURATION.INFO }),
  loading: m => toast.loading(m),
  dismiss: id => toast.dismiss(id),
  promise: (p, m) =>
    toast.promise(p, {
      loading: m.loading,
      success: m.success,
      error: m.error,
    }),
}

export const toastMessage = globalToast
