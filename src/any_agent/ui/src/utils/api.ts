import {
  AgentMetadata,
  ChatCreateSessionResponse,
  ChatSendMessageResponse,
  ChatCancelTaskResponse,
  ApiResponse,
} from '@/types';
import { isTauriEnvironment, getBackendURL } from '@/utils/tauri_api_adapter';

// Dynamic API base URL - returns backend URL in Tauri mode, empty string for browser mode
async function getApiBaseUrl(): Promise<string> {
  if (isTauriEnvironment()) {
    try {
      return await getBackendURL();
    } catch (error) {
      console.error('Failed to get backend URL in Tauri mode:', error);
      return 'http://localhost:8035'; // Fallback to default port
    }
  }
  return ''; // Browser mode - use relative URLs
}

export const api = {
  // Agent metadata
  async getAgentCard(): Promise<AgentMetadata> {
    try {
      const baseUrl = await getApiBaseUrl();
      const response = await fetch(`${baseUrl}/.well-known/agent-card.json`);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.warn('Failed to fetch agent card, using fallback:', error);
      // Fallback to environment variables or defaults
      const windowEnv = window as unknown as {
        AGENT_NAME?: string;
        AGENT_FRAMEWORK?: string;
        AGENT_MODEL?: string;
        AGENT_PORT?: string;
      };
      return {
        name: windowEnv.AGENT_NAME || 'Unknown Agent',
        framework: windowEnv.AGENT_FRAMEWORK || 'unknown',
        model: windowEnv.AGENT_MODEL || 'Not specified',
        port: parseInt(windowEnv.AGENT_PORT || '8080'),
        status: 'active',
      };
    }
  },

  // Health check
  async healthCheck(): Promise<ApiResponse> {
    const baseUrl = await getApiBaseUrl();
    const response = await fetch(`${baseUrl}/health`);
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  },

  // Chat session management
  async createChatSession(sessionId: string): Promise<ChatCreateSessionResponse> {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000); // 10 second timeout

    try {
      const baseUrl = await getApiBaseUrl();
      const response = await fetch(`${baseUrl}/chat/create-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          agent_url: window.location.origin,
        }),
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      clearTimeout(timeoutId);
      throw error;
    }
  },

  async sendMessage(sessionId: string, message: string): Promise<ChatSendMessageResponse> {
    const baseUrl = await getApiBaseUrl();
    const response = await fetch(`${baseUrl}/chat/send-message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: sessionId,
        message: message,
      }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  },

  async cleanupSession(sessionId: string): Promise<void> {
    try {
      const baseUrl = await getApiBaseUrl();
      await fetch(`${baseUrl}/chat/cleanup-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: sessionId }),
      });
    } catch (error) {
      console.warn('Failed to cleanup session:', error);
    }
  },

  async cancelTask(sessionId: string): Promise<ChatCancelTaskResponse> {
    const baseUrl = await getApiBaseUrl();
    const response = await fetch(`${baseUrl}/chat/cancel-task`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId }),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
  },

  // Beacon cleanup for page unload
  async cleanupSessionBeacon(sessionId: string): Promise<void> {
    const baseUrl = await getApiBaseUrl();
    navigator.sendBeacon(
      `${baseUrl}/chat/cleanup-session`,
      JSON.stringify({ session_id: sessionId })
    );
  },
};

export default api;