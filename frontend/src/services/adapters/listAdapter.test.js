import { describe, it, expect } from 'vitest'
import {
  extractListItems,
  normalizeArrayResult,
  coerceUnwrappedArray,
  normalizeListResult,
  normalizePagination,
} from './listAdapter'

describe('normalizePagination', () => {
  it('fills defaults for missing fields', () => {
    expect(normalizePagination({ total: 5, page: 2 })).toEqual({
      total: 5,
      page: 2,
      page_size: 10,
      total_pages: 1,
    })
  })
})

describe('extractListItems', () => {
  it('accepts bare array', () => {
    expect(extractListItems([{ id: 1 }])).toEqual([{ id: 1 }])
  })

  it('accepts { data: array }', () => {
    expect(extractListItems({ data: [{ id: 1 }] })).toEqual([{ id: 1 }])
  })

  it('accepts { items: array }', () => {
    expect(extractListItems({ items: [{ id: 2 }], summary: {} })).toEqual([{ id: 2 }])
  })

  it('returns empty array for invalid shapes', () => {
    expect(extractListItems(null)).toEqual([])
    expect(extractListItems({ data: 'invalid' })).toEqual([])
  })
})

describe('normalizeListResult', () => {
  it('extracts items and pagination from v2 response', () => {
    const out = normalizeListResult({
      data: [{ id: 'a1' }],
      pagination: { page: 1, page_size: 20, total: 1, total_pages: 1 },
    })
    expect(out.items).toEqual([{ id: 'a1' }])
    expect(out.pagination.total).toBe(1)
    expect(out.pagination.page).toBe(1)
  })

  it('extracts items and summary from items envelope', () => {
    const out = normalizeListResult({
      items: [{ id: 'r1' }],
      summary: { tier3: 12 },
    })
    expect(out.items).toEqual([{ id: 'r1' }])
    expect(out.summary).toEqual({ tier3: 12 })
  })

  it('returns empty items when data is not an array', () => {
    const out = normalizeListResult({ data: null })
    expect(out.items).toEqual([])
  })
})

describe('normalizeArrayResult', () => {
  it('accepts { data: array } shape', () => {
    const out = normalizeArrayResult({ data: [{ id: 1 }, { id: 2 }] })
    expect(out).toEqual([{ id: 1 }, { id: 2 }])
  })

  it('accepts { items: array } shape', () => {
    const out = normalizeArrayResult({ items: [{ id: 1 }] })
    expect(out).toEqual([{ id: 1 }])
  })

  it('accepts bare array input', () => {
    expect(normalizeArrayResult([{ id: 1 }])).toEqual([{ id: 1 }])
  })

  it('returns empty array when data is not an array', () => {
    expect(normalizeArrayResult({ data: 'invalid' })).toEqual([])
    expect(normalizeArrayResult(null)).toEqual([])
  })

  it('applies itemMapper and filters falsy results', () => {
    const out = normalizeArrayResult(
      { data: [{ id: 1 }, null, { id: 2 }] },
      (item) => (item ? { ...item, mapped: true } : null),
    )
    expect(out).toEqual([
      { id: 1, mapped: true },
      { id: 2, mapped: true },
    ])
  })
})

describe('coerceUnwrappedArray', () => {
  it('accepts bare array from axios unwrap', () => {
    const out = coerceUnwrappedArray([{ id: 1 }, { id: 2 }])
    expect(out).toEqual([{ id: 1 }, { id: 2 }])
  })

  it('falls back to normalizeArrayResult for envelope shape', () => {
    const out = coerceUnwrappedArray({ data: [{ id: 3 }] })
    expect(out).toEqual([{ id: 3 }])
  })

  it('accepts items envelope shape', () => {
    const out = coerceUnwrappedArray({ items: [{ id: 4 }] })
    expect(out).toEqual([{ id: 4 }])
  })
})
