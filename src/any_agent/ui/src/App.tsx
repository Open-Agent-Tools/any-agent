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
  const [backendReady, setBackendReady] = useState(false);

  console.log('App component initializing');
  console.log('Current URL:', window.location.href);
  console.log('Current pathname:', window.location.pathname);
  console.log('Location from useLocation:', location.pathname);
  console.log('UI Build timestamp: 2025-01-19T18:15:00Z - Router Bypass Fix v0.2.5');

  // Initialize Tauri backend and check for first-run setup
  useEffect(() => {
    const initializeTauriAndCheckSetup = async () => {
      console.log('[App.tsx] Step 1: Starting initialization');

      // Improved Tauri detection
      const tauri = typeof window !== 'undefined' && ('__TAURI__' in window || '__TAURI_INTERNALS__' in window);

      console.log('[App.tsx] Step 2: Tauri mode check:', {
        tauri,
        hasTauriGlobal: typeof window !== 'undefined' && '__TAURI__' in window,
        hasTauriInternals: typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window,
        windowKeys: typeof window !== 'undefined' ? Object.keys(window).filter(k => k.includes('TAURI')) : []
      });

      setIsTauriMode(tauri);
      console.log('[App.tsx] Step 3: Set Tauri mode to:', tauri);

      // Initialize Tauri backend if in Tauri mode
      if (tauri) {
        try {
          console.log('[App.tsx] Step 4: In Tauri mode, importing adapter...');
          // Dynamically import and initialize Tauri adapter
          const tauriAdapter = await import('@/utils/tauri_api_adapter');
          console.log('[App.tsx] Step 5: Tauri adapter imported successfully, calling initializeTauriBackend()...');

          const port = await tauriAdapter.initializeTauriBackend();
          console.log('[App.tsx] Step 6: Tauri backend initialized successfully on port:', port);

          // Check for first-run setup
          console.log('[App.tsx] Step 7: Checking if config exists...');
          const configExists = await ConfigManager.configExists();
          console.log('[App.tsx] Step 8: Config exists:', configExists);

          if (!configExists) {
            console.log('[App.tsx] Step 9: First run detected - showing setup wizard');
            setShowSetupWizard(true);
          } else {
            console.log('[App.tsx] Step 9: Config exists, skipping setup wizard');
          }
        } catch (error) {
          console.error('[App.tsx] ERROR in Tauri initialization or config check:', error);
          console.error('[App.tsx] Error details:', {
            name: error instanceof Error ? error.name : 'Unknown',
            message: error instanceof Error ? error.message : String(error),
            stack: error instanceof Error ? error.stack : undefined
          });
          // Even if initialization fails, mark backend as ready to avoid infinite loading
          console.log('[App.tsx] Proceeding despite error to avoid freeze');
        }
      } else {
        console.log('[App.tsx] Step 4: Not in Tauri mode - skipping backend initialization and setup wizard check');
      }

      // Mark backend as ready (either Tauri initialized or web mode)
      console.log('[App.tsx] Step 10: Setting backend ready to true');
      setBackendReady(true);
      console.log('[App.tsx] Step 11: Backend ready state updated');
    };

    console.log('[App.tsx] Calling initializeTauriAndCheckSetup()');
    initializeTauriAndCheckSetup();
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
    console.log('[App.tsx] Metadata fetch useEffect triggered, backendReady:', backendReady);

    // Only fetch agent metadata after backend is ready
    if (!backendReady) {
      console.log('[App.tsx] Waiting for backend to be ready before fetching metadata...');
      return;
    }

    const fetchAgentMetadata = async () => {
      try {
        console.log('[App.tsx] Backend ready, fetching agent metadata from API...');
        const metadata = await api.getAgentCard();
        console.log('[App.tsx] Agent metadata fetched successfully:', metadata);
        setAgentMetadata(metadata);
        console.log('[App.tsx] Agent metadata state updated');
      } catch (error) {
        console.error('[App.tsx] Failed to load agent metadata:', error);
        console.error('[App.tsx] Error details:', {
          name: error instanceof Error ? error.name : 'Unknown',
          message: error instanceof Error ? error.message : String(error),
          stack: error instanceof Error ? error.stack : undefined
        });
        setError(error as Error);
        // Set fallback metadata
        console.log('[App.tsx] Setting fallback metadata');
        setAgentMetadata({
          name: 'Unknown Agent',
          framework: 'unknown',
          model: 'Not specified',
          port: 8080,
          status: 'active',
        });
      } finally {
        console.log('[App.tsx] Setting isLoading to false');
        setIsLoading(false);
        console.log('[App.tsx] Loading complete, app should render now');
      }
    };

    console.log('[App.tsx] Calling fetchAgentMetadata()');
    fetchAgentMetadata();
  }, [backendReady]);

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