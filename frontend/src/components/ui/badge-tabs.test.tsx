import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Badge } from './Badge'
import { Tabs } from './Tabs'

describe('Badge and Tabs accents', () => {
  it('action tone avoids brand classes', () => {
    render(<Badge tone="action">进行中</Badge>)
    expect(screen.getByText('进行中').className).not.toMatch(/brand/)
    expect(screen.getByText('进行中').className).toMatch(/action/)
  })

  it('tabs active uses action underline', () => {
    render(
      <Tabs
        items={[{ id: 'a', label: '全部' }]}
        value="a"
        onChange={() => undefined}
      />,
    )
    const tab = screen.getByRole('tab', { name: '全部' })
    expect(tab.className).toMatch(/text-action/)
  })
})
