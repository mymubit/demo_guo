# 一次性修复全部剩余问题 - 实施计划

## 仓库研究结论

经过多轮修复，短剧剧本创作网站的核心功能已全部正常：
- ✅ 后端接口：权限控制、异常处理、事务保护、参数验证均已完善
- ✅ 前端页面：loading/error状态、内存泄漏修复、动态Tailwind类问题已解决
- ✅ 中文乱码：views.py/services.py/urls.py/progress_service.py等核心业务文件乱码已修复
- ✅ 构建验证：Python语法检查通过，前端生产构建成功

剩余待修复问题共5项，均为非核心Bug但影响代码质量和用户体验。

## 待修复问题清单

| 序号 | 问题 | 优先级 | 影响范围 | 文件 |
|------|------|--------|----------|------|
| 1 | 测试文件中文乱码 | 低 | 测试注释/数据 | `backend/apps/drama/tests/test_services.py` `backend/apps/drama/tests/test_workspace_api.py` |
| 2 | 前端死代码 `validateAllWordCounts` | 极低 | 前端service | `frontend/src/services/drama/index.js` |
| 3 | 缺少Django Admin模型注册 | 低 | 后台管理 | 需新建 `backend/apps/drama/admin.py` |
| 4 | Admin页面缺少loading/error状态和toast反馈 | 中 | 管理后台用户体验 | `frontend/src/pages/Admin/drama-models/index.jsx` |
| 5 | 剧本修改建议接口返回提示不明确 | 中 | 用户体验 | `backend/apps/drama/views.py` |

> **说明**：剧本修改建议的LLM实际调用是完整功能开发（涉及prompt设计、LLM接入、重试机制、内容校验等），属于新功能开发而非bug修复。本次修复将完善错误提示和占位说明，避免用户误解。

## 修改步骤

### 步骤1：修复测试文件中文乱码

**文件**：
- [test_services.py](file:///workspace/backend/apps/drama/tests/test_services.py)
- [test_workspace_api.py](file:///workspace/backend/apps/drama/tests/test_workspace_api.py)

**修改内容**：
- 将 `"""Drama Services ?????? - DramaWordCountService / DramaQualityService"""` 替换为 `"""Drama Services 单元测试 - DramaWordCountService / DramaQualityService"""`
- 将 `"""??????"""` 类文档字符串替换为对应的中文：
  - `"""字数校验服务测试"""`
  - `"""质量评估服务测试"""`
- 修复test_workspace_api.py中的乱码注释和测试数据（`"????"` → `"测试创意"`）

**风险**：无，仅修改注释，不影响测试逻辑。

---

### 步骤2：移除前端死代码

**文件**：[drama/index.js](file:///workspace/frontend/src/services/drama/index.js)

**修改内容**：
- 删除未被任何组件调用且后端无对应接口的 `validateAllWordCounts` 函数
- 保留其他已使用的API函数不变

**风险**：无，Tree-shaking本来就会移除未使用代码，显式删除更清晰。

---

### 步骤3：创建Django Admin注册

**新建文件**：[backend/apps/drama/admin.py](file:///workspace/backend/apps/drama/admin.py)

**修改内容**：
- 注册以下模型到Django Admin后台：
  - DramaRoleExecution（角色执行记录）
  - DramaEpisodeArtifact（单集剧本产物）
  - DramaEpisodeQuality（单集质量评估）
  - DramaGenerationPlan（批量生成计划）
  - DramaEpisodePlan（单集执行计划）
- 配置list_display、list_filter、search_fields方便管理员查看和排查问题
- 设置只读字段防止误修改关键执行数据

**风险**：低，仅新增后台管理功能，不影响现有业务逻辑。

---

### 步骤4：优化Admin模型配置页面体验

**文件**：[drama-models/index.jsx](file:///workspace/frontend/src/pages/Admin/drama-models/index.jsx)

**修改内容**：
1. 添加数据加载状态：
   - configs加载中显示loading spinner
   - stats加载中显示loading状态
2. 添加错误状态：
   - API请求失败时显示错误提示和重试按钮
3. 添加操作反馈：
   - 保存成功显示toast成功提示
   - 保存失败显示toast错误提示
4. 使用项目统一UI组件（Button/Card）替换原生button
5. 将原生input/select样式与项目风格统一

**依赖**：需要导入项目已有的toast（sonner）、Button、Card、Loader2等组件

**风险**：低，仅改进用户体验，不改变原有功能逻辑。

---

### 步骤5：完善剧本修改建议接口的提示

**文件**：[views.py](file:///workspace/backend/apps/drama/views.py) 中的 EpisodeArtifactView.post

**修改内容**：
1. 在返回结果中明确标注功能状态：
   ```python
   "feature_status": "placeholder",
   "message": "修改建议功能开发中，当前为占位实现，暂未实际修改剧本内容"
   ```
2. 同时在前端ScriptsPage.jsx的相关处理中，如果接收到placeholder状态，显示明确提示而不是静默"应用"
3. 保持现有接口结构不变，避免破坏前端调用

**风险**：低，仅增加提示信息，不改变接口契约。

## 验证方案

每完成一个步骤后进行验证：
1. 后端修改：`python -m py_compile` 语法检查
2. 前端修改：运行 `npm run build` 确保构建成功
3. 全部完成后：
   - 后端语法全量检查
   - 前端生产构建
   - （可选）运行后端测试确保无回归

## 依赖和注意事项

1. **无新增第三方依赖**：所有修复均使用项目已有组件和库
2. **无数据库迁移**：新增admin.py不涉及schema变更
3. **向后兼容**：所有API接口保持原有响应结构，仅新增字段（前端可选择性处理）
4. **代码风格**：遵循项目现有规范（Django分层、React Hooks、Tailwind风格）
