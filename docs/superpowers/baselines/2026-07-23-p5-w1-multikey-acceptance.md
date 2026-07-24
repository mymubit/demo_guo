# P5-W1 多 Key 轮询验收清单（2026-07-23）

> 计划：`docs/superpowers/plans/2026-07-23-drama-website-v3-p5-w1-multikey.md`  
> 设计：`docs/superpowers/specs/2026-07-23-drama-website-v3-multikey-dashboard-design.md`（A 多 Key）  
> 验收日：2026-07-23

## 验收标准

| # | 标准 | 证据 | 结果 |
|---|------|------|------|
| 1 | `V3LlmProviderKey` 模型（provider FK、label、api_key_encrypted、sort_order、is_enabled）+ migration `0024` | `models.V3LlmProviderKey`；`migrations/0024_v3_llm_provider_key.py` | ☑ |
| 2 | `iter_api_keys`：主 Key 优先，其后启用附加 Key 按 `sort_order` | `orchestrator/provider_keys.py`；`test_v3_provider_keys.ProviderKeysHelperTests` | ☑ |
| 3 | `chat_with_failover` 同 hop 内轮询 Key，可切换错误才换供应商；attempt 含 key label、无明文 key | `llm_router.py`；`MultiKeyRouterTests` | ☑ |
| 4 | REST `…/providers/{id}/keys/` CRUD；响应仅 `api_key_set`，无明文 | `models_views` / `urls`；`V3ProviderKeysApiTests`；OpenAPI | ☑ |
| 5 | ModelsPage 可添加/列表/删除附加密钥；UI 无明文 | `ModelsPage` + vitest | ☑ |
| 6 | 回归：router 旧用例 + ModelsPage + OpenAPI keys 路径 | 后端 12 tests OK；前端 ModelsPage/api 绿 | ☑ |

## API 路径

前缀：`/api/v3/`

| Method | Path | 说明 |
|--------|------|------|
| GET | `/models/providers/{id}/keys/` | 附加密钥列表（脱敏） |
| POST | `/models/providers/{id}/keys/` | 创建（`api_key` write_only） |
| PATCH | `/models/providers/{id}/keys/{key_id}/` | 更新；空 `api_key` 不覆盖 |
| DELETE | `/models/providers/{id}/keys/{key_id}/` | 删除 |

## 机跑

### 后端

```text
DRAMA_SKILLS_ROOT=<repo>/drama-skills
py -3 manage.py test apps.drama.tests.test_v3_provider_keys apps.drama.tests.test_v3_llm_router --settings=config.settings.sqlite_test
→ 12 tests OK
```

### 前端

```text
npm test -- --run src/pages/ModelsPage.test.tsx src/types/v3/api.test.ts
→ ModelsPage + OpenAPI keys 路径通过
```

## 备注

- 主 Key 仍存 `DramaLlmProvider.api_key_encrypted`（逻辑 sort_order=0 / 标签「主密钥」）。
- FailoverAttempt `error_message` 可含密钥标签，严禁明文 key。
