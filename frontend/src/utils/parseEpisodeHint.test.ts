import { describe, expect, it } from 'vitest'
import { parseEpisodeNumber } from '@/utils/parseEpisodeHint'

describe('parseEpisodeNumber', () => {
  it('reads episode_number from object', () => {
    expect(parseEpisodeNumber({ episode_number: 3 })).toBe(3)
    expect(parseEpisodeNumber({ episode_number: '5' })).toBe(5)
  })

  it('reads episode from object when episode_number missing', () => {
    expect(parseEpisodeNumber({ episode: 2 })).toBe(2)
    expect(parseEpisodeNumber({ episode: '4' })).toBe(4)
  })

  it('prefers episode_number over episode on object', () => {
    expect(parseEpisodeNumber({ episode_number: 1, episode: 9 })).toBe(1)
  })

  it('parses 第N集 from text', () => {
    expect(parseEpisodeNumber('问题出现在第 12 集')).toBe(12)
    expect(parseEpisodeNumber('第3集节奏偏慢')).toBe(3)
  })

  it('parses plain numeric strings', () => {
    expect(parseEpisodeNumber('7')).toBe(7)
  })

  it('returns null for invalid input', () => {
    expect(parseEpisodeNumber(null)).toBeNull()
    expect(parseEpisodeNumber(undefined)).toBeNull()
    expect(parseEpisodeNumber('')).toBeNull()
    expect(parseEpisodeNumber(0)).toBeNull()
    expect(parseEpisodeNumber(-1)).toBeNull()
    expect(parseEpisodeNumber('abc')).toBeNull()
    expect(parseEpisodeNumber([])).toBeNull()
  })
})
