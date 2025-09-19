import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router } from 'react-router-dom';
import { ThemeProvider, CssBaseline, Box } from '@mui/material';
import anyAgentTheme from '@/theme';
import { AgentMetadata } from '@/types';
import { api } from '@/utils/api';
import Header from '@/components/Header';
import Footer from '@/components/Footer';
import ChatPage from '@/pages/ChatPage';
import DescriptionPage from '@/pages/DescriptionPage';

const App: React.FC = () => {
  const [agentMetadata, setAgentMetadata] = useState<AgentMetadata | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  console.log('App component initializing');
  console.log('Current URL:', window.location.href);
  console.log('Current pathname:', window.location.pathname);

  // Force navigation to root if we're on describe page but want chat interface
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('force_chat') === 'true') {
      console.log('Force chat parameter detected, navigating to root');
      window.history.replaceState({}, '', '/');
    }
  }, []);

  // Force chat interface by default unless explicitly on /describe
  const shouldShowDescription = window.location.pathname === '/describe' && !window.location.search.includes('force_chat=true');
  console.log('shouldShowDescription:', shouldShowDescription, 'pathname:', window.location.pathname);

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
    <ThemeProvider theme={anyAgentTheme}>
      <CssBaseline />
      <Router>
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
            {shouldShowDescription ? (
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

          <Footer agentMetadata={agentMetadata} />
        </Box>
      </Router>
    </ThemeProvider>
  );
};

export default App;