### Task 1: 鏈琛ㄤ笌鍛戒护瀛楀吀

**Files:**
- Create: `docs/contracts/v3/glossary.md`
- Create: `docs/contracts/v3/commands.md`

**Interfaces:**
- Consumes: Spec 搂2銆伮?
- Produces: 绋冲畾 `command_type` 鏋氫妇涓庝腑鏂囧睍绀哄悕鏄犲皠锛屼緵 OpenAPI/`commands.ts` 寮曠敤

- [ ] **Step 1: 鍐欐湳璇〃**

鍒涘缓 `docs/contracts/v3/glossary.md`锛岃嚦灏戝寘鍚細

| 鐢ㄦ埛鍙 | 鍐呴儴绋冲畾 ID | 绂佹瀵圭敤鎴疯 |
|----------|-------------|--------------|
| 閫夐瀹氳皟 / 椤圭洰绠€鎶?| `project_brief` | `create-project-brief`銆乣operation.*` |
| 鏁呬簨钃濆浘 | `story_bible` | `compose-story-bible` |
| 鍒嗛泦瑙勫垝 | `episode_plan` | `design-episode-plan` |
| 鍓ф湰姝ｆ枃 | `episode_scripts` | `write-episodes` |
| 璐ㄩ噺鎶ュ憡 | `quality_report` | `score-script` |
| 鍚堣鎶ュ憡 | `compliance_report` | `check-compliance` |
| 鍒朵綔浜や粯鍖?| `production_package` | `prepare-delivery` |
| 杩愯 / 鎵ц鏃ュ織 | `command_run` | `OperationRun`锛堝澶栵級 |

- [ ] **Step 2: 鍐欏懡浠ゅ瓧鍏?*

鍒涘缓 `docs/contracts/v3/commands.md`锛?

```markdown
# V3 浜у搧鍛戒护瀛楀吀

| command_type | 涓枃鍚?| 妯″潡 | 寮傛 | 闇€纭鍊欓€?|
|--------------|--------|------|------|------------|
| create_project | 鍒涘缓椤圭洰 | 椤圭洰 | 鍚?| 鍚?|
| generate_topic_brief | 鐢熸垚閫夐绠€鎶?| 閫夐 | 鏄?| 鏄?|
| confirm_topic_brief | 纭閫夐绠€鎶?| 閫夐 | 鍚?| 鍚?|
| generate_blueprint | 鐢熸垚鏁呬簨钃濆浘 | 钃濆浘 | 鏄?| 鏄?|
| confirm_blueprint | 纭鏁呬簨钃濆浘 | 钃濆浘 | 鍚?| 鍚?|
| generate_episode_plan | 鐢熸垚鍒嗛泦瑙勫垝 | 鍒嗛泦 | 鏄?| 鏄?|
| revise_episode_plan | 灞€閮ㄤ慨璁㈠垎闆?| 鍒嗛泦 | 鏄?| 鏄?|
| write_episode_batch | 鍒嗘壒鍐欐鏂?| 姝ｆ枃 | 鏄?| 鏄?|
| confirm_script_candidate | 纭姝ｆ枃鍊欓€?| 姝ｆ枃 | 鍚?| 鍚?|
| score_quality | 璐ㄩ噺璇勫垎 | 璐ㄦ | 鏄?| 鍚?|
| check_compliance | 鍚堣瀹℃煡 | 璐ㄦ | 鏄?| 鍚?|
| accept_findings | 鎺ュ彈璐ㄦ闂 | 璐ㄦ | 鍚?| 鍚?|
| revise_from_findings | 鎸夐棶棰樹慨璁?| 璐ㄦ | 鏄?| 鏄?|
| prepare_delivery | 鐢熸垚浜や粯鍖?| 浜や粯 | 鏄?| 鍚?|
| test_model_provider | 璇曡繛妯″瀷 | 妯″瀷 | 鏄?| 鍚?|
```

璇存槑锛氬唴閮?skills 閰嶆柟 ID锛堝 `operation.create-project-brief`锛夊彧鍐欏湪缂栨帓鍣ㄦ槧灏勮〃锛屼笉杩涙湰琛ㄣ€屽鐢ㄦ埛銆嶅垪銆?

- [ ] **Step 3: 鑷**

纭琛ㄤ腑姣忎釜 `command_type` 涓?`^[a-z][a-z0-9_]*$`锛屼笖涓?Spec 搂5 鍗佹ā鍧楄鐩栨棤閬楁紡锛堝椁愭棤鍛戒护銆佺郴缁熼厤缃敤 REST 璧勬簮鑰岄潪 command锛夈€?

---


