import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type {
  ModelPrice,
  ModelProvider,
  ProviderKey,
  RoleModelMappingTable,
} from '@/types/v3/domain'
import { ROLE_MODEL_KEYS } from '@/types/v3/domain'
import { ModelsPage } from './ModelsPage'

const listProviders = vi.fn()
const createProvider = vi.fn()
const updateProvider = vi.fn()
const deleteProvider = vi.fn()
const activateProvider = vi.fn()
const testProvider = vi.fn()
const listProviderKeys = vi.fn()
const createProviderKey = vi.fn()
const deleteProviderKey = vi.fn()
const getRoleMappings = vi.fn()
const putRoleMappings = vi.fn()
const getModelPrices = vi.fn()
const putModelPrices = vi.fn()
const deleteModelPrice = vi.fn()

vi.mock('@/services/v3/models', () => ({
  listProviders: (...args: unknown[]) => listProviders(...args),
  createProvider: (...args: unknown[]) => createProvider(...args),
  updateProvider: (...args: unknown[]) => updateProvider(...args),
  deleteProvider: (...args: unknown[]) => deleteProvider(...args),
  activateProvider: (...args: unknown[]) => activateProvider(...args),
  testProvider: (...args: unknown[]) => testProvider(...args),
  listProviderKeys: (...args: unknown[]) => listProviderKeys(...args),
  createProviderKey: (...args: unknown[]) => createProviderKey(...args),
  updateProviderKey: vi.fn(),
  deleteProviderKey: (...args: unknown[]) => deleteProviderKey(...args),
  getRoleMappings: (...args: unknown[]) => getRoleMappings(...args),
  putRoleMappings: (...args: unknown[]) => putRoleMappings(...args),
}))

vi.mock('@/services/v3/prices', () => ({
  getModelPrices: (...args: unknown[]) => getModelPrices(...args),
  putModelPrices: (...args: unknown[]) => putModelPrices(...args),
  deleteModelPrice: (...args: unknown[]) => deleteModelPrice(...args),
}))

function makeProvider(overrides: Partial<ModelProvider> = {}): ModelProvider {
  return {
    id: overrides.id ?? '11111111-1111-1111-1111-111111111111',
    name: overrides.name ?? '默认供应商',
    base_url: overrides.base_url ?? 'https://llm.example/v1',
    model_name: overrides.model_name ?? 'gpt-test',
    temperature: overrides.temperature ?? 0.7,
    max_tokens: overrides.max_tokens ?? 4096,
    is_enabled: overrides.is_enabled ?? true,
    is_active: overrides.is_active ?? false,
    api_key_set: overrides.api_key_set ?? true,
    remark: overrides.remark ?? '',
    updated_at: overrides.updated_at ?? '2026-07-23T00:00:00Z',
  }
}

function makeMappings(providerId: string): RoleModelMappingTable {
  return {
    items: ROLE_MODEL_KEYS.map((role_key) => ({
      role_key,
      provider_id: providerId,
      backup_provider_ids: [],
      temperature: null,
      max_tokens: null,
      updated_at: null as unknown as string,
    })),
  }
}

function renderModels() {
  const client = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={['/models']}>
        <Routes>
          <Route path="/models" element={<ModelsPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe('ModelsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    getModelPrices.mockResolvedValue({ items: [] })
    listProviderKeys.mockResolvedValue({ items: [] })
  })

  it('renders Chinese UI without operation ids or plaintext keys', async () => {
    const provider = makeProvider({
      name: '主模型',
      is_active: true,
      api_key_set: true,
    })
    listProviders.mockResolvedValue({ items: [provider] })
    getRoleMappings.mockResolvedValue(makeMappings(provider.id))

    renderModels()

    expect(await screen.findByRole('heading', { name: '模型配置' })).toBeInTheDocument()
    expect(await screen.findByText('供应商列表')).toBeInTheDocument()
    expect(screen.getByText('角色映射')).toBeInTheDocument()
    expect(screen.getByText(/密钥：已配置/)).toBeInTheDocument()
    expect(screen.queryByText(/sk-/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/operation\./i)).not.toBeInTheDocument()
    expect(screen.queryByText(/test_model_provider/i)).not.toBeInTheDocument()
  })

  it('creates a provider with api_key via drawer', async () => {
    const user = userEvent.setup()
    listProviders.mockResolvedValue({ items: [] })
    getRoleMappings.mockResolvedValue({ items: [] })
    const created = makeProvider({
      id: '22222222-2222-2222-2222-222222222222',
      name: '新供应商',
      api_key_set: true,
    })
    createProvider.mockResolvedValue(created)

    renderModels()

    await user.click(await screen.findByRole('button', { name: '新建供应商' }))
    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText('新建供应商')).toBeInTheDocument()

    await user.type(within(dialog).getByLabelText('供应商名称'), '新供应商')
    await user.type(within(dialog).getByLabelText('Base URL'), 'https://new.example/v1')
    await user.clear(within(dialog).getByLabelText('模型名称'))
    await user.type(within(dialog).getByLabelText('模型名称'), 'gpt-new')
    await user.type(within(dialog).getByLabelText('API Key'), 'sk-secret-never-show')
    await user.click(within(dialog).getByRole('button', { name: '创建' }))

    await waitFor(() => {
      expect(createProvider).toHaveBeenCalledWith(
        expect.objectContaining({
          name: '新供应商',
          base_url: 'https://new.example/v1',
          model_name: 'gpt-new',
          api_key: 'sk-secret-never-show',
        }),
      )
    })
  })

  it('edits provider without sending empty api_key', async () => {
    const user = userEvent.setup()
    const provider = makeProvider({ name: '可编辑', api_key_set: true })
    listProviders.mockResolvedValue({ items: [provider] })
    getRoleMappings.mockResolvedValue(makeMappings(provider.id))
    updateProvider.mockResolvedValue({ ...provider, name: '已改名' })

    renderModels()

    await user.click(await screen.findByRole('button', { name: '编辑' }))
    const dialog = await screen.findByRole('dialog')
    const nameInput = within(dialog).getByLabelText('供应商名称')
    await user.clear(nameInput)
    await user.type(nameInput, '已改名')
    // API Key 保持空
    expect(within(dialog).getByLabelText('API Key')).toHaveValue('')
    await user.click(within(dialog).getByRole('button', { name: '保存' }))

    await waitFor(() => {
      expect(updateProvider).toHaveBeenCalledWith(
        provider.id,
        expect.objectContaining({ name: '已改名' }),
      )
    })
    const body = updateProvider.mock.calls[0][1] as Record<string, unknown>
    expect(body).not.toHaveProperty('api_key')
  })

  it('activates a provider and shows test result', async () => {
    const user = userEvent.setup()
    const inactive = makeProvider({
      id: '33333333-3333-3333-3333-333333333333',
      name: '备用模型',
      is_active: false,
      api_key_set: true,
    })
    const active = makeProvider({
      id: '44444444-4444-4444-4444-444444444444',
      name: '主模型',
      is_active: true,
      api_key_set: true,
    })
    listProviders.mockResolvedValue({ items: [inactive, active] })
    getRoleMappings.mockResolvedValue(makeMappings(active.id))
    activateProvider.mockResolvedValue({ ...inactive, is_active: true })
    testProvider.mockResolvedValue({
      ok: true,
      provider_id: inactive.id,
      message: '连通成功',
      latency_ms: 42,
    })

    renderModels()

    expect(await screen.findByText('备用模型')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '激活 备用模型' }))
    await waitFor(() => {
      expect(activateProvider).toHaveBeenCalledWith(inactive.id)
    })

    await user.click(screen.getByRole('button', { name: '试连 备用模型' }))
    expect(await screen.findByTestId(`test-result-${inactive.id}`)).toHaveTextContent(
      /连通成功.*42 ms/,
    )
    expect(testProvider).toHaveBeenCalledWith(inactive.id)
  })

  it('saves role mapping table', async () => {
    const user = userEvent.setup()
    const a = makeProvider({
      id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      name: '供应商A',
      is_active: true,
    })
    const b = makeProvider({
      id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
      name: '供应商B',
      is_active: false,
    })
    listProviders.mockResolvedValue({ items: [a, b] })
    getRoleMappings.mockResolvedValue(makeMappings(a.id))
    putRoleMappings.mockResolvedValue({
      items: ROLE_MODEL_KEYS.map((role_key) => ({
        role_key,
        provider_id: role_key === 'drama-script-writer' ? b.id : a.id,
        backup_provider_ids: [],
      })),
    })

    renderModels()

    const select = await screen.findByLabelText('角色 剧本正文 的主供应商')
    await user.selectOptions(select, b.id)
    await user.click(screen.getByRole('button', { name: '保存映射' }))

    await waitFor(() => {
      expect(putRoleMappings).toHaveBeenCalled()
    })
    const body = putRoleMappings.mock.calls[0][0] as RoleModelMappingTable
    const writer = body.items.find((item) => item.role_key === 'drama-script-writer')
    expect(writer?.provider_id).toBe(b.id)
  })

  it('adds backup providers and PUTs backup_provider_ids', async () => {
    const user = userEvent.setup()
    const primary = makeProvider({
      id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      name: '主供应商',
      is_active: true,
    })
    const backupA = makeProvider({
      id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
      name: '备选甲',
      is_active: false,
    })
    const backupB = makeProvider({
      id: 'cccccccc-cccc-cccc-cccc-cccccccccccc',
      name: '备选乙',
      is_active: false,
    })
    listProviders.mockResolvedValue({ items: [primary, backupA, backupB] })
    getRoleMappings.mockResolvedValue({
      items: ROLE_MODEL_KEYS.map((role_key) => ({
        role_key,
        provider_id: primary.id,
        backup_provider_ids: [],
        temperature: null,
        max_tokens: null,
      })),
    })
    putRoleMappings.mockResolvedValue({
      items: ROLE_MODEL_KEYS.map((role_key) => ({
        role_key,
        provider_id: primary.id,
        backup_provider_ids:
          role_key === 'drama-script-writer' ? [backupA.id, backupB.id] : [],
      })),
    })

    renderModels()

    const writerRow = await screen.findByTestId('role-mapping-drama-script-writer')
    expect(within(writerRow).getByText('备选供应商')).toBeInTheDocument()
    expect(screen.queryByText(/operation\./i)).not.toBeInTheDocument()

    const addSelect = within(writerRow).getByLabelText('角色 剧本正文 添加备选')
    await user.selectOptions(addSelect, backupA.id)
    await user.click(
      within(writerRow).getByRole('button', { name: '角色 剧本正文 添加备选供应商' }),
    )

    expect(
      within(writerRow).getByRole('button', { name: '角色 剧本正文 备选甲 删除' }),
    ).toBeInTheDocument()

    await user.selectOptions(
      within(writerRow).getByLabelText('角色 剧本正文 添加备选'),
      backupB.id,
    )
    await user.click(
      within(writerRow).getByRole('button', { name: '角色 剧本正文 添加备选供应商' }),
    )

    expect(
      within(writerRow).getByRole('button', { name: '角色 剧本正文 备选乙 删除' }),
    ).toBeInTheDocument()

    await user.click(
      within(writerRow).getByRole('button', { name: '角色 剧本正文 备选乙 上移' }),
    )
    await user.click(screen.getByRole('button', { name: '保存映射' }))

    await waitFor(() => {
      expect(putRoleMappings).toHaveBeenCalled()
    })
    const body = putRoleMappings.mock.calls[0][0] as RoleModelMappingTable
    const writer = body.items.find((item) => item.role_key === 'drama-script-writer')
    expect(writer?.provider_id).toBe(primary.id)
    expect(writer?.backup_provider_ids).toEqual([backupB.id, backupA.id])
  })

  it('removes a backup provider from the ordered list', async () => {
    const user = userEvent.setup()
    const primary = makeProvider({
      id: 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
      name: '主供应商',
      is_active: true,
    })
    const backup = makeProvider({
      id: 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
      name: '待删备选',
      is_active: false,
    })
    listProviders.mockResolvedValue({ items: [primary, backup] })
    getRoleMappings.mockResolvedValue({
      items: ROLE_MODEL_KEYS.map((role_key) => ({
        role_key,
        provider_id: primary.id,
        backup_provider_ids: role_key === 'drama-script-writer' ? [backup.id] : [],
        temperature: null,
        max_tokens: null,
      })),
    })
    putRoleMappings.mockResolvedValue({
      items: ROLE_MODEL_KEYS.map((role_key) => ({
        role_key,
        provider_id: primary.id,
        backup_provider_ids: [],
      })),
    })

    renderModels()

    const writerRow = await screen.findByTestId('role-mapping-drama-script-writer')
    expect(
      within(writerRow).getByRole('button', { name: '角色 剧本正文 待删备选 删除' }),
    ).toBeInTheDocument()
    await user.click(
      within(writerRow).getByRole('button', { name: '角色 剧本正文 待删备选 删除' }),
    )
    expect(
      within(writerRow).queryByRole('button', { name: '角色 剧本正文 待删备选 删除' }),
    ).not.toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: '保存映射' }))
    await waitFor(() => {
      expect(putRoleMappings).toHaveBeenCalled()
    })
    const body = putRoleMappings.mock.calls[0][0] as RoleModelMappingTable
    const writer = body.items.find((item) => item.role_key === 'drama-script-writer')
    expect(writer?.backup_provider_ids).toEqual([])
  })

  it('shows load error in Chinese', async () => {
    listProviders.mockRejectedValue(new Error('网络异常'))
    getRoleMappings.mockResolvedValue({ items: [] })

    renderModels()

    expect(await screen.findByText(/网络异常/)).toBeInTheDocument()
    expect(screen.queryByText('供应商列表')).not.toBeInTheDocument()
  })

  it('deletes a provider after confirm and refreshes list', async () => {
    const user = userEvent.setup()
    const provider = makeProvider({
      id: 'dddddddd-dddd-dddd-dddd-dddddddddddd',
      name: '待删除供应商',
      is_active: false,
    })
    listProviders
      .mockResolvedValueOnce({ items: [provider] })
      .mockResolvedValueOnce({ items: [] })
    getRoleMappings.mockResolvedValue(makeMappings(provider.id))
    deleteProvider.mockResolvedValue(null)
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)

    renderModels()

    expect(await screen.findByText('待删除供应商')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '删除 待删除供应商' }))

    expect(confirmSpy).toHaveBeenCalled()
    await waitFor(() => {
      expect(deleteProvider).toHaveBeenCalledWith(provider.id)
    })
    await waitFor(() => {
      expect(listProviders.mock.calls.length).toBeGreaterThanOrEqual(2)
    })
    await waitFor(() => {
      expect(screen.queryByText('待删除供应商')).not.toBeInTheDocument()
    })

    confirmSpy.mockRestore()
  })

  it('does not delete when confirm is cancelled', async () => {
    const user = userEvent.setup()
    const provider = makeProvider({ name: '保留供应商', is_active: true })
    listProviders.mockResolvedValue({ items: [provider] })
    getRoleMappings.mockResolvedValue(makeMappings(provider.id))
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false)

    renderModels()

    expect(await screen.findByText('保留供应商')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: '删除 保留供应商' }))

    expect(confirmSpy).toHaveBeenCalled()
    expect(deleteProvider).not.toHaveBeenCalled()
    expect(screen.getByText('保留供应商')).toBeInTheDocument()

    confirmSpy.mockRestore()
  })

  it('adds and removes extra provider keys without showing plaintext', async () => {
    const user = userEvent.setup()
    const provider = makeProvider({
      id: 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
      name: '多密钥供应商',
      is_active: true,
    })
    const createdKey: ProviderKey = {
      id: 'ffffffff-ffff-ffff-ffff-ffffffffffff',
      provider_id: provider.id,
      label: '备用线路',
      sort_order: 0,
      is_enabled: true,
      api_key_set: true,
    }
    listProviders.mockResolvedValue({ items: [provider] })
    getRoleMappings.mockResolvedValue(makeMappings(provider.id))
    listProviderKeys
      .mockResolvedValueOnce({ items: [] })
      .mockResolvedValueOnce({ items: [createdKey] })
      .mockResolvedValueOnce({ items: [] })
    createProviderKey.mockResolvedValue(createdKey)
    deleteProviderKey.mockResolvedValue(null)
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(true)

    renderModels()

    await user.click(await screen.findByRole('button', { name: '管理 多密钥供应商 附加密钥' }))
    const panel = await screen.findByTestId(`provider-keys-${provider.id}`)
    expect(within(panel).getByText('暂无附加密钥。')).toBeInTheDocument()

    await user.type(within(panel).getByLabelText('多密钥供应商 附加密钥标签'), '备用线路')
    await user.type(
      within(panel).getByLabelText('多密钥供应商 附加密钥 API Key'),
      'sk-extra-never-show',
    )
    await user.click(within(panel).getByRole('button', { name: '添加 多密钥供应商 附加密钥' }))

    await waitFor(() => {
      expect(createProviderKey).toHaveBeenCalledWith(provider.id, {
        label: '备用线路',
        api_key: 'sk-extra-never-show',
      })
    })
    const keyRow = await screen.findByTestId(`provider-key-${createdKey.id}`)
    expect(within(keyRow).getByText('备用线路')).toBeInTheDocument()
    expect(within(keyRow).getByText(/已配置/)).toBeInTheDocument()
    expect(screen.queryByText(/sk-extra/i)).not.toBeInTheDocument()

    await user.click(within(panel).getByRole('button', { name: '删除附加密钥 备用线路' }))
    await waitFor(() => {
      expect(deleteProviderKey).toHaveBeenCalledWith(provider.id, createdKey.id)
    })

    confirmSpy.mockRestore()
  })

  it('fills inline price inputs from GET prices and saves via PUT', async () => {
    const user = userEvent.setup()
    const provider = makeProvider({ name: '定价供应商', model_name: 'gpt-test' })
    const existing: ModelPrice = {
      id: 42,
      provider_id: provider.id,
      provider_name: provider.name,
      model_name: 'gpt-test',
      price_in_per_1k: 0.001,
      price_out_per_1k: 0.002,
      price_cache_in_per_1k: 0.0001,
      currency: 'CNY',
    }
    listProviders.mockResolvedValue({ items: [provider] })
    getRoleMappings.mockResolvedValue(makeMappings(provider.id))
    getModelPrices.mockResolvedValue({ items: [existing] })
    putModelPrices.mockResolvedValue({
      items: [
        {
          ...existing,
          price_in_per_1k: 0.01,
          price_out_per_1k: 0.02,
          price_cache_in_per_1k: 0.001,
        },
      ],
    })

    renderModels()

    const panel = await screen.findByTestId(`provider-price-${provider.id}`)
    const inInput = within(panel).getByLabelText('定价供应商 输入单价')
    const outInput = within(panel).getByLabelText('定价供应商 输出单价')
    const cacheInput = within(panel).getByLabelText('定价供应商 缓存命中单价')
    expect(inInput).toHaveValue(0.001)
    expect(outInput).toHaveValue(0.002)
    expect(cacheInput).toHaveValue(0.0001)

    await user.clear(inInput)
    await user.type(inInput, '0.01')
    await user.clear(outInput)
    await user.type(outInput, '0.02')
    await user.clear(cacheInput)
    await user.type(cacheInput, '0.001')
    await user.click(within(panel).getByRole('button', { name: '保存 定价供应商 定价' }))

    await waitFor(() => {
      expect(putModelPrices).toHaveBeenCalledWith({
        items: [
          {
            provider_id: provider.id,
            model_name: 'gpt-test',
            price_in_per_1k: 0.01,
            price_out_per_1k: 0.02,
            price_cache_in_per_1k: 0.001,
            currency: 'CNY',
          },
        ],
      })
    })
    expect(deleteModelPrice).not.toHaveBeenCalled()
  })

  it('clears price via DELETE when both inputs empty', async () => {
    const user = userEvent.setup()
    const provider = makeProvider({ name: '清空定价', model_name: 'gpt-test' })
    const existing: ModelPrice = {
      id: 7,
      provider_id: provider.id,
      provider_name: provider.name,
      model_name: 'gpt-test',
      price_in_per_1k: 0.001,
      price_out_per_1k: 0.002,
      currency: 'CNY',
    }
    listProviders.mockResolvedValue({ items: [provider] })
    getRoleMappings.mockResolvedValue(makeMappings(provider.id))
    getModelPrices.mockResolvedValue({ items: [existing] })
    deleteModelPrice.mockResolvedValue({ deleted: true, id: 7 })

    renderModels()

    const panel = await screen.findByTestId(`provider-price-${provider.id}`)
    await user.clear(within(panel).getByLabelText('清空定价 输入单价'))
    await user.clear(within(panel).getByLabelText('清空定价 输出单价'))
    await user.click(within(panel).getByRole('button', { name: '保存 清空定价 定价' }))

    await waitFor(() => {
      expect(deleteModelPrice).toHaveBeenCalledWith(7)
    })
    expect(putModelPrices).not.toHaveBeenCalled()
  })

  it('blocks save when only one price side is filled', async () => {
    const user = userEvent.setup()
    const provider = makeProvider({ name: '半边定价' })
    listProviders.mockResolvedValue({ items: [provider] })
    getRoleMappings.mockResolvedValue(makeMappings(provider.id))

    renderModels()

    const panel = await screen.findByTestId(`provider-price-${provider.id}`)
    await user.type(within(panel).getByLabelText('半边定价 输入单价'), '0.01')
    await user.click(within(panel).getByRole('button', { name: '保存 半边定价 定价' }))

    expect(await within(panel).findByText(/同时填写输入与输出单价/)).toBeInTheDocument()
    expect(putModelPrices).not.toHaveBeenCalled()
    expect(deleteModelPrice).not.toHaveBeenCalled()
  })
})
