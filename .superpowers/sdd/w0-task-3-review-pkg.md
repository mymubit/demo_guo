# Review Package W0 Task 3

## commands.ts

export const PRODUCT_COMMAND_TYPES = [
  'create_project',
  'generate_topic_brief',
  'confirm_topic_brief',
  'generate_blueprint',
  'confirm_blueprint',
  'generate_episode_plan',
  'revise_episode_plan',
  'write_episode_batch',
  'confirm_script_candidate',
  'score_quality',
  'check_compliance',
  'accept_findings',
  'revise_from_findings',
  'prepare_delivery',
  'test_model_provider',
] as const

export type ProductCommandType = (typeof PRODUCT_COMMAND_TYPES)[number]


## domain.ts

export type ProjectEntryType = 'original' | 'adapt'
export type ProjectStage = 'topic' | 'blueprint' | 'episodes' | 'writing' | 'quality' | 'delivery'

export interface ProjectSummary {
  id: string
  title: string
  entry_type: ProjectEntryType
  stage: ProjectStage
  progress_percent?: number
  updated_at: string
}

export interface CreateProjectRequest {
  title: string
  entry_type: ProjectEntryType
}

export interface BillingPlan {
  id: string
  name: string
  price_label: string
  features: string[]
}


## api.ts

export type { ProductCommandType } from './commands'
export type {
  BillingPlan,
  CreateProjectRequest,
  ProjectEntryType,
  ProjectStage,
  ProjectSummary,
} from './domain'

export interface ApiEnvelope<T> {
  code: number
  message: string
  data: T
}


## api.test.ts

import { describe, expect, it } from 'vitest'
import { PRODUCT_COMMAND_TYPES } from './commands'

describe('v3 commands contract', () => {
  it('includes generate_topic_brief and prepare_delivery', () => {
    expect(PRODUCT_COMMAND_TYPES).toContain('generate_topic_brief')
    expect(PRODUCT_COMMAND_TYPES).toContain('prepare_delivery')
    expect(PRODUCT_COMMAND_TYPES).not.toContain('create-project-brief')
  })
})

