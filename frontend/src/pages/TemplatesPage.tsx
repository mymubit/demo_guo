import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/auth/AuthContext'
import { PageShell } from '@/components/layout/PageShell'
import { Button } from '@/components/ui/Button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { formatApiError } from '@/services/errors'
import { createProject } from '@/services/v3/projects'
import {
  createCustomTemplate,
  deleteCustomTemplate,
  listTemplates,
  updateCustomTemplate,
} from '@/services/v3/templates'
import type {
  BuiltinTemplate,
  CreateProjectRequest,
  CustomTemplate,
  CustomTemplateWrite,
} from '@/types/v3/domain'
import { CreateProjectDialog } from './dashboard/CreateProjectDialog'

const TEMPLATES_QUERY_KEY = ['v3', 'templates'] as const

type TemplateSeed = { theme_code?: string; template_id?: string }

type CustomFormState = {
  name: string
  theme_code: string
  label_zh: string
  description: string
}

const EMPTY_CUSTOM_FORM: CustomFormState = {
  name: '',
  theme_code: '',
  label_zh: '',
  description: '',
}

function formFromCustom(item: CustomTemplate): CustomFormState {
  return {
    name: item.name,
    theme_code: item.theme_code,
    label_zh: item.label_zh,
    description: item.description || '',
  }
}

function BuiltinCard({
  item,
  onUse,
}: {
  item: BuiltinTemplate
  onUse: (seed: TemplateSeed) => void
}) {
  return (
    <article
      data-testid={`builtin-template-${item.theme_code}`}
      className="sf-panel flex flex-col p-4"
    >
      <h3 className="text-base font-semibold text-ink">{item.label_zh}</h3>
      <p className="mt-1 text-xs text-ink-faint">theme_code · {item.theme_code}</p>
      <div className="mt-4">
        <Button type="button" size="sm" onClick={() => onUse({ theme_code: item.theme_code })}>
          用此模板创建
        </Button>
      </div>
    </article>
  )
}

function CustomCard({
  item,
  canManage,
  onUse,
  onEdit,
  onDelete,
  deleting,
}: {
  item: CustomTemplate
  canManage: boolean
  onUse: (seed: TemplateSeed) => void
  onEdit: (item: CustomTemplate) => void
  onDelete: (item: CustomTemplate) => void
  deleting: boolean
}) {
  return (
    <article data-testid={`custom-template-${item.id}`} className="sf-panel flex flex-col p-4">
      <h3 className="text-base font-semibold text-ink">{item.label_zh}</h3>
      <p className="mt-1 text-sm text-ink-muted">{item.name}</p>
      <p className="mt-1 text-xs text-ink-faint">theme_code · {item.theme_code}</p>
      {item.description ? (
        <p className="mt-2 line-clamp-2 text-sm text-ink-muted">{item.description}</p>
      ) : null}
      <div className="mt-4 flex flex-wrap gap-2">
        <Button type="button" size="sm" onClick={() => onUse({ template_id: item.id })}>
          用此模板创建
        </Button>
        {canManage ? (
          <>
            <Button type="button" size="sm" variant="secondary" onClick={() => onEdit(item)}>
              编辑
            </Button>
            <Button
              type="button"
              size="sm"
              variant="danger"
              loading={deleting}
              onClick={() => onDelete(item)}
            >
              删除
            </Button>
          </>
        ) : null}
      </div>
    </article>
  )
}

export function TemplatesPage() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { auth } = useAuth()
  const isStaff = Boolean(auth?.user?.is_staff)

  const [createSeed, setCreateSeed] = useState<TemplateSeed | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)

  const [customFormOpen, setCustomFormOpen] = useState(false)
  const [editing, setEditing] = useState<CustomTemplate | null>(null)
  const [customForm, setCustomForm] = useState<CustomFormState>(EMPTY_CUSTOM_FORM)
  const [customFormError, setCustomFormError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const templatesQuery = useQuery({
    queryKey: TEMPLATES_QUERY_KEY,
    queryFn: listTemplates,
  })

  const createProjectMutation = useMutation({
    mutationFn: (body: CreateProjectRequest) => createProject(body),
    onSuccess: (project) => {
      setCreateOpen(false)
      setCreateSeed(null)
      setCreateError(null)
      navigate(`/projects/${project.id}/topic`)
    },
    onError: (err) => {
      setCreateError(formatApiError(err))
    },
  })

  const saveCustomMutation = useMutation({
    mutationFn: async (body: CustomTemplateWrite) => {
      if (editing) {
        return updateCustomTemplate(editing.id, body)
      }
      return createCustomTemplate(body)
    },
    onSuccess: async () => {
      setCustomFormOpen(false)
      setEditing(null)
      setCustomForm(EMPTY_CUSTOM_FORM)
      setCustomFormError(null)
      await queryClient.invalidateQueries({ queryKey: TEMPLATES_QUERY_KEY })
    },
    onError: (err) => {
      setCustomFormError(formatApiError(err))
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteCustomTemplate(id),
    onSuccess: async () => {
      setDeletingId(null)
      await queryClient.invalidateQueries({ queryKey: TEMPLATES_QUERY_KEY })
    },
    onError: () => {
      setDeletingId(null)
    },
  })

  const handleUseTemplate = (seed: TemplateSeed) => {
    setCreateSeed(seed)
    setCreateError(null)
    setCreateOpen(true)
  }

  const openCreateCustom = () => {
    setEditing(null)
    setCustomForm(EMPTY_CUSTOM_FORM)
    setCustomFormError(null)
    setCustomFormOpen(true)
  }

  const openEditCustom = (item: CustomTemplate) => {
    setEditing(item)
    setCustomForm(formFromCustom(item))
    setCustomFormError(null)
    setCustomFormOpen(true)
  }

  const handleDeleteCustom = (item: CustomTemplate) => {
    if (!window.confirm(`确认删除自定义模板「${item.label_zh}」？`)) return
    setDeletingId(item.id)
    deleteMutation.mutate(item.id)
  }

  const handleCustomFormSubmit = (event: FormEvent) => {
    event.preventDefault()
    const name = customForm.name.trim()
    const theme_code = customForm.theme_code.trim()
    const label_zh = customForm.label_zh.trim()
    if (!name || !theme_code || !label_zh) {
      setCustomFormError('请填写名称、主题码与中文标签')
      return
    }
    saveCustomMutation.mutate({
      name,
      theme_code,
      label_zh,
      description: customForm.description.trim(),
      dims: {},
    })
  }

  const builtin = templatesQuery.data?.builtin ?? []
  const custom = templatesQuery.data?.custom ?? []

  return (
    <PageShell
      title="模板库"
      description="浏览内置主题模板与自定义模板，一键创建项目。"
      actions={
        isStaff ? (
          <Button type="button" onClick={openCreateCustom}>
            新建自定义模板
          </Button>
        ) : null
      }
    >
      {templatesQuery.isLoading ? <p className="text-sm text-ink-muted">正在加载模板…</p> : null}
      {templatesQuery.isError ? (
        <p className="text-sm text-danger">{formatApiError(templatesQuery.error)}</p>
      ) : null}

      {templatesQuery.isSuccess ? (
        <div className="space-y-8">
          <section>
            <h2 className="mb-3 text-sm font-semibold text-ink">内置模板</h2>
            {builtin.length === 0 ? (
              <p className="text-sm text-ink-muted">暂无内置模板</p>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {builtin.map((item) => (
                  <BuiltinCard key={item.theme_code} item={item} onUse={handleUseTemplate} />
                ))}
              </div>
            )}
          </section>

          <section>
            <h2 className="mb-3 text-sm font-semibold text-ink">自定义模板</h2>
            {custom.length === 0 ? (
              <p className="text-sm text-ink-muted">暂无自定义模板</p>
            ) : (
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                {custom.map((item) => (
                  <CustomCard
                    key={item.id}
                    item={item}
                    canManage={isStaff}
                    onUse={handleUseTemplate}
                    onEdit={openEditCustom}
                    onDelete={handleDeleteCustom}
                    deleting={deletingId === item.id && deleteMutation.isPending}
                  />
                ))}
              </div>
            )}
          </section>
        </div>
      ) : null}

      <CreateProjectDialog
        open={createOpen}
        busy={createProjectMutation.isPending}
        errorMessage={createError}
        seed={createSeed}
        onOpenChange={(open) => {
          setCreateOpen(open)
          if (!open) {
            setCreateSeed(null)
            setCreateError(null)
          }
        }}
        onSubmit={(body) => createProjectMutation.mutate(body)}
      />

      <Dialog
        open={customFormOpen}
        onOpenChange={(open) => {
          setCustomFormOpen(open)
          if (!open) {
            setEditing(null)
            setCustomForm(EMPTY_CUSTOM_FORM)
            setCustomFormError(null)
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editing ? '编辑自定义模板' : '新建自定义模板'}</DialogTitle>
            <DialogDescription>仅 staff 可写；全员登录可读。</DialogDescription>
          </DialogHeader>
          <form className="space-y-4" onSubmit={handleCustomFormSubmit}>
            <label className="block space-y-1.5 text-sm font-medium text-ink">
              名称
              <Input
                value={customForm.name}
                onChange={(e) => setCustomForm((prev) => ({ ...prev, name: e.target.value }))}
                required
                disabled={saveCustomMutation.isPending}
              />
            </label>
            <label className="block space-y-1.5 text-sm font-medium text-ink">
              主题码
              <Input
                value={customForm.theme_code}
                onChange={(e) => setCustomForm((prev) => ({ ...prev, theme_code: e.target.value }))}
                required
                disabled={saveCustomMutation.isPending}
              />
            </label>
            <label className="block space-y-1.5 text-sm font-medium text-ink">
              中文标签
              <Input
                value={customForm.label_zh}
                onChange={(e) => setCustomForm((prev) => ({ ...prev, label_zh: e.target.value }))}
                required
                disabled={saveCustomMutation.isPending}
              />
            </label>
            <label className="block space-y-1.5 text-sm font-medium text-ink">
              描述
              <Input
                value={customForm.description}
                onChange={(e) =>
                  setCustomForm((prev) => ({ ...prev, description: e.target.value }))
                }
                disabled={saveCustomMutation.isPending}
              />
            </label>
            {customFormError ? <p className="text-sm text-danger">{customFormError}</p> : null}
            <DialogFooter>
              <Button
                type="button"
                variant="secondary"
                disabled={saveCustomMutation.isPending}
                onClick={() => setCustomFormOpen(false)}
              >
                取消
              </Button>
              <Button type="submit" loading={saveCustomMutation.isPending}>
                保存
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </PageShell>
  )
}
