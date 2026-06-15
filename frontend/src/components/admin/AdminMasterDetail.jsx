import { useEffect, useState } from 'react'

export function useAdminSelection(items, getId) {
  const [selectedId, setSelectedId] = useState(null)

  useEffect(() => {
    if (!items?.length) {
      setSelectedId(null)
      return
    }
    setSelectedId((prev) => {
      if (prev != null && items.some((item) => getId(item) === prev)) return prev
      return getId(items[0])
    })
    // getId 常由调用方内联传入，不宜作为依赖以免每次渲染重复触发
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [items])

  return [selectedId, setSelectedId]
}

export function AdminMasterDetailListButton({
  active,
  onClick,
  index,
  title,
  subtitle,
  meta,
  dirty,
  badges = [],
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`w-full text-left rounded-xl px-3 py-2.5 transition-all border ${
        active
          ? 'bg-gold-500/15 border-gold-500/30 text-gold-200'
          : 'border-transparent text-navy-200 hover:bg-navy-800/50 hover:text-white'
      }`}
    >
      <div className="flex items-start gap-2">
        {index != null && (
          <span
            className={`mt-0.5 w-6 h-6 rounded-lg text-xs font-bold flex items-center justify-center shrink-0 ${
              active ? 'bg-gold-500/20 text-gold-300' : 'bg-navy-800 text-navy-400'
            }`}
          >
            {index}
          </span>
        )}
        <div className="min-w-0 flex-1">
          <div className="font-medium truncate">{title}</div>
          {subtitle && <div className="text-[11px] text-navy-500 truncate">{subtitle}</div>}
          {(meta || dirty || badges.length > 0) && (
            <div className="mt-1 flex items-center gap-2 flex-wrap text-[11px]">
              {meta && <span className="text-navy-500">{meta}</span>}
              {badges.map((badge) => (
                <span key={badge} className="text-green-400">
                  {badge}
                </span>
              ))}
              {dirty && <span className="text-amber-400">未保存</span>}
            </div>
          )}
        </div>
      </div>
    </button>
  )
}

export default function AdminMasterDetail({
  listTitle,
  listHint,
  listHeader,
  detailTitle,
  detailHint,
  items = [],
  selectedId,
  onSelect,
  getId = (item) => item.id,
  renderListItem,
  renderDetail,
  emptyList,
  emptyDetail = '请从左侧列表选择一项进行编辑',
  showDetail = false,
  sidebarWidthClass = 'lg:grid-cols-[280px_minmax(0,1fr)]',
  minHeightClass = 'min-h-[420px]',
}) {
  const selected = items.find((item) => getId(item) === selectedId)

  return (
    <div className={`grid grid-cols-1 ${sidebarWidthClass} gap-4 ${minHeightClass}`}>
      <div className="glass-card rounded-2xl p-3 lg:max-h-[calc(100vh-280px)] lg:overflow-y-auto">
        {listTitle && (
          <div className="px-2 py-2 mb-1 border-b border-navy-700/30">
            <div className="text-sm font-medium text-navy-200">
              {listTitle}
              {items.length ? `（${items.length}）` : ''}
            </div>
            {listHint && <p className="text-[11px] text-navy-500 mt-1 leading-relaxed">{listHint}</p>}
          </div>
        )}
        {listHeader}
        <div className="space-y-1">
          {items.length === 0
            ? emptyList || <p className="px-2 py-4 text-sm text-navy-500">暂无数据</p>
            : items.map((item, index) => {
                const id = getId(item)
                const active = id === selectedId
                if (renderListItem) {
                  return renderListItem(item, { active, index, id, onSelect: () => onSelect(id) })
                }
                return (
                  <AdminMasterDetailListButton
                    key={id}
                    active={active}
                    onClick={() => onSelect(id)}
                    index={index + 1}
                    title={item.title || String(id)}
                    subtitle={item.subtitle}
                    meta={item.meta}
                    dirty={item.dirty}
                  />
                )
              })}
        </div>
      </div>

      <div className="glass-card rounded-2xl p-5 lg:max-h-[calc(100vh-280px)] lg:overflow-y-auto">
        {(detailTitle || detailHint) && (
          <div className="mb-4 pb-4 border-b border-navy-700/30">
            {detailTitle && <h3 className="text-base font-semibold text-white">{detailTitle}</h3>}
            {detailHint && <p className="text-xs text-navy-500 mt-1 leading-relaxed">{detailHint}</p>}
          </div>
        )}
        {(selected || showDetail) ? (
          renderDetail(selected)
        ) : (
          <div className="h-full min-h-[240px] flex items-center justify-center text-navy-500 text-sm">
            {emptyDetail}
          </div>
        )}
      </div>
    </div>
  )
}
