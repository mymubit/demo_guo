# Review Package Task 8 r2
BASE: e20484fb69b9104054d554c27ff53abad0895146
HEAD: 0bea66b757144e5df7be97eaf9e84ca632aa2107

## Commits


## Stat
 .superpowers/sdd/task-8-report.md                  |  56 ++++++++++++
 .../drama/tests/test_schema_prompt_contract.py     |  25 ++++++
 .../roles/drama-story-bible/fewshots.v1.yaml       |  24 +++--
 frontend/src/pages/NewProjectPage.tsx              |   4 +-
 frontend/src/pages/ProjectListPage.tsx             | 100 ++++++++++++---------
 frontend/src/pages/ProjectSettingsPage.tsx         |  75 ++++++++--------
 frontend/src/pages/create-domain.tokens.test.ts    |  14 +++
 7 files changed, 206 insertions(+), 92 deletions(-)

## Diff (task files only)
diff --git a/frontend/src/pages/NewProjectPage.tsx b/frontend/src/pages/NewProjectPage.tsx
index 40cde9b..1970d0f 100644
--- a/frontend/src/pages/NewProjectPage.tsx
+++ b/frontend/src/pages/NewProjectPage.tsx
@@ -291,15 +291,15 @@ export function NewProjectPage() {
           <p className="text-sm text-ink-muted">
             褰撳墠涓哄揩閫熷缓椤癸紱棰樻潗鐭╅樀涓庣洰鏍囧钩鍙拌鍦ㄤ笅涓€姝ャ€屽垱浣滆瀹氥€嶄腑瀹屽杽銆?           </p>
         )}
 
-        <div className="flex items-center justify-end gap-3 border-t border-slate-100 pt-4">
+        <div className="flex items-center justify-end gap-3 border-t border-border pt-4">
           <Button type="button" variant="secondary" onClick={() => navigate('/projects')}>
             鍙栨秷
           </Button>
-          <Button type="submit" loading={mutation.isPending} disabled={!canSubmit}>
+          <Button type="submit" variant="action" loading={mutation.isPending} disabled={!canSubmit}>
             鍒涘缓骞跺畬鍠勫垱浣滆瀹?           </Button>
         </div>
       </form>
     </div>
diff --git a/frontend/src/pages/ProjectListPage.tsx b/frontend/src/pages/ProjectListPage.tsx
index d750a3e..90b935e 100644
--- a/frontend/src/pages/ProjectListPage.tsx
+++ b/frontend/src/pages/ProjectListPage.tsx
@@ -58,11 +58,13 @@ export function ProjectListPage() {
         <div>
           <h1 className="text-2xl font-semibold text-ink">椤圭洰</h1>
           <p className="mt-1 text-sm text-ink-muted">绠＄悊鍘熷垱涓庢敼缂栫煭鍓ч」鐩紝浠庢渶杩戜綔鍝佸揩閫熺户缁?/p>
         </div>
         <Link to="/projects/new">
-          <Button iconLeft={<Plus className="h-4 w-4" />}>鏂板缓鍒涗綔</Button>
+          <Button variant="action" iconLeft={<Plus className="h-4 w-4" />}>
+            鏂板缓椤圭洰
+          </Button>
         </Link>
       </div>
 
       {query.isLoading ? <LoadingBlock /> : null}
       {query.isError ? (
@@ -74,70 +76,70 @@ export function ProjectListPage() {
           title="杩樻病鏈夊垱浣滈」鐩?
           description="鍏堝啓鍚嶇О涓庣伒鎰燂紝鍐嶅畬鍠勯鏉愯瀹氾紝鍗冲彲杩涘叆宸ヤ綔鍙拌窇涓婚摼銆?
           action={
             <div className="flex flex-wrap items-center justify-center gap-3">
               <Link to="/projects/new">
-                <Button iconLeft={<Plus className="h-4 w-4" />}>鏂板缓绗竴閮ㄧ煭鍓?/Button>
+                <Button variant="action" iconLeft={<Plus className="h-4 w-4" />}>
+                  鏂板缓绗竴閮ㄧ煭鍓?+                </Button>
               </Link>
               <Link
                 to="/admin/model"
-                className="text-sm text-navy-600 underline-offset-2 hover:underline"
+                className="text-sm text-action underline-offset-2 hover:underline"
               >
                 鍏堥厤缃ā鍨?鈫?               </Link>
             </div>
           }
         />
       ) : null}
 
       {query.data && query.data.length > 0 && continueProject ? (
-        <div className="space-y-6">
-          <section className="overflow-hidden rounded-xl border border-slate-200 shadow-panel">
-            <div className="flex flex-wrap items-center justify-between gap-4 bg-gradient-to-r from-navy-900 to-navy-800 px-5 py-4 text-white">
-              <div className="min-w-0">
-                <div className="text-xs font-medium tracking-wide text-slate-300">缁х画鍒涗綔</div>
-                <div className="mt-1 truncate text-lg font-semibold">
-                  {continueProject.title || '鏈懡鍚嶉」鐩?}
-                </div>
-                <div className="mt-1 text-xs text-slate-400">
-                  {entryLabel(continueProject.entry_type)}閫氶亾
-                  {continueProject.updated_at
-                    ? ` 路 鏇存柊浜?${formatRelativeTime(continueProject.updated_at)}`
-                    : null}
-                </div>
+        <div className="space-y-8">
+          <section className="sf-panel flex flex-wrap items-center justify-between gap-4 p-5">
+            <div className="min-w-0">
+              <div className="text-xs font-medium tracking-wide text-ink-muted">缁х画鍒涗綔</div>
+              <div className="mt-1 truncate text-lg font-semibold text-ink">
+                {continueProject.title || '鏈懡鍚嶉」鐩?}
               </div>
-              <div className="flex shrink-0 gap-2">
-                <Link to={`/projects/${continueProject.id}/settings`}>
-                  <Button
-                    variant="secondary"
-                    size="sm"
-                    className="border-white/20 bg-white/10 text-white hover:bg-white/15"
-                  >
-                    鍒涗綔璁惧畾
-                  </Button>
-                </Link>
-                <Link to={`/projects/${continueProject.id}/workbench`}>
-                  <Button size="sm" iconLeft={<ArrowRight className="h-3.5 w-3.5" />}>
-                    杩涘叆宸ヤ綔鍙?-                  </Button>
-                </Link>
+              <div className="mt-1 text-xs text-ink-faint">
+                {entryLabel(continueProject.entry_type)}閫氶亾
+                {continueProject.updated_at
+                  ? ` 路 鏇存柊浜?${formatRelativeTime(continueProject.updated_at)}`
+                  : null}
               </div>
             </div>
+            <div className="flex shrink-0 gap-2">
+              <Link to={`/projects/${continueProject.id}/settings`}>
+                <Button variant="secondary" size="sm">
+                  鍒涗綔璁惧畾
+                </Button>
+              </Link>
+              <Link to={`/projects/${continueProject.id}/workbench`}>
+                <Button
+                  variant="action"
+                  size="sm"
+                  iconLeft={<ArrowRight className="h-3.5 w-3.5" />}
+                >
+                  杩涘叆宸ヤ綔鍙?+                </Button>
+              </Link>
+            </div>
           </section>
 
           {recent.length > 1 ? (
             <section>
-              <h2 className="mb-3 text-sm font-semibold text-ink">鏈€杩戞墦寮€</h2>
-              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
+              <h2 className="mb-4 text-sm font-semibold text-ink">鏈€杩戞墦寮€</h2>
+              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                 {recent.map((item) => (
                   <Link
                     key={item.id}
                     to={`/projects/${item.id}/workbench`}
-                    className="sf-panel block p-4 transition hover:border-navy-300"
+                    className="sf-panel block p-4 transition hover:border-action/40"
                   >
                     <div className="flex items-start gap-3">
-                      <Clapperboard className="mt-0.5 h-4 w-4 shrink-0 text-navy-700" />
+                      <Clapperboard className="mt-0.5 h-4 w-4 shrink-0 text-action" />
                       <div className="min-w-0">
                         <div className="truncate font-medium text-ink">{item.title}</div>
                         <div className="mt-1 text-xs text-ink-muted">
                           {entryLabel(item.entry_type)} 路 {formatRelativeTime(item.visited_at)}
                         </div>
@@ -148,30 +150,38 @@ export function ProjectListPage() {
               </div>
             </section>
           ) : null}
 
           <section>
-            <h2 className="mb-3 text-sm font-semibold text-ink">鍏ㄩ儴椤圭洰</h2>
-            <ul className="divide-y divide-slate-200 overflow-hidden rounded-xl border border-slate-200 bg-white">
+            <h2 className="mb-4 text-sm font-semibold text-ink">鍏ㄩ儴椤圭洰</h2>
+            <ul className="flex flex-col gap-3">
               {projects.map((project) => (
                 <li
                   key={project.id}
-                  className="flex items-center justify-between gap-4 px-5 py-4 hover:bg-slate-50"
+                  className="sf-panel flex items-center justify-between gap-4 px-5 py-4 transition hover:border-action/30"
                 >
                   <div className="min-w-0">
                     <Link
                       to={`/projects/${project.id}/workbench`}
-                      className="text-base font-medium text-ink hover:text-brand-600"
+                      className="text-base font-medium text-ink hover:text-action"
                     >
                       {project.title || '鏈懡鍚嶉」鐩?}
                     </Link>
-                    <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-ink-muted">
-                      <Badge tone={project.entry_type === 'original_track' ? 'action' : 'gold'}>
+                    <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-ink-muted">
+                      <Badge tone={project.entry_type === 'original_track' ? 'action' : 'default'}>
                         {entryLabel(project.entry_type)}
                       </Badge>
                       {project.status ? (
-                        <Badge tone="default">
+                        <Badge
+                          tone={
+                            project.status === 'completed'
+                              ? 'success'
+                              : project.status === 'active'
+                                ? 'action'
+                                : 'default'
+                          }
+                        >
                           {STATUS_LABEL[project.status] ?? project.status}
                         </Badge>
                       ) : null}
                       {project.episode_count ? <span>{project.episode_count} 闆?/span> : null}
                       {project.updated_at ? (
@@ -188,11 +198,13 @@ export function ProjectListPage() {
                       >
                         鍒涗綔璁惧畾
                       </Button>
                     </Link>
                     <Link to={`/projects/${project.id}/workbench`}>
-                      <Button size="sm">杩涘叆宸ヤ綔鍙?/Button>
+                      <Button variant="action" size="sm">
+                        杩涘叆宸ヤ綔鍙?+                      </Button>
                     </Link>
                   </div>
                 </li>
               ))}
             </ul>
diff --git a/frontend/src/pages/ProjectSettingsPage.tsx b/frontend/src/pages/ProjectSettingsPage.tsx
index e72a96b..b0c03e0 100644
--- a/frontend/src/pages/ProjectSettingsPage.tsx
+++ b/frontend/src/pages/ProjectSettingsPage.tsx
@@ -1,10 +1,11 @@
 import { useEffect, useMemo, useState } from 'react'
 import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
 import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
 import { Button } from '@/components/ui/Button'
 import { ErrorBanner, LoadingBlock } from '@/components/ui/Tabs'
+import { PageShell } from '@/components/layout/PageShell'
 import { ThemeMatrixPicker } from '@/components/theme/ThemeMatrixPicker'
 import { useWorkbenchDefinition } from '@/hooks/useWorkbenchDefinition'
 import { dramaApi } from '@/services/drama'
 import { ApiError, formatApiError } from '@/services/errors'
 import {
@@ -17,11 +18,11 @@ import { isGenreMatrixComplete } from '@/utils/firstRunGuide'
 import { rememberRecentProject } from '@/utils/recentProjects'
 import type { AdaptNotes, GenreMatrix, ProjectSettings } from '@/types/domain'
 import type { SettingsFieldDef, ThemeMatrix } from '@/types/workbench'
 import { cn } from '@/utils/cn'
 
-/** 鍊熼壌鐏垫劅椤碉細鍒嗙粍鑱氱劍銆佷腑鏂囪鏄庛€佸噺灏戞妧鏈櫔闊筹紱瑙嗚浠嶇敤鏈珯娴呰壊鍝佺墝 */
+/** 鍊熼壌鐏垫劅椤碉細鍒嗙粍鑱氱劍銆佷腑鏂囪鏄庛€佸噺灏戞妧鏈櫔闊筹紱瑙嗚瀵归綈鍐烽浘 + action */
 
 export function ProjectSettingsPage() {
   const { projectId = '' } = useParams()
   const navigate = useNavigate()
   const [searchParams] = useSearchParams()
@@ -107,10 +108,13 @@ export function ProjectSettingsPage() {
       setActiveGroup(groups[0]?.id ?? '')
     }
   }, [groups, activeGroup, focusTheme, themeFocusApplied])
 
   const themeMatrix = definition.theme_matrix
+  const platformField = definition.fields.target_platform
+  const currentGroup = groups.find((g) => g.id === activeGroup) ?? groups[0]
+  const themeReady = isGenreMatrixComplete(draft?.genre_matrix)
 
   if (settingsQuery.isLoading) return <LoadingBlock />
   if (settingsQuery.isError) {
     return (
       <div className="p-8">
@@ -130,40 +134,42 @@ export function ProjectSettingsPage() {
   function updateField(field: SettingsFieldDef, value: unknown) {
     patch((prev) => writeSettingValue(prev, field, value))
   }
 
   return (
-    <div className="mx-auto max-w-5xl px-8 py-8">
-      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
-        <div>
-          <h1 className="text-2xl font-semibold text-ink">鍒涗綔璁惧畾</h1>
-          <p className="mt-1 text-sm text-ink-muted">
-            鎸夊垎缁勮皟鏁撮渶姹傦紱棰樻潗鐢ㄧ偣閫夊畬鎴愶紝涓嶅繀璁拌嫳鏂囨爣璇?-          </p>
-        </div>
+    <PageShell
+      title="鍒涗綔璁惧畾"
+      description="鎸夊垎缁勮皟鏁撮渶姹傦紱棰樻潗鐢ㄧ偣閫夊畬鎴愶紝涓嶅繀璁拌嫳鏂囨爣璇?
+      width="form"
+      actions={
         <div className="flex gap-2">
           <Link to={`/projects/${projectId}/workbench${themeReady ? '?guide=1' : ''}`}>
             <Button variant="secondary">杩涘叆宸ヤ綔鍙?/Button>
           </Link>
-          <Button loading={saveMutation.isPending && !saveMutation.variables?.enterWorkbench} onClick={() => saveMutation.mutate()}>
+          <Button
+            variant="action"
+            loading={saveMutation.isPending && !saveMutation.variables?.enterWorkbench}
+            onClick={() => saveMutation.mutate()}
+          >
             {saveOk && !saveMutation.variables?.enterWorkbench ? '宸蹭繚瀛? : '淇濆瓨璁惧畾'}
           </Button>
           {themeReady ? (
             <Button
+              variant="action"
               loading={saveMutation.isPending && Boolean(saveMutation.variables?.enterWorkbench)}
               onClick={() => saveMutation.mutate({ enterWorkbench: true })}
             >
               淇濆瓨骞跺紑濮嬪垱浣?             </Button>
           ) : null}
         </div>
-      </div>
-
+      }
+    >
       {isFromNew ? (
-        <div className="mb-4 rounded-lg border border-brand-200 bg-brand-50 px-4 py-3 text-sm text-brand-800">
+        <div className="mb-4 rounded-lg border border-action/30 bg-action/10 px-4 py-3 text-sm text-action">
           <p className="font-medium">椤圭洰宸插垱寤猴紝璇峰厛瀹屽杽棰樻潗涓庣洰鏍囧钩鍙?/p>
-          <p className="mt-1 text-brand-700/90">
+          <p className="mt-1 text-action/90">
             鍚嶇О涓庣伒鎰熷凡淇濆瓨銆傜偣閫夐鏉愮煩闃靛苟纭骞冲彴鍚庯紝鍙€屼繚瀛樺苟寮€濮嬪垱浣溿€嶈繘鍏ュ伐浣滃彴鎵ц绔嬮」绠€鎶ャ€?           </p>
         </div>
       ) : null}
 
@@ -219,12 +225,12 @@ export function ProjectSettingsPage() {
                 type="button"
                 onClick={() => setActiveGroup(group.id)}
                 className={cn(
                   'w-full rounded-lg px-3 py-2 text-left text-sm transition',
                   currentGroup?.id === group.id
-                    ? 'bg-brand-50 font-medium text-brand-700'
-                    : 'text-ink-muted hover:bg-slate-100 hover:text-ink',
+                    ? 'bg-action/10 font-medium text-action'
+                    : 'text-ink-muted hover:bg-canvas-muted hover:text-ink',
                 )}
               >
                 {group.label_zh}
               </button>
             ))}
@@ -239,41 +245,30 @@ export function ProjectSettingsPage() {
                 type="button"
                 onClick={() => setActiveGroup(group.id)}
                 className={cn(
                   'shrink-0 rounded-full px-3 py-1 text-xs',
                   currentGroup?.id === group.id
-                    ? 'bg-brand-500 text-white'
-                    : 'bg-slate-100 text-ink-muted',
+                    ? 'bg-action text-white'
+                    : 'bg-canvas-muted text-ink-muted',
                 )}
               >
                 {group.label_zh}
               </button>
             ))}
           </div>
 
-      <div className="space-y-8">
-        {groups.map((group) => (
-          <section key={group.id} className="sf-panel p-5">
-            <h2 className="sf-section-title">{group.label_zh}</h2>
-            <div className="mt-4 space-y-4">
-              {group.id === 'theme' && themeMatrix ? (
-                <ThemeSection
-                  draft={draft}
-                  matrix={themeMatrix}
-                  fields={group.fields}
-                  onPatch={patch}
-                  onFieldChange={updateField}
-                />
-              ) : (
-                group.fields.map((field) => (
-                  <FieldEditor
-                    key={field.key}
-                    field={field}
+          {currentGroup ? (
+            <section className="sf-panel p-6">
+              <h2 className="sf-section-title">{currentGroup.label_zh}</h2>
+              <div className="mt-5 space-y-5">
+                {currentGroup.id === 'theme' && themeMatrix ? (
+                  <ThemeSection
                     draft={draft}
                     matrix={themeMatrix}
-                    platformField={platformField}
+                    fields={currentGroup.fields}
                     onPatch={patch}
+                    onFieldChange={updateField}
                   />
                 ) : (
                   <div className="grid grid-cols-1 gap-5 md:grid-cols-2">
                     {currentGroup.fields.map((field) => (
                       <div
@@ -300,11 +295,11 @@ export function ProjectSettingsPage() {
               </div>
             </section>
           ) : null}
         </div>
       </div>
-    </div>
+    </PageShell>
   )
 }
 
 /** 鐢?ThemeMatrixPicker 涓撳睘娓叉煋鐨勫瓧娈碉紱鍏朵綑棰樻潗瀛楁锛堥閬?涓昏缁撴瀯/骞冲彴锛夎蛋閫氱敤 FieldEditor */
 const PICKER_FIELD_KEYS = new Set(['genre_matrix', 'flavor_tags', 'preset_theme_code'])
@@ -463,12 +458,12 @@ function FieldEditor({
                   else onChange([...current, opt.value])
                 }}
                 className={cn(
                   'rounded-lg border px-3 py-1.5 text-sm transition',
                   selected
-                    ? 'border-brand-500 bg-brand-50 text-brand-700'
-                    : 'border-slate-200 bg-white text-ink-muted hover:border-brand-300',
+                    ? 'border-action bg-action/10 text-action'
+                    : 'border-border bg-surface text-ink-muted hover:border-action/40',
                 )}
               >
                 {opt.label}
               </button>
             )
diff --git a/frontend/src/pages/create-domain.tokens.test.ts b/frontend/src/pages/create-domain.tokens.test.ts
new file mode 100644
index 0000000..1fa6160
--- /dev/null
+++ b/frontend/src/pages/create-domain.tokens.test.ts
@@ -0,0 +1,14 @@
+import { readFileSync } from 'node:fs'
+import { resolve } from 'node:path'
+import { describe, expect, it } from 'vitest'
+
+const files = ['ProjectListPage.tsx', 'NewProjectPage.tsx', 'ProjectSettingsPage.tsx']
+
+describe('create-domain pages tokens', () => {
+  for (const file of files) {
+    it(`${file} has no indigo brand classes`, () => {
+      const src = readFileSync(resolve(__dirname, file), 'utf8')
+      expect(src).not.toMatch(/brand-500|brand-600|bg-brand|text-brand|tone=\"brand\"|variant=\"brand\"/)
+    })
+  }
+})
