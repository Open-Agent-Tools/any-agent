import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, useLocation } from 'react-router-dom';
import { ThemeProvider, CssBaseline, Box } from '@mui/material';
import anyAgentTheme from '@/theme';
import { AgentMetadata } from '@/types';
import { api } from '@/utils/api';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import ChatPage from '@/pages/ChatPage';
import DescriptionPage from '@/pages/DescriptionPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { SetupWizard } from '@/components/SetupWizard';
import { ConfigManager } from '@/utils/configManager';

const AppContent: React.FC = () => {
  const location = useLocation();
  const [agentMetadata, setAgentMetadata] = useState<AgentMetadata | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);
  const [showSetupWizard, setShowSetupWizard] = useState(false);
  const [isTauriMode, setIsTauriMode] = useState(false);

  console.log('App component initializing');
  console.log('Current URL:', window.location.href);
  console.log('Current pathname:', window.location.pathname);
  console.log('Location from useLocation:', location.pathname);
  console.log('UI Build timestamp: 2025-01-19T18:15:00Z - Router Bypass Fix v0.2.5');

  // Check for first-run setup (Tauri mode only)
  useEffect(() => {
    const checkFirstRun = async () => {
      // Improved Tauri detection
      const tauri = typeof window !== 'undefined' && ('__TAURI__' in window || '__TAURI_INTERNALS__' in window);

      console.log('Tauri mode check:', {
        tauri,
        hasTauriGlobal: typeof window !== 'undefined' && '__TAURI__' in window,
        hasTauriInternals: typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window,
        windowKeys: typeof window !== 'undefined' ? Object.keys(window).filter(k => k.includes('TAURI')) : []
      });

      setIsTauriMode(tauri);

      if (tauri) {
        try {
          const configExists = await ConfigManager.configExists();
          console.log('Config exists:', configExists);

          if (!configExists) {
            console.log('First run detected - showing setup wizard');
            setShowSetupWizard(true);
          }
        } catch (error) {
          console.error('Error checking config:', error);
        }
      } else {
        console.log('Not in Tauri mode - skipping setup wizard check');
      }
    };

    checkFirstRun();
  }, []);

  const handleSetupComplete = () => {
    console.log('Setup wizard completed');
    setShowSetupWizard(false);
    // Optionally reload the page to apply new credentials
    window.location.reload();
  };

  // Force navigation to root if we're on describe page but want chat interface
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('force_chat') === 'true') {
      console.log('Force chat parameter detected, navigating to root');
      window.history.replaceState({}, '', '/');
    }
  }, []);

  // Routing logic - check for settings, describe, or default to chat
  const currentPath = location.pathname;
  const hasForceChat = location.search.includes('force_chat=true');
  const isSettingsPage = currentPath === '/settings';
  const isExplicitlyDescribe = currentPath === '/describe' && !hasForceChat;
  const shouldShowDescription = isExplicitlyDescribe;

  console.log('PATH DEBUG:', {
    currentPath,
    hasForceChat,
    isSettingsPage,
    isExplicitlyDescribe,
    shouldShowDescription,
    search: location.search
  });

  useEffect(() => {
    const fetchAgentMetadata = async () => {
      try {
        console.log('Fetching agent metadata...');
        const metadata = await api.getAgentCard();
        console.log('Agent metadata fetched:', metadata);
        setAgentMetadata(metadata);
      } catch (error) {
        console.error('Failed to load agent metadata:', error);
        setError(error as Error);
        // Set fallback metadata
        setAgentMetadata({
          name: 'Unknown Agent',
          framework: 'unknown',
          model: 'Not specified',
          port: 8080,
          status: 'active',
        });
      } finally {
        setIsLoading(false);
        console.log('Loading complete');
      }
    };

    fetchAgentMetadata();
  }, []);

  const handleAgentMetadataUpdate = (metadata: AgentMetadata) => {
    setAgentMetadata(metadata);
  };

  if (isLoading) {
    return (
      <ThemeProvider theme={anyAgentTheme}>
        <CssBaseline />
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '100vh',
            backgroundColor: 'background.default',
            padding: 2,
          }}
        >
          {/* Simple loading state without additional components to avoid circular deps */}
          <div style={{ fontSize: '1.2rem', marginBottom: '1rem' }}>Loading Any Agent...</div>
          {error && (
            <div style={{ 
              color: '#d32f2f', 
              textAlign: 'center',
              maxWidth: '600px',
              backgroundColor: '#ffebee',
              padding: '1rem',
              borderRadius: '4px',
              border: '1px solid #ffcdd2'
            }}>
              <strong>Error loading agent metadata:</strong><br />
              {error.message}
            </div>
          )}
        </Box>
      </ThemeProvider>
    );
  }

  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        minHeight: '100vh',
        backgroundColor: 'background.default',
      }}
    >
      <Header />

      <Box
        component="main"
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
        }}
      >
        {/* Direct conditional rendering to bypass router issues */}
        {isSettingsPage ? (
          <>
            {console.log('Rendering SettingsPage')}
            <SettingsPage />
          </>
        ) : shouldShowDescription ? (
          <>
            {console.log('Rendering DescriptionPage based on direct pathname check')}
            <DescriptionPage agentMetadata={agentMetadata} />
          </>
        ) : (
          <>
            {console.log('Rendering ChatPage as default (not DescriptionPage)')}
            <ChatPage
              agentMetadata={agentMetadata}
              onAgentMetadataUpdate={handleAgentMetadataUpdate}
            />
          </>
        )}
      </Box>

      {/* Setup Wizard - only in Tauri mode */}
      {isTauriMode && (
        <SetupWizard
          open={showSetupWizard}
          onComplete={handleSetupComplete}
        />
      )}

      <Footer agentMetadata={agentMetadata} />
    </Box>
  );
};

const App: React.FC = () => {
  return (
    <ThemeProvider theme={anyAgentTheme}>
      <CssBaseline />
      <Router>
        <AppContent />
      </Router>
    </ThemeProvider>
  );
};

export default App;