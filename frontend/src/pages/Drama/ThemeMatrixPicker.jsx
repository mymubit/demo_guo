import { useMemo, useState } from 'react';
import { Search, Sparkles, Check } from 'lucide-react';
import { cn } from '@/utils/cn';

const BROWSE_LIMIT = 9;

function labelForAxisValue(axes, axis, value) {
  return axes[axis]?.options?.find(o => o.value === value)?.label || value;
}

function SelectionSummary({ dimOrder, axes, dimSelections, flavorTagSelections, flavorOptions }) {
  const parts = dimOrder
    .filter(axis => dimSelections[axis])
    .map(axis => labelForAxisValue(axes, axis, dimSelections[axis]));
  flavorTagSelections.forEach(tag => {
    const opt = flavorOptions?.find(o => o.value === tag);
    if (opt?.label) parts.push(opt.label);
  });
  if (!parts.length) return null;
  return (
    <div className="rounded-xl border border-gold-500/30 bg-gold-500/10 px-5 py-3.5 text-base text-slate-200">
      <span className="text-gold-400 font-medium">当前组合：</span>
      {parts.join(' × ')}
    </div>
  );
}

function AxisPanel({ axisKey, config, selectedValue, onSelectDim }) {
  if (!config) return null;
  return (
    <div className="rounded-xl border border-white/12 bg-slate-950/60 p-5 h-full">
      <div className="mb-4">
        <h4 className="text-base font-semibold text-white">{config.label}</h4>
        <p className="text-sm text-slate-400 mt-1">{config.hint}</p>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
        {(config.options || []).map(opt => {
          const selected = selectedValue === opt.value;
          return (
            <button
              key={opt.value}
              type="button"
              onClick={() => onSelectDim(axisKey, opt.value)}
              className={cn(
                'w-full rounded-xl border px-4 py-3 text-left transition-all',
                selected
                  ? 'bg-gold-500 text-navy-950 border-gold-500 font-medium shadow-sm'
                  : 'bg-slate-800/90 text-slate-200 border-white/12 hover:border-gold-500/40 hover:text-gold-200',
              )}
            >
              <div className="text-sm font-medium">{opt.label}</div>
              <div className={cn('text-xs mt-1 line-clamp-2', selected ? 'text-navy-900/75' : 'text-slate-500')}>
                {opt.desc}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default function ThemeMatrixPicker({
  dimOrder,
  axes,
  featuredCombos,
  flavorConfig,
  flavorGroups,
  flavorMaxSelect,
  dimSelections,
  flavorTagSelections,
  activeThemeCode,
  onSelectDim,
  onToggleFlavorTag,
  onApplyCombo,
  onClearCustom,
  onClearFlavorTags,
}) {
  const [comboSearch, setComboSearch] = useState('');
  const [showAllCombos, setShowAllCombos] = useState(false);
  const [flavorFilter, setFlavorFilter] = useState('');

  const flavorOptions = flavorConfig?.options || [];

  const filteredCombos = useMemo(() => {
    const q = comboSearch.trim().toLowerCase();
    if (!q) return featuredCombos;
    return featuredCombos.filter(
      c => c.label?.toLowerCase().includes(q)
        || c.code?.toLowerCase().includes(q)
        || c.heat?.toLowerCase().includes(q),
    );
  }, [featuredCombos, comboSearch]);

  const visibleCombos = useMemo(() => {
    if (comboSearch.trim() || showAllCombos) return filteredCombos;
    return filteredCombos.slice(0, BROWSE_LIMIT);
  }, [filteredCombos, comboSearch, showAllCombos]);

  const visibleFlavorGroups = useMemo(() => {
    const q = flavorFilter.trim().toLowerCase();
    if (!q) return flavorGroups;
    return flavorGroups
      .map(group => ({
        ...group,
        options: group.options.filter(
          o => o.label?.toLowerCase().includes(q) || o.value?.toLowerCase().includes(q),
        ),
      }))
      .filter(group => group.options.length > 0);
  }, [flavorGroups, flavorFilter]);

  return (
    <div className="space-y-7">
      <SelectionSummary
        dimOrder={dimOrder}
        axes={axes}
        dimSelections={dimSelections}
        flavorTagSelections={flavorTagSelections}
        flavorOptions={flavorOptions}
      />

      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-base font-semibold text-gold-300 flex items-center gap-2">
            <Sparkles className="w-4 h-4" />
            热门组合
            <span className="text-slate-500 font-normal text-sm">点选可一键填充下方四轴</span>
          </p>
          <button
            type="button"
            onClick={onClearCustom}
            className="text-sm text-slate-400 hover:text-gold-300"
          >
            清空选择
          </button>
        </div>
        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="search"
            value={comboSearch}
            onChange={(e) => setComboSearch(e.target.value)}
            placeholder="筛选热门组合…"
            className="sf-control pl-9 py-3 text-sm w-full"
          />
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {visibleCombos.map(combo => {
            const isActive = activeThemeCode === combo.code;
            return (
              <button
                key={combo.code}
                type="button"
                onClick={() => onApplyCombo(combo)}
                className={cn(
                  'rounded-xl border p-4 text-left transition-all min-h-[88px] w-full',
                  isActive
                    ? 'border-gold-500 bg-gold-500/15 ring-1 ring-gold-500/30'
                    : 'border-white/12 bg-slate-950/70 hover:border-gold-500/35 hover:bg-gold-500/5',
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <span className="text-base font-medium text-slate-100 leading-snug">{combo.label}</span>
                  {isActive ? <Check className="w-5 h-5 text-gold-400 shrink-0" /> : null}
                </div>
                <span className="inline-block mt-2.5 text-xs px-2 py-0.5 rounded-md bg-slate-800 text-slate-400">
                  {combo.heat}
                </span>
              </button>
            );
          })}
        </div>
        {!comboSearch.trim() && filteredCombos.length > BROWSE_LIMIT && !showAllCombos ? (
          <button
            type="button"
            onClick={() => setShowAllCombos(true)}
            className="text-sm text-slate-400 hover:text-gold-300"
          >
            展开全部 {filteredCombos.length} 个组合
          </button>
        ) : null}
      </section>

      <section className="space-y-4">
        <div>
          <h4 className="text-base font-semibold text-white">四轴搭配</h4>
          <p className="text-sm text-slate-400 mt-1">每轴任选 1 项，四轴可同时点选，无先后顺序</p>
        </div>
        <div className="grid grid-cols-1 xl:grid-cols-2 gap-5">
          {dimOrder.map(axis => (
            <AxisPanel
              key={axis}
              axisKey={axis}
              config={axes[axis]}
              selectedValue={dimSelections[axis]}
              onSelectDim={onSelectDim}
            />
          ))}
        </div>
      </section>

      <section className="space-y-4 rounded-xl border border-white/10 bg-slate-950/40 p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h4 className="text-base font-semibold text-white">
              风味标签
              <span className="text-slate-500 font-normal ml-2 text-sm">
                可选，最多 {flavorMaxSelect} 个
              </span>
            </h4>
            {flavorConfig.hint ? (
              <p className="text-sm text-slate-400 mt-1">{flavorConfig.hint}</p>
            ) : null}
          </div>
          {flavorTagSelections.length > 0 ? (
            <button
              type="button"
              onClick={onClearFlavorTags}
              className="text-sm text-slate-400 hover:text-gold-300"
            >
              清空标签
            </button>
          ) : null}
        </div>

        {flavorTagSelections.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {flavorTagSelections.map(tag => {
              const opt = flavorOptions.find(o => o.value === tag);
              return (
                <button
                  key={tag}
                  type="button"
                  onClick={() => onToggleFlavorTag(tag)}
                  className="px-3 py-2 rounded-lg text-sm bg-gold-500/20 text-gold-300 border border-gold-500/35"
                >
                  {opt?.label || tag} ×
                </button>
              );
            })}
          </div>
        ) : null}

        <div className="relative w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
          <input
            type="search"
            value={flavorFilter}
            onChange={(e) => setFlavorFilter(e.target.value)}
            placeholder="快速筛选标签（可选）…"
            className="sf-control pl-9 py-2.5 text-sm w-full"
          />
        </div>

        <div className="space-y-5 max-h-[min(40vh,420px)] overflow-y-auto pr-1">
          {visibleFlavorGroups.map(group => (
            <div key={group.id}>
              <p className="text-sm font-medium text-slate-300 mb-2.5 sticky top-0 bg-slate-950/95 py-1 backdrop-blur-sm">
                {group.label}
              </p>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
                {group.options.map(opt => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => onToggleFlavorTag(opt.value)}
                    className={cn(
                      'px-3 py-2 rounded-lg text-sm border transition-all text-center truncate',
                      flavorTagSelections.includes(opt.value)
                        ? 'bg-gold-500 text-navy-950 border-gold-500 font-medium'
                        : 'bg-slate-800 text-slate-200 border-white/12 hover:border-gold-500/35 hover:text-gold-200',
                    )}
                    title={opt.label}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
          ))}
          {visibleFlavorGroups.length === 0 ? (
            <p className="text-sm text-slate-500 py-4 text-center">没有匹配的标签</p>
          ) : null}
        </div>
      </section>
    </div>
  );
}
