import { useEffect, useState } from 'react'
import { KeyRound, Save } from 'lucide-react'
import { admin } from '@/services/api'
import { VOLCANO_PAYG_URL } from '@/constants/adminShared'

export default function LlmVendorCredentialForm({
  vendor,
  credential,
  disabled = false,
  onSaved,
  onMessage,
}) {
  const [apiKey, setApiKey] = useState('')
  const [apiKeyTouched, setApiKeyTouched] = useState(false)
  const [volcanoKeyType, setVolcanoKeyType] = useState('payg')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    setApiKey('')
    setApiKeyTouched(false)
    setVolcanoKeyType(credential?.volcano_key_type || 'payg')
  }, [credential?.vendor, credential?.volcano_key_type])

  async function handleSave() {
    setSaving(true)
    try {
      const payload = {}
      if (apiKeyTouched && apiKey) payload.api_key = apiKey
      if (vendor === 'volcengine') payload.volcano_key_type = volcanoKeyType
      const data = await admin.updateLlmVendorCredential(vendor, payload)
      onSaved?.(data)
      onMessage?.(`「${credential?.vendor_label || vendor}」厂商 Key 已保存`)
      setApiKeyTouched(false)
      setApiKey('')
    } catch (err) {
      onMessage?.(err.message || '保存厂商 Key 失败', 'error')
    } finally {
      setSaving(false)
    }
  }

  const keySet = credential?.api_key_set

  return (
    <div className="rounded-lg border border-gold-500/20 bg-gold-500/5 p-3 space-y-3">
      <p className="text-xs text-navy-300">
        <KeyRound className="w-3.5 h-3.5 inline mr-1 text-gold-400" />
        厂商共用 API Key（该厂商下所有模型共用，只需填一次）
      </p>
      {vendor === 'volcengine' ? (
        <label className="block">
          <span className="text-xs text-navy-400 mb-1 block">火山 Key 类型</span>
          <select
            value={volcanoKeyType}
            onChange={(e) => setVolcanoKeyType(e.target.value)}
            className="w-full px-3 py-2 rounded-lg bg-navy-800/60 border border-navy-700/40 text-white text-sm"
          >
            <option value="payg">按量付费（推荐）— ep-xxx / Model ID</option>
            <option value="coding_plan">Coding Plan — 仅编程订阅 Key</option>
          </select>
          <p className="text-[10px] text-navy-500 mt-1 font-mono truncate">{VOLCANO_PAYG_URL}</p>
        </label>
      ) : null}
      <label className="block">
        <span className="text-xs text-navy-400 flex items-center gap-1 mb-1">
          API Key
          {credential?.api_key_url ? (
            <a
              href={credential.api_key_url}
              target="_blank"
              rel="noreferrer"
              className="text-gold-400 hover:underline ml-2"
            >
              去控制台获取
            </a>
          ) : null}
        </span>
        <input
          type="password"
          autoComplete="off"
          value={apiKey}
          placeholder={keySet && !apiKeyTouched ? '已设置，修改请重新输入' : '粘贴该厂商 API Key'}
          onChange={(e) => {
            setApiKeyTouched(true)
            setApiKey(e.target.value)
          }}
          className="w-full px-3 py-2 rounded-lg bg-navy-800/60 border border-navy-700/40 text-white font-mono text-sm"
        />
      </label>
      <button
        type="button"
        disabled={
          disabled || saving || (!keySet && !apiKey) || (apiKeyTouched && !apiKey)
        }
        onClick={handleSave}
        className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-sm bg-gold-500/15 text-gold-300 border border-gold-500/30 hover:bg-gold-500/25 disabled:opacity-50"
      >
        <Save className="w-3.5 h-3.5" />
        {saving ? '保存中…' : keySet ? '更新厂商 Key' : '保存厂商 Key'}
      </button>
    </div>
  )
}
