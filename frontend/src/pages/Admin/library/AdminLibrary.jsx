import React, { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Upload,
  RefreshCw,
  Trash2,
  FileText,
  ChevronDown,
  ChevronRight,
  AlertCircle,
  CheckCircle,
  XCircle,
  Loader2,
} from 'lucide-react'
import AdminShell from '@/components/admin/AdminShell'
import { adminLibrary } from '@/services/admin/library'
import {
  AdminPageHeader,
  AdminPanel,
  AdminTable,
  AdminPagination,
  AdminLoading,
  AdminMessage,
  AdminBadge,
  AdminToolbar,
  AdminSearchInput,
  AdminConfirmDialog,
  formatDateTime,
} from '@/components/admin/AdminUI'
import { cardEnter, modalOverlay, modalPanel } from '@/constants/motion'
import { cn } from '@/utils/cn'

const STATUS_OPTIONS = [
  { key: '', label: '全部状态' },
  { key: 'pending', label: '待解析' },
  { key: 'parsing', label: '解析中' },
  { key: 'ready', label: '已就绪' },
  { key: 'failed', label: '解析失败' },
]

const STATUS_TONE = {
  pending: 'default',
  parsing: 'warning',
  ready: 'success',
  failed: 'danger',
}

const STATUS_LABEL = {
  pending: '待解析',
  parsing: '解析中',
  ready: '已就绪',
  failed: '解析失败',
}

const FILE_TYPE_LABEL = {
  pdf: 'PDF',
  docx: 'Word',
  doc: 'Word',
  txt: 'TXT',
}

function ParseStatusBadge({ status }) {
  return (
    <AdminBadge tone={STATUS_TONE[status] || 'default'}>
      {STATUS_LABEL[status] || status}
    </AdminBadge>
  )
}

/** 拖拽上传区 */
function UploadZone({ onUpload, uploading, uploadProgress }) {
  const [dragging, setDragging] = useState(false)

  function handleDragOver(e) {
    e.preventDefault()
    setDragging(true)
  }

  function handleDragLeave(e) {
    e.preventDefault()
    setDragging(false)
  }

  function handleDrop(e) {
    e.preventDefault()
    setDragging(false)
    const files = Array.from(e.dataTransfer.files)
    if (files.length > 0) {
      onUpload(files)
    }
  }

  function handleFileInput(e) {
    const files = Array.from(e.target.files)
    if (files.length > 0) {
      onUpload(files)
    }
    e.target.value = ''
  }

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      className={cn(
        'relative border-2 border-dashed rounded-2xl p-8 text-center transition-all',
        dragging
          ? 'border-gold-400/50 bg-gold-400/5'
          : 'border-white/10 hover:border-white/20 bg-white/[0.02]',
        uploading && 'opacity-60 pointer-events-none'
      )}
    >
      <input
        type="file"
        multiple
        accept=".pdf,.docx,.doc,.txt"
        onChange={handleFileInput}
        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
      />

      {uploading ? (
        <div className="space-y-3">
          <Loader2 className="w-10 h-10 text-gold-400 animate-spin mx-auto" />
          <div className="text-sm text-navy-300">上传中… {uploadProgress}%</div>
          <div className="w-48 h-1.5 bg-white/10 rounded-full mx-auto overflow-hidden">
            <div
              className="h-full bg-gold-400 transition-all duration-300"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      ) : (
        <>
          <Upload className={cn('w-10 h-10 mx-auto mb-3', dragging ? 'text-gold-400' : 'text-navy-400')} />
          <div className="text-sm text-navy-200 mb-1">
            拖拽文件到此处，或 <span className="text-gold-400">点击选择</span>
          </div>
          <div className="text-xs text-navy-500">
            支持 PDF / Word / TXT 格式
          </div>
        </>
      )}
    </div>
  )
}

/** JSON 树形预览 */
function JsonTree({ data, depth = 0 }) {
  if (data === null || data === undefined) {
    return <span className="text-navy-500">null</span>
  }
  if (typeof data === 'string') {
    return <span className="text-emerald-400">"{data}"</span>
  }
  if (typeof data === 'number') {
    return <span className="text-amber-400">{data}</span>
  }
  if (typeof data === 'boolean') {
    return <span className="text-purple-400">{String(data)}</span>
  }
  if (Array.isArray(data)) {
    if (data.length === 0) return <span className="text-navy-500">[]</span>
    return (
      <div className="pl-4">
        <span className="text-navy-400">[
        </span>
        {data.map((item, i) => (
          <div key={i}>
            <JsonTree data={item} depth={depth + 1} />
            {i < data.length - 1 && <span className="text-navy-400">,</span>}
          </div>
        ))}
        <span className="text-navy-400">]</span>
      </div>
    )
  }
  if (typeof data === 'object') {
    const keys = Object.keys(data)
    if (keys.length === 0) return <span className="text-navy-500">{'{}'}</span>
    return (
      <div className="pl-4">
        <span className="text-navy-400">{'{'}</span>
        {keys.map((key, i) => (
          <div key={key} style={{ paddingLeft: depth * 8 }}>
            <span className="text-cyan-400">"{key}"</span>
            <span className="text-navy-400">: </span>
            <JsonTree data={data[key]} depth={depth + 1} />
            {i < keys.length - 1 && <span className="text-navy-400">,</span>}
          </div>
        ))}
        <span className="text-navy-400">{'}'}</span>
      </div>
    )
  }
  return <span>{String(data)}</span>
}

/** 素材详情弹窗 */
function MaterialDetailModal({ material, open, onClose, onReparse, onDelete }) {
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(false)
  const [actionLoading, setActionLoading] = useState(false)
  const [message, setMessage] = useState(null)

  useEffect(() => {
    if (open && material) {
      setLoading(true)
      adminLibrary.getDetail(material.id)
        .then(setDetail)
        .catch((e) => setMessage({ type: 'error', text: e.message || '加载详情失败' }))
        .finally(() => setLoading(false))
    }
  }, [open, material])

  async function handleReparse() {
    setActionLoading(true)
    try {
      await adminLibrary.parse(material.id)
      setMessage({ type: 'success', text: '重新解析已触发' })
      if (onReparse) onReparse()
      onClose()
    } catch (e) {
      setMessage({ type: 'error', text: e.message || '解析失败' })
    } finally {
      setActionLoading(false)
    }
  }

  async function handleDelete() {
    if (!window.confirm(`确定删除「${material.name}」？删除后无法恢复。`)) return
    setActionLoading(true)
    try {
      await adminLibrary.delete(material.id)
      setMessage({ type: 'success', text: '素材已删除' })
      if (onDelete) onDelete()
      onClose()
    } catch (e) {
      setMessage({ type: 'error', text: e.message || '删除失败' })
    } finally {
      setActionLoading(false)
    }
  }

  if (!open) return null

  return (
    <motion.div
      {...modalOverlay}
      className="fixed inset-0 z-[100] flex items-start justify-center p-6 bg-navy-950/80 backdrop-blur-sm overflow-y-auto"
    >
      <motion.div
        {...modalPanel}
        className="sf-console-panel p-6 max-w-4xl w-full shadow-modal my-8"
      >
        <AdminMessage message={message} onClose={() => setMessage(null)} />

        <div className="flex items-start gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-gold-500/15 flex items-center justify-center flex-shrink-0">
            <FileText className="w-5 h-5 text-gold-400" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-white">{material.name}</h3>
            <div className="flex items-center gap-3 mt-1">
              <span className="text-xs text-navy-400">
                {FILE_TYPE_LABEL[material.file_type] || material.file_type} · {material.file_size ? `${(material.file_size / 1024).toFixed(1)} KB` : '未知大小'}
              </span>
              <ParseStatusBadge status={material.parse_status} />
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-navy-400 hover:text-white text-sm"
          >
            关闭
          </button>
        </div>

        {loading ? (
          <AdminLoading label="加载详情…" />
        ) : detail ? (
          <div className="space-y-4">
            <AdminPanel title="基本信息">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-navy-400">文件名：</span>
                  <span className="text-white">{detail.name}</span>
                </div>
                <div>
                  <span className="text-navy-400">类型：</span>
                  <span className="text-white">{FILE_TYPE_LABEL[detail.file_type] || detail.file_type}</span>
                </div>
                <div>
                  <span className="text-navy-400">上传时间：</span>
                  <span className="text-navy-300">{formatDateTime(detail.created_at)}</span>
                </div>
                <div>
                  <span className="text-navy-400">解析状态：</span>
                  <ParseStatusBadge status={detail.parse_status} />
                </div>
              </div>
            </AdminPanel>

            {detail.parsed_content && (
              <AdminPanel title="解析内容预览">
                <div className="bg-navy-950/50 rounded-xl p-4 font-mono text-xs overflow-x-auto max-h-96 overflow-y-auto">
                  <pre className="text-navy-300 whitespace-pre-wrap">
                    <JsonTree data={detail.parsed_content} />
                  </pre>
                </div>
              </AdminPanel>
            )}

            <div className="flex justify-between pt-2">
              <button
                type="button"
                disabled={actionLoading}
                onClick={handleDelete}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-red-500/30 text-red-400 text-sm hover:bg-red-500/10 disabled:opacity-50"
              >
                <Trash2 className="w-4 h-4" />
                {actionLoading ? '删除中…' : '删除素材'}
              </button>
              <button
                type="button"
                disabled={actionLoading}
                onClick={handleReparse}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gold-400/20 text-gold-300 text-sm hover:bg-gold-400/30 disabled:opacity-50"
              >
                <RefreshCw className="w-4 h-4" />
                {actionLoading ? '触发中…' : '重新解析'}
              </button>
            </div>
          </div>
        ) : null}
      </motion.div>
    </motion.div>
  )
}

/** 素材库主组件 */
export default function AdminLibrary() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [message, setMessage] = useState(null)
  const [loading, setLoading] = useState(true)
  const [items, setItems] = useState([])
  const [pagination, setPagination] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [selectedMaterial, setSelectedMaterial] = useState(null)
  const [detailModalOpen, setDetailModalOpen] = useState(false)

  const keyword = searchParams.get('q') || ''
  const status = searchParams.get('status') || ''
  const page = Math.max(1, parseInt(searchParams.get('page') || '1', 10))

  const patchParams = useCallback(
    (patch, resetPage = true) => {
      const next = new URLSearchParams(searchParams)
      Object.entries(patch).forEach(([key, value]) => {
        if (value === '' || value == null) {
          next.delete(key)
        } else {
          next.set(key, String(value))
        }
      })
      if (resetPage) next.delete('page')
      setSearchParams(next, { replace: true })
    },
    [searchParams, setSearchParams]
  )

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const res = await adminLibrary.list({
        page,
        page_size: 20,
        keyword: keyword.trim() || undefined,
        parse_status: status || undefined,
      })
      setItems(res.items || [])
      setPagination({
        page: res.pagination?.page || 1,
        total_pages: res.pagination?.total_pages || 1,
        total: res.pagination?.total || 0,
        page_size: res.pagination?.page_size || 20,
      })
    } catch (e) {
      setMessage({ type: 'error', text: e.message || '加载失败' })
      setItems([])
    } finally {
      setLoading(false)
    }
  }, [page, keyword, status])

  useEffect(() => {
    load()
  }, [load])

  async function handleUpload(files) {
    const validTypes = ['pdf', 'docx', 'doc', 'txt']
    const file = files[0]
    const ext = file.name.split('.').pop().toLowerCase()

    if (!validTypes.includes(ext)) {
      setMessage({ type: 'error', text: '仅支持 PDF / Word / TXT 格式文件' })
      return
    }

    setUploading(true)
    setUploadProgress(0)

    const formData = new FormData()
    formData.append('file', file)
    formData.append('name', file.name.replace(/\.[^.]+$/, ''))

    await new Promise((resolve, reject) => {
      adminLibrary
        .upload(formData, {
          onUploadProgress: (event) => {
            if (event.total) {
              setUploadProgress(Math.round((event.loaded / event.total) * 100))
            }
          },
        })
        .then(resolve)
        .catch(reject)
    })
      .then(() => {
        setMessage({ type: 'success', text: '上传成功，解析将在后台进行' })
        load()
      })
      .catch((e) => {
        setMessage({ type: 'error', text: e.message || '上传失败' })
      })
      .finally(() => {
        setUploading(false)
        setUploadProgress(0)
      })
  }

  function handleViewDetail(material) {
    setSelectedMaterial(material)
    setDetailModalOpen(true)
  }

  async function handleReparse(materialId) {
    try {
      await adminLibrary.parse(materialId)
      setMessage({ type: 'success', text: '重新解析已触发' })
      load()
    } catch (e) {
      setMessage({ type: 'error', text: e.message || '解析失败' })
    }
  }

  async function handleDelete(materialId) {
    try {
      await adminLibrary.delete(materialId)
      setMessage({ type: 'success', text: '素材已删除' })
      load()
    } catch (e) {
      setMessage({ type: 'error', text: e.message || '删除失败' })
    }
  }

  function formatFileSize(bytes) {
    if (!bytes) return '—'
    if (bytes < 1024) return `${bytes} B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  }

  const columns = [
    {
      key: 'name',
      title: '素材名称',
      render: (row) => (
        <button
          type="button"
          onClick={() => handleViewDetail(row)}
          className="text-gold-400 hover:text-gold-300 font-medium hover:underline text-left"
        >
          {row.name}
        </button>
      ),
    },
    {
      key: 'file_type',
      title: '类型',
      render: (row) => (
        <span className="text-xs text-navy-300">
          {FILE_TYPE_LABEL[row.file_type] || row.file_type}
        </span>
      ),
    },
    {
      key: 'parse_status',
      title: '解析状态',
      render: (row) => <ParseStatusBadge status={row.parse_status} />,
    },
    {
      key: 'file_size',
      title: '大小',
      render: (row) => (
        <span className="text-xs text-navy-400">{formatFileSize(row.file_size)}</span>
      ),
    },
    {
      key: 'created_at',
      title: '上传时间',
      render: (row) => (
        <span className="text-xs text-navy-400 whitespace-nowrap">
          {formatDateTime(row.created_at)}
        </span>
      ),
    },
    {
      key: 'actions',
      title: '操作',
      align: 'right',
      render: (row) => (
        <div className="flex items-center justify-end gap-2">
          <button
            type="button"
            onClick={() => handleViewDetail(row)}
            className="inline-flex items-center gap-1 text-xs text-navy-300 hover:text-white"
          >
            <FileText className="w-3.5 h-3.5" />
            详情
          </button>
          {row.parse_status === 'ready' && (
            <button
              type="button"
              onClick={() => handleReparse(row.id)}
              className="inline-flex items-center gap-1 text-xs text-yellow-400 hover:text-yellow-300"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              重解析
            </button>
          )}
          <button
            type="button"
            onClick={() => handleDelete(row.id)}
            className="inline-flex items-center gap-1 text-xs text-red-400 hover:text-red-300"
          >
            <Trash2 className="w-3.5 h-3.5" />
            删除
          </button>
        </div>
      ),
    },
  ]

  return (
    <AdminShell hideDescription>
      <AdminMessage message={message} onClose={() => setMessage(null)} />

      <AdminPageHeader
        crumbs={[{ label: 'Console' }, { label: '素材库' }]}
        title="素材库管理"
        description="参考作品结构化管理 / 创作时自动注入"
      />

      <AdminPanel title="上传素材" className="mb-6">
        <UploadZone
          onUpload={handleUpload}
          uploading={uploading}
          uploadProgress={uploadProgress}
        />
      </AdminPanel>

      <AdminToolbar>
        <AdminSearchInput
          value={keyword}
          onChange={(v) => patchParams({ q: v })}
          placeholder="搜索素材名称…"
        />
        <select
          value={status}
          onChange={(e) => patchParams({ status: e.target.value })}
          className="sf-control"
        >
          {STATUS_OPTIONS.map((o) => (
            <option key={o.key} value={o.key}>
              {o.label}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={load}
          className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-sm text-navy-200 hover:bg-white/[0.06]"
        >
          <RefreshCw className="w-4 h-4" />
          刷新
        </button>
      </AdminToolbar>

      {loading ? (
        <AdminLoading label="加载素材…" />
      ) : (
        <AdminPanel
          title="素材列表"
          sub={`共 ${pagination?.total ?? 0} 个素材`}
        >
          <AdminTable
            rowKey="id"
            rows={items}
            columns={columns}
            emptyText="暂无素材"
          />
          <AdminPagination
            page={pagination?.page || 1}
            totalPages={pagination?.total_pages || 1}
            total={pagination?.total}
            onPageChange={(p) => patchParams({ page: p }, false)}
          />
        </AdminPanel>
      )}

      <MaterialDetailModal
        material={selectedMaterial}
        open={detailModalOpen}
        onClose={() => {
          setDetailModalOpen(false)
          setSelectedMaterial(null)
        }}
        onReparse={load}
        onDelete={load}
      />
    </AdminShell>
  )
}
