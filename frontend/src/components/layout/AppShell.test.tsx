import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { describe, expect, it, vi } from 'vitest'

vi.mock('@/auth/AuthContext', () => ({
  useAuth: () => ({
    auth: { user: { username: 'demo', nickname: '演示' } },
    logout: vi.fn(),
  }),
}))

vi.mock('@/hooks/useRecentProjects', () => ({
  useRecentProjects: () => [],
}))

import { AppShell } from './AppShell'

describe('AppShell', () => {
  it('marks projects nav with shell accent when active', () => {
    const qc = new QueryClient()
    render(
      <QueryClientProvider client={qc}>
        <MemoryRouter initialEntries={['/projects']}>
          <Routes>
            <Route element={<AppShell />}>
              <Route path="/projects" element={<div>列表</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>,
    )
    const link = screen.getByRole('link', { name: /项目/ })
    expect(link.className).toMatch(/gold|shell-accent|accent-shell/)
  })
})
