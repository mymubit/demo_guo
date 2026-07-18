import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'

const files = [
  'ExternalReviewPage.tsx',
  'ExternalReviewRecordsPage.tsx',
  'ModelHubPage.tsx',
  'LlmLogsPage.tsx',
  'AdminConfigPage.tsx',
  'SkillOpsPage.tsx',
]

describe('ops-tools pages tokens', () => {
  for (const file of files) {
    it(`${file} has no indigo brand classes`, () => {
      const src = readFileSync(resolve(__dirname, file), 'utf8')
      expect(src).not.toMatch(/brand-500|brand-600|bg-brand|text-brand|tone="brand"|variant="brand"/)
    })
  }
})
