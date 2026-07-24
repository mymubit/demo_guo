# V3 Phase-3：编辑体验 / 导出 / 定位 / 回滚 / 费用预警 — 设计

> 日期：2026-07-23  
> 产品真相源：`drama-website-design/drama-website-design.html`  
> 前置：phase-1（W0–W6）、phase-2（P2-W1–W3）已收口  
> 状态：**已确认**（对话设计 §1–§3 OK）

## 1. 目标

补齐 HTML 中未交付、且**非支付类**的体验缺口：Tiptap 正文编辑、后端 Word 导出、质检→正文定位、主链产物版本回滚、日费用预警。

## 2. 决策记录

| 点 | 选择 |
|----|------|
| 范围 | C（Tiptap+导出）+ D（定位/回滚/预警）；支付不做 |
| 并行 | 交错里程碑，执行中不停顿确认 |
| 回滚 | R2 主链多 key |
| 导出 | E3 仅 Word；PDF=打印说明；**方案 2 后端生成** |
| Tiptap | T2 beat 级 + 简单工具栏；结构化 JSON |
| 定位 | J1 尽力解析集号 |
| 预警 | C2 阈值 + 横幅 + 行着色；无邮件 |

## 3. 非目标

- 支付 / 订阅 / 配额扣减 / 剩余额度强制  
- 服务端 PDF、Excel/Fountain  
- T3 整集自由文档、邮件/站内信  
- 模板库 / 知识库一级导航、多人协作  

## 4. 架构（方案 2）

### 4.1 依赖（实现 plan 钉版本）

- 前端：`@tiptap/react` + `@tiptap/starter-kit`（及官方必要扩展）  
- 后端：`python-docx`  

### 4.2 组件

| 单元 | 职责 |
|------|------|
| `BeatTiptap` + `SceneListEditor` | beat 正文 Tiptap；落库 **纯文本**（`getText()`）；粘贴剥 HTML |
| `POST /api/v3/projects/{id}/delivery/export/docx/` | 门禁通过后生成 docx `FileResponse` |
| `GET /api/v3/projects/{id}/artifacts/?artifact_key=` | committed 版本列表 |
| `POST /api/v3/projects/{id}/artifacts/rollback/` | `{ artifact_key, source_version }` → 新 committed |
| Quality→Editor | query `episode` / `finding`；无集号 toast |
| system overlay | `daily_cost_alert_cny`；Usage/Dashboard 横幅；Usage/Logs 着色 |

### 4.3 回滚 keys

- `project_brief`  
- 蓝图：`story_bible`, `character_system`, `world_system`, `emotion_system`, `originality_report`  
- `episode_plan`  
- `episode_scripts`  
默认 **仅回滚用户选中的单一 key**（不自动捆绑 memory_checkpoint，除非同请求显式传入）。

### 4.4 导出门禁

与 `prepare_delivery` / delivery_gate 一致；失败 400 中文原因。

## 5. 里程碑

| 里程碑 | 交付 |
|--------|------|
| **P3-W1** | Tiptap T2 + 质检定位 J1 |
| **P3-W2** | 后端 docx + Delivery UI（PDF 说明） |
| **P3-W3** | 版本列表 + 回滚 R2 |
| **P3-W4** | 日费用预警 C2 + 全量回归 |

## 6. 验收

1. beat 可用 Tiptap 编辑并保存草稿  
2. Delivery 下载后端 `.docx`；UI 注明 PDF 用打印  
3. 带集号 finding 可跳到对应集；无集号有提示  
4. 主链 key 可回滚为新 committed 版本  
5. 配置日费用阈值后超限有横幅与行着色  
6. 无支付/配额；v2/v6 产品路径仍净  

## 7. 测试

- 前端：Tiptap、Editor query、Delivery 导出、横幅/着色  
- 后端：docx 内容、rollback version+1、overlay 新键  
- mock；禁止外网  
