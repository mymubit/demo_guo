import fs from 'fs'
import path from 'path'
import { execSync } from 'node:child_process'

const root = path.join(process.cwd(), 'src')

/** 十大中心重组后易漏 import 的符号（运行时 ReferenceError） */
const ADMIN_RUNTIME_SYMBOLS = [
  'AdminShell',
  'useAdminPanelMessage',
  'resolveFusionNodeAgent',
  'formatAgentStepTitle',
  'formatAgentStepSubtitle',
  'formatActionKeyTitle',
  'resolveAgentId',
  'resolveAgentDisplayName',
  'mergeSubSkillSteps',
  'formatProjectExecutionSummary',
  'motion',
]

const SCAN_DIRS = ['src/pages/Admin', 'src/components/admin']

function walk(dir, out = []) {
  if (!fs.existsSync(dir)) return out
  for (const f of fs.readdirSync(dir)) {
    const p = path.join(dir, f)
    if (fs.statSync(p).isDirectory()) walk(p, out)
    else if (/\.(jsx|js)$/.test(f)) out.push(p)
  }
  return out
}

function collectImports(src) {
  const set = new Set()
  for (const m of src.matchAll(/import\s*\{([^}]+)\}\s*from\s*['"][^'"]+['"]/g)) {
    m[1].split(',').forEach((part) => {
      const name = part.trim().split(/\s+as\s+/).pop().trim()
      if (name) set.add(name)
    })
  }
  for (const m of src.matchAll(/import\s+([A-Za-z_$][\w$]*)\s*,\s*\{([^}]+)\}\s*from\s*['"][^'"]+['"]/g)) {
    set.add(m[1])
    m[2].split(',').forEach((part) => {
      const name = part.trim().split(/\s+as\s+/).pop().trim()
      if (name) set.add(name)
    })
  }
  for (const m of src.matchAll(/import\s+([A-Za-z_$][\w$]*)\s+from\s*['"][^'"]+['"]/g)) {
    set.add(m[1])
  }
  return set
}

function isDefinedLocally(src, sym) {
  return (
    src.includes(`function ${sym}`) ||
    src.includes(`const ${sym}`) ||
    src.includes(`export function ${sym}`) ||
    src.includes(`export const ${sym}`) ||
    src.includes(`export default function ${sym}`)
  )
}

function usesSymbol(src, sym) {
  const body = src.replace(/^import[\s\S]*?from\s+['"][^'"]+['"];?\s*/gm, '')
  return new RegExp(`\\b${sym}\\b`).test(body)
}

const issues = []

for (const dir of SCAN_DIRS) {
  for (const file of walk(path.join(process.cwd(), dir))) {
    const src = fs.readFileSync(file, 'utf8')
    const rel = path.relative(process.cwd(), file).replace(/\\/g, '/')
    const imports = collectImports(src)

    for (const sym of ADMIN_RUNTIME_SYMBOLS) {
      if (!usesSymbol(src, sym)) continue
      if (imports.has(sym) || isDefinedLocally(src, sym)) continue
      issues.push({ file: rel, symbol: sym })
    }
  }
}

if (!issues.length) {
  console.log('No Admin missing-import issues detected.')
} else {
  console.log(`Found ${issues.length} potential missing imports:`)
  for (const i of issues) console.log(`  ${i.file} -> ${i.symbol}`)
}

// Vite 构建校验 — 捕获「模块未导出 named export」类错误
let buildOutput = ''
try {
  buildOutput = execSync('npm run build', { encoding: 'utf8', stdio: 'pipe' })
} catch (e) {
  buildOutput = `${e.stdout || ''}${e.stderr || ''}`
}

const exportRe = /"([^"]+)" is not exported by "([^"]+)"/g
const exportIssues = []
let exportMatch
while ((exportMatch = exportRe.exec(buildOutput))) {
  exportIssues.push({ exportName: exportMatch[1], module: exportMatch[2] })
}

if (exportIssues.length) {
  console.log(`Found ${exportIssues.length} missing export(s) from build:`)
  for (const item of exportIssues) {
    console.log(`  - ${item.exportName} from ${item.module}`)
  }
}

// adminNav 路径 vs router 子路由
const adminNavPath = path.join(process.cwd(), 'src/config/adminNav.js')
const consumerNavPath = path.join(process.cwd(), 'src/config/consumerNav.js')
const routerPath = path.join(process.cwd(), 'src/router/index.jsx')
const routeIssues = []

function normalizeRouterPaths(routerSrc) {
  const paths = new Set()
  for (const match of routerSrc.matchAll(/path:\s*['"]([^'"]+)['"]/g)) {
    const raw = match[1]
    if (raw === '*' || raw === '/admin') continue
    if (raw.startsWith('/')) {
      paths.add(raw.split('?')[0])
      continue
    }
    paths.add(`/admin/${raw.replace(/^\//, '')}`.split('?')[0])
  }
  paths.add('/admin/dashboard')
  return paths
}

function routeMatches(registeredPaths, targetPath) {
  const base = targetPath.split('?')[0]
  if (registeredPaths.has(base)) return true
  for (const routePath of registeredPaths) {
    if (!routePath.includes(':')) continue
    const pattern = new RegExp(
      `^${routePath.replace(/:[^/]+/g, '[^/]+').replace(/\//g, '\\/')}$`,
    )
    if (pattern.test(base)) return true
  }
  return false
}

if (fs.existsSync(adminNavPath) && fs.existsSync(routerPath)) {
  const navSrc = fs.readFileSync(adminNavPath, 'utf8')
  const routerSrc = fs.readFileSync(routerPath, 'utf8')
  const routePaths = normalizeRouterPaths(routerSrc)

  const navPaths = [...navSrc.matchAll(/path:\s*['"](\/admin[^'"]*)['"]/g)].map((m) => m[1])

  for (const itemPath of navPaths) {
    const base = itemPath.split('?')[0]
    if (!routeMatches(routePaths, base)) {
      routeIssues.push({ navPath: itemPath, reason: 'missing admin router child' })
    }
  }
}

if (fs.existsSync(consumerNavPath) && fs.existsSync(routerPath)) {
  const consumerSrc = fs.readFileSync(consumerNavPath, 'utf8')
  const routerSrc = fs.readFileSync(routerPath, 'utf8')
  const routePaths = normalizeRouterPaths(routerSrc)

  const consumerPaths = [
    ...consumerSrc.matchAll(/path:\s*['"](\/[^'"]+)['"]/g),
  ].map((m) => m[1])

  for (const itemPath of consumerPaths) {
    const base = itemPath.split('?')[0]
    if (itemPath.includes('redirectTo')) continue
    if (!routeMatches(routePaths, base)) {
      routeIssues.push({ navPath: itemPath, reason: 'missing consumer route' })
    }
  }
}

// 页面容器：C 端页面手写 mx-auto + max-w-* 而未用 PageContainer / sf-page-shell
const pageShellIssues = []
const legacyPageShellRe = /(?:mx-auto[^"'`]*max-w-(?:4xl|5xl|6xl|7xl)|max-w-(?:4xl|5xl|6xl|7xl)[^"'`]*mx-auto)/
for (const file of walk(path.join(process.cwd(), 'src/pages'))) {
  const rel = path.relative(process.cwd(), file).replace(/\\/g, '/')
  if (rel.includes('_design/')) continue
  const src = fs.readFileSync(file, 'utf8')
  if (src.includes('PageContainer') || src.includes('ConsumerShell') || src.includes('sf-page-shell')) continue
  if (legacyPageShellRe.test(src)) {
    pageShellIssues.push(rel)
  }
}

if (pageShellIssues.length) {
  console.log(`Found ${pageShellIssues.length} page(s) with legacy page shell (use PageContainer):`)
  for (const file of pageShellIssues) console.log(`  - ${file}`)
}

// 遗留组件类：源码引用但 globals.css 未定义会导致无样式（按钮/标题/焦点环等）
const LEGACY_COMPONENT_CLASSES = [
  'btn-gold',
  'btn-primary',
  'btn-ghost',
  'section-title',
  'section-subtitle',
  'sf-focus-ring',
  'sf-progress-rendered',
  'node-preview-content',
  'gradient-text',
  'gradient-text-primary',
]
const globalsCssPath = path.join(process.cwd(), 'src/styles/globals.css')
const globalsCss = fs.existsSync(globalsCssPath) ? fs.readFileSync(globalsCssPath, 'utf8') : ''
const legacyClassIssues = []

for (const cls of LEGACY_COMPONENT_CLASSES) {
  let used = false
  for (const dir of ['src/pages', 'src/components']) {
    for (const file of walk(path.join(process.cwd(), dir))) {
      if (file.includes('_design')) continue
      if (fs.readFileSync(file, 'utf8').includes(cls)) {
        used = true
        break
      }
    }
    if (used) break
  }
  if (used && !globalsCss.includes(`.${cls}`)) {
    legacyClassIssues.push(cls)
  }
}

if (legacyClassIssues.length) {
  console.log(`Missing legacy component CSS in globals.css: ${legacyClassIssues.join(', ')}`)
}

// 危险工具栏：flex 行内按钮/select 未使用 sf-toolbar，易挤压竖排
const toolbarIssues = []
const riskyToolbarRe = /className="[^"]*flex flex-col (?:md|sm|lg):flex-row[^"]*"[^>]*>[\s\S]{0,400}?<(button|select)/g
for (const dir of ['src/pages', 'src/components']) {
  for (const file of walk(path.join(process.cwd(), dir))) {
    const rel = path.relative(process.cwd(), file).replace(/\\/g, '/')
    if (rel.includes('_design/')) continue
    const src = fs.readFileSync(file, 'utf8')
    if (src.includes('sf-toolbar') || src.includes('AdminToolbar') || src.includes('ConsumerListToolbar')) continue
    riskyToolbarRe.lastIndex = 0
    if (riskyToolbarRe.test(src)) {
      toolbarIssues.push(rel)
    }
    riskyToolbarRe.lastIndex = 0
  }
}

if (toolbarIssues.length) {
  console.log(`Found ${toolbarIssues.length} file(s) with risky flex toolbar (use sf-toolbar):`)
  for (const file of toolbarIssues) console.log(`  - ${file}`)
}

// 危险 icon 渲染模式：<Icon className= 且 icon 可能为 JSX
const iconRenderIssues = []
const iconRenderRe = /<(\w+)\.icon\s+className=|<Icon\s+className=/g
for (const dir of ['src/pages', 'src/components']) {
  for (const file of walk(path.join(process.cwd(), dir))) {
    const rel = path.relative(process.cwd(), file).replace(/\\/g, '/')
    const src = fs.readFileSync(file, 'utf8')
    if (iconRenderRe.test(src) && !src.includes('renderLucideIcon')) {
      iconRenderIssues.push(path.relative(process.cwd(), file).replace(/\\/g, '/'))
    }
    iconRenderRe.lastIndex = 0
  }
}

if (iconRenderIssues.length) {
  console.log(`Found ${iconRenderIssues.length} file(s) with legacy icon render pattern:`)
  for (const file of iconRenderIssues) console.log(`  - ${file}`)
}

if (issues.length || exportIssues.length || routeIssues.length || iconRenderIssues.length || toolbarIssues.length || pageShellIssues.length || legacyClassIssues.length) {
  process.exit(1)
}

console.log('Build export check passed.')
process.exit(0)
