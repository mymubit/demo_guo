import { describe, expect, it } from 'vitest'
import { isCompactPcWidth } from './useDesktopLayout'

describe('PC工作台宽度分档', () => {
  it.each([
    [1280, true],
    [1366, true],
    [1399, true],
    [1440, false],
    [1920, false],
    [2560, false],
  ])('%i 像素 compact=%s', (width, expected) => {
    expect(isCompactPcWidth(width)).toBe(expected)
  })
})
