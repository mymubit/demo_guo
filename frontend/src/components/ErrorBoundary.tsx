import { Component, type ErrorInfo, type ReactNode } from 'react'
import { Button } from '@/components/ui/Button'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

/** 捕获渲染期异常，避免整页静默白屏。 */
export class ErrorBoundary extends Component<Props, State> {
  override state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('ErrorBoundary', error, info.componentStack)
  }

  override render() {
    const { error } = this.state
    if (!error) return this.props.children

    return (
      <div className="flex min-h-dvh flex-col items-center justify-center gap-4 bg-canvas px-6 text-center">
        <h1 className="text-lg font-semibold text-ink">页面渲染失败</h1>
        <p className="max-w-xl text-sm text-ink-muted break-all">{error.message}</p>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            onClick={() => {
              this.setState({ error: null })
              window.location.assign('/login')
            }}
          >
            回登录页
          </Button>
          <Button variant="action" onClick={() => window.location.reload()}>
            刷新重试
          </Button>
        </div>
      </div>
    )
  }
}
