### Task 1: 加依赖 + docx 生成服务

**Files:** `backend/requirements*.txt` or pyproject；Create `orchestrator/docx_export.py`；Test `test_v3_docx_export.py`

```python
def build_episode_scripts_docx(*, project_title: str, scripts_payload: dict) -> bytes:
    """返回 docx 文件字节；含标题与各集正文。"""
```

- [ ] TDD：bytes 以 PK\\x03\\x04 开头或 Document 可读段落含标题
- [ ] pip/requirements 加 python-docx==1.1.2
- [ ] Implement

