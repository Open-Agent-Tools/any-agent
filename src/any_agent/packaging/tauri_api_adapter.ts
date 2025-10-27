/**
 * Tauri API adapter for dynamic backend port discovery.
 * This file is injected into the Tauri build to handle communication
 * with the Python backend running on a dynamic port.
 */

// Tauri API will be available in the packaged app
declare global {
  interface Window {
    __TAURI__?: {
      invoke: (cmd: string, args?: any) => Promise<any>;
      event: {
        listen: (event: string, handler: (event: any) => void) => Promise<() => void>;
      };
    };
    BACKEND_PORT?: number;
  }
}

let backendPort: number | null = null;
let portResolve: ((port: number) => void) | null = null;
const portPromise = new Promise<number>((resolve) => {
  portResolve = resolve;
});

/**
 * Initialize Tauri backend port discovery.
 * This should be called early in the app lifecycle.
 */
export async function initializeTauriBackend(): Promise<number> {
  // Check if we're running in Tauri
  if (!window.__TAURI__) {
    console.log('Not running in Tauri, using default port');
    return 8080; // Fallback for development
  }

  // Check if port is already set via environment variable
  const envPort = process.env.AGENT_PORT;
  if (envPort) {
    const port = parseInt(envPort, 10);
    if (!isNaN(port)) {
      backendPort = port;
      if (portResolve) portResolve(port);
      return port;
    }
  }

  // Try to get port from Tauri command
  try {
    const port = await window.__TAURI__.invoke('get_backend_port');
    if (typeof port === 'number') {
      backendPort = port;
      if (portResolve) portResolve(port);
      window.BACKEND_PORT = port;
      return port;
    }
  } catch (error) {
    console.warn('Failed to get backend port from Tauri:', error);
  }

  // Wait for port to be discovered (timeout after 10 seconds)
  const timeoutPromise = new Promise<number>((_, reject) => {
    setTimeout(() => reject(new Error('Backend port discovery timeout')), 10000);
  });

  return Promise.race([portPromise, timeoutPromise]);
}

/**
 * Get the current backend port (waits for discovery if not yet available).
 */
export async function getBackendPort(): Promise<number> {
  if (backendPort !== null) {
    return backendPort;
  }
  return portPromise;
}

/**
 * Get the backend base URL.
 */
export async function getBackendURL(): Promise<string> {
  const port = await getBackendPort();
  return `http://localhost:${port}`;
}

/**
 * Check if running in Tauri environment.
 */
export function isTauriEnvironment(): boolean {
  return !!window.__TAURI__;
}
