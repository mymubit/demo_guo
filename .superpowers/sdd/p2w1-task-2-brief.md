### Task 2: failover_policy — 链解析 + 错误可切换判定

**Files:**
- Create: `backend/apps/drama/orchestrator/failover_policy.py`
- Test: `backend/apps/drama/tests/test_v3_failover_policy.py`

**Interfaces:**
- Consumes: `V3RoleModelMapping`, `DramaLlmProvider`, `LlmConfigService.resolve_for_role` / provider 行
- Produces:
```python
@dataclass(frozen=True)
class ProviderHop:
    provider_id: str
    provider_name: str
    config: ResolvedLlmConfig  # 已有类型
    attempt_index: int

def resolve_chain(role_key: str) -> list[ProviderHop]:
    """主 provider + backup_provider_ids 去重保序；跳过不存在 id；空映射则单跳 active/resolve。"""

def classify_provider_error(exc: BaseException) -> tuple[str, bool]:
    """返回 (error_code, is_switchable)。
    可切换：timeout/连接、HTTP 401/403/408/429/5xx、未启用/配置不全。
    不可切换：其它（默认 False，避免吞业务错）。
    """
```

- [ ] **Step 1: Write the failing test**

```python
def test_resolve_chain_primary_then_backups_deduped(self):
    # 建 p1,p2,p3；mapping.provider=p1, backup=[p2.id, p1.id, p3.id]
    # hops = resolve_chain("drama-script-writer")
    # ids == [p1, p2, p3]  # 主不重复

def test_classify_timeout_switchable(self):
    code, ok = classify_provider_error(TimeoutError("x"))
    assert ok and code == "timeout"

def test_classify_generic_not_switchable(self):
    code, ok = classify_provider_error(ValueError("bad json later"))
    assert not ok
```

对 `LlmProviderError`：解析 message / 可选挂 `http_status` 属性（若现有异常无 status，用消息子串 `HTTP 429` 等匹配，与 `llm_provider.py` 抛错文案对齐）。

- [ ] **Step 2: Run — expect FAIL**

```powershell
py -3 manage.py test apps.drama.tests.test_v3_failover_policy --settings=config.settings.sqlite_test -v 1
```

- [ ] **Step 3: Implement `failover_policy.py`**

- `resolve_chain`：若存在 mapping → 主 + backups；每跳用该 provider 构建 `ResolvedLlmConfig`（复用 `LlmConfigService` 已有从 provider 构造逻辑；必要时抽小函数 `_config_from_provider(provider, temperature=, max_tokens=)`）。
- 无 mapping：单元素链，等价今日 `resolve()` / `resolve_for_role` 行为。
- `classify_provider_error`：按 Spec §5。

- [ ] **Step 4: Run — expect OK**

- [ ] **Step 5: Commit** — 跳过

---
