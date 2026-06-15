# Fullstack Release Deploy — 详细参考

## 发布前检查清单

```markdown
# [版本号] 发布前检查清单

## 代码与构建
- [ ] 目标分支已合并，CI 通过
- [ ] 前端 `npm run build` 成功
- [ ] 后端依赖锁定，镜像可构建

## 数据库
- [ ] `showmigrations` 无未应用迁移
- [ ] 迁移已在预发执行并验证
- [ ] 生产数据库已备份（快照/导出）
- [ ] 回滚方案已确认（反向迁移或恢复备份）

## 环境与安全
- [ ] `DEBUG=False`
- [ ] `SECRET_KEY`、DB、Redis 等来自环境变量
- [ ] `ALLOWED_HOSTS`、CORS 配置正确
- [ ] 无调试端点暴露

## 测试与审计
- [ ] [fullstack-testing 上线准入](../fullstack-testing/REFERENCE.md#上线准入清单) P0 通过
- [ ] 安全高危项已关闭（如有 security-audit）

## 监控
- [ ] 关键接口有监控/日志采集
- [ ] 告警接收人已确认
```

---

## 推荐发布顺序

```
1. 通知维护窗口（如需要）
2. 生产数据库备份
3. 部署后端新版本
4. python manage.py migrate --plan   # 先预览
5. python manage.py migrate          # 执行迁移
6. 健康检查：/api/health 或等价端点
7. 部署前端静态资源 / 前端容器
8. 冒烟：登录 → 核心业务流程
9. 观察 15–30 分钟：错误率、慢请求、日志
10. 发布完成通知
```

**含破坏性迁移时**：优先灰度单实例或维护窗口；准备 `migrate <app> <previous_migration>` 回退路径。

---

## 环境变量清单模板

```markdown
| 变量名 | 必填 | 敏感 | 说明 | 示例 |
|--------|------|------|------|------|
| DEBUG | 是 | 否 | 生产必须为 False | False |
| SECRET_KEY | 是 | 是 | Django 密钥 | — |
| DATABASE_URL | 是 | 是 | 数据库连接 | postgres://... |
| REDIS_URL | 否 | 是 | 缓存/队列 | redis://... |
| ALLOWED_HOSTS | 是 | 否 | 逗号分隔域名 | api.example.com |
| CORS_ALLOWED_ORIGINS | 是 | 否 | 前端域名 | https://app.example.com |
```

敏感变量禁止写入 compose 明文；使用 `.env`（不入库）或密钥管理服务。

---

## Docker Compose 检查项

- [ ] 服务依赖顺序：`depends_on` + healthcheck
- [ ] 数据卷持久化：数据库、媒体文件
- [ ] 生产 compose 与开发 compose 分离
- [ ] 镜像 tag 固定版本，生产不用 `latest`
- [ ] 资源限制（memory/cpu）如适用
- [ ] 日志驱动与轮转配置

---

## 回滚 Playbook 模板

```markdown
# [版本号] 回滚 Playbook

## 触发条件
- 核心接口错误率 > X%
- 迁移失败 / 数据异常
- P0 冒烟不通过

## 回滚步骤
1. 停止新版本流量（切换 LB / 缩容新容器）
2. 后端回滚至镜像 tag: `vX.Y.Z-1`
3. 若已执行迁移：
   - 方案 A：`python manage.py migrate <app> <prev_migration>`
   - 方案 B：从备份恢复数据库（说明 RPO/RTO）
4. 前端回滚至上一构建产物
5. 验证核心流程
6. 记录事故时间与根因

## 联系人
- 发布负责人：…
- DBA/运维：…
```

---

## 灰度发布要点

| 策略 | 适用 | 注意 |
|------|------|------|
| 金丝雀 | 后端 API 变更 | 新旧版本短暂并存需接口兼容 |
| 蓝绿 | 全量切换 | 数据库迁移须在切换前完成 |
| 功能开关 | 配置中心控制 | 配合 dynamic-system-config |

---

## 发布后冒烟清单（最小集）

- [ ] 首页/登录可访问
- [ ] 登录 → Token 有效 → 鉴权接口 200
- [ ] 核心业务一条完整链路（因项目而异：创作/订单/支付等）
- [ ] 管理后台可访问（如适用）
- [ ] 静态资源 200，无大量 404
- [ ] 监控面板有最新数据
