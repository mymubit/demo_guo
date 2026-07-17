import { describe, expect, it } from 'vitest'

describe('shadcn primitives', () => {
  it('exposes Input module', async () => {
    const mod = await import('./input')
    expect(mod.Input).toBeTypeOf('function')
  })
})
