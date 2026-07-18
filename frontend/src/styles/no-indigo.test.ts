import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative } from 'node:path'
import { describe, expect, it } from 'vitest'

const SRC_ROOT = join(__dirname, '..')
const FORBIDDEN = /brand-500|#6366f1|bg-brand-|text-brand-/
const ALLOWED_TEST_SUFFIX = /\.tokens\.test\.(ts|tsx)$|tokens\.test\.ts$/

function walk(dir: string, out: string[] = []): string[] {
  for (const name of readdirSync(dir)) {
    const full = join(dir, name)
    const st = statSync(full)
    if (st.isDirectory()) {
      if (name === 'node_modules' || name === 'dist') continue
      walk(full, out)
    } else if (/\.(tsx?|css|js)$/.test(name)) {
      out.push(full)
    }
  }
  return out
}

describe('no indigo brand leftovers', () => {
  it('src has no indigo brand utilities outside token guard tests', () => {
    const hits: string[] = []
    for (const file of walk(SRC_ROOT)) {
      const rel = relative(SRC_ROOT, file).replace(/\\/g, '/')
      if (
        ALLOWED_TEST_SUFFIX.test(rel) ||
        rel === 'styles/tokens.test.ts' ||
        rel === 'styles/no-indigo.test.ts'
      ) {
        continue
      }
      const src = readFileSync(file, 'utf8')
      if (FORBIDDEN.test(src)) hits.push(rel)
    }
    expect(hits).toEqual([])
  })
})
