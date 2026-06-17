/**
 * ScriptForge 表单控件 — 统一风格（深色主题 + 金色点缀）
 *
 * 设计令牌对齐:
 *  - 容器: sf-control (样式详见 globals.css)
 *  - 文字: navy-100 / navy-400
 *  - 激活色: accent-400/400 (金色)
 *  - 错误色: danger-500/60
 *
 * 组件清单:
 *  - FieldShell: 通用标签/描述/错误外框
 *  - Input: 单行文本输入
 *  - Textarea: 多行文本输入
 *  - Select: 下拉选择
 *  - Switch: 开关切换
 *  - Checkbox: 复选框 (支持受控)
 *  - Radio/RadioGroup: 单选组
 *
 */

import * as React from 'react'
import { useCallback, useMemo, forwardRef } from 'react'
import { Check } from 'lucide-react'
import { cn } from '@/utils/cn'

/* ============================================================================
 * FieldShell — 通用标签/描述/错误外框
 * ========================================================================== */

function FieldShell({ label, hint, error, children, className }) {
  return (
    <label className={cn('block', className)}>
      {label ? <span className="sf-label">{label}</span> : null}
      {children}
      {error ? (
        <span className="mt-1.5 block text-xs text-danger-300">{error}</span>
      ) : hint ? (
        <span className="sf-help-text">{hint}</span>
      ) : null}
    </label>
  )
}

/* ============================================================================
 * Input — 单行输入
 * ========================================================================== */

export const Input = forwardRef(function Input(
  { label, hint, error, className, inputClassName, leftIcon, rightAddon, ...props },
  ref,
) {
  return (
    <FieldShell label={label} hint={hint} error={error} className={className}>
      <div className="relative">
        {leftIcon ? (
          <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-navy-400">
            {leftIcon}
          </span>
        ) : null}
        <input
          ref={ref}
          className={cn('sf-control', leftIcon && 'pl-10', rightAddon && 'pr-16', error && 'border-danger-500/60', inputClassName)}
          {...props}
        />
        {rightAddon ? (
          <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-navy-400">
            {rightAddon}
          </span>
        ) : null}
      </div>
    </FieldShell>
  )
})

/* ============================================================================
 * Textarea — 多行输入
 * ========================================================================== */

export const Textarea = forwardRef(function Textarea(
  { label, hint, error, className, textareaClassName, rows = 4, ...props },
  ref,
) {
  return (
    <FieldShell label={label} hint={hint} error={error} className={className}>
      <textarea
        ref={ref}
        rows={rows}
        className={cn('sf-control resize-y leading-relaxed', error && 'border-danger-500/60', textareaClassName)}
        {...props}
      />
    </FieldShell>
  )
})

/* ============================================================================
 * Select — 下拉选择
 * ========================================================================== */

export const Select = forwardRef(function Select(
  { label, hint, error, className, selectClassName, children, ...props },
  ref,
) {
  return (
    <FieldShell label={label} hint={hint} error={error} className={className}>
      <select
        ref={ref}
        className={cn('sf-control appearance-none', error && 'border-danger-500/60', selectClassName)}
        {...props}
      >
        {children}
      </select>
    </FieldShell>
  )
})

/* ============================================================================
 * Switch — 开关切换 (受控组件)
 * 用法: <Switch label="启用灰度" checked={enabled} onChange={setEnabled} />
 * ========================================================================== */

export function Switch({
  label,
  hint,
  checked = false,
  onChange,
  disabled,
  size = 'md',
  className,
}) {
  const sizes = {
    sm: { track: 'h-5 w-9', thumb: 'h-4 w-4', translate: 'translate-x-4' },
    md: { track: 'h-6 w-11', thumb: 'h-5 w-5', translate: 'translate-x-[22px]' },
    lg: { track: 'h-7 w-12', thumb: 'h-6 w-6', translate: 'translate-x-6' },
  }
  const s = sizes[size]

  const handleToggle = useCallback(() => {
    if (disabled) return
    onChange?.(!checked)
  }, [checked, onChange, disabled])

  return (
    <FieldShell label={null} hint={null} error={null} className={className}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          {label && <span className="block text-sm font-medium text-navy-100">{label}</span>}
          {hint && <span className="sf-help-text mt-1">{hint}</span>}
        </div>
        <button
          type="button"
          role="switch"
          aria-checked={checked}
          onClick={handleToggle}
          disabled={disabled}
          className={cn(
            'relative inline-flex shrink-0 items-center rounded-full transition-colors duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent-400/50',
            checked ? 'bg-gradient-to-r from-accent-300 to-accent-500' : 'bg-slate-700/80',
            disabled && 'opacity-50 cursor-not-allowed',
            s.track,
          )}
        >
          <span
            className={cn(
              'inline-block rounded-full bg-white shadow-md transform transition-transform duration-200',
              s.thumb,
              checked ? s.translate : 'translate-x-[3px]',
            )}
          />
        </button>
      </div>
    </FieldShell>
  )
}

/* ============================================================================
 * Checkbox — 复选框 (受控)
 * 用法: <Checkbox checked={v} onChange={setV}>启用此项</Checkbox>
 * ========================================================================== */

export function Checkbox({
  checked = false,
  onChange,
  disabled,
  children,
  className,
  label,
  hint,
}) {
  const labelText = children || label
  const handleToggle = useCallback(() => {
    if (disabled) return
    onChange?.(!checked)
  }, [checked, onChange, disabled])

  return (
    <FieldShell label={null} hint={hint} error={null} className={className}>
      <div className="flex items-start gap-3">
        <button
          type="button"
          role="checkbox"
          aria-checked={checked}
          onClick={handleToggle}
          disabled={disabled}
          className={cn(
            'mt-0.5 shrink-0 flex items-center justify-center rounded-md border transition-all duration-150',
            checked
              ? 'bg-gradient-to-br from-accent-300 to-accent-500 border-accent-400/60 text-slate-900'
              : 'border-white/15 bg-slate-900/60 text-transparent hover:border-white/30',
            disabled && 'opacity-50 cursor-not-allowed',
            'h-5 w-5',
          )}
        >
          <Check className="w-3.5 h-3.5" strokeWidth={3} />
        </button>
        {labelText && (
          <div className="min-w-0">
            <span className="text-sm text-navy-100">{labelText}</span>
            {hint && <span className="sf-help-text">{hint}</span>}
          </div>
        )}
      </div>
    </FieldShell>
  )
}

/* ============================================================================
 * Radio / RadioGroup — 单选组 (受控)
 * 用法:
 *   <RadioGroup value={v} onChange={setV}>
 *     <Radio value="A">选项 A</Radio>
 *     <Radio value="B">选项 B</Radio>
 *   </RadioGroup>
 * ========================================================================== */

const RadioContext = React.createContext({ value: null, onChange: () => {}, name: 'default' })

export function RadioGroup({ name, value, onChange, children, className }) {
  const groupName = name || `radio-${Math.random().toString(36).slice(2, 8)}`
  const ctxValue = useMemo(() => ({ value, onChange, name: groupName }), [value, onChange, groupName])
  return (
    <RadioContext.Provider value={ctxValue}>
      <div className={cn('space-y-2', className)} role="radiogroup">{children}</div>
    </RadioContext.Provider>
  )
}

export function Radio({ value, children, label, disabled, className, hint }) {
  const ctx = React.useContext(RadioContext)
  const checked = ctx.value === value
  const handleSelect = useCallback(() => {
    if (disabled) return
    ctx.onChange?.(value)
  }, [ctx, disabled, value])

  return (
    <div className={cn('flex items-start gap-3', className)}>
      <button
        type="button"
        role="radio"
        aria-checked={checked}
        disabled={disabled}
        onClick={handleSelect}
        className={cn(
          'mt-0.5 shrink-0 flex items-center justify-center rounded-full border transition-all duration-150',
          checked
            ? 'border-accent-400 bg-gradient-to-br from-accent-300 to-accent-500 shadow-sm shadow-accent-400/20'
            : 'border-white/15 bg-slate-900/60 hover:border-white/30',
          disabled && 'opacity-50 cursor-not-allowed',
          'h-5 w-5',
        )}
      >
        {checked && <span className="h-1.5 w-1.5 rounded-full bg-slate-900" />}
      </button>
      <div className="min-w-0">
        <span className="text-sm text-navy-100">{children || label}</span>
        {hint && <span className="sf-help-text">{hint}</span>}
      </div>
    </div>
  )
}

export { FieldShell }
