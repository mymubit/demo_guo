import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const src = readFileSync(resolve(__dirname, 'LoginPage.tsx'), 'utf8')

describe('LoginPage tokens', () => {
  it('does not reference indigo brand utilities', () => {
    expect(src).not.toMatch(/brand-500|brand-600|#6366f1/)
  })

  it('does not use Studio or Operation graph branding', () => {
    expect(src).not.toMatch(/Operation graph|Studio V6|operation/i)
  })
})
