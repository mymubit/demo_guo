import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { PageShell } from './PageShell'

describe('PageShell', () => {
  it('renders cold-mist header border token', () => {
    const { container } = render(
      <PageShell title="项目列表" description="管理项目">
        <div>内容</div>
      </PageShell>,
    )
    expect(screen.getByRole('heading', { name: '项目列表' })).toBeInTheDocument()
    const header = container.querySelector('header')
    expect(header?.className).toMatch(/border-border/)
  })
})
