# Review Package — W0 Task 1
Base: (no commit; working tree only)
Head: working tree

## Files
- docs/contracts/v3/glossary.md
- docs/contracts/v3/commands.md

## Diff (new files)
--- glossary ---
# V3 浜у搧鏈琛?

> 濂戠害鍐荤粨锛圵0锛夆€?鍒涗綔鑰呭彲瑙佷腑鏂囦笟鍔″悕 鈫?鍐呴儴绋冲畾 ID 鏄犲皠銆? 
> 渚?OpenAPI銆乣domain.ts`銆乣commands.ts` 鍙?UI 鏂囨寮曠敤銆?

## 浜х墿涓庤繍琛岃褰?

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

## 浣跨敤璇存槑

- **鐢ㄦ埛鍙**锛氶〉闈㈡爣棰樸€佹寜閽€乀oast銆佸府鍔╂枃妗堢瓑闈㈠悜鍒涗綔鑰呯殑涓枃涓氬姟鏈銆?
- **鍐呴儴绋冲畾 ID**锛欰PI 瀛楁銆佹暟鎹簱 artifact 绫诲瀷銆乀S 绫诲瀷鏋氫妇绛夌ǔ瀹氭爣璇嗭紝浣跨敤 snake_case銆?
- **绂佹瀵圭敤鎴疯**锛歴kills 閰嶆柟 ID銆乂6 operation 鐩綍鍚嶃€佸唴閮ㄧ被鍚嶇瓑锛涗粎鍑虹幇鍦ㄧ紪鎺掑櫒鏄犲皠琛ㄦ垨鎵ц鏃ュ織楂樼骇鎬併€?

==== commands ====
# V3 浜у搧鍛戒护瀛楀吀

> 濂戠害鍐荤粨锛圵0锛夆€?浜у搧 `command_type` 鏋氫妇涓庝腑鏂囧睍绀哄悕銆? 
> 渚?OpenAPI銆乣commands.ts` 鍙婄紪鎺掑櫒鍏ュ彛寮曠敤銆?

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

## 璇存槑

鍐呴儴 skills 閰嶆柟 ID锛堝 `operation.create-project-brief`锛夊彧鍐欏湪缂栨帓鍣ㄦ槧灏勮〃锛屼笉杩涙湰琛ㄣ€屽鐢ㄦ埛銆嶅垪銆?

### 妯″潡瑕嗙洊锛圫pec 搂5锛?

| HTML 妯″潡 | 鏈〃 command | 澶囨敞 |
|-----------|--------------|------|
| 椤圭洰绠＄悊 | `create_project` | 褰掓。/杩涘害鑱氬悎涓?REST 璇绘搷浣滐紝鏃犵嫭绔?command |
| 閫夐瀹氳皟 | `generate_topic_brief`銆乣confirm_topic_brief` | |
| 钃濆浘缂栬緫 | `generate_blueprint`銆乣confirm_blueprint` | |
| 鍒嗛泦鐢诲竷 | `generate_episode_plan`銆乣revise_episode_plan` | |
| 姝ｆ枃缂栬緫 | `write_episode_batch`銆乣confirm_script_candidate` | |
| 璐ㄦ涓績 | `score_quality`銆乣check_compliance`銆乣accept_findings`銆乣revise_from_findings` | |
| 浜や粯宸ュ叿 | `prepare_delivery` | |
| 绯荤粺閰嶇疆 | 鈥?| REST 璧勬簮锛坄/api/v3/system/`锛夛紝闈?command |
| 妯″瀷閰嶇疆 | `test_model_provider` | 渚涘簲鍟?瀵嗛挜/鏄犲皠涓?REST CRUD |
| 鎵ц鏃ュ織 | 鈥?| REST 鍙锛坄/api/v3/logs/`锛夛紝闈?command |
| 濂楅澹?| 鈥?| REST 鍙锛坄/api/v3/billing/plans/`锛夛紝鏃?command |

