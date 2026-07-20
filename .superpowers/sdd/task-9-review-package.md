# Review Package Task 9 r2
BASE: 0bea66b757144e5df7be97eaf9e84ca632aa2107
HEAD: 65b2913e09e6af377eddefbeb1ea00bc77126876
## Commits (frontend workbench-related)

## Stat
 .../src/components/artifacts/ArtifactViews.tsx     |  6 ++--
 .../src/components/theme/ThemeMatrixPicker.tsx     | 18 +++++-----
 .../components/workbench/GenerationJobPanel.tsx    |  6 ++--
 .../components/workbench/GenerationTroubleCard.tsx |  2 +-
 .../components/workbench/JobLlmCallLogsPanel.tsx   | 14 ++++----
 frontend/src/components/workbench/ModulePanel.tsx  | 16 ++++-----
 frontend/src/components/workbench/PipelineRail.tsx | 22 ++++++------
 .../src/components/workbench/QualityLoopPanel.tsx  | 14 ++++----
 frontend/src/components/workbench/StageCanvas.tsx  | 16 +++++----
 frontend/src/pages/WorkbenchPage.tsx               | 16 ++++-----
 frontend/src/pages/workbench.tokens.test.ts        | 40 ++++++++++++++++++++++
 11 files changed, 106 insertions(+), 64 deletions(-)
## Diff
diff --git a/frontend/src/components/artifacts/ArtifactViews.tsx b/frontend/src/components/artifacts/ArtifactViews.tsx
index 3e31ac2..2c77d8b 100644
--- a/frontend/src/components/artifacts/ArtifactViews.tsx
+++ b/frontend/src/components/artifacts/ArtifactViews.tsx
@@ -127,9 +127,9 @@ export function ReportArtifactView({
               return (
                 <div key={idx} className="sf-panel p-3 text-sm">
                   <div className="font-medium text-ink">{row.type || `椋庨櫓 ${idx + 1}`}</div>
                   {row.description ? <p className="mt-1 text-ink-muted">{row.description}</p> : null}
-                  {row.suggestion ? <p className="mt-1 text-xs text-brand-700">寤鸿锛歿row.suggestion}</p> : null}
+                  {row.suggestion ? <p className="mt-1 text-xs text-action">寤鸿锛歿row.suggestion}</p> : null}
                 </div>
               )
             })}
           </section>
@@ -230,17 +230,17 @@ export function StoryBibleView({
             <button
               type="button"
               disabled={approvalPending}
               onClick={onReject}
-              className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm"
+              className="rounded-lg border border-border bg-surface px-3 py-2 text-sm"
             >
               椹冲洖
             </button>
             <button
               type="button"
               disabled={approvalPending}
               onClick={onApprove}
-              className="rounded-lg bg-brand-500 px-3 py-2 text-sm font-medium text-white hover:bg-brand-600"
+              className="rounded-lg bg-action px-3 py-2 text-sm font-medium text-white hover:bg-action-hover"
             >
               鎵瑰噯钃濆浘
             </button>
           </div>
diff --git a/frontend/src/components/theme/ThemeMatrixPicker.tsx b/frontend/src/components/theme/ThemeMatrixPicker.tsx
index 0e80bb3..1eb1838 100644
--- a/frontend/src/components/theme/ThemeMatrixPicker.tsx
+++ b/frontend/src/components/theme/ThemeMatrixPicker.tsx
@@ -79,9 +79,9 @@ export function ThemeMatrixPicker({
 
   return (
     <div className="space-y-6">
       {summary.length > 0 ? (
-        <div className="rounded-lg border border-brand-200 bg-brand-50 px-4 py-3 text-sm text-brand-800">
+        <div className="rounded-lg border border-action/20 bg-action/10 px-4 py-3 text-sm text-action">
           <span className="font-medium">褰撳墠缁勫悎锛?/span>
           {summary.join(' 脳 ')}
           {flavorTags.length > 0 ? ` 路 ${flavorTags.length} 涓爣绛綻 : ''}
         </div>
@@ -129,9 +129,9 @@ export function ThemeMatrixPicker({
                     className={cn(
                       'rounded-lg border px-3 py-2.5 text-left text-sm transition',
                       active
                         ? 'border-gold-400 bg-amber-50'
-                        : 'border-slate-200 bg-white hover:border-brand-300',
+                        : 'border-border bg-surface hover:border-action/40',
                     )}
                   >
                     <div className="flex items-center justify-between gap-1">
                       <span className="line-clamp-1 font-medium text-ink">
@@ -152,9 +152,9 @@ export function ThemeMatrixPicker({
           const axis = matrix.axes[axisKey]
           if (!axis) return null
           const selected = genreMatrix[axisKey as keyof GenreMatrix]
           return (
-            <div key={axisKey} className="rounded-xl border border-slate-200 bg-slate-50/60 p-4">
+            <div key={axisKey} className="rounded-xl border border-border bg-canvas-muted/60 p-4">
               <h4 className="text-sm font-semibold text-ink">{axis.label_zh}</h4>
               {axis.hint ? <p className="mt-1 text-xs text-ink-muted">{axis.hint}</p> : null}
               <div className="mt-3 grid grid-cols-2 gap-2">
                 {axis.options.map((opt) => {
@@ -169,10 +169,10 @@ export function ThemeMatrixPicker({
                       }}
                       className={cn(
                         'rounded-lg border px-2.5 py-2 text-left transition',
                         isSelected
-                          ? 'border-brand-500 bg-brand-50 text-brand-700'
-                          : 'border-slate-200 bg-white hover:border-slate-300',
+                          ? 'border-action bg-action/10 text-action'
+                          : 'border-border bg-surface hover:border-action/40',
                       )}
                     >
                       <div className="text-sm font-medium">{opt.label_zh}</div>
                       {opt.desc ? (
@@ -198,9 +198,9 @@ export function ThemeMatrixPicker({
             </span>
           </h4>
           <button
             type="button"
-            className="text-xs text-ink-muted hover:text-brand-600"
+            className="text-xs text-ink-muted hover:text-action"
             onClick={() => onChangeFlavorTags([])}
           >
             娓呯┖
           </button>
@@ -226,12 +226,12 @@ export function ThemeMatrixPicker({
                       onClick={() => toggleFlavor(opt.value)}
                       className={cn(
                         'rounded-full border px-3 py-1 text-xs transition',
                         active
-                          ? 'border-brand-500 bg-brand-500 text-white'
+                          ? 'border-action bg-action text-white'
                           : isHot
-                            ? 'border-amber-300 bg-amber-50 text-ink hover:border-brand-300'
-                            : 'border-slate-200 bg-white text-ink-muted hover:border-brand-300',
+                            ? 'border-amber-300 bg-amber-50 text-ink hover:border-action/40'
+                            : 'border-border bg-surface text-ink-muted hover:border-action/40',
                       )}
                     >
                       {isHot && !active ? (
                         <span className="mr-1 rounded-sm bg-amber-200 px-1 text-[10px] font-medium text-amber-800">
diff --git a/frontend/src/components/workbench/GenerationJobPanel.tsx b/frontend/src/components/workbench/GenerationJobPanel.tsx
index 3ca4a42..2c07e88 100644
--- a/frontend/src/components/workbench/GenerationJobPanel.tsx
+++ b/frontend/src/components/workbench/GenerationJobPanel.tsx
@@ -116,25 +116,25 @@ export function GenerationJobPanel({
   const clamped = Math.min(100, Math.max(0, progress))
   const showTrouble = status === 'failed' || status === 'disabled'
 
   return (
-    <section className="sf-panel p-4" aria-label="鐢熸垚浠诲姟杩涘害">
+    <section className="sf-panel p-5" aria-label="鐢熸垚浠诲姟杩涘害">
       <div className="flex items-center justify-between gap-3">
         <div>
           <h4 className="text-sm font-semibold text-ink">鐢熸垚浠诲姟</h4>
           <p className="mt-1 font-mono text-xs text-ink-muted">{job.job_id}</p>
         </div>
         <Badge tone={badgeTone}>{STATUS_LABEL[status ?? ''] ?? status}</Badge>
       </div>
       <div
-        className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100"
+        className="mt-4 h-2 overflow-hidden rounded-md bg-canvas-muted"
         role="progressbar"
         aria-valuenow={clamped}
         aria-valuemin={0}
         aria-valuemax={100}
         aria-label="鐢熸垚杩涘害"
       >
-        <div className="h-full bg-brand-500 transition-all" style={{ width: `${clamped}%` }} />
+        <div className="h-full bg-action transition-all" style={{ width: `${clamped}%` }} />
       </div>
       <div className="sr-only" aria-live="polite">
         杩涘害 {clamped}% 路 {STATUS_LABEL[status ?? ''] ?? status}
       </div>
diff --git a/frontend/src/components/workbench/GenerationTroubleCard.tsx b/frontend/src/components/workbench/GenerationTroubleCard.tsx
index 7fdc573..a25d99f 100644
--- a/frontend/src/components/workbench/GenerationTroubleCard.tsx
+++ b/frontend/src/components/workbench/GenerationTroubleCard.tsx
@@ -49,9 +49,9 @@ function TroubleBody({
       {trouble.showModelHubLink ? (
         <p className="mt-3">
           <Link
             to="/admin/model"
-            className="font-medium underline underline-offset-2 hover:opacity-80"
+            className="font-medium text-action underline underline-offset-2 hover:text-action-hover"
           >
             鍓嶅線妯″瀷绠＄悊 鈫?           </Link>
         </p>
diff --git a/frontend/src/components/workbench/JobLlmCallLogsPanel.tsx b/frontend/src/components/workbench/JobLlmCallLogsPanel.tsx
index 674b97e..75eee85 100644
--- a/frontend/src/components/workbench/JobLlmCallLogsPanel.tsx
+++ b/frontend/src/components/workbench/JobLlmCallLogsPanel.tsx
@@ -40,13 +40,13 @@ function CallLogCard({ item, defaultOpen = false }: { item: LlmCallLogDetail; de
         ? item.user_prompt || '锛堢┖锛?
         : item.response_text || '锛堢┖锛?
 
   return (
-    <div className="rounded-lg border border-line bg-white">
+    <div className="rounded-lg border border-border bg-surface">
       <button
         type="button"
         onClick={() => setOpen((v) => !v)}
-        className="flex w-full items-start gap-2 px-3 py-2.5 text-left hover:bg-slate-50"
+        className="flex w-full items-start gap-2 px-3 py-3 text-left hover:bg-canvas-muted"
       >
         <span className="mt-0.5 text-ink-muted">
           {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
         </span>
@@ -75,9 +75,9 @@ function CallLogCard({ item, defaultOpen = false }: { item: LlmCallLogDetail; de
           </span>
         </span>
       </button>
       {open ? (
-        <div className="border-t border-line px-3 pb-3 pt-2">
+        <div className="border-t border-border px-3 pb-3 pt-2">
           <div className="mb-2 flex gap-1">
             {(
               [
                 ['user', '鐢ㄦ埛杈撳叆'],
@@ -91,17 +91,17 @@ function CallLogCard({ item, defaultOpen = false }: { item: LlmCallLogDetail; de
                 onClick={() => setTab(key)}
                 className={cn(
                   'rounded-md px-2.5 py-1 text-xs font-medium',
                   tab === key
-                    ? 'bg-navy-900 text-white'
-                    : 'bg-slate-100 text-ink-muted hover:bg-slate-200',
+                    ? 'bg-action text-white'
+                    : 'bg-canvas-muted text-ink-muted hover:bg-canvas',
                 )}
               >
                 {label}
               </button>
             ))}
           </div>
-          <pre className="max-h-80 overflow-auto whitespace-pre-wrap break-words rounded-md bg-slate-50 p-3 text-xs leading-relaxed text-ink">
+          <pre className="max-h-80 overflow-auto whitespace-pre-wrap break-words rounded-md bg-canvas p-3 text-xs leading-relaxed text-ink">
             {body}
           </pre>
         </div>
       ) : null}
@@ -135,9 +135,9 @@ export function JobLlmCallLogsPanel({
 
   const items = (query.data?.items ?? []) as LlmCallLogDetail[]
 
   return (
-    <section id="job-llm-logs" className="sf-panel space-y-3 p-4">
+    <section id="job-llm-logs" className="sf-panel space-y-4 p-5">
       <div className="flex items-center justify-between gap-2">
         <div>
           <h3 className="text-sm font-semibold text-ink">璋冪敤鏃ュ織</h3>
           <p className="mt-0.5 text-xs text-ink-muted">
diff --git a/frontend/src/components/workbench/ModulePanel.tsx b/frontend/src/components/workbench/ModulePanel.tsx
index 0833153..868efda 100644
--- a/frontend/src/components/workbench/ModulePanel.tsx
+++ b/frontend/src/components/workbench/ModulePanel.tsx
@@ -44,20 +44,20 @@ export function ModulePanel({
 
   return (
     <aside
       className={cn(
-        'flex h-full w-[clamp(15rem,18vw,18.75rem)] shrink-0 flex-col border-l border-slate-200 bg-white',
+        'flex h-full w-[clamp(15rem,18vw,18.75rem)] shrink-0 flex-col border-l border-border bg-surface',
         className,
       )}
     >
-      <div className="border-b border-slate-200 px-4 py-3">
+      <div className="border-b border-border px-5 py-4">
         <div className="flex items-center justify-between gap-2">
           <div className="text-xs font-medium tracking-wide text-ink-faint">鏈樁娈佃兘鍔?/div>
           {onClose ? (
             <button
               type="button"
               aria-label="鍏抽棴鑳藉姏妯″潡"
-              className="rounded-md p-1 text-ink-muted transition hover:bg-slate-100 hover:text-ink"
+              className="rounded-md p-1 text-ink-muted transition hover:bg-canvas-muted hover:text-ink"
               onClick={onClose}
             >
               <X className="h-4 w-4" />
             </button>
@@ -74,24 +74,24 @@ export function ModulePanel({
         <p className="mt-2 text-[11px] leading-relaxed text-ink-muted">
           浠ヤ笅涓哄綋鍓嶉樁娈典細鍔犺浇鐨勬妧鑳芥ā鍧楋紙鍙鐩綍锛夈€傛墽琛岃鐢ㄧ敾甯冧腑鐨勩€屾墽琛屾湰闃舵銆嶃€?         </p>
       </div>
-      <div className="flex-1 space-y-4 overflow-auto p-3">
+      <div className="flex-1 space-y-5 overflow-auto p-4">
         {groups.length === 0 ? (
-          <div className="rounded-lg border border-dashed border-slate-200 px-3 py-6 text-center text-sm text-ink-muted">
+          <div className="rounded-lg border border-dashed border-border px-3 py-8 text-center text-sm text-ink-muted">
             褰撳墠闃舵鏆傛棤鍙妯″潡銆傚彲鍏堝畬鍠勫垱浣滆瀹氾紝鎴栧垏鎹㈠埌鍏朵粬娴佹按绾块樁娈点€?           </div>
         ) : (
           groups.map(([domain, items]) => (
             <section key={domain}>
-              <div className="mb-2 px-1 text-xs font-medium tracking-wide text-ink-faint">
+              <div className="mb-2.5 px-1 text-xs font-medium tracking-wide text-ink-faint">
                 {DOMAIN_LABELS[domain] ?? domain}
               </div>
-              <ul className="space-y-1.5">
+              <ul className="space-y-2">
                 {items.map((m) => (
                   <li
                     key={m.id}
-                    className="rounded-lg border border-slate-200 bg-canvas px-3 py-2"
+                    className="rounded-lg border border-border bg-canvas px-3 py-2.5"
                   >
                     <div className="flex items-center justify-between gap-2">
                       <span className="text-sm text-ink">{m.label_zh}</span>
                       <Badge tone={m.kind === 'core' ? 'action' : 'default'}>
diff --git a/frontend/src/components/workbench/PipelineRail.tsx b/frontend/src/components/workbench/PipelineRail.tsx
index 3f0a89e..c7ea6f8 100644
--- a/frontend/src/components/workbench/PipelineRail.tsx
+++ b/frontend/src/components/workbench/PipelineRail.tsx
@@ -21,11 +21,11 @@ const statusIcon: Record<StageRailStatus, typeof Circle> = {
   blocked: AlertTriangle,
 }
 
 const statusTone: Record<StageRailStatus, string> = {
-  locked: 'text-slate-400',
-  pending: 'text-slate-500',
-  active: 'text-brand-600',
+  locked: 'text-ink-faint',
+  pending: 'text-ink-muted',
+  active: 'text-shell-accent',
   waiting: 'text-amber-600',
   done: 'text-emerald-600',
   blocked: 'text-red-600',
 }
@@ -79,10 +79,10 @@ function StageButton({
         if (locked) return
         onSelect(stage)
       }}
       className={cn(
-        'flex w-full items-start gap-2 rounded-lg px-3 py-2.5 text-left transition',
-        active ? 'bg-brand-50 ring-1 ring-brand-200' : 'hover:bg-slate-50',
+        'flex w-full items-start gap-1.5 rounded-md px-2.5 py-1.5 text-left transition',
+        active ? 'bg-shell-accent/15 ring-1 ring-shell-accent/40' : 'hover:bg-canvas-muted',
         locked && 'cursor-not-allowed opacity-50 hover:bg-transparent',
         highlight && !locked && 'ring-1 ring-amber-200 bg-amber-50/70',
       )}
     >
@@ -119,14 +119,14 @@ export function PipelineRail({
   const qualityStages = qualityLoopStages(definition.stages, ctx)
   const qualityHighlight = isQualityPhaseHighlight(workflow)
 
   return (
-    <aside className="flex h-full w-[clamp(12.5rem,16vw,15rem)] shrink-0 flex-col border-r border-slate-200 bg-white">
-      <div className="border-b border-slate-200 px-4 py-3">
-        <div className="text-xs font-medium uppercase tracking-wide text-ink-faint">娴佹按绾?/div>
-        <div className="mt-1 text-sm font-semibold text-ink">鍒涗綔涓婚摼</div>
+    <aside className="flex h-full w-[clamp(12.5rem,16vw,15rem)] shrink-0 flex-col border-r border-border bg-surface">
+      <div className="border-b border-border px-3 py-2">
+        <div className="text-[11px] font-medium uppercase tracking-wide text-ink-faint">娴佹按绾?/div>
+        <div className="mt-0.5 text-sm font-semibold text-ink">鍒涗綔涓婚摼</div>
         {workflow ? (
-          <div className="mt-2">
+          <div className="mt-1.5">
             <Badge
               tone={
                 workflow.status === 'blocked'
                   ? 'danger'
@@ -141,9 +141,9 @@ export function PipelineRail({
             </Badge>
           </div>
         ) : null}
       </div>
-      <ol className="flex-1 space-y-1 overflow-auto p-2">
+      <ol className="flex-1 space-y-0.5 overflow-auto p-1.5">
         {stages.map((stage, index) => {
           const status = resolveStageStatus(stage, workflow)
           return (
             <li key={stage.id}>
diff --git a/frontend/src/components/workbench/QualityLoopPanel.tsx b/frontend/src/components/workbench/QualityLoopPanel.tsx
index b8b2139..37bd7e1 100644
--- a/frontend/src/components/workbench/QualityLoopPanel.tsx
+++ b/frontend/src/components/workbench/QualityLoopPanel.tsx
@@ -51,21 +51,21 @@ export function QualityLoopPanel({
       ? USER_DECISION_OPTIONS.filter((o) => workflow.pending_user_options?.includes(o.value))
       : USER_DECISION_OPTIONS
 
   return (
-    <div className="space-y-4">
+    <div className="space-y-5">
       <div className="flex items-center justify-between">
         <h3 className="sf-section-title">璐ㄦ鐜?/h3>
         <div className="text-xs text-ink-muted">淇杞 路 {workflow.revision_round}</div>
       </div>
 
-      <div className="grid grid-cols-2 gap-4">
-        <section className="sf-panel p-4">
+      <div className="grid grid-cols-2 gap-5">
+        <section className="sf-panel p-5">
           <h4 className="text-sm font-semibold text-ink">璇勫垎</h4>
           {qualityReport ? (
             <div className="mt-3 space-y-2 text-sm">
               <div className="flex items-baseline gap-2">
-                <span className="text-3xl font-semibold text-brand-600">
+                <span className="text-3xl font-semibold text-action">
                   {qualityReport.overall_score ?? '鈥?}
                 </span>
                 <span className="text-ink-muted">{qualityReport.grade}</span>
               </div>
@@ -85,9 +85,9 @@ export function QualityLoopPanel({
             <p className="mt-3 text-sm text-ink-muted">鏆傛棤璇勫垎鎶ュ憡</p>
           )}
         </section>
 
-        <section className="sf-panel p-4">
+        <section className="sf-panel p-5">
           <h4 className="text-sm font-semibold text-ink">鍚堣</h4>
           {complianceReport ? (
             <div className="mt-3 space-y-2 text-sm">
               <p className="font-medium text-ink">{complianceReport.overall_result}</p>
@@ -115,17 +115,17 @@ export function QualityLoopPanel({
         </div>
       ) : null}
 
       {waitingUser ? (
-        <section className="sf-panel border-amber-200 bg-amber-50/60 p-4">
+        <section className="sf-panel border-amber-200 bg-amber-50/60 p-5">
           <h4 className="text-sm font-semibold text-amber-900">绛夊緟鐢ㄦ埛鍐崇瓥</h4>
           <p className="mt-1 text-sm text-amber-800">璐ㄦ鏈嚜鍔ㄩ€氳繃锛岃涓夐€変竴缁х画娴佺▼銆?/p>
           {decisionMutation.isError ? (
             <div className="mt-3">
               <ErrorBanner message={formatApiError(decisionMutation.error)} />
             </div>
           ) : null}
-          <div className="mt-4 flex flex-wrap gap-2">
+          <div className="mt-5 flex flex-wrap gap-2">
             {options.map((opt) => (
               <Button
                 key={opt.value}
                 variant={opt.value === 'accept_current' ? 'action' : 'secondary'}
diff --git a/frontend/src/components/workbench/StageCanvas.tsx b/frontend/src/components/workbench/StageCanvas.tsx
index c67ca3e..2086991 100644
--- a/frontend/src/components/workbench/StageCanvas.tsx
+++ b/frontend/src/components/workbench/StageCanvas.tsx
@@ -162,17 +162,18 @@ export function StageCanvas({
     forceGuide: forceFirstRunGuide,
   })
 
   return (
-    <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
-      <header className="flex items-center justify-between border-b border-slate-200 bg-white px-5 py-3">
+    <div className="flex min-w-0 flex-1 flex-col overflow-hidden bg-canvas">
+      <header className="flex items-center justify-between border-b border-border bg-surface px-6 py-4">
         <div>
-          <h2 className="text-base font-semibold text-ink">{stage.label_zh}</h2>
-          <p className="text-xs text-ink-muted">
+          <h2 className="text-lg font-semibold text-ink">{stage.label_zh}</h2>
+          <p className="mt-0.5 text-sm text-ink-muted">
             褰撳墠鐢卞搴斿垱浣滆鑹叉墽琛岋紝瀹屾垚鍚庤嚜鍔ㄤ繚瀛橀樁娈典骇鐗?           </p>
         </div>
         <Button
+          variant="action"
           iconLeft={<Play className="h-4 w-4" />}
           loading={runMutation.isPending}
           disabled={!executable}
           aria-disabled={!executable}
@@ -186,16 +187,16 @@ export function StageCanvas({
           鎵ц鏈樁娈?         </Button>
       </header>
 
-      <div className="mx-auto w-full max-w-[1600px] flex-1 space-y-4 overflow-auto p-[clamp(1rem,1.5vw,2rem)]">
+      <div className="w-full flex-1 space-y-5 overflow-auto px-[clamp(1.5rem,2.5vw,2.75rem)] py-[clamp(1.25rem,2vw,2rem)]">
         {themeIncomplete ? (
           <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
             <p className="font-medium">棰樻潗灏氭湭閫夐綈锛岀敓鎴愯川閲忓彲鑳藉彈褰卞搷</p>
             <p className="mt-1">
               寤鸿鍏堝埌{' '}
               <Link
-                className="font-medium underline underline-offset-2"
+                className="font-medium text-action underline underline-offset-2"
                 to={`/projects/${projectId}/settings?focus=theme`}
               >
                 鍒涗綔璁惧畾
               </Link>{' '}
@@ -214,8 +215,9 @@ export function StageCanvas({
                 </p>
               </div>
               <div className="flex gap-2">
                 <Button
+                  variant="action"
                   size="sm"
                   loading={runMutation.isPending}
                   disabled={!executable}
                   iconLeft={<Play className="h-3.5 w-3.5" />}
@@ -237,9 +239,9 @@ export function StageCanvas({
           </div>
         ) : null}
 
         {!executable && gateReason ? (
-          <div className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-ink">
+          <div className="rounded-lg border border-border bg-surface px-4 py-3 text-sm text-ink">
             <p className="font-medium text-ink">褰撳墠鏃犳硶鎵ц鏈樁娈?/p>
             <p className="mt-1 text-ink-muted">{gateReason}</p>
           </div>
         ) : null}
diff --git a/frontend/src/pages/WorkbenchPage.tsx b/frontend/src/pages/WorkbenchPage.tsx
index 88a51f9..2d988d7 100644
--- a/frontend/src/pages/WorkbenchPage.tsx
+++ b/frontend/src/pages/WorkbenchPage.tsx
@@ -135,21 +135,21 @@ export function WorkbenchPage() {
   const themeReady = isGenreMatrixComplete(settingsQuery.data.genre_matrix)
   const firstRun = isWorkflowFirstRun(workflowQuery.data)
 
   return (
-    <div className="flex h-full min-h-0 flex-col">
-      <div className="flex items-center justify-between border-b border-slate-200 bg-white px-5 py-3">
+    <div className="flex h-full min-h-0 flex-col bg-canvas">
+      <div className="flex items-center justify-between border-b border-border bg-surface px-4 py-2">
         <div>
-          <h1 className="text-base font-semibold text-ink">
+          <h1 className="text-sm font-semibold text-ink">
             {settingsQuery.data.title || '鍒涗綔宸ヤ綔鍙?}
           </h1>
-          <p className="text-xs text-ink-muted">
+          <p className="text-[11px] text-ink-muted">
             {settingsQuery.data.entry_type === 'original_track' ? '鍘熷垱閫氶亾' : '鏀圭紪閫氶亾'} 路{' '}
             {WORKFLOW_STATUS_LABELS[workflowQuery.data.status]}
             {firstRun ? ' 路 棣栬窇' : ''}
           </p>
         </div>
-        <div className="flex items-center gap-2">
+        <div className="flex items-center gap-1.5">
           {isCompactPc ? (
             <Button
               variant="secondary"
               size="sm"
@@ -172,12 +172,12 @@ export function WorkbenchPage() {
         </div>
       </div>
 
       {!themeReady ? (
-        <div className="border-b border-amber-200 bg-amber-50 px-5 py-2 text-xs text-amber-900">
+        <div className="border-b border-amber-200 bg-amber-50 px-4 py-1.5 text-xs text-amber-900">
           棰樻潗鏈€夐綈锛屽缓璁厛瀹屽杽鍒涗綔璁惧畾鍐嶆墽琛屼富閾俱€?           <Link
-            className="ml-2 font-medium underline underline-offset-2"
+            className="ml-2 font-medium text-action underline underline-offset-2"
             to={`/projects/${projectId}/settings?focus=theme`}
           >
             鍘婚€夐鏉?           </Link>
@@ -214,9 +214,9 @@ export function WorkbenchPage() {
             />
             <ModulePanel
               stage={activeStage}
               settings={settingsQuery.data}
-              className="absolute inset-y-0 right-0 z-30 w-[300px] shadow-xl"
+              className="absolute inset-y-0 right-0 z-30 w-[300px] shadow-panel"
               onClose={() => setIsModulePanelOpen(false)}
             />
           </>
         ) : null}
diff --git a/frontend/src/pages/workbench.tokens.test.ts b/frontend/src/pages/workbench.tokens.test.ts
new file mode 100644
index 0000000..4fdbbe1
--- /dev/null
+++ b/frontend/src/pages/workbench.tokens.test.ts
@@ -0,0 +1,40 @@
+import { readdirSync, readFileSync, statSync } from 'node:fs'
+import { resolve } from 'node:path'
+import { describe, expect, it } from 'vitest'
+
+const BRAND_RE = /brand-500|brand-600|bg-brand|text-brand|tone="brand"|variant="brand"/
+
+function collectTsx(dir: string): string[] {
+  const out: string[] = []
+  for (const name of readdirSync(dir)) {
+    const full = resolve(dir, name)
+    if (statSync(full).isDirectory()) {
+      out.push(...collectTsx(full))
+      continue
+    }
+    if (name.endsWith('.tsx') && !name.includes('.test.')) out.push(full)
+  }
+  return out
+}
+
+const files = [
+  resolve(__dirname, 'WorkbenchPage.tsx'),
+  ...collectTsx(resolve(__dirname, '../components/workbench')),
+  resolve(__dirname, '../components/theme/ThemeMatrixPicker.tsx'),
+  resolve(__dirname, '../components/artifacts/ArtifactViews.tsx'),
+]
+
+describe('workbench tokens', () => {
+  it('PipelineRail source has no indigo brand utilities', () => {
+    const src = readFileSync(resolve(__dirname, '../components/workbench/PipelineRail.tsx'), 'utf8')
+    expect(src).not.toMatch(/brand-500|bg-brand|text-brand/)
+  })
+
+  for (const file of files) {
+    const label = file.replace(/\\/g, '/').split('/src/')[1] ?? file
+    it(`${label} has no indigo brand classes`, () => {
+      const src = readFileSync(file, 'utf8')
+      expect(src).not.toMatch(BRAND_RE)
+    })
+  }
+})
