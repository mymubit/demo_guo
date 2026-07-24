### Task 4: QualityPage「定位到正文」

**Files:** `QualityPage.tsx` + test

- 每条 issue 增加按钮/链接「定位到正文」
- `navigate(`/projects/${id}/editor?${params}`)`  
  - `episode` = parseEpisodeNumber(row 原始项或 title+detail)  
  - `finding` = finding_key
- 无 operation ID

- [ ] TDD 点击带 episode 的行产生正确 navigate（mock useNavigate）
- [ ] Implement
- [ ] Commit 跳过

---
