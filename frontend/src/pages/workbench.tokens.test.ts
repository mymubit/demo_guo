import { readdirSync, readFileSync, statSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const BRAND_RE = /brand-500|brand-600|bg-brand|text-brand|tone="brand"|variant="brand"/

function collectTsx(dir: string): string[] {
  const out: string[] = []
  for (const name of readdirSync(dir)) {
    const full = resolve(dir, name)
    if (statSync(full).isDirectory()) {
      out.push(...collectTsx(full))
      continue
    }
    if (name.endsWith('.tsx') && !name.includes('.test.')) out.push(full)
  }
  return out
}

const files = [
  resolve(__dirname, 'WorkbenchPage.tsx'),
  ...collectTsx(resolve(__dirname, '../components/workbench')),
  resolve(__dirname, '../components/theme/ThemeMatrixPicker.tsx'),
  resolve(__dirname, '../components/artifacts/ArtifactViews.tsx'),
]

describe('workbench tokens', () => {
  it('PipelineRail source has no indigo brand utilities', () => {
    const src = readFileSync(resolve(__dirname, '../components/workbench/PipelineRail.tsx'), 'utf8')
    expect(src).not.toMatch(/brand-500|bg-brand|text-brand/)
  })

  for (const file of files) {
    const label = file.replace(/\\/g, '/').split('/src/')[1] ?? file
    it(`${label} has no indigo brand classes`, () => {
      const src = readFileSync(file, 'utf8')
      expect(src).not.toMatch(BRAND_RE)
    })
  }
})
