import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// Debug logging
console.log('Any Agent React SPA - Starting initialization');

// Error boundary component
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error?: Error }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error) {
    console.error('React Error Boundary caught error:', error);
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Error details:', error, errorInfo);
    
    // Try to show error in the DOM
    const rootElement = document.getElementById('root');
    if (rootElement) {
      rootElement.innerHTML = `
        <div style="padding: 2rem; font-family: system-ui, sans-serif; color: #d32f2f; background: #fff;">
          <h2>React App Error</h2>
          <p><strong>Error:</strong> ${error.message}</p>
          <details style="margin-top: 1rem;">
            <summary>Error Details</summary>
            <pre style="background: #f5f5f5; padding: 1rem; overflow: auto; font-size: 0.8rem;">
              ${error.stack || 'No stack trace available'}
            </pre>
          </details>
          <p style="margin-top: 1rem;">
            <a href="/health">Health Check</a> | 
            <a href="/.well-known/agent-card.json">Agent Card</a>
          </p>
        </div>
      `;
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', fontFamily: 'system-ui, sans-serif' }}>
          <h2 style={{ color: '#d32f2f' }}>Something went wrong with the React app</h2>
          <p>Error: {this.state.error?.message}</p>
          <button 
            onClick={() => window.location.reload()} 
            style={{ 
              marginTop: '1rem', 
              padding: '0.5rem 1rem', 
              backgroundColor: '#1976d2', 
              color: 'white', 
              border: 'none', 
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

try {
  // Ensure we have a root element
  const rootElement = document.getElementById('root');
  if (!rootElement) {
    console.error('Root element not found!');
    throw new Error('Root element not found');
  }

  console.log('Root element found, creating React root');
  
  const root = ReactDOM.createRoot(rootElement);
  console.log('React root created, rendering app');
  
  root.render(
    <React.StrictMode>
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </React.StrictMode>
  );
  
  console.log('React app render initiated');
} catch (error) {
  console.error('Failed to initialize React app:', error);
  
  // Fallback error display
  const rootElement = document.getElementById('root');
  if (rootElement) {
    rootElement.innerHTML = `
      <div style="padding: 2rem; font-family: system-ui, sans-serif; color: #d32f2f; background: #fff;">
        <h2>Failed to Initialize React App</h2>
        <p><strong>Error:</strong> ${error instanceof Error ? error.message : 'Unknown error'}</p>
        <p style="margin-top: 1rem;">
          <a href="/health">Health Check</a> | 
          <a href="/.well-known/agent-card.json">Agent Card</a>
        </p>
      </div>
    `;
  }
}