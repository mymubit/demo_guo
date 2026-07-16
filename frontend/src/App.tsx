import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AuthProvider } from '@/auth/AuthContext'
import { ProtectedRoute } from '@/router/ProtectedRoute'
import { AppShell } from '@/components/layout/AppShell'
import { WorkbenchDefinitionProvider } from '@/hooks/useWorkbenchDefinition'
import { LoginPage } from '@/pages/LoginPage'
import { ProjectListPage } from '@/pages/ProjectListPage'
import { NewProjectPage } from '@/pages/NewProjectPage'
import { ProjectSettingsPage } from '@/pages/ProjectSettingsPage'
import { WorkbenchPage } from '@/pages/WorkbenchPage'
import { ExternalReviewPage } from '@/pages/ExternalReviewPage'
import { AdminConfigPage } from '@/pages/AdminConfigPage'
import { ModelHubPage } from '@/pages/ModelHubPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 15_000,
      refetchOnWindowFocus: false,
      retry: false,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route element={<ProtectedRoute />}>
              <Route
                element={
                  <WorkbenchDefinitionProvider>
                    <AppShell />
                  </WorkbenchDefinitionProvider>
                }
              >
                <Route path="/" element={<Navigate to="/projects" replace />} />
                <Route path="/projects" element={<ProjectListPage />} />
                <Route path="/projects/new" element={<NewProjectPage />} />
                <Route path="/projects/:projectId/settings" element={<ProjectSettingsPage />} />
                <Route path="/projects/:projectId/workbench" element={<WorkbenchPage />} />
                <Route
                  path="/projects/:projectId"
                  element={<Navigate to="workbench" replace />}
                />
                <Route path="/tools/script-review" element={<ExternalReviewPage />} />
                <Route path="/admin/model" element={<ModelHubPage />} />
                <Route path="/admin/config" element={<AdminConfigPage />} />
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/projects" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  )
}
