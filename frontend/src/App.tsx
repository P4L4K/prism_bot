
import { MainLayout } from './layouts/MainLayout';
import { StorybookDashboard } from './pages/StorybookDashboard';
import { BookshelfPage } from './pages/BookshelfPage';
import { SettingsPage } from './pages/SettingsPage';
import { useAppStore } from './store/useAppStore';
import { useSSE } from './hooks/useSSE';
import { ErrorBoundary } from './components/ErrorBoundary';

function App() {
  const { currentView } = useAppStore();
  
  // Connect to FastAPI backend SSE bridge
  useSSE(`${import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'}/api/events`);

  return (
    <ErrorBoundary>
      <MainLayout>
        {currentView === 'chat' && <StorybookDashboard />}
        {currentView === 'history' && <BookshelfPage />}
        {currentView === 'settings' && <SettingsPage />}
      </MainLayout>
    </ErrorBoundary>
  );
}

export default App;
