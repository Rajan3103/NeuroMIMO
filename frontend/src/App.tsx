import { useState, useEffect } from 'react';
import { Navbar } from './components/layout/Navbar';
import { Sidebar } from './components/layout/Sidebar';
import type { NavTab } from './components/layout/Sidebar';
import { OverviewPage } from './pages/OverviewPage';
import { SimulatorPage } from './pages/SimulatorPage';
import { ChannelEstimationPage } from './pages/ChannelEstimationPage';
import { ModelTrainingPage } from './pages/ModelTrainingPage';
import { PerformanceComparisonPage } from './pages/PerformanceComparisonPage';
import { SignalVisualizationPage } from './pages/SignalVisualizationPage';
import { ExperimentHistoryPage } from './pages/ExperimentHistoryPage';
import { AboutPage } from './pages/AboutPage';
import { api } from './api/client';
import type { HealthResponse, ModelStatus } from './types';

export type Theme = 'light' | 'dark';
const THEME_STORAGE_KEY = 'neuromimo-theme';

function loadSavedTheme(): Theme {
  try {
    return localStorage.getItem(THEME_STORAGE_KEY) === 'dark' ? 'dark' : 'light';
  } catch {
    return 'light';
  }
}

export function App() {
  const [currentTab, setCurrentTab] = useState<NavTab>('overview');
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState<boolean>(false);
  const [theme, setTheme] = useState<Theme>(loadSavedTheme);

  // Apply the theme class to <html> so the CSS colour variables switch everywhere
  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark');
    try {
      localStorage.setItem(THEME_STORAGE_KEY, theme);
    } catch {
      // Storage can be unavailable (private mode); the theme still applies for this visit
    }
  }, [theme]);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const [healthData, statusData] = await Promise.all([
        api.getHealth(),
        api.getModelStatus(),
      ]);
      setHealth(healthData);
      setModelStatus(statusData);
    } catch (err) {
      console.warn('API currently unavailable or server starting:', err);
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  return (
    <div className="min-h-screen bg-page text-slate-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-black">
      <Navbar
        health={health}
        loading={loading}
        onRefresh={fetchStatus}
        onToggleSidebar={() => setMobileSidebarOpen((prev) => !prev)}
        theme={theme}
        onToggleTheme={() => setTheme((prev) => (prev === 'dark' ? 'light' : 'dark'))}
      />

      <div className="flex flex-1 overflow-hidden relative">
        <Sidebar
          currentTab={currentTab}
          onSelectTab={setCurrentTab}
          isMobileOpen={mobileSidebarOpen}
          onCloseMobile={() => setMobileSidebarOpen(false)}
        />

        <main className="flex-1 overflow-y-auto p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto">
            {currentTab === 'overview' && (
              <OverviewPage
                health={health}
                modelStatus={modelStatus}
                onNavigate={setCurrentTab}
              />
            )}
            {currentTab === 'simulator' && <SimulatorPage />}
            {currentTab === 'estimation' && <ChannelEstimationPage />}
            {currentTab === 'training' && (
              <ModelTrainingPage
                modelStatus={modelStatus}
                onRefreshStatus={fetchStatus}
              />
            )}
            {currentTab === 'comparison' && <PerformanceComparisonPage />}
            {currentTab === 'visualization' && <SignalVisualizationPage />}
            {currentTab === 'history' && <ExperimentHistoryPage />}
            {currentTab === 'about' && <AboutPage />}
          </div>
        </main>
      </div>
    </div>
  );
}

export default App;
