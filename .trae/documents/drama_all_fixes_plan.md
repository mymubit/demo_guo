# Drama Skills 系统问题一次性修复计划

## 仓库调研结论

根据代码库分析，当前存在以下5类待修复问题：
1. **测试文件中文乱码**：测试用例中的中文注释和测试数据出现乱码字符（????），影响代码可读性和维护性
2. **前端死代码**：`validateAllWordCounts`函数存在于drama service中，但无对应后端API实现且未被使用
3. **Django Admin模型未注册**：Drama模块的核心模型未在Admin后台注册，无法通过管理界面查看数据
4. **Admin页面用户体验不佳**：模型配置管理页面缺少loading状态、错误处理和操作反馈
5. **占位功能提示不清晰**：剧本修改建议接口是占位实现，但响应中未明确告知用户，容易造成误解

## 需要修改的文件与模块

### 后端文件
- [test_services.py](file:///workspace/backend/apps/drama/tests/test_services.py) - 修复测试文件中文乱码
- [test_workspace_api.py](file:///workspace/backend/apps/drama/tests/test_workspace_api.py) - 修复测试文件中文乱码
- [admin.py](file:///workspace/backend/apps/drama/admin.py) - 新建Admin模型注册配置
- [views.py](file:///workspace/backend/apps/drama/views.py) - 完善剧本修改建议接口提示

### 前端文件
- [index.js](file:///workspace/frontend/src/services/drama/index.js) - 移除死代码validateAllWordCounts
- [index.jsx](file:///workspace/frontend/src/pages/Admin/drama-models/index.jsx) - 优化Admin页面体验
- [ScriptsPage.jsx](file:///workspace/frontend/src/pages/Drama/ScriptsPage.jsx) - 添加占位功能提示反馈

## 修改步骤

### 步骤1：修复测试文件中文乱码（低优先级）
- 检查test_services.py中的乱码注释，将"??????"替换为有意义的中文描述（如"字数校验服务测试"、"质量评估服务测试"）
- 检查test_workspace_api.py中的docstring和测试数据，将乱码替换为正确的中文描述
- 确保测试用例语义清晰可维护

### 步骤2：移除前端死代码（低优先级）
- 在drama service中删除`validateAllWordCounts`函数，该函数无对应后端API且未被任何组件调用
- 清理相关导入，避免未使用变量警告

### 步骤3：创建Django Admin模型注册（低优先级）
- 新建apps/drama/admin.py文件
- 注册以下5个核心模型：DramaRoleExecution、DramaEpisodeArtifact、DramaEpisodeQuality、DramaTokenUsage、DramaProjectConfig
- 配置只读权限（禁止添加/修改/删除，仅允许查看）
- 设置合理的list_display、list_filter、search_fields和readonly_fields，方便后台数据排查

### 步骤4：优化Admin页面体验（中优先级）
- 为模型配置页面添加LoadingState组件（加载中显示spinner）
- 添加ErrorState组件（加载失败显示错误信息和重试按钮）
- 为保存操作添加toast反馈（成功/失败提示）
- 使用项目统一的Button、Card组件，保持UI风格一致
- 处理加载中禁用按钮状态，防止重复提交

### 步骤5：完善剧本修改建议接口提示（中优先级）
- 后端API响应中添加`feature_status: "placeholder"`字段明确标注占位状态
- 更新响应message，清晰告知用户功能开发中
- 在note字段说明"自动修改剧本功能待接入LLM后开放，当前仅记录修改建议"
- 前端ScriptsPage的onSuccess回调中检测feature_status，分别显示不同提示：
  - placeholder状态：使用toast.info显示"修改建议已记录"及说明
  - 正常状态：保持原有成功提示

### 步骤6：最终验证（高优先级）
- 后端所有修改文件进行Python语法检查（py_compile）
- 前端执行生产构建（npm run build）确保无编译错误
- 验证所有改动不破坏现有功能

## 潜在依赖与注意事项

1. **Admin模型注册**：所有模型均设置为只读权限（has_add_permission/has_change_permission/has_delete_permission返回False），避免后台误操作影响数据
2. **API兼容性**：后端添加feature_status字段属于新增字段，不改变原有响应结构，保持向后兼容
3. **UI组件复用**：Admin页面优化复用项目已有的Button、Card组件和sonner toast库，不引入新依赖
4. **测试文件**：仅修复注释和测试数据乱码，不修改测试逻辑本身

## 风险处理

- **风险1**：Admin注册可能暴露敏感数据 → 缓解：所有模型设为只读，且仅超级管理员可访问Django Admin
- **风险2**：前端修改可能引入编译错误 → 缓解：执行生产构建验证，使用TypeScript类型检查
- **风险3**：API字段新增影响旧版前端 → 缓解：新增字段为可选，旧版前端忽略不影响使用
- **风险4**：死代码移除可能遗漏调用点 → 缓解：全局搜索确认函数未被使用后再删除
