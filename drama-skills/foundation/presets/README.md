# foundation/presets — 可调预设（C4）

> 与 `foundation/rules/`（铁律叙述）和 `foundation/constraints/`（方法论/硬指标 SSOT）分离。  
> 本目录文件默认 `config_tier: seed_default`，允许后台 overlay（见 `manifest/config-policy.yaml`）。

## 文件清单

| 文件 | 用途 | 迁移说明 |
|------|------|----------|
| `scoring-presets.yaml` | 评分预设权重与通过线 | 自 constraints 迁入；旧路径经 loader 别名兼容 |
| `platform-profiles.yaml` | 平台画像与 seed_checks | 同上 |
| `agent-runtime.yaml` | 角色 token/温度等运行时 | 同上 |
| `production-feasibility.yaml` | 制作复杂度标签 | 同上 |

## 仍留在 constraints/ 的原因

| 文件 | 原因 |
|------|------|
| `quality-scoring.yaml` | 十维方法论为 `git_ssot`；仅业务阈值可 overlay |
| `script-format.yaml` 等硬指标 | 与铁律强绑定 |
| `continuity-checkpoint.yaml` | 产物结构 SSOT，受保护 |

## Manifest 层名

运行时注入层规范名见 backend `injection_manifest.CANONICAL_LAYER_NAMES`（含别名映射表）。
