import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import { describe, expect, it } from 'vitest'
import { PRODUCT_COMMAND_TYPES } from './commands'
import type {
  LogCall,
  LogRun,
  ModelPrice,
  ModelProvider,
  RoleModelMapping,
  SystemConfigState,
  UsageSummary,
} from './domain'
import { ROLE_MODEL_KEYS } from './domain'

const openapi = readFileSync(
  resolve(__dirname, '../../../../docs/contracts/v3/openapi.yaml'),
  'utf8',
)

describe('v3 commands contract', () => {
  it('includes generate_topic_brief and prepare_delivery', () => {
    expect(PRODUCT_COMMAND_TYPES).toContain('generate_topic_brief')
    expect(PRODUCT_COMMAND_TYPES).toContain('prepare_delivery')
    expect(PRODUCT_COMMAND_TYPES).not.toContain('create-project-brief')
  })

  it('includes confirm_episode_plan for W3 episode confirmation', () => {
    expect(PRODUCT_COMMAND_TYPES).toContain('confirm_episode_plan')
  })

  it('includes test_model_provider for W5 model connectivity', () => {
    expect(PRODUCT_COMMAND_TYPES).toContain('test_model_provider')
  })
})

describe('v3 openapi W4 quality/delivery paths', () => {
  it('registers quality and delivery resource paths', () => {
    expect(openapi).toContain('/projects/{project_id}/quality/:')
    expect(openapi).toContain('/projects/{project_id}/quality/score/:')
    expect(openapi).toContain('/projects/{project_id}/quality/compliance/:')
    expect(openapi).toContain('/projects/{project_id}/quality/accept/:')
    expect(openapi).toContain('/projects/{project_id}/quality/revise/:')
    expect(openapi).toContain('/projects/{project_id}/delivery/:')
    expect(openapi).toContain('/projects/{project_id}/delivery/prepare/:')
  })
})

describe('v3 openapi P4 templates/knowledge paths', () => {
  it('registers templates and knowledge resource paths', () => {
    expect(openapi).toContain('/templates/:')
    expect(openapi).toContain('/templates/custom/:')
    expect(openapi).toContain('/templates/custom/{template_id}/:')
    expect(openapi).toContain('/knowledge/:')
    expect(openapi).toContain('/knowledge/doc/:')
  })
})

describe('v3 openapi W5 system/models/logs paths', () => {
  it('registers system config, models, and logs paths', () => {
    expect(openapi).toContain('/system/config/:')
    expect(openapi).toContain('/models/providers/:')
    expect(openapi).toContain('/models/providers/{provider_id}/:')
    expect(openapi).toContain('/models/providers/{provider_id}/activate/:')
    expect(openapi).toContain('/models/providers/{provider_id}/test/:')
    expect(openapi).toContain('/models/providers/{provider_id}/keys/:')
    expect(openapi).toContain('/models/providers/{provider_id}/keys/{key_id}/:')
    expect(openapi).toContain('/models/role-mappings/:')
    expect(openapi).toContain('/models/prices/:')
    expect(openapi).toContain('/models/prices/{price_id}/:')
    expect(openapi).toContain('deleteModelPrice')
    expect(openapi).toContain('EnvelopeModelPriceDeleted')
    expect(openapi).toContain('/usage/summary/:')
    expect(openapi).toContain('/logs/runs/:')
    expect(openapi).toContain('/logs/runs/{run_id}/:')
    expect(openapi).toContain('/logs/calls/{call_id}/:')
  })

  it('defines W5 domain schemas without api_key plaintext on provider', () => {
    expect(openapi).toContain('SystemConfigState:')
    expect(openapi).toContain('daily_cost_alert_cny:')
    expect(openapi).toContain('ModelProvider:')
    expect(openapi).toContain('ProviderKey:')
    expect(openapi).toContain('RoleModelMapping:')
    expect(openapi).toContain('ModelPrice:')
    expect(openapi).toContain('UsageSummary:')
    expect(openapi).toContain('LogRun:')
    expect(openapi).toContain('LogCall:')
    expect(openapi).toContain('FailoverAttempt:')
    expect(openapi).toContain('api_key_set:')
    // 响应 schema 不得把 api_key 列为 ModelProvider 必填/公开字段块
    const providerBlock = openapi.slice(
      openapi.indexOf('ModelProvider:'),
      openapi.indexOf('ModelProviderWrite:'),
    )
    expect(providerBlock).toContain('api_key_set')
    expect(providerBlock).not.toMatch(/^\s+api_key:/m)
  })
})

describe('v3 domain W5 types', () => {
  it('exposes role model keys aligned with recipe roles', () => {
    expect(ROLE_MODEL_KEYS).toEqual([
      'drama-topic-director',
      'drama-story-bible',
      'drama-episode-designer',
      'drama-script-writer',
      'drama-script-scorer',
      'drama-compliance-guard',
      'drama-revision-master',
      'drama-delivery-tool',
    ])
  })

  it('SystemConfigState / ModelProvider / RoleMapping / LogRun / LogCall key shapes', () => {
    const systemKeys: (keyof SystemConfigState)[] = [
      'revision',
      'overlay',
      'effective',
    ]
    const providerKeys: (keyof ModelProvider)[] = [
      'id',
      'name',
      'base_url',
      'model_name',
      'temperature',
      'max_tokens',
      'is_enabled',
      'is_active',
      'api_key_set',
      'remark',
      'updated_at',
    ]
    const mappingKeys: (keyof RoleModelMapping)[] = [
      'role_key',
      'provider_id',
      'temperature',
      'max_tokens',
      'updated_at',
    ]
    const priceKeys: (keyof ModelPrice)[] = [
      'id',
      'provider_id',
      'provider_name',
      'model_name',
      'price_in_per_1k',
      'price_out_per_1k',
      'price_cache_in_per_1k',
      'currency',
    ]
    const usageKeys: (keyof UsageSummary)[] = [
      'timezone',
      'date_from',
      'date_to',
      'group_by',
      'rows',
      'totals',
    ]
    const runKeys: (keyof LogRun)[] = [
      'id',
      'command_type',
      'status',
      'project_id',
      'error_message',
      'result_payload',
      'created_at',
      'updated_at',
      'calls',
      'failover_attempts',
    ]
    const callKeys: (keyof LogCall)[] = [
      'id',
      'role',
      'purpose',
      'status',
      'model_name',
      'latency_ms',
      'system_prompt',
      'user_prompt',
      'response_text',
      'created_at',
    ]

    expect(systemKeys).toHaveLength(3)
    expect(providerKeys).toContain('api_key_set')
    expect(providerKeys).not.toContain('api_key' as keyof ModelProvider)
    expect(mappingKeys).toContain('role_key')
    expect(priceKeys).toContain('provider_name')
    expect(usageKeys).toEqual([
      'timezone',
      'date_from',
      'date_to',
      'group_by',
      'rows',
      'totals',
    ])
    expect(runKeys).toContain('calls')
    expect(runKeys).toContain('failover_attempts')
    expect(callKeys).toContain('system_prompt')
    expect(callKeys).toContain('response_text')
  })
})
