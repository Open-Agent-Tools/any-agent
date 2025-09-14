export interface AgentMetadata {
  name: string;
  framework: string;
  model?: string;
  port?: number;
  status?: string;
  description?: string;
}

export interface Message {
  content: string;
  sender: 'user' | 'agent';
  message_type: 'text' | 'system' | 'error';
  timestamp?: string;
}

export interface ChatSession {
  session_id: string;
  messages: Message[];
  created_at?: string;
  updated_at?: string;
}

export interface ApiResponse<T = unknown> {
  success: boolean;
  error?: string;
  data?: T;
}

export interface ChatCreateSessionResponse extends ApiResponse {
  session?: ChatSession;
}

export interface ChatSendMessageResponse extends ApiResponse {
  messages?: Message[];
}

export interface ChatCancelTaskResponse extends ApiResponse {
  message?: string;
  session_id?: string;
  cancel_result?: any;
  system_message?: Message;
  error_message?: Message;
}

export interface ApiEndpoint {
  method: 'GET' | 'POST' | 'PUT' | 'DELETE';
  path: string;
  description: string;
}

export type ConnectionStatus = 'connecting' | 'connected' | 'error' | 'disconnected';

export interface ChatState {
  sessionId: string | null;
  isConnected: boolean;
  messages: Message[];
  status: ConnectionStatus;
  agentMetadata: AgentMetadata | null;
}