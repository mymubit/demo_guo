import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { KnowledgeDoc, KnowledgeDocSummary } from '@/types/v3/domain'
import { KnowledgePage } from './KnowledgePage'

const listKnowledge = vi.fn()
const getKnowledgeDoc = vi.fn()

vi.mock('@/services/v3/knowledge', () => ({
  listKnowledge: (...args: unknown[]) => listKnowledge(...args),
  getKnowledgeDoc: (...args: unknown[]) => getKnowledgeDoc(...args),
}))

const DOCS: KnowledgeDocSummary[] = [
  {
    path: 'craft/theme-templates.md',
    title: '题材模板',
    section: 'craft',
    excerpt: '题材与模板对照',
  },
  {
    path: 'market/hooks.md',
    title: '钩子清单',
    section: 'market',
    excerpt: '开篇钩子',
  },
]

const DOC: KnowledgeDoc = {
  path: 'craft/theme-templates.md',
  title: '题材模板',
  content: '# 题材模板\n\n正文示例内容。',
}

function renderKnowledge() {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/knowledge']}>
        <Routes>
          <Route path="/knowledge" element={<KnowledgePage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('KnowledgePage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    listKnowledge.mockResolvedValue({ items: DOCS })
    getKnowledgeDoc.mockResolvedValue(DOC)
  })

  it('lists knowledge docs and loads preview on click', async () => {
    const user = userEvent.setup()
    renderKnowledge()

    expect(await screen.findByRole('heading', { name: '知识库' })).toBeInTheDocument()
    expect(await screen.findByText('题材模板')).toBeInTheDocument()
    expect(screen.getByText('钩子清单')).toBeInTheDocument()

    await user.click(screen.getByTestId('knowledge-item-craft/theme-templates.md'))

    await waitFor(() => {
      expect(getKnowledgeDoc).toHaveBeenCalledWith('craft/theme-templates.md')
    })
    const preview = await screen.findByTestId('knowledge-doc-preview')
    expect(preview).toHaveTextContent('正文示例内容')
    expect(preview.querySelector('h1')).toHaveTextContent('题材模板')
    expect(preview.textContent).not.toMatch(/^#\s/m)
  })

  it('searches with q parameter', async () => {
    const user = userEvent.setup()
    listKnowledge
      .mockResolvedValueOnce({ items: DOCS })
      .mockResolvedValueOnce({ items: [DOCS[0]] })

    renderKnowledge()
    await screen.findByText('题材模板')

    await user.type(screen.getByLabelText('知识库搜索'), '题材')
    await user.click(screen.getByRole('button', { name: '搜索' }))

    await waitFor(() => {
      expect(listKnowledge).toHaveBeenLastCalledWith({ q: '题材' })
    })
  })
})
