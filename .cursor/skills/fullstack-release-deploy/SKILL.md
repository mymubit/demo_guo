---
name: fullstack-release-deploy
description: 为 Django+DRF 与 React 前后端分离项目制定发布上线、Docker 部署、数据库迁移、环境配置与回滚方案。适用于用户提出上线发布、生产部署、docker-compose 配置、迁移执行、环境变量梳理、灰度发布或发布回滚时使用。
---

# Fullstack Release Deploy

## 项目基础信息

- 前后端分离 Web 网站（ScriptForge / flickplay）
- 后端：Django + Django REST Framework
- 前端：React + Vite/Webpack 构建产物
- 部署：Docker Compose（`docker-compose.yml`、`docker-compose.prod.yml`）
- 规范对齐：`.cursor/rules/security-testing-standards.mdc`、`project-core-standards.mdc`

## 适用场景

当用户提出以下需求时使用本技能：

- 制定版本上线发布流程与检查项
- 配置或排查 Docker / docker-compose 部署
- 执行或规划 Django 数据库迁移（含回滚策略）
- 梳理生产环境变量与配置安全
- 灰度发布、滚动更新或紧急回滚方案

与其他技能分工：

- **本技能**：发布、部署、迁移、环境、回滚落地
- [fullstack-testing](../fullstack-testing/SKILL.md)：功能回归与上线准入测试清单
- [fullstack-security-audit](../fullstack-security-audit/SKILL.md)：发布前安全审计
- [fullstack-monitoring-system](../fullstack-monitoring-system/SKILL.md)：发布后监控与告警接入
- [dynamic-system-config](../dynamic-system-config/SKILL.md)：配置中心灰度与缓存刷新

## 工作原则

1. **先读再改**：必须读取现有 `docker-compose*.yml`、Dockerfile、`.env.example`、部署文档
2. 生产环境 `DEBUG=False`；密钥、DB、Redis、对象存储、支付参数**仅**环境变量
3. 数据库迁移：先备份 → 预发验证 → 生产执行 → 保留回滚迁移或快照
4. 前后端发布顺序：先后端（含迁移）→ 前端静态资源；或兼容窗口内可并行
5. 接口契约变更须前后端版本对齐，避免「新前端 + 旧后端」或反之
6. 发布清单与 [fullstack-testing 上线准入](../fullstack-testing/REFERENCE.md#上线准入清单) 联动
7. 输出默认中文；命令、路径、变量名保持英文

## 工作流程

```
1. 确认发布范围 → 版本号、改动模块、是否含迁移/配置变更
2. 读取部署资产 → compose、Dockerfile、nginx、env 模板、CI 脚本
3. 制定发布计划 → 顺序、停机窗口、回滚点、验证步骤
4. 输出检查清单 → 环境、迁移、构建、健康检查、监控
5. 发布后验证 → 冒烟 + 监控 + 日志抽查
```

## 发布阶段速查

| 阶段 | 关键动作 |
|------|----------|
| 发布前 | 准入测试、安全审计、迁移预演、备份 |
| 构建 | 前端 build、后端镜像、依赖锁定 |
| 部署 | compose up、迁移 migrate、静态资源同步 |
| 发布后 | 冒烟、监控告警、错误率观察 |
| 回滚 | 镜像回退、迁移反向、前端版本回退 |

## 输出要求

### 用户要「发布方案」时

1. 版本与改动摘要
2. 环境变量清单（区分必填/可选/敏感）
3. 发布顺序与时间表
4. 迁移步骤与回滚策略
5. Docker/compose 调整说明（如有）
6. 发布后验证清单（链接 testing 准入项）
7. 回滚 playbook（逐步命令）

### 用户要「直接执行部署」时

1. 先输出简要风险与回滚点
2. 逐步执行并记录每步结果
3. 失败时立即停止并给回滚建议

## 分析前置步骤

动手前优先读取（若项目存在）：

1. `docker-compose.yml`、`docker-compose.prod.yml`
2. `backend/` 或 Django 项目根：`settings/`、`manage.py`、`requirements*.txt`
3. `frontend/`：`package.json`、构建脚本、`vite.config.*`
4. `.env.example`、部署文档、nginx 配置
5. 最近未执行迁移：`python manage.py showmigrations`

## 详细参考

- 发布清单模板、env 模板、回滚 playbook：[REFERENCE.md](REFERENCE.md)
