import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  useTheme,
  useMediaQuery,
} from '@mui/material';
import { Circle as CircleIcon, Send as SendIcon, Cancel as CancelIcon } from '@mui/icons-material';
import { Message, ChatState, ConnectionStatus, AgentMetadata } from '@/types';
import { api } from '@/utils/api';
import { formatMessageContent, generateSessionId, formatTimestamp, testUrlLinkification } from '@/utils/messageFormatter';
import LoadingIndicator from '@/components/LoadingIndicator';
import ThinkingDots from '@/components/ThinkingDots';

interface ChatPageProps {
  agentMetadata: AgentMetadata | null;
  onAgentMetadataUpdate?: (metadata: AgentMetadata) => void;
}

/**
 * ChatPage component with enhanced message rendering
 * 
 * Features:
 * - Auto-detects URLs in chat messages and makes them clickable
 * - Links open in new tabs with proper security attributes (rel="noopener noreferrer")
 * - Responsive styling that adapts to user vs agent message contexts
 * - Accessibility support with ARIA labels and keyboard navigation
 * - Handles edge cases like URLs with punctuation, parentheses, and complex parameters
 */

const ChatPage: React.FC<ChatPageProps> = ({ agentMetadata }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  
  const [chatState, setChatState] = useState<ChatState>({
    sessionId: null,
    isConnected: false,
    messages: [],
    status: 'connecting',
    agentMetadata: null,
  });
  
  const [messageInput, setMessageInput] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [isThinking, setIsThinking] = useState<boolean>(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [canCancel, setCanCancel] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  const addMessage = useCallback((message: Message) => {
    setChatState(prev => ({
      ...prev,
      messages: [...prev.messages, message],
    }));
    setTimeout(scrollToBottom, 100);
  }, [scrollToBottom]);

  const addThinkingIndicator = useCallback(() => {
    console.log('Adding thinking indicator');
    setIsThinking(true);
    setTimeout(scrollToBottom, 100);
  }, [scrollToBottom]);

  const removeThinkingIndicator = useCallback(() => {
    console.log('Removing thinking indicator');
    setIsThinking(false);
  }, []);

  const updateConnectionStatus = useCallback((status: ConnectionStatus, sessionId?: string) => {
    setChatState(prev => ({
      ...prev,
      status,
      isConnected: status === 'connected',
      ...(sessionId && { sessionId }),
    }));
  }, []);

  const initializeChat = useCallback(async () => {
    try {
      console.log('Starting chat initialization...');
      updateConnectionStatus('connecting');
      
      // Generate session ID
      const newSessionId = generateSessionId();
      console.log('Sending session creation request...', { session_id: newSessionId });
      
      const response = await api.createChatSession(newSessionId);
      console.log('Session creation result:', response);
      
      if (response.success) {
        updateConnectionStatus('connected', newSessionId);
        
        // Load session messages if any
        if (response.session && response.session.messages) {
          setChatState(prev => ({
            ...prev,
            messages: response.session!.messages,
          }));
        }
        // No automatic welcome message - just start with empty chat
      } else {
        throw new Error(response.error || 'Failed to create session');
      }
      
    } catch (error) {
      console.error('Chat initialization failed:', error);
      updateConnectionStatus('error');
      addMessage({
        content: `Connection error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        sender: 'agent',
        message_type: 'error',
        timestamp: formatTimestamp(),
      });
      
      // Keep trying to reconnect every 5 seconds
      setTimeout(initializeChat, 5000);
    }
  }, [updateConnectionStatus, addMessage]);

  const sendMessage = useCallback(async () => {
    const message = messageInput.trim();
    if (!message || !chatState.isConnected || !chatState.sessionId) return;
    
    // Add user message to chat
    addMessage({
      content: message,
      sender: 'user',
      message_type: 'text',
      timestamp: formatTimestamp(),
    });
    
    // Clear input and disable send
    setMessageInput('');
    setIsSending(true);
    setCanCancel(true); // Enable cancel button when task starts
    
    // Show thinking indicator
    addThinkingIndicator();
    
    try {
      const response = await api.sendMessage(chatState.sessionId, message);
      
      // Remove thinking indicator before adding response
      removeThinkingIndicator();
      
      if (response.success && response.messages) {
        // Add agent responses
        response.messages.forEach(msg => {
          addMessage({
            ...msg,
            timestamp: formatTimestamp(),
          });
        });
      } else {
        addMessage({
          content: `Error: ${response.error || 'Unknown error'}`,
          sender: 'agent',
          message_type: 'error',
          timestamp: formatTimestamp(),
        });
      }
      
    } catch (error) {
      // Remove thinking indicator on error too
      removeThinkingIndicator();
      addMessage({
        content: `Connection error: ${error instanceof Error ? error.message : 'Unknown error'}`,
        sender: 'agent',
        message_type: 'error',
        timestamp: formatTimestamp(),
      });
    } finally {
      setIsSending(false);
      // Keep cancel button visible for minimum 2 seconds to allow user interaction
      setTimeout(() => setCanCancel(false), 2000);
      inputRef.current?.focus();
    }
  }, [messageInput, chatState.isConnected, chatState.sessionId, addMessage, addThinkingIndicator, removeThinkingIndicator]);

  const cancelTask = useCallback(async () => {
    if (!chatState.sessionId || !canCancel) return;
    
    setIsCancelling(true);
    
    try {
      const response = await api.cancelTask(chatState.sessionId);
      
      if (response.success) {
        // Remove thinking indicator
        removeThinkingIndicator();
        
        // Add cancellation message if provided
        if (response.system_message) {
          addMessage({
            ...response.system_message,
            timestamp: formatTimestamp(),
          });
        }
        
        // Update state - immediately hide cancel button when cancelled successfully
        setIsSending(false);
        setCanCancel(false);
        
        addMessage({
          content: response.message || 'Task cancelled successfully',
          sender: 'agent',
          message_type: 'system',
          timestamp: formatTimestamp(),
        });
      } else {
        // Add error message if provided
        if (response.error_message) {
          addMessage({
            ...response.error_message,
            timestamp: formatTimestamp(),
          });
        } else {
          addMessage({
            content: `Failed to cancel task: ${response.error || 'Unknown error'}`,
            sender: 'agent',
            message_type: 'error',
            timestamp: formatTimestamp(),
          });
        }
      }
      
    } catch (error) {
      addMessage({
        content: `Error cancelling task: ${error instanceof Error ? error.message : 'Unknown error'}`,
        sender: 'agent',
        message_type: 'error',
        timestamp: formatTimestamp(),
      });
    } finally {
      setIsCancelling(false);
    }
  }, [chatState.sessionId, canCancel, addMessage, removeThinkingIndicator]);

  const startNewChat = useCallback(async () => {
    // Cleanup current session
    if (chatState.sessionId) {
      try {
        await api.cleanupSession(chatState.sessionId);
      } catch (error) {
        console.warn('Failed to cleanup session:', error);
      }
    }
    
    // Reset all states
    setChatState(prev => ({
      ...prev,
      sessionId: null,
      isConnected: false,
      messages: [],
      status: 'connecting',
    }));
    setMessageInput('');
    setIsSending(false);
    setIsThinking(false);
    setIsCancelling(false);
    setCanCancel(false);
    
    // Initialize new session
    await initializeChat();
  }, [chatState.sessionId, initializeChat]);

  // Initialize chat on mount
  useEffect(() => {
    // Test URL linkification in development
    testUrlLinkification();
    
    initializeChat();
    
    return () => {
      if (chatState.sessionId) {
        api.cleanupSessionBeacon(chatState.sessionId);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Handle Enter key
  const handleKeyPress = useCallback((event: React.KeyboardEvent) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  }, [sendMessage]);

  const getStatusInfo = () => {
    switch (chatState.status) {
      case 'connecting':
        return {
          text: 'Connecting to agent...',
          color: 'warning' as const,
          icon: <LoadingIndicator message="" size={12} />,
        };
      case 'connected':
        return {
          text: `Connected to ${agentMetadata?.name || 'Agent'}`,
          color: 'success' as const,
          icon: <CircleIcon sx={{ fontSize: 12, color: 'success.main' }} />,
        };
      case 'error':
        return {
          text: 'Connection failed',
          color: 'error' as const,
          icon: <CircleIcon sx={{ fontSize: 12, color: 'error.main' }} />,
        };
      default:
        return {
          text: 'Disconnected',
          color: 'default' as const,
          icon: <CircleIcon sx={{ fontSize: 12, color: 'grey.500' }} />,
        };
    }
  };

  const statusInfo = getStatusInfo();

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: 'calc(100vh - 110px)',
        p: { xs: 1, sm: 1.5 },
        mt: { xs: 6, sm: 7 },
        mb: { xs: 6, sm: 7 },
      }}
    >
      <Paper
        elevation={2}
        sx={{
          display: 'flex',
          flexDirection: 'column',
          width: { xs: '98%', md: '75%' },
          maxWidth: '1200px',
          minWidth: { xs: '300px', sm: '500px' },
          height: { xs: 'calc(100vh - 140px)', md: 'calc(100vh - 120px)' },
          maxHeight: 'calc(100vh - 120px)',
          overflow: 'hidden',
          border: `1px solid ${theme.palette.divider}`,
        }}
      >
        {/* Chat Header */}
        <Box
          sx={{
            backgroundColor: theme.palette.info.light,
            borderBottom: `1px solid ${theme.palette.divider}`,
            p: { xs: 1.5, sm: 2 },
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexShrink: 0,
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {statusInfo.icon}
            <Box>
              <Typography
                variant="body2"
                sx={{
                  fontWeight: 500,
                  color: 'text.primary',
                  fontSize: '0.9rem',
                }}
              >
                {statusInfo.text}
              </Typography>
              {chatState.sessionId && chatState.isConnected && (
                <Typography
                  variant="caption"
                  sx={{
                    fontSize: '0.75rem',
                    color: 'text.secondary',
                    fontFamily: '"Roboto Mono", monospace',
                    display: 'block',
                  }}
                >
                  Session: {chatState.sessionId}
                </Typography>
              )}
            </Box>
          </Box>
          
          <Button
            variant="contained"
            color="secondary"
            size="small"
            onClick={startNewChat}
            disabled={!chatState.isConnected}
            sx={{
              textTransform: 'none',
              fontWeight: 500,
            }}
          >
            New
          </Button>
        </Box>

        {/* Messages Area */}
        <Box
          sx={{
            flex: 1,
            p: { xs: 1.5, sm: 2 },
            overflowY: 'auto',
            overflowX: 'hidden',
            borderBottom: `1px solid ${theme.palette.divider}`,
            minHeight: '200px',
            '&::-webkit-scrollbar': {
              width: 6,
            },
            '&::-webkit-scrollbar-track': {
              background: theme.palette.grey[100],
              borderRadius: 2,
            },
            '&::-webkit-scrollbar-thumb': {
              background: theme.palette.grey[400],
              borderRadius: 2,
              '&:hover': {
                background: theme.palette.grey[600],
              },
            },
          }}
        >
          {chatState.messages.map((message, index) => (
            <Box
              key={index}
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: message.sender === 'user' ? 'flex-end' : 'flex-start',
                mb: 2,
                maxWidth: '88%',
                ...(message.sender === 'user' && { ml: 'auto' }),
              }}
            >
              <Paper
                elevation={0}
                sx={{
                  p: 1.5,
                  borderRadius: 2,
                  fontSize: '0.9rem',
                  lineHeight: 1.4,
                  whiteSpace: 'pre-wrap',
                  wordWrap: 'break-word',
                  ...(message.sender === 'user' ? {
                    backgroundColor: theme.palette.primary.main,
                    color: theme.palette.primary.contrastText,
                  } : {
                    backgroundColor: message.message_type === 'error' 
                      ? theme.palette.error.light
                      : message.message_type === 'system'
                      ? theme.palette.info.light
                      : theme.palette.grey[100],
                    color: message.message_type === 'error'
                      ? theme.palette.error.main
                      : message.message_type === 'system'
                      ? theme.palette.info.main
                      : theme.palette.text.primary,
                    ...(message.message_type === 'error' && {
                      borderLeft: `4px solid ${theme.palette.error.main}`,
                    }),
                    ...(message.message_type === 'system' && {
                      borderLeft: `4px solid ${theme.palette.info.main}`,
                    }),
                  }),
                }}
              >
                {message.message_type === 'text' || message.message_type === 'system' ? (
                  <Box
                    dangerouslySetInnerHTML={{
                      __html: formatMessageContent(message.content),
                    }}
                    sx={{
                      '& ul, & ol': {
                        my: 1,
                        pl: 3,
                      },
                      '& li': {
                        mb: 0.5,
                      },
                      '& code': {
                        backgroundColor: 'rgba(0, 0, 0, 0.1)',
                        px: 0.5,
                        py: 0.25,
                        borderRadius: 0.5,
                        fontFamily: '"Roboto Mono", monospace',
                        fontSize: '0.85em',
                      },
                      '& pre': {
                        backgroundColor: 'rgba(0, 0, 0, 0.05)',
                        p: 1,
                        borderRadius: 1,
                        overflow: 'auto',
                        my: 1,
                        '& code': {
                          backgroundColor: 'transparent',
                          p: 0,
                        },
                      },
                      '& p': {
                        mb: 1,
                        '&:last-child': {
                          mb: 0,
                        },
                      },
                      // Styling for clickable links
                      '& a.message-link': {
                        color: message.sender === 'user' 
                          ? theme.palette.primary.contrastText
                          : theme.palette.primary.main,
                        textDecoration: 'underline',
                        textDecorationColor: message.sender === 'user' 
                          ? 'rgba(255, 255, 255, 0.7)'
                          : theme.palette.primary.main,
                        fontWeight: 500,
                        cursor: 'pointer',
                        wordBreak: 'break-all',
                        transition: 'all 0.2s ease-in-out',
                        '&:hover': {
                          textDecorationThickness: '2px',
                          filter: message.sender === 'user' 
                            ? 'brightness(0.9)'
                            : 'brightness(1.1)',
                        },
                        '&:focus': {
                          outline: `2px solid ${theme.palette.primary.main}`,
                          outlineOffset: '2px',
                          borderRadius: '2px',
                        },
                        '&:focus-visible': {
                          outline: `2px solid ${theme.palette.primary.main}`,
                          outlineOffset: '2px',
                          borderRadius: '2px',
                        },
                      },
                    }}
                  />
                ) : (
                  <Typography component="span">
                    {message.content}
                  </Typography>
                )}
              </Paper>
              
              {message.timestamp && (
                <Typography
                  variant="caption"
                  sx={{
                    mt: 0.5,
                    fontSize: '0.75rem',
                    color: 'text.secondary',
                    fontFamily: '"Roboto Mono", monospace',
                  }}
                >
                  {message.timestamp}
                </Typography>
              )}
            </Box>
          ))}
          
          {/* Thinking indicator */}
          {isThinking && (
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'flex-start',
                mb: 2,
                maxWidth: '88%',
              }}
            >
              <Paper
                elevation={0}
                sx={{
                  p: 1.5,
                  borderRadius: 2,
                  fontSize: '0.9rem',
                  lineHeight: 1.4,
                  backgroundColor: theme.palette.grey[100],
                  color: theme.palette.text.primary,
                }}
              >
                <ThinkingDots />
              </Paper>
            </Box>
          )}
          
          <div ref={messagesEndRef} />
        </Box>

        {/* Input Area */}
        <Box
          sx={{
            display: 'flex',
            p: { xs: 1.5, sm: 2 },
            backgroundColor: 'background.paper',
            gap: 1,
            flexShrink: 0,
          }}
        >
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Ask me anything..."
            value={messageInput}
            onChange={(e) => setMessageInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={!chatState.isConnected || isSending}
            inputRef={inputRef}
            size="small"
            sx={{
              '& .MuiOutlinedInput-root': {
                backgroundColor: 'background.paper',
              },
            }}
          />
          
          {/* Cancel Button - only show when task is active and can be cancelled */}
          {canCancel && (
            <Button
              variant="outlined"
              color="warning"
              onClick={cancelTask}
              disabled={isCancelling || !chatState.isConnected}
              sx={{
                minWidth: { xs: 40, sm: 80 },
                textTransform: 'none',
                fontWeight: 500,
                borderColor: theme.palette.warning.main,
                '&:hover': {
                  borderColor: theme.palette.warning.dark,
                  backgroundColor: 'rgba(255, 152, 0, 0.04)',
                },
              }}
              startIcon={!isMobile ? <CancelIcon /> : undefined}
              aria-label="Cancel current task"
            >
              {isMobile ? <CancelIcon /> : (isCancelling ? 'Cancelling...' : 'Cancel')}
            </Button>
          )}
          
          <Button
            variant="contained"
            color="primary"
            onClick={sendMessage}
            disabled={!chatState.isConnected || isSending || !messageInput.trim()}
            sx={{
              minWidth: { xs: 40, sm: 80 },
              textTransform: 'none',
              fontWeight: 500,
            }}
            startIcon={!isMobile ? <SendIcon /> : undefined}
          >
            {isMobile ? <SendIcon /> : (isSending ? 'Sending...' : 'Send')}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default ChatPage;