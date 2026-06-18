import { Component } from 'react'
import { Link } from 'react-router-dom'

export default class ConsumerErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false }
  }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch(error, info) {
    if (!import.meta.env.PROD) {
      console.error('[ConsumerErrorBoundary]', error, info)
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[40vh] flex-col items-center justify-center px-6 text-center">
          <h2 className="text-xl font-semibold text-white">页面加载出错</h2>
          <p className="mt-2 text-sm text-navy-300">请刷新页面或返回首页重试</p>
          <Link
            to="/"
            className="mt-6 rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-white hover:bg-white/10"
          >
            返回首页
          </Link>
        </div>
      )
    }
    return this.props.children
  }
}
