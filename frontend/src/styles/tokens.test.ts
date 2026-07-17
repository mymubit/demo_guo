import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const css = readFileSync(resolve(__dirname, 'index.css'), 'utf8')
const tw = readFileSync(resolve(__dirname, '../../tailwind.config.js'), 'utf8')

describe('design tokens', () => {
  it('defines dual accents and cold mist canvas', () => {
    expect(css).toContain('--accent-shell: #f4b719')
    expect(css).toContain('--accent-action: #0f2744')
    expect(css).toContain('--canvas: #eef1f5')
    expect(css).toContain('--shell-bg: #0a1628')
  })

  it('does not keep indigo brand-500 as system brand', () => {
    expect(css).not.toContain('--brand-500: #6366f1')
    expect(tw).not.toMatch(/brand:\s*\{[^}]*500:\s*'#6366f1'/)
  })
})
