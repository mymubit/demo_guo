# W5 Task 4 Brief

Plan Task 4: V3RoleModelMapping + Models REST 适配层

**Files:**
- Model + migration (0018 if 0017 exists)
- Create: `api/v3/models_service.py`, `models_views.py`
- Reuse: `LlmConfigService`, `secret_crypto`
- Test: `test_v3_models_api.py`

**Mapping model (verbatim from plan):**

```python
class V3RoleModelMapping(models.Model):
    role_key = models.CharField(max_length=64, unique=True)
    provider = models.ForeignKey(DramaLlmProvider, on_delete=models.CASCADE, related_name="role_mappings")
    temperature = models.FloatField(null=True, blank=True)
    max_tokens = models.PositiveIntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "drama_v3_role_model_mapping"
```

Paths:
- GET/POST `/api/v3/models/providers/`
- GET/PATCH/DELETE `/api/v3/models/providers/{id}/`
- POST `/api/v3/models/providers/{id}/activate/`
- GET/PUT `/api/v3/models/role-mappings/`

Provider response: id,name,base_url,model_name,temperature,max_tokens,is_enabled,is_active,api_key_set,remark,updated_at — NEVER api_key plaintext.
Empty api_key on PATCH = do not overwrite ciphertext.

Role keys (8): drama-topic-director, drama-story-bible, drama-episode-designer, drama-script-writer, drama-script-scorer, drama-compliance-guard, drama-revision-master, drama-delivery-tool

Do NOT implement test_model_provider yet (Task 5).
Do NOT git commit.
Work: c:\Users\99193\Desktop\demo_guo
sqlite_test.

## Global Constraints
No v6_*; no new deps; skip commit; never return api_key.
