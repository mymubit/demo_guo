import fs from 'fs'
import path from 'path'

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
  process.exit(0)
}

console.log(`Found ${issues.length} potential missing imports:`)
for (const i of issues) console.log(`  ${i.file} -> ${i.symbol}`)
process.exit(1)
