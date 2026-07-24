### Task 1: 安装 echarts + UsagePage

**Files:** package.json；Create UsagePage.tsx；Create UsagePage.test.tsx

**UI:**
- 筛选：项目、date_from、date_to、group_by（day/model）
- 汇总表：rows + totals（token、estimated_cost、unpriced_call_count；未定价显示「未定价」）
- ECharts：折线/柱状按日 token 与费用；按模型对比柱图
- 动态 `import('echarts')`；中文；无 operation ID
- 默认 `live=0`

- [ ] TDD：渲染标题「用量」、筛选、表、图表容器 data-testid
- [ ] npm install echarts@5.5.1
- [ ] Implement
- [ ] Commit 跳过

---
