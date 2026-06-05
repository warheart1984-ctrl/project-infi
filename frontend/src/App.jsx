import React, { Suspense, lazy } from 'react';
import { Toaster } from 'react-hot-toast';
import { BrowserRouter as Router, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import Navbar from './components/Navbar';
import { AuthGate, AuthProvider } from './components/AuthProvider';
import './App.css';

const routerBasename = (() => {
  const configuredBasename = import.meta?.env?.VITE_ROUTER_BASENAME || '';
  const value = String(configuredBasename).trim();
  if (!value || value === '/') {
    return undefined;
  }
  return `/${value.replace(/^\/+|\/+$/g, '')}`;
})();

const JarvisPage = lazy(() => import('./pages/JarvisPage'));
const RepoManager = lazy(() => import('./pages/RepoManager'));
const NovaPage = lazy(() => import('./pages/NovaPage'));
const MemoryBank = lazy(() => import('./pages/MemoryBank'));
const TextGenerator = lazy(() => import('./pages/TextGenerator'));
const ImageAnalyzer = lazy(() => import('./pages/ImageAnalyzer'));
const ImageGenerator = lazy(() => import('./pages/ImageGenerator'));
const AudioProcessor = lazy(() => import('./pages/AudioProcessor'));
const BatchProcessor = lazy(() => import('./pages/BatchProcessor'));
const History = lazy(() => import('./pages/History'));
const Settings = lazy(() => import('./pages/Settings'));
// These pages are canonical workflow-shell surfaces owned by `app/main.py`.
// They are live product routes, but they do not redefine core Jarvis runtime
// authority, which still lives in `src/api.py`.
const WorkflowBuilder = lazy(() => import('./pages/WorkflowBuilder'));
const WorkflowRuns = lazy(() => import('./pages/WorkflowRuns'));
const WorkflowRunDetail = lazy(() => import('./pages/WorkflowRunDetail'));
const WorkflowApprovals = lazy(() => import('./pages/WorkflowApprovals'));
const WorkflowTemplates = lazy(() => import('./pages/WorkflowTemplates'));
const OperatorConsole = lazy(() => import('./pages/OperatorConsole'));
const TemporalReplay = lazy(() => import('./pages/TemporalReplay/TemporalReplay'));
const PlatformConsole = lazy(() => import('./pages/PlatformConsole'));
const PlatformJobDetail = lazy(() => import('./pages/PlatformJobDetail'));
const PlatformArtifacts = lazy(() => import('./pages/PlatformArtifacts'));
const PlatformGettingStarted = lazy(() => import('./pages/PlatformGettingStarted'));
const PlatformAssistant = lazy(() => import('./pages/PlatformAssistant'));
const PlatformWorkflow = lazy(() => import('./pages/PlatformWorkflow'));
const PlatformMesh = lazy(() => import('./pages/PlatformMesh'));
const PlatformMarketplace = lazy(() => import('./pages/PlatformMarketplace'));
const Login = lazy(() => import('./pages/Login'));
const Onboarding = lazy(() => import('./pages/Onboarding'));

function RouteFallback() {
  return (
    <div className="page-shell page-shell--loading" role="status" aria-live="polite">
      <div className="page-shell__content">Loading interface...</div>
    </div>
  );
}

function AppShell() {
  const location = useLocation();
  const isNovaRoute = location.pathname === '/' || location.pathname.startsWith('/nova');
  const isJarvisRoute = location.pathname.startsWith('/jarvis');
  const isLoginRoute = location.pathname === '/login';

  return (
    <div className={`App ${isNovaRoute ? 'App--nova' : ''} ${isJarvisRoute ? 'App--jarvis' : ''} ${isLoginRoute ? 'App--login' : ''}`}>
      {!isLoginRoute ? <Navbar /> : null}
      <main className={`main-content ${isNovaRoute ? 'main-content--nova' : ''} ${isJarvisRoute ? 'main-content--jarvis' : ''}`}>
        <Suspense fallback={<RouteFallback />}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<NovaPage />} />
            <Route path="/nova" element={<NovaPage />} />
            <Route path="/nova-the-north-star" element={<NovaPage />} />
            <Route path="/jarvis" element={<JarvisPage />} />
            <Route path="/jarvis/repo-manager" element={<RepoManager />} />
            <Route path="/repo-manager" element={<Navigate to="/jarvis/repo-manager" replace />} />
            <Route path="/workbench" element={<Navigate to="/jarvis" replace />} />
            <Route path="/dashboard" element={<Navigate to="/jarvis" replace />} />
            <Route path="/memory" element={<MemoryBank />} />
            <Route path="/prompt-lab" element={<TextGenerator />} />
            <Route path="/text-generator" element={<TextGenerator />} />
            <Route path="/image-analyzer" element={<ImageAnalyzer />} />
            <Route path="/image-generator" element={<ImageGenerator />} />
            <Route path="/audio-processor" element={<AudioProcessor />} />
            <Route path="/batch-processor" element={<BatchProcessor />} />
            <Route path="/history" element={<History />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/workflows" element={<WorkflowBuilder />} />
            <Route path="/workflows/runs" element={<WorkflowRuns />} />
            <Route path="/workflows/runs/:runId" element={<WorkflowRunDetail />} />
            <Route path="/workflows/approvals" element={<WorkflowApprovals />} />
            <Route path="/workflows/templates" element={<WorkflowTemplates />} />
            <Route path="/operator" element={<OperatorConsole />} />
            <Route path="/operator/replay" element={<TemporalReplay />} />
            <Route path="/operator/replay/:subjectType/:subjectId" element={<TemporalReplay />} />
            <Route path="/platform" element={<PlatformConsole />} />
            <Route path="/platform/jobs/:jobId" element={<PlatformJobDetail />} />
            <Route path="/platform/artifacts" element={<PlatformArtifacts />} />
            <Route path="/platform/getting-started" element={<PlatformGettingStarted />} />
            <Route path="/platform/assistant" element={<PlatformAssistant />} />
            <Route path="/platform/workflows" element={<PlatformWorkflow />} />
            <Route path="/platform/mesh" element={<PlatformMesh />} />
            <Route path="/platform/marketplace" element={<PlatformMarketplace />} />
            <Route path="/onboarding" element={<Onboarding />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </main>
      <Toaster
        position="top-right"
        toastOptions={{
          style: {
            background: '#102132',
            color: '#f8fafc',
            border: '1px solid rgba(255,255,255,0.08)',
          },
        }}
      />
    </div>
  );
}

function App() {
  return (
    <Router basename={routerBasename}>
      <AuthProvider>
        <AuthGate>
          <AppShell />
        </AuthGate>
      </AuthProvider>
    </Router>
  );
}

export default App;
