import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { Button } from './Button'

describe('Button', () => {
  it('defaults to action variant classes', () => {
    render(<Button>保存</Button>)
    const el = screen.getByRole('button', { name: '保存' })
    expect(el.className).toMatch(/bg-action/)
    expect(el.className).not.toMatch(/bg-brand/)
  })

  it('supports shell variant for chrome-only accents', () => {
    render(<Button variant="shell">壳层</Button>)
    expect(screen.getByRole('button', { name: '壳层' }).className).toMatch(/bg-shell-accent|bg-gold/)
  })
})
