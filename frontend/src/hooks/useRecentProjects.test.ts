import { describe, expect, it, beforeEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useRecentProjects } from '@/hooks/useRecentProjects'
import { rememberRecentProject } from '@/utils/recentProjects'

describe('useRecentProjects', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('refreshes when recent projects change in the same page', () => {
    const { result } = renderHook(() => useRecentProjects(1))
    expect(result.current).toEqual([])

    act(() => {
      rememberRecentProject({ id: 'p1', title: '侧栏项目' })
    })

    expect(result.current[0]?.id).toBe('p1')
    expect(result.current[0]?.title).toBe('侧栏项目')
  })
})
