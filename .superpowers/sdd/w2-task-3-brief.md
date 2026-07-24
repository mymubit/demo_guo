### Task 3: LLM executor（可注入 mock）

**Files:**
- Create: `backend/apps/drama/skills_bridge/executor.py`
- Extend tests in `test_v3_skills_bridge.py`

**Interfaces:**
- Produces:

```python
def execute_generation(
    *,
    command_type: str,
    project: V3Project,
    run: V3CommandRun,
    llm_call: Callable[..., str] | None = None,
) -> list[V3ArtifactVersion]:
    """
    1) recipe_for(command_type)
    2) 组装最小 user/system 上下文（项目 title/entry_type + 已 committed 依赖产物）
    3) llm_call(prompt) -> JSON text；默认实现走 LlmProvider（读激活供应商）
    4) 解析 JSON；按 writes 拆分或整包映射
    5) validate；失败 raise GenerationError
    6) 为每个 write 创建 V3ArtifactVersion(status=candidate, command_run=run)
    返回创建的候选列表
    """
```

**generate_topic_brief 输出约定（测试用）：** LLM 返回单个 JSON 对象 = `project_brief` payload。  
**generate_blueprint 输出约定：** LLM 返回：

```json
{
  "story_bible": {},
  "character_system": {},
  "world_system": {},
  "emotion_system": {},
  "originality_report": {}
}
```

- [ ] **Step 1: 测试用 fake `llm_call` 返回 fixture** — 断言写出 1 或 5 条 candidate，且 `validate` 通过

- [ ] **Step 2: FAIL → 实现 → PASS**

- [ ] **Step 3: 默认 `llm_call` 路径** — 若无激活 Provider，抛出人话错误「请先在模型配置中配置并启用供应商」（W5 前可在测试中不覆盖默认路径，或 mock Provider）

**注意：** Prompt 拼装可极简（角色 SKILL.md 前 N 字 + 用户输入 JSON）；W2 不追求 injection 完整度，但必须从 `drama-skills/roles/.../SKILL.md` 或 role.yaml 读取，禁止硬编码整份技能正文在 Python 里。

---

