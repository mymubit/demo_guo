# ScriptForge Drama Skills 全站测试方案

> **版本**：v1.0 · 2026-06-22  
> **技术栈**：Django 6 + DRF · React + TailwindCSS  
> **测试范围**：35个drama.* 角色 · 两条创作通道 · 全部API接口 · 前端页面  
> **准入标准**：P0/P1 零缺陷，P2 缺陷不超过3个，整体覆盖率 ≥ 85%

---

## 一、测试范围与优先级矩阵

| 模块 | 优先级 | 用例数 | 测试类型 |
|------|--------|--------|---------|
| 快速通道（8角色端到端）| P0 | 40 | 功能+接口+流程 |
| 专家通道（35角色端到端）| P0 | 35×8=280 | 功能+接口 |
| `/api/drama/` API接口 | P0 | 60 | 接口专项 |
| 字数治理官验证 | P0 | 20 | 接口+边界 |
| 质量报告（10维评分）| P0 | 24 | 功能+边界 |
| 合规守卫检测 | P0 | 15 | 功能+安全 |
| 前端工作台页面 | P1 | 35 | UI+交互 |
| 前端剧本展示页 | P1 | 20 | UI+交互 |
| Token/计费统计 | P1 | 18 | 功能+接口 |
| 模型配置Admin | P1 | 15 | 功能+权限 |
| 交付打包官 | P1 | 12 | 功能+边界 |
| 安全专项 | P0 | 18 | 安全 |
| 性能基线 | P2 | 10 | 性能 |
| 回归矩阵 | P0 | 30 | 回归 |

**总计：约 597 个用例**

---

## 二、快速通道（Fast Track）端到端测试

> 8个核心角色完整链路：topic-planner → world-architect → character-designer → plot-architect → script-writer → script-reviewer → quality-reporter → compliance-guard

### 2.1 正常主流程

| ID | 用例标题 | 步骤 | 预期结果 | 优先级 |
|----|---------|------|---------|--------|
| FT-001 | 创建快速通道项目 | POST `/api/drama/projects/` `{"title":"测试剧","track_mode":"fast"}` | 返回201，`track_mode=fast`，`completed_roles=[]` | P0 |
| FT-002 | 选题定调官执行成功 | POST `/api/drama/projects/{id}/run/drama.topic-director/` | 返回200，状态=queued | P0 |
| FT-003 | 8角色顺序执行完成 | 依次执行8个角色 | `completed_roles` 包含所有8个ID，`delivery_status=ready` | P0 |
| FT-004 | 完成率计算正确 | GET `/api/drama/projects/{id}/progress/` | `completion_rate=100.0`，每个角色`is_completed=true` | P0 |
| FT-005 | 质量报告生成 | 所有角色完成后 | `quality_scores.overall >= 0`，8个维度均有分值 | P0 |
| FT-006 | 合规检测通过 | 执行 compliance-guard | `compliance_report.overall_result=通过` | P0 |
| FT-007 | 字数验证全部达标 | POST `/api/drama/validate/word-count/` 逐集验证 | 首集900-1100字，其余700-900字，台词≥28% | P0 |
| FT-008 | 交付状态更新 | 所有P0角色完成后 | `delivery_status=ready` 自动更新 | P0 |

### 2.2 快速通道边界场景

| ID | 用例标题 | 输入 | 预期结果 | 优先级 |
|----|---------|------|---------|--------|
| FT-B01 | 跳过非必选角色 | 仅执行8个快速通道角色 | 其余27个角色 `is_completed=false`，进度仍能100% | P0 |
| FT-B02 | 角色重复执行 | 对同一角色执行两次 | 幂等处理，最新一次覆盖，`completed_roles` 不重复 | P1 |
| FT-B03 | 角色执行中断 | 执行时模拟中断 | `status=failed`，可重新执行，不影响其他角色 | P1 |
| FT-B04 | 极端集数 | `total_episodes=200` | 正常创建，字数验证按集数线性计算 | P2 |
| FT-B05 | 最小集数 | `total_episodes=5` | 正常创建，所有验证适配最小体量 | P2 |

### 2.3 专家通道与快速通道切换

| ID | 用例标题 | 步骤 | 预期结果 | 优先级 |
|----|---------|------|---------|--------|
| FT-C01 | 快速通道项目无法访问专家通道角色 | GET `/api/drama/projects/{id}/progress/` fast模式 | 只返回8个角色，专家通道角色不在列表 | P0 |
| FT-C02 | 两种通道项目并存 | 同时创建fast和expert两个项目 | 各自独立，进度互不影响 | P1 |

---

## 三、专家通道（Expert Track）各角色测试

### 3.1 角色输入输出契约测试（35个角色）

**每个角色的标准测试用例结构（3用例/角色 = 105个）：**

| 用例类型 | 测试目标 | 优先级 |
|---------|---------|--------|
| 正常执行 | 输入合法产物，验证输出schema正确 | P0 |
| 缺少必需产物 | 缺少 required_artifacts，验证返回错误 | P0 |
| 输出schema合规 | 验证output_contract中声明的产物都存在 | P1 |

#### 战略选题部（5个角色）

| 角色ID | 必需输入 | 主要输出 | 关键验证点 |
|--------|---------|---------|-----------|
| `drama.market-radar` | platform, genre_hint | market_analysis | 含题材热度评级、竞品分析、平台口味 |
| `drama.formula-analyst` | market_analysis | formula_analysis | 含梦境三指标预估、付费卡点框架 |
| `drama.topic-director` | core_idea, genre, episode_count | project_brief | 含卖点×3、受众画像、梦境预估 |
| `drama.project-reviewer` | project_brief | project_review | 含三维评分（市场/创作/合规各30/40/30分） |
| `drama.lapian-analyst` | drama_content | lapian_report | 含6维度分析结果、可复用模板 |

**选题部专项用例：**

| ID | 用例 | 验证点 | 优先级 |
|----|------|--------|--------|
| ST-001 | 立项复审否决流程 | 合规高风险→自动否决，不进入下一阶段 | P0 |
| ST-002 | 市场雷达各平台差异 | 抖音/快手/微信三平台偏好分析不同 | P1 |
| ST-003 | 爆款公式梦境指标预估 | 安全感/满足感/真实感三项输出范围0-10 | P0 |
| ST-004 | 拉片分析新模式发现 | 发现不在库中的模式时，触发新模式提案 | P1 |

#### 世界构建部（3个角色）

| 角色ID | 必需输入 | 主要输出 | 关键验证点 |
|--------|---------|---------|-----------|
| `drama.character-relations` | project_brief | character_bible | 含settingSummary/rootRules(≤3)/coreNouns/dreamIndicators |
| `drama.character-relations` | project_brief, character_bible | character_bible | 含Want/Need/Ghost/Lie/Flaw，主角≤2，配角2-4，总≤6 |
| `drama.dream-analyst` | character_bible, character_bible | dream_check | 含三指标评分，安全感<7时触发熔断 |

**世界构建部专项用例：**

| ID | 用例 | 验证点 | 优先级 |
|----|------|--------|--------|
| WB-001 | 梦境指标师熔断触发 | 安全感评分=6（<7），触发熔断，返回工程阻断信号 | P0 |
| WB-002 | 角色数量上限验证 | 创建>6个需记忆关系的角色时，quality-reporter扣分 | P1 |
| WB-003 | 世界观规则数量约束 | rootRules>3条时，world-architect质量降级 | P1 |
| WB-004 | 音色标签完整性 | character_bible中每个角色都有音色标签 | P2 |

#### 剧情引擎部（7个角色）

| 角色ID | 必需输入 | 主要输出 | 关键验证点 |
|--------|---------|---------|-----------|
| `drama.emotion-architect` | project_brief, character_bible | emotion_blueprint | 含8节点情绪图，每节点有情绪值(1-10)和外化方式 |
| `drama.series-architect` | project_brief, character_bible, character_bible | series_outline | 含六阶段+每集四段式+EV/ET/TP标注+双轨节奏 |
| `drama.hook-designer` | series_outline | hook_plan | 含S/A/B/C四级钩子，至少1个S级，集末钩子≥90%集 |
| `drama.conflict-engine` | series_outline | conflict_plan | 含四级冲突体系，无连续同质冲突 |
| `drama.reversal-master` | series_outline | reversal_plan | 含5类反转，S级在55-75%处，反转多样性达标 |
| `drama.rhythm-designer` | series_outline | emotion_curve | 含EV/ET/TP全集标注，疲软区间识别 |
| `drama.psychology-architect` | character_bible, series_outline | psychology_guide | 含认知缺口/预期管理/情绪共鸣三机制 |

**剧情引擎部专项用例：**

| ID | 用例 | 验证点 | 优先级 |
|----|------|--------|--------|
| PE-001 | 情绪曲线中段疲软检测 | rhythm-designer识别连续3+集EV<6区间 | P0 |
| PE-002 | S级钩子时机验证 | reversal-master的S级反转在55-75%集数范围内 | P0 |
| PE-003 | 大纲时间预算 | plot-architect各阶段比例之和=100% | P0 |
| PE-004 | 双轨节奏标注完整性 | rhythm-designer每集都有情节/情感节奏标注 | P1 |
| PE-005 | 钩子密度验证 | hook-designer前10集每集≥1个B级以上钩子 | P0 |
| PE-006 | 心理框架与角色弧光一致 | psychology-architect输出与character_bible弧光对应 | P1 |
| PE-007 | 冲突不重复质量门 | conflict-engine无连续2集同类型+同烈度冲突 | P1 |

#### 创作执行部（4个角色）

| 角色ID | 必需输入 | 主要输出 | 关键验证点 |
|--------|---------|---------|-----------|
| `drama.script-writer` | series_outline, character_bible, character_bible | episode_scripts | 商业剧本格式，无引号台词，无括号暗示，无心理描写 |
| `drama.dialogue-expert` | episode_scripts | episode_scripts | AI腔5大指标全部通过，角色语言有差异化 |
| `drama.scene-director` | episode_scripts | visual_prompts | 竖屏9:16 Prompt规范，景别/情绪对应正确 |
| `drama.ip-adapter` | mode+source_content | adaptation_plan+project_brief | 三模式独立测试（adapt/reference/derivative）|

**创作执行部专项用例：**

| ID | 用例 | 验证点 | 优先级 |
|----|------|--------|--------|
| EW-001 | 剧本格式强制合规 | script-writer输出无方括号场景头、无台词引号 | P0 |
| EW-002 | AI腔检测覆盖率 | dialogue-expert修复后5大AI腔指标全部通过 | P0 |
| EW-003 | 竖屏约束验证 | scene-director所有Prompt含"竖屏9:16" | P1 |
| EW-004 | IP改编原创度 | ip-adapter reference模式原创度>90% | P0 |
| EW-005 | 衍生续集OOC防护 | ip-adapter derivative模式角色性格一致性检查 | P0 |
| EW-006 | 小说改编集数压缩 | ip-adapter adapt模式，100万字→30集大纲 | P1 |
| EW-007 | 记忆检查点生成 | script-writer每集完成后自动附带记忆检查点 | P1 |

#### 评审质控部（4个角色）

| 角色ID | 必需输入 | 主要输出 | 关键验证点 |
|--------|---------|---------|-----------|
| `drama.script-scorer` | episode_scripts | review_report | 格式/结构/逻辑三维检查，McKee价值转变验证 |
| `drama.reader-reviewer` | episode_scripts, project_brief | reader_review | 追剧意愿/弃剧风险/付费转化三维评估 |
| `drama.emotion-auditor` | episode_scripts | emotion_audit | 实际EV/ET/TP与蓝图对比，疲软区间报告 |
| `drama.script-scorer` | episode_scripts, review_report | quality_report | 10维度综合评分，verdict字段，defects列表 |

**评审质控部专项用例：**

| ID | 用例 | 验证点 | 优先级 |
|----|------|--------|--------|
| QR-001 | 10维评分权重之和=100% | format×15+structure×20+...+commercial×5=100 | P0 |
| QR-002 | 熔断条件触发 | 格式<70或梦境安全感<7→verdict=重大返工 | P0 |
| QR-003 | McKee无效场景检测 | script-reviewer识别场景前后价值无变化 | P0 |
| QR-004 | 读者视角弃剧风险 | reader-reviewer识别连续2集情绪平台为弃剧风险 | P1 |
| QR-005 | 情绪审计偏差报告 | emotion-auditor对比蓝图，偏差>2分标红 | P0 |
| QR-006 | 质量报告数值范围 | 所有维度分值0-100，overall_score=加权平均 | P0 |
| QR-007 | 缺陷列表格式 | defects每项含dimension/location/severity/suggestion | P1 |

#### 修改润色部（5个角色）

| 角色ID | 必需输入 | 主要输出 | 关键验证点 |
|--------|---------|---------|-----------|
| `drama.script-editor` | episode_scripts, review_report | episode_scripts | 最小改动原则，只修复报告中缺陷 |
| `drama.pacing-optimizer` | episode_scripts | episode_scripts | 场景时长调整，不改情节 |
| `drama.formatter` | episode_scripts | episode_scripts | 格式100%合规，不改创作内容 |
| `drama.word-governor` | episode_scripts | word_count_report | 每集字数、台词占比、场景数报告 |
| `drama.style-guardian` | episode_scripts | style_check | 跨集风格漂移识别，P1/P2分级 |

**修改润色部专项用例：**

| ID | 用例 | 验证点 | 优先级 |
|----|------|--------|--------|
| PO-001 | 字数治理官首集检测 | 900<字数<1100，台词≥28%，场景≤3 | P0 |
| PO-002 | 字数治理官其余集检测 | 700<字数<900，台词≥28% | P0 |
| PO-003 | 字数偏短修复建议 | 字数<700时，给出扩写方向（不改情节） | P0 |
| PO-004 | 格式规范师零内容修改 | formatter输出内容与输入100%一致（仅格式变化） | P0 |
| PO-005 | 风格漂移首集对比 | style-guardian提取第1集指纹，与第20集对比 | P1 |
| PO-006 | 节奏优化师不改情节 | pacing-optimizer前后情节事件完全一致 | P0 |
| PO-007 | 修稿最小改动验证 | script-editor只修改review_report中标注的defect_id | P0 |

#### 制作宣发部（4个角色）

| 角色ID | 必需输入 | 主要输出 | 关键验证点 |
|--------|---------|---------|-----------|
| `drama.visual-producer` | episode_scripts, character_bible | visual_pack | 角色锚点卡片，场景Prompt含"竖屏9:16" |
| `drama.storyboard-director` | episode_scripts | storyboard | 九列格式完整，每镜有叙事目的 |
| `drama.post-processor` | episode_scripts | post_assets | 配音情绪脚本，字幕规范，时长适配 |
| `drama.marketing-officer` | episode_scripts, project_brief | marketing_kit | 3-5个剧名方案，投流标题冲突/反转优先 |

**制作宣发部专项用例：**

| ID | 用例 | 验证点 | 优先级 |
|----|------|--------|--------|
| PR-001 | 九列分镜表完整性 | 每列（镜号/时长/角度/景别/内容/场景/声音/备注/叙事目的）均不为空 | P0 |
| PR-002 | 角色视觉锚点一致性 | visual_pack中同一角色的锚点描述在各场景中一致 | P1 |
| PR-003 | 投流切片优先级 | marketing-officer优先选冲突爆发/打脸反转场景 | P0 |
| PR-004 | 配音情绪三峰值 | post-processor在15s/35s/55s处标注峰值情绪≥8级 | P1 |
| PR-005 | 字幕平台差异化 | 抖音≤12字/快手≤14字/微信≤15字 | P1 |

#### 合规总编室（3个角色）

| 角色ID | 必需输入 | 主要输出 | 关键验证点 |
|--------|---------|---------|-----------|
| `drama.compliance-guard` | episode_scripts | compliance_report | P0熔断/P1强制/P2建议三级检测，犯罪正义收束验证 |
| `drama.delivery-packer` | 所有前序产物 | delivery_pack | 四项验证通过，生成《剧名》交付包.md |
| `drama.evolution-analyst` | quality_report | evolution_proposal | 双轨进化（技能+灵感归档）输出 |

**合规总编室专项用例：**

| ID | 用例 | 验证点 | 优先级 |
|----|------|--------|--------|
| CO-001 | P0熔断词触发 | "拐卖"/"未成年犯罪"词出现→overall_result=不通过 | P0 |
| CO-002 | 犯罪正义收束验证 | 犯罪词≥2处→须有正义词≥2处，否则P1 | P0 |
| CO-003 | 交付打包四项验证 | character_bible/character_bible/series_outline/episode_scripts全部存在 | P0 |
| CO-004 | 交付包字数达标 | delivery-packer检测字数未达标→delivery_status=pending（不生成包）| P0 |
| CO-005 | 进化分析双轨 | evolution-analyst在low_quality时触发技能规则提案，创作亮点触发灵感归档 | P1 |
| CO-006 | 合规通过后才能打包 | compliance_report=不通过时，delivery-packer拒绝执行 | P0 |

---

## 四、API 接口测试矩阵（`/api/drama/`）

### 4.1 项目管理接口

| 接口 | 方法 | 正常用例 | 异常用例 | 权限 | 优先级 |
|------|------|---------|---------|------|--------|
| `/api/drama/projects/` | POST | 创建fast/expert两种通道项目 | 缺少title/无效track_mode/total_episodes越界 | 需登录 | P0 |
| `/api/drama/projects/` | GET | 返回当前用户项目列表 | 越权访问他人项目 | 需登录 | P0 |
| `/api/drama/projects/{id}/` | GET | 返回项目详情 | 不存在ID/他人ID | 需登录 | P0 |
| `/api/drama/projects/{id}/progress/` | GET | 返回进度+角色列表 | fast模式只返回8角色 | 需登录 | P0 |
| `/api/drama/projects/{id}/run/{role}/` | POST | 触发角色执行 | 无效role_id/项目不存在 | 需登录 | P0 |

**接口详细用例：**

| ID | 接口 | 输入 | 预期 | 优先级 |
|----|------|------|------|--------|
| API-001 | POST /projects/ | 合法数据 | 201，id/project_id/track_mode/completed_roles=[] | P0 |
| API-002 | POST /projects/ | 无title | 400，title字段错误信息 | P0 |
| API-003 | POST /projects/ | track_mode=invalid | 400，枚举校验错误 | P0 |
| API-004 | POST /projects/ | total_episodes=201 | 400，最大值200越界 | P1 |
| API-005 | POST /projects/ | total_episodes=4 | 400，最小值5越界 | P1 |
| API-006 | GET /projects/{id}/ | 他人项目ID | 404（非403，不暴露存在性）| P0 |
| API-007 | GET /progress/ | fast模式项目 | roles数组长度=8 | P0 |
| API-008 | GET /progress/ | expert模式项目 | roles数组长度=35 | P0 |
| API-009 | POST /run/{role}/ | 无效role_id | 404，角色不存在 | P0 |
| API-010 | POST /run/{role}/ | 未登录 | 401，需要认证 | P0 |

### 4.2 角色列表接口

| ID | 接口 | 输入 | 预期 | 优先级 |
|----|------|------|------|--------|
| API-011 | GET /roles/ | 无参数 | 8个部门，每部门角色数正确，总计35个 | P0 |
| API-012 | GET /roles/ | 未登录 | 401 | P0 |
| API-013 | GET /roles/ | 响应结构 | 每角色含is_fast_track/current_model/input_contract/output_contract | P0 |
| API-014 | GET /roles/ | 快速通道标记 | 8个is_fast_track=true角色正确 | P0 |

### 4.3 字数验证接口

| ID | 接口 | 输入 | 预期 | 优先级 |
|----|------|------|------|--------|
| API-015 | POST /validate/word-count/ | 首集900字内容 | overall=通过，无recommendations | P0 |
| API-016 | POST /validate/word-count/ | 首集800字内容 | overall=不通过，偏短-100字 | P0 |
| API-017 | POST /validate/word-count/ | 首集1200字内容 | overall=不通过，偏长+100字 | P0 |
| API-018 | POST /validate/word-count/ | 台词占比20%内容 | dialogue_ratio.status=台词不足 | P0 |
| API-019 | POST /validate/word-count/ | 4个场景的内容 | scene_count.status=场景过多 | P1 |
| API-020 | POST /validate/word-count/ | 非第1集episode_number=5 | target_range=[700,900] | P0 |
| API-021 | POST /validate/word-count/ | 含AI提示词块 | 清洗后字数不含提示词 | P0 |
| API-022 | POST /validate/word-count/ | 空content | 400，content必填 | P0 |

### 4.4 质量雷达接口

| ID | 接口 | 预期 | 优先级 |
|----|------|------|--------|
| API-023 | GET /projects/{id}/quality-radar/ | 8个维度，含score/weight/dimension | P0 |
| API-024 | GET /projects/{id}/quality-radar/ | overall_score=加权计算值 | P0 |
| API-025 | GET /projects/{id}/quality-radar/ | grade计算：≥90=S/≥80=A/≥75=B/≥60=C/<60=D | P0 |
| API-026 | GET /projects/{id}/quality-radar/ | 无评分时所有score=0 | P1 |

### 4.5 Token统计接口

| ID | 接口 | 预期 | 优先级 |
|----|------|------|--------|
| API-027 | GET /stats/token/?days=30 | totals含total_tokens/total_cost_yuan/total_calls | P1 |
| API-028 | GET /stats/token/?days=7 | by_day数组长度≤7 | P1 |
| API-029 | GET /stats/token/?user_only=true | 只返回当前用户数据 | P0 |
| API-030 | GET /stats/token/ | 未登录→401 | P0 |

### 4.6 模型配置接口（Admin）

| ID | 接口 | 预期 | 优先级 |
|----|------|------|--------|
| API-031 | GET /models/config/ | 返回35个角色的模型配置 | P0 |
| API-032 | PUT /models/config/ | 非管理员→403 | P0 |
| API-033 | PUT /models/config/ | 管理员更新某角色provider → 下次执行使用新provider | P0 |
| API-034 | PUT /models/config/ | 无效provider_id→404 | P1 |

---

## 五、前端页面测试

### 5.1 创作中心首页（`/drama`）

| ID | 用例 | 步骤 | 预期 | 优先级 |
|----|------|------|------|--------|
| UI-001 | 首页正常加载 | 访问/drama（已登录）| 显示双轨模式说明，项目列表加载 | P0 |
| UI-002 | 未登录重定向 | 未登录访问/drama | 跳转到/login | P0 |
| UI-003 | 新建项目弹窗 | 点击"新建剧本项目" | 弹窗打开，9个表单字段正确 | P0 |
| UI-004 | 新建项目成功 | 填写合法数据提交 | 关闭弹窗，跳转到工作台 | P0 |
| UI-005 | 项目卡片信息 | 查看已有项目 | 显示剧名/集数/平台/完成度/通道类型/交付状态 | P1 |
| UI-006 | 完成度进度条 | completed_roles=4（fast模式）| 进度条=50% | P0 |
| UI-007 | 空态展示 | 无项目时 | 显示空态图标和引导文案 | P1 |
| UI-008 | 旧/creation路由重定向 | 访问/creation | 自动跳转到/drama | P0 |

### 5.2 项目工作台（`/drama/workspace/:id`）

| ID | 用例 | 步骤 | 预期 | 优先级 |
|----|------|------|------|--------|
| UI-009 | 工作台正常加载 | 进入fast模式项目 | 左侧显示8个角色，右侧为角色详情区 | P0 |
| UI-010 | 专家通道角色显示 | 进入expert模式项目 | 左侧显示35个角色，按8个部门分组 | P0 |
| UI-011 | 快速通道过滤 | 点击"只看快速通道" | 只显示8个角色 | P1 |
| UI-012 | 角色选中状态 | 点击某角色 | 右侧显示详情，左侧选中高亮 | P0 |
| UI-013 | 已完成角色标记 | completed_roles包含某角色 | ✅图标，绿色背景 | P0 |
| UI-014 | 执行角色按钮 | 选中角色后点击"执行角色" | 显示加载态，轮询进度 | P0 |
| UI-015 | 角色依赖展示 | 查看plot-architect | 输入依赖显示project_brief/character_bible/character_bible（红色必需，灰色可选）| P1 |
| UI-016 | 输出产物展示 | 角色执行成功 | 输出区显示产物键列表 | P1 |
| UI-017 | 进度条实时更新 | 执行过程中 | 顶部进度条百分比递增 | P1 |
| UI-018 | 模型配置链接 | 点击"配置模型" | 跳转到/admin/drama-models | P1 |
| UI-019 | 查看剧本按钮 | 左下角点击 | 跳转到/drama/scripts/:id | P0 |
| UI-020 | 当前模型显示 | 角色详情面板 | 显示"Provider名/模型名"或"未配置" | P2 |

### 5.3 剧本展示页（`/drama/scripts/:id`）

| ID | 用例 | 步骤 | 预期 | 优先级 |
|----|------|------|------|--------|
| UI-021 | 剧本展示正常加载 | 访问/drama/scripts/:id | 左侧集数列表，右侧剧本内容 | P0 |
| UI-022 | 集数列表完整 | 30集项目 | 左侧显示30个集数按钮 | P0 |
| UI-023 | 字数徽章显示 | 有word_count_stats | 每集显示"Xw字 ✅/❌"徽章 | P1 |
| UI-024 | 集数切换 | 点击不同集数 | 右侧内容切换，无闪烁 | P0 |
| UI-025 | 8维雷达图 | 有quality_scores | 雷达图正确渲染，8个维度 | P0 |
| UI-026 | 雷达图评级显示 | overall_score=82 | 显示"A级·82分" | P0 |
| UI-027 | 无剧本时空态 | episode_scripts未生成 | 显示空态提示 | P1 |
| UI-028 | 剧本内容格式 | 有剧本内容 | 保留等宽字体，场景头/台词/△格式正确 | P1 |
| UI-029 | 交付状态四项检验 | 查看交付状态区域 | 剧本完整性/审稿/合规/字数四项各有✅或○ | P0 |
| UI-030 | 综合评分标题栏 | 有quality_scores.grade | 顶部显示评级徽章 | P1 |

### 5.4 模型配置Admin（`/admin/drama-models`）

| ID | 用例 | 步骤 | 预期 | 优先级 |
|----|------|------|------|--------|
| UI-031 | 模型配置加载 | 管理员访问 | 显示35个角色按8部门分组 | P0 |
| UI-032 | 非管理员访问 | 普通用户访问 | 重定向到403或首页 | P0 |
| UI-033 | 切换模型 | 点击修改→选择Provider | 表单展开，选择后保存成功 | P0 |
| UI-034 | Token统计Tab | 点击"Token统计" | 切换到统计面板 | P1 |
| UI-035 | Token总量显示 | 有执行记录 | 显示总Token/总费用/总调用次数 | P1 |
| UI-036 | 按角色Token排行 | 有多个角色数据 | 按total_tokens降序排列Top 20 | P1 |

---

## 六、安全专项测试

### 6.1 权限与越权

| ID | 测试场景 | 方法 | 预期结果 | 优先级 |
|----|---------|------|---------|--------|
| SEC-001 | 水平越权：访问他人项目 | GET `/api/drama/projects/{他人id}/` | 404，不暴露存在性 | P0 |
| SEC-002 | 水平越权：执行他人项目角色 | POST `/api/drama/projects/{他人id}/run/drama.topic-director/` | 404 | P0 |
| SEC-003 | 未认证访问所有drama接口 | 无Token请求 | 401 | P0 |
| SEC-004 | 非管理员修改模型配置 | 普通用户 PUT `/api/drama/models/config/` | 403 | P0 |
| SEC-005 | JWT过期后重试 | Token过期后发请求 | 401，前端自动跳转登录 | P0 |
| SEC-006 | 垂直越权：普通用户访问管理员接口 | GET `/api/drama/stats/token/?user_only=false` | 只返回本人数据 | P0 |

### 6.2 输入安全

| ID | 测试场景 | 输入 | 预期结果 | 优先级 |
|----|---------|------|---------|--------|
| SEC-007 | XSS注入title | `<script>alert(1)</script>` | 存储时转义，展示时不执行 | P0 |
| SEC-008 | SQL注入参数 | `' OR 1=1--` in title | ORM参数化，无SQL错误 | P0 |
| SEC-009 | 超长字段 | title=5000字符 | 400，max_length校验 | P1 |
| SEC-010 | 恶意episode_number | episode_number=-1 | 400，min_value校验 | P1 |
| SEC-011 | 路径穿越 | project_id=../../etc/passwd | 404或UUID校验失败 | P0 |
| SEC-012 | 敏感字段不泄露 | API响应体 | 不含api_key/password/secret | P0 |

### 6.3 合规安全

| ID | 测试场景 | 输入 | 预期结果 | 优先级 |
|----|---------|------|---------|--------|
| SEC-013 | P0熔断词检测 | content包含"拐卖儿童" | compliance_report.overall_result=不通过，blocking_issues非空 | P0 |
| SEC-014 | 犯罪无收束检测 | content有5处犯罪词，无正义词 | P1级风险，建议修改 | P0 |
| SEC-015 | 恐怖内容P0 | content包含"活体解剖" | 直接熔断 | P0 |

---

## 七、性能基线测试

| ID | 测试场景 | 目标 | 优先级 |
|----|---------|------|--------|
| PERF-001 | GET /roles/ 响应时间 | <200ms（无LLM调用）| P1 |
| PERF-002 | POST /validate/word-count/ | <100ms（纯计算）| P1 |
| PERF-003 | GET /projects/{id}/progress/ | <300ms（DB查询）| P1 |
| PERF-004 | 10个并发项目创建 | 无数据丢失，所有请求200/201 | P1 |
| PERF-005 | 前端工作台加载 | 首屏<3s（含API）| P2 |
| PERF-006 | 雷达图渲染 | 纯CSS绘制，<100ms | P2 |

---

## 八、回归测试矩阵

### 8.1 改动点 → 影响面映射

| 改动模块 | 影响范围 | 回归用例范围 |
|---------|---------|------------|
| drama/defaults.py（角色定义）| 所有角色API | 全部角色接口测试 |
| drama/models.py | DramaProject CRUD | API-001~API-010 |
| drama/services.py（字数）| validate/word-count | API-015~API-022 |
| agent/binding.py（移除compat）| 所有依赖binding的执行路径 | 全角色执行测试 |
| agent/runtime.py | 工作台角色列表 | UI-009~UI-020 |
| stream_service.py | 流式生成 | 角色流式执行测试 |
| 前端router（/creation→/drama）| 旧路由重定向 | UI-008 |

### 8.2 清理向后兼容代码回归

由于本次大规模删除兼容代码，以下P0回归必跑：

| ID | 回归场景 | 验证点 |
|----|---------|--------|
| REG-001 | 角色列表API正常返回 | 无FusionNodeRegistry报错 |
| REG-002 | 字数治理官工作正常 | 纯计算逻辑，无workflow依赖 |
| REG-003 | 创作Catalog正常加载 | ssot_catalog→creation_catalog替换正确 |
| REG-004 | 模型路由正常解析 | drama.* agent_id直接查路由表 |
| REG-005 | billing计费正常 | drama.agent.*格式action_key正确 |
| REG-006 | 进化分析师正常执行 | 双轨进化输出正常 |
| REG-007 | 合规守卫P0检测 | 无workflow.fusion依赖后检测仍准确 |

---

## 九、上线准入检查清单

### P0 门禁（全部通过才能上线）

- [ ] 快速通道8角色端到端流程通过（FT-001~FT-008）
- [ ] 合规守卫P0熔断词检测通过（CO-001/SEC-013~015）
- [ ] 字数治理官首集+非首集检测通过（PO-001~002）
- [ ] 质量报告10维评分权重正确（QR-001）
- [ ] 交付打包四项验证通过（CO-003/CO-004）
- [ ] 水平越权防护通过（SEC-001/002）
- [ ] 未认证访问返回401（SEC-003）
- [ ] API关键字段校验（API-002~005/API-008/API-010）
- [ ] seed_drama_skills命令成功种入35个角色
- [ ] CI通过（backend tests + frontend tests）
- [ ] Django migrations无冲突

### P1 门禁（允许带小问题上线，需记录）

- [ ] 所有35个角色输入输出契约正确
- [ ] 前端工作台双轨模式切换正常
- [ ] 雷达图8维度正确渲染
- [ ] Token统计数据准确
- [ ] 管理员模型配置保存后生效

---

## 十、缺陷记录模板

```markdown
【缺陷ID】BUG-YYYYMMDD-NNN
【标题】[模块/角色] 简洁描述
【严重等级】P0致命 / P1严重 / P2一般 / P3轻微
【复现步骤】
1. 
2. 
3. 
【实际结果】
【预期结果】
【影响范围】哪些角色/接口/页面受影响
【修复建议】
【附件】截图/接口响应/日志
```

---

## 十一、自动化测试代码覆盖计划

> 需结合 `fullstack-unit-test` 技能实现，以下为优先级排序

| 优先级 | 测试对象 | 覆盖场景 |
|--------|---------|---------|
| P0 | `DramaWordCountService.validate_episode()` | 首集/非首集/台词占比/场景数 |
| P0 | `DramaProject.get_completion_rate()` | fast/expert两种模式 |
| P0 | `drama/views.py` 所有接口 | 正常/权限/边界 |
| P0 | `agent_billing.charge_agent_run()` | 幂等/退款 |
| P1 | `seed_drama_skills` 管理命令 | 35个角色种入后验证 |
| P1 | `tier1_sections` 区块映射 | 35个角色都有映射 |
| P2 | 前端 `Drama/index.jsx` | 新建项目表单验证 |
| P2 | 前端 `WorkspacePage.jsx` | 角色执行状态变化 |
