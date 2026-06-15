const BLOCKED_TAGS = new Set(['SCRIPT', 'STYLE', 'IFRAME', 'OBJECT', 'EMBED'])

export function sanitizeHtml(html) {
  const source = String(html || '')
  if (!source || typeof DOMParser === 'undefined') return source

  const doc = new DOMParser().parseFromString(source, 'text/html')
  doc.body.querySelectorAll('*').forEach((node) => {
    if (BLOCKED_TAGS.has(node.tagName)) {
      node.remove()
      return
    }
    Array.from(node.attributes).forEach((attr) => {
      const name = attr.name.toLowerCase()
      const value = String(attr.value || '').trim().toLowerCase()
      if (name.startsWith('on') || value.startsWith('javascript:')) {
        node.removeAttribute(attr.name)
      }
    })
  })
  return doc.body.innerHTML
}
