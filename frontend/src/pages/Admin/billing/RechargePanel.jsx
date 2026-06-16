import { Plus, Save, Trash2 } from 'lucide-react'
import { AdminBadge, AdminEmpty } from '@/components/admin/AdminUI'
import AdminMasterDetail, { AdminMasterDetailListButton } from '@/components/admin/AdminMasterDetail'
import {
  formatPricePreview,
  isAutoChargePrice,
} from '@/utils/adminEconomics'
import { useBilling } from './BillingContext.jsx'

function rechargeListMeta(row, currencyName) {
  const total = row.total_coins ?? Number(row.base_coins) + Number(row.bonus_coins)
  const bonus = Number(row.bonus_coins) || 0
  const coinText = bonus > 0 ? `${total} ${currencyName}（含赠送${bonus}）` : `${total} ${currencyName}`
  return coinText
}

export default function RechargePanel() {
  const {
    savingId,
    rechargePackages,
    selectedRechargeId,
    setSelectedRechargeId,
    rechargeDirty,
    currencyName,
    createRechargePackageRow,
    patchRechargeRow,
    deleteRechargePackageRow,
    saveRechargeRow,
  } = useBilling()

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-navy-400">
          人民币侧可设划线原价 + 折扣(%) 自动算实付，或直接填实付价；创作币侧可设基础到账 + 额外赠送，二者可叠加。
        </p>
        <button
          type="button"
          disabled={!!savingId}
          onClick={createRechargePackageRow}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 text-sm font-semibold disabled:opacity-50"
        >
          <Plus className="w-4 h-4" />
          新建档位
        </button>
      </div>
      {rechargePackages.length === 0 ? (
        <AdminEmpty title="暂无充值档位" description="点击「新建档位」添加" />
      ) : (
        <AdminMasterDetail
          listTitle="充值档位"
          items={rechargePackages}
          selectedId={selectedRechargeId}
          onSelect={setSelectedRechargeId}
          getId={(row) => row.id}
          renderListItem={(row, { active, onSelect }) => (
            <AdminMasterDetailListButton
              key={row.id}
              active={active}
              onClick={onSelect}
              title={row.name}
              subtitle={
                row.discount_label
                  ? `¥${row.price_yuan}（${row.discount_label}）`
                  : `¥${row.price_yuan}`
              }
              meta={rechargeListMeta(row, currencyName)}
              dirty={rechargeDirty.has(row.id)}
            />
          )}
          renderDetail={(row) => {
            const bonus = Number(row.bonus_coins) || 0
            const base = Number(row.base_coins) || 0
            const total = row.total_coins ?? base + bonus
            const autoCharge = isAutoChargePrice(row.discount_percent, row.original_price_yuan)
            return (
            <div className="space-y-4">
              <div className="flex items-center justify-between gap-2 flex-wrap">
                <h3 className="text-lg font-semibold text-white">编辑档位</h3>
                <AdminBadge tone={row.is_active ? 'success' : 'default'}>
                  {row.is_active ? '上架' : '下架'}
                </AdminBadge>
              </div>
              <label className="block text-sm text-navy-300">
                档位名称
                <input
                  className="sf-control mt-1 max-w-md"
                  value={row.name}
                  onChange={(e) => patchRechargeRow(row.id, { name: e.target.value })}
                />
              </label>

              <div className="space-y-3 rounded-xl border border-white/5 bg-slate-900/40 p-4">
                <h4 className="text-sm font-semibold text-white">人民币定价（打折）</h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <label className="text-sm text-navy-300">
                    划线原价(元)
                    <input
                      className="sf-control mt-1"
                      placeholder="可选"
                      value={row.original_price_yuan ?? ''}
                      onChange={(e) =>
                        patchRechargeRow(row.id, {
                          original_price_yuan: e.target.value === '' ? null : e.target.value,
                        })
                      }
                    />
                  </label>
                  <label className="text-sm text-navy-300">
                    折扣(%)
                    <input
                      type="number"
                      min={1}
                      max={100}
                      className="sf-control mt-1"
                      value={row.discount_percent ?? 100}
                      onChange={(e) =>
                        patchRechargeRow(row.id, { discount_percent: e.target.value })
                      }
                    />
                  </label>
                  <label className="text-sm text-navy-300">
                    实付(元){autoCharge ? '（自动计算）' : ''}
                    <input
                      readOnly={autoCharge}
                      className={`sf-control mt-1 text-sm ${
                        autoCharge
                          ? 'bg-slate-950 text-gold-300 cursor-not-allowed'
                          : 'bg-slate-900 text-white'
                      }`}
                      value={row.price_yuan}
                      onChange={(e) => patchRechargeRow(row.id, { price_yuan: e.target.value })}
                    />
                  </label>
                </div>
                <p className="text-xs text-gold-400/90">
                  {formatPricePreview({
                    original: row.original_price_yuan,
                    discountPercent: row.discount_percent,
                    manualPrice: row.price_yuan,
                  })}
                  {autoCharge
                    ? ' · 实付 = 划线原价 × 折扣%'
                    : ' · 折扣 100 时手动填写实付价'}
                </p>
              </div>

              <div className="space-y-3 rounded-xl border border-white/5 bg-slate-900/40 p-4">
                <h4 className="text-sm font-semibold text-white">创作币到账（送积分）</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <label className="text-sm text-navy-300">
                    基础到账
                    <input
                      type="number"
                      className="sf-control mt-1"
                      value={row.base_coins}
                      onChange={(e) => patchRechargeRow(row.id, { base_coins: e.target.value })}
                    />
                  </label>
                  <label className="text-sm text-navy-300">
                    额外赠送
                    <input
                      type="number"
                      className="sf-control mt-1"
                      value={row.bonus_coins}
                      onChange={(e) => patchRechargeRow(row.id, { bonus_coins: e.target.value })}
                    />
                  </label>
                </div>
                <p className="text-xs text-navy-400">
                  用户支付后到账 <span className="text-white font-medium">{total}</span> {currencyName}
                  {bonus > 0 ? (
                    <span className="text-green-400">（基础 {base} + 赠送 {bonus}）</span>
                  ) : null}
                </p>
              </div>

              <label className="inline-flex items-center gap-2 text-sm text-navy-200">
                <input
                  type="checkbox"
                  checked={!!row.is_active}
                  onChange={(e) => patchRechargeRow(row.id, { is_active: e.target.checked })}
                />
                上架销售
              </label>
              <div className="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-white/5">
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    onClick={() => deleteRechargePackageRow(row.id)}
                    className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm text-red-400 border border-red-500/30 hover:bg-red-500/10"
                  >
                    <Trash2 className="w-4 h-4" />
                    删除
                  </button>
                  <button
                    type="button"
                    disabled={savingId === `recharge-${row.id}`}
                    onClick={() => saveRechargeRow(rechargePackages.find((item) => item.id === row.id))}
                    className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-gold-400 to-gold-600 text-navy-950 text-sm font-medium disabled:opacity-50"
                  >
                    <Save className="w-4 h-4" />
                    {savingId === `recharge-${row.id}` ? '保存中…' : '保存'}
                  </button>
                </div>
              </div>
            </div>
            )
          }}
        />
      )}
    </div>
  )
}
