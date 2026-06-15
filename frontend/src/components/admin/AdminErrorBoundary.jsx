import { Component } from 'react'

export default class AdminErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error('[AdminErrorBoundary]', error, info)
  }

  render() {
    const { error } = this.state
    if (error) {
      return (
        <div className="glass-card rounded-2xl border border-red-500/25 bg-red-500/5 p-6 space-y-3">
          <h2 className="text-lg font-semibold text-red-300">页面渲染失败</h2>
          <p className="text-sm text-navy-300">{error.message || String(error)}</p>
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="px-4 py-2 rounded-xl text-sm bg-navy-800 text-navy-200 hover:bg-navy-700"
          >
            刷新页面
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
