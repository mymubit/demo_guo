import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { BuiltinTemplate, CustomTemplate, ProjectSummary } from '@/types/v3/domain'
import { TemplatesPage } from './TemplatesPage'

const listTemplates = vi.fn()
const createCustomTemplate = vi.fn()
const updateCustomTemplate = vi.fn()
const deleteCustomTemplate = vi.fn()
const createProject = vi.fn()
const useAuth = vi.fn()

vi.mock('@/services/v3/templates', () => ({
  listTemplates: (...args: unknown[]) => listTemplates(...args),
  createCustomTemplate: (...args: unknown[]) => createCustomTemplate(...args),
  updateCustomTemplate: (...args: unknown[]) => updateCustomTemplate(...args),
  deleteCustomTemplate: (...args: unknown[]) => deleteCustomTemplate(...args),
}))

vi.mock('@/services/v3/projects', () => ({
  createProject: (...args: unknown[]) => createProject(...args),
}))

vi.mock('@/auth/AuthContext', () => ({
  useAuth: () => useAuth(),
}))

const BUILTIN: BuiltinTemplate = {
  theme_code: 'revenge_rebirth',
  label_zh: '重生逆袭',
  dims: { tone: '爽' },
  kind: 'builtin',
}

const CUSTOM: CustomTemplate = {
  id: '22222222-2222-4222-8222-222222222222',
  name: '都市情感定制',
  theme_code: 'urban_romance',
  label_zh: '都市情感',
  dims: {},
  description: '自定义描述',
  kind: 'custom',
}

function renderTemplates(initialPath = '/templates') {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path="/templates" element={<TemplatesPage />} />
          <Route path="/projects/:id/topic" element={<div>选题定调</div>} />
          <Route path="/projects/:id" element={<div>项目概览</div>} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('TemplatesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    useAuth.mockReturnValue({
      auth: { accessToken: 't', refreshToken: 'r', user: { id: '1', is_staff: false } },
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
    })
    listTemplates.mockResolvedValue({ builtin: [BUILTIN], custom: [CUSTOM] })
  })

  it('renders builtin and custom templates', async () => {
    renderTemplates()

    expect(await screen.findByRole('heading', { name: '模板库' })).toBeInTheDocument()
    expect(await screen.findByText('重生逆袭')).toBeInTheDocument()
    expect(screen.getByText('内置模板')).toBeInTheDocument()
    expect(screen.getByText('自定义模板')).toBeInTheDocument()
    expect(screen.getByText('都市情感')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '新建自定义模板' })).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: '编辑' })).not.toBeInTheDocument()
  })

  it('staff can create custom template', async () => {
    const user = userEvent.setup()
    useAuth.mockReturnValue({
      auth: { accessToken: 't', refreshToken: 'r', user: { id: '1', is_staff: true } },
      isAuthenticated: true,
      login: vi.fn(),
      logout: vi.fn(),
    })
    createCustomTemplate.mockResolvedValue({
      ...CUSTOM,
      id: '33333333-3333-4333-8333-333333333333',
      name: '新模板',
      label_zh: '新标签',
      theme_code: 'new_theme',
    })

    renderTemplates()
    expect(await screen.findByRole('button', { name: '新建自定义模板' })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: '新建自定义模板' }))
    const dialog = await screen.findByRole('dialog')
    await user.type(within(dialog).getByLabelText('名称'), '新模板')
    await user.type(within(dialog).getByLabelText('主题码'), 'new_theme')
    await user.type(within(dialog).getByLabelText('中文标签'), '新标签')
    await user.click(within(dialog).getByRole('button', { name: '保存' }))

    await waitFor(() => {
      expect(createCustomTemplate).toHaveBeenCalledWith({
        name: '新模板',
        theme_code: 'new_theme',
        label_zh: '新标签',
        description: '',
        dims: {},
      })
    })
  })

  it('uses builtin template to create project with theme_code', async () => {
    const user = userEvent.setup()
    const project: ProjectSummary = {
      id: '11111111-1111-4111-8111-111111111111',
      title: '模板项目',
      entry_type: 'original',
      stage: 'topic',
      updated_at: '2026-07-23T00:00:00Z',
    }
    createProject.mockResolvedValue(project)

    renderTemplates()
    await screen.findByText('重生逆袭')

    const card = screen.getByTestId('builtin-template-revenge_rebirth')
    await user.click(within(card).getByRole('button', { name: '用此模板创建' }))

    const dialog = await screen.findByRole('dialog')
    await user.type(within(dialog).getByPlaceholderText('例如：重生之逆袭人生'), '模板项目')
    await user.click(within(dialog).getByRole('button', { name: '创建并进入' }))

    await waitFor(() => {
      expect(createProject).toHaveBeenCalledWith({
        title: '模板项目',
        entry_type: 'original',
        theme_code: 'revenge_rebirth',
      })
    })
    expect(await screen.findByText('选题定调')).toBeInTheDocument()
  })

  it('uses custom template to create project with template_id', async () => {
    const user = userEvent.setup()
    createProject.mockResolvedValue({
      id: '11111111-1111-4111-8111-111111111111',
      title: '自定义模板项目',
      entry_type: 'original',
      stage: 'topic',
      updated_at: '2026-07-23T00:00:00Z',
    })

    renderTemplates()
    await screen.findByText('都市情感')

    const card = screen.getByTestId(`custom-template-${CUSTOM.id}`)
    await user.click(within(card).getByRole('button', { name: '用此模板创建' }))

    const dialog = await screen.findByRole('dialog')
    await user.type(within(dialog).getByPlaceholderText('例如：重生之逆袭人生'), '自定义模板项目')
    await user.click(within(dialog).getByRole('button', { name: '创建并进入' }))

    await waitFor(() => {
      expect(createProject).toHaveBeenCalledWith({
        title: '自定义模板项目',
        entry_type: 'original',
        template_id: CUSTOM.id,
      })
    })
  })
})
