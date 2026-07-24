### Task 3: 前端 TS 类型与契约测试

**Files:**
- Create: `frontend/src/types/v3/domain.ts`
- Create: `frontend/src/types/v3/commands.ts`
- Create: `frontend/src/types/v3/api.ts`
- Create: `frontend/src/types/v3/api.test.ts`

**Interfaces:**
- Consumes: OpenAPI schemas、commands.md
- Produces: 导出类型供页面与 services 使用

- [ ] **Step 1: 写失败测试（命令枚举完整性）**

创建 `frontend/src/types/v3/api.test.ts`：

```typescript
import { describe, expect, it } from 'vitest'
import { PRODUCT_COMMAND_TYPES } from './commands'

describe('v3 commands contract', () => {
  it('includes generate_topic_brief and prepare_delivery', () => {
    expect(PRODUCT_COMMAND_TYPES).toContain('generate_topic_brief')
    expect(PRODUCT_COMMAND_TYPES).toContain('prepare_delivery')
    expect(PRODUCT_COMMAND_TYPES).not.toContain('create-project-brief')
  })
})
```

- [ ] **Step 2: 运行测试确认失败**

Run: `cd frontend && npm test -- src/types/v3/api.test.ts`  
Expected: FAIL（模块不存在或 `PRODUCT_COMMAND_TYPES` 未定义）

- [ ] **Step 3: 实现类型文件**

`frontend/src/types/v3/commands.ts`：

```typescript
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
```

`frontend/src/types/v3/domain.ts`：

```typescript
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
```

`frontend/src/types/v3/api.ts`：

```typescript
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
```

- [ ] **Step 4: 运行测试确认通过**

Run: `cd frontend && npm test -- src/types/v3/api.test.ts`  
Expected: PASS

---

