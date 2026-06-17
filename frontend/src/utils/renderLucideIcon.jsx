import { isValidElement } from 'react'

/** 兼容 Lucide 组件与已渲染 JSX 元素两种 icon 传参 */
export function renderLucideIcon(icon, className, props = {}) {
  if (!icon) return null
  if (isValidElement(icon)) return icon
  const IconComponent = icon
  return <IconComponent className={className} {...props} />
}
