import { Settings2, Sparkles } from 'lucide-react'
import { useBilling } from './BillingContext.jsx'
import RechargePanel from './RechargePanel.jsx'
import { COMMERCE_PAGE_NOTE } from '@/utils/adminEconomics'

export default function CommerceSettingsPanel() {
  const { settings, setSettings, savingId, saveSettings } = useBilling()
  return (
<div className="space-y-6">
              <p className="text-sm text-navy-400 rounded-xl border border-white/5 bg-slate-900/60 px-4 py-3">
                {COMMERCE_PAGE_NOTE}
              </p>
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
              <div className="sf-console-panel p-6 space-y-4">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Settings2 className="w-5 h-5 text-gold-400" />
                  站点币种
                </h3>
                <label className="block text-sm text-navy-300">
                  币种名称
                  <input
                    className="sf-control mt-1 px-4 py-2 text-white"
                    value={settings.currency_name || ''}
                    onChange={(e) => setSettings((s) => ({ ...s, currency_name: e.target.value }))}
                  />
                </label>
                <label className="block text-sm text-navy-300">
                  注册赠送
                  <input
                    type="number"
                    className="sf-control mt-1 px-4 py-2 text-white"
                    value={settings.signup_bonus ?? 0}
                    onChange={(e) =>
                      setSettings((s) => ({ ...s, signup_bonus: Number(e.target.value) }))
                    }
                  />
                  <span className="text-xs text-navy-400 mt-1 block">
                    所有新用户注册即得；会员开通额外赠币在「会员与卡密」单独配置，可叠加。
                  </span>
                </label>
                <label className="block text-sm text-navy-300">
                  默认创作模式
                  <select
                    className="sf-control mt-1 px-4 py-2 text-white"
                    value={settings.default_pipeline_mode || 'step'}
                    onChange={(e) =>
                      setSettings((s) => ({ ...s, default_pipeline_mode: e.target.value }))
                    }
                  >
                    <option value="step">分步掌控</option>
                    <option value="auto">一键生成</option>
                  </select>
                </label>
                <label className="flex items-center gap-2 text-sm text-navy-200">
                  <input
                    type="checkbox"
                    checked={!!settings.require_membership_for_creation}
                    onChange={(e) =>
                      setSettings((s) => ({
                        ...s,
                        require_membership_for_creation: e.target.checked,
                      }))
                    }
                  />
                  创作需有效会员（仍按币扣费）
                </label>
                <button
                  type="button"
                  disabled={savingId === 'settings'}
                  onClick={saveSettings}
                  className="px-5 py-2 rounded-xl btn-gold font-semibold disabled:opacity-60"
                >
                  {savingId === 'settings' ? '保存中…' : '保存币种设置'}
                </button>
              </div>

              <div id="commerce-recharge" className="space-y-4 scroll-mt-24">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-purple-400" />
                  充值档位
                </h3>
                <RechargePanel />
              </div>
            </div>
            </div>
  )
}
