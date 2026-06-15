---
name: fullstack-security-audit
description: 对 Django+DRF 后端与 React+Tailwind 前端进行系统化安全审计，覆盖鉴权越权、输入校验、敏感数据、接口暴露、日志泄密与发布前安全检查。适用于用户提出安全审计、越权排查、XSS/注入风险评估、发布前安全自查或安全加固方案时使用。
---

# Fullstack Security Audit

## 项目基础信息

- 前后端分离 Web 网站
- 后端：Django + Django REST Framework
- 前端：React + TailwindCSS + clsx + tailwind-merge + lucide-react + framer-motion + sonner + echarts-for-react
- 规范对齐：`.cursor/rules/security-testing-standards.mdc`、`django-backend-standards.mdc`、`project-core-standards.mdc`

## 适用场景

当用户提出以下需求时使用本技能：

- 对页面、接口、模块进行发布前安全自查
- 排查水平/垂直越权、未授权访问、IDOR
- 评估 XSS、参数篡改、SQL 注入、敏感信息泄露风险
- 审计日志、错误响应、环境变量与生产配置安全性
- 输出安全加固建议与修复优先级

与其他技能分工：

- **本技能**：安全专项审计与加固建议，默认不直接改代码（除非用户明确要求）
- [fullstack-testing](../fullstack-testing/SKILL.md)：功能/接口测试用例，含安全基础校验场景
- [fullstack-bidirectional-review](../fullstack-bidirectional-review/SKILL.md)：代码质量评审，安全仅为维度之一
- [fullstack-release-deploy](../fullstack-release-deploy/SKILL.md)：生产发布与环境安全配置落地

## 工作原则

1. 所有外部输入、接口参数、上传内容默认**不可信**，必须核查校验与权限
2. 审计基于用户提供的代码/接口/配置，**禁止臆造**业务权限模型
3. 数据修改、删除、批量操作、金额/权益变更须标注风险等级
4. 密码仅 Django 哈希存储；禁止明文出现在日志、响应、异常中
5. 生产必须 `DEBUG=False`；密钥、DB、Redis、支付参数走环境变量
6. 每条发现须含：风险描述、攻击面、修复建议、验证用例编号（可引用 testing 技能）
7. 输出默认中文；路径、字段名、代码保持英文

## 工作流程

```
1. 确认审计范围 → 页面/接口/模块/全站；明确角色与权限模型
2. 读取上下文 → 权限类、鉴权中间件、Serializer 校验、View  queryset 过滤
3. 按维度扫描 → 鉴权、越权、输入、敏感数据、接口暴露、配置（见 REFERENCE）
4. 仅输出有证据的风险项 → 每条含等级、复现思路、修复建议
5. 汇总 → P0 阻塞项优先，加固路线图与回归验证点
```

## 审计维度速查

| # | 维度 | 要点 |
|---|------|------|
| 1 | 鉴权与会话 | Token 校验、过期、刷新、登出失效 |
| 2 | 授权与越权 | 水平 IDOR、垂直角色提升、对象级权限 |
| 3 | 输入与注入 | XSS、SQL 注入、文件上传、Mass Assignment |
| 4 | 敏感数据 | 响应脱敏、日志脱敏、错误信息、前端存储 |
| 5 | 接口暴露 | 未授权端点、调试接口、CORS、速率限制 |
| 6 | 生产配置 | DEBUG、SECRET_KEY、环境变量、HTTPS |

## 输出格式

完整模板见 [REFERENCE.md](REFERENCE.md#安全审计报告模板)。结构固定为：

1. **审计摘要**：范围、风险统计、总体结论
2. **【高危风险清单】**：须立即修复
3. **【中危风险清单】**：本迭代内修复
4. **【低危与加固建议】**
5. **验证用例映射**：对应 security 测试点
6. **发布前安全准入**：是否建议上线

## 分析前置步骤

审计前优先读取（若项目存在）：

**后端**

1. 全局权限类、认证配置、`REST_FRAMEWORK` 设置
2. 目标 View/ViewSet 的 `permission_classes`、`get_queryset`、`get_object`
3. Serializer 的 `read_only_fields`、`write_only`、字段级校验
4. 中间件、throttle、CORS、日志配置

**前端**

1. 路由权限守卫、Token 存储与刷新逻辑
2. 富文本/表单输入渲染方式（是否 `dangerouslySetInnerHTML`）
3. 错误处理是否展示原始堆栈或内部路径
4. 敏感字段是否缓存到 localStorage

## 详细参考

- 检查清单、报告模板、常见漏洞模式：[REFERENCE.md](REFERENCE.md)
