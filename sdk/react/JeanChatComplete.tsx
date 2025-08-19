/**
 * Jean Memory React SDK - Complete Chat Component
 * Drop-in chat interface with authentication, input, and messages
 */
import React, { useState } from 'react';
import { useJean } from './provider';
import { JeanAuthGuard } from './JeanAuthGuard';

interface JeanChatCompleteProps {
  /** Custom styles for the chat container */
  style?: React.CSSProperties;
  /** Custom CSS class for the chat container */
  className?: string;
  /** Placeholder text for the input field */
  placeholder?: string;
  /** Welcome message to show when chat is empty */
  welcomeMessage?: string;
  /** Example prompts to show users */
  examplePrompts?: string[];
  /** Show example prompts (default: true) */
  showExamples?: boolean;
  /** Show sign-out button (default: true) */
  showSignOut?: boolean;
  /** Custom header content */
  header?: React.ReactNode;
  /** Height of the chat area (default: 400px) */
  chatHeight?: number;
}

/**
 * Complete chat component with authentication guard
 * Handles everything: auth, input, messages, sign out
 * 
 * @example
 * ```jsx
 * <JeanProvider apiKey="your-key">
 *   <JeanChatComplete />
 * </JeanProvider>
 * ```
 */
export function JeanChatComplete({
  style,
  className,
  placeholder = "Ask Jean anything...",
  welcomeMessage = "Start a conversation! I remember everything we discuss.",
  examplePrompts = [
    "What did I work on recently?",
    "Remember that I prefer TypeScript",
    "What are my current projects?",
    "Help me plan my week"
  ],
  showExamples = true,
  showSignOut = true,
  header,
  chatHeight = 400
}: JeanChatCompleteProps) {
  return (
    <JeanAuthGuard>
      <JeanChatInterface
        style={style}
        className={className}
        placeholder={placeholder}
        welcomeMessage={welcomeMessage}
        examplePrompts={examplePrompts}
        showExamples={showExamples}
        showSignOut={showSignOut}
        header={header}
        chatHeight={chatHeight}
      />
    </JeanAuthGuard>
  );
}

/**
 * Internal chat interface (assumes user is authenticated)
 */
function JeanChatInterface({
  style,
  className,
  placeholder,
  welcomeMessage,
  examplePrompts,
  showExamples,
  showSignOut,
  header,
  chatHeight
}: JeanChatCompleteProps) {
  const { sendMessage, messages, isLoading, user, signOut } = useJean();
  const [input, setInput] = useState('');

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;
    
    try {
      await sendMessage(input);
      setInput('');
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const defaultStyles = {
    container: {
      maxWidth: '800px',
      margin: '0 auto',
      padding: '20px',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      ...style
    },
    header: {
      display: 'flex' as const,
      justifyContent: 'space-between' as const,
      alignItems: 'center' as const,
      marginBottom: '20px',
      paddingBottom: '16px',
      borderBottom: '1px solid #e5e5e5'
    },
    title: {
      margin: 0,
      fontSize: '24px',
      fontWeight: 'bold' as const,
      color: '#333'
    },
    userInfo: {
      fontSize: '14px',
      color: '#666'
    },
    signOutButton: {
      padding: '8px 16px',
      backgroundColor: '#dc3545',
      color: 'white',
      border: 'none',
      borderRadius: '6px',
      cursor: 'pointer' as const,
      fontSize: '14px'
    },
    chatArea: {
      height: `${chatHeight}px`,
      border: '1px solid #ddd',
      borderRadius: '8px',
      padding: '16px',
      marginBottom: '16px',
      overflowY: 'auto' as const,
      backgroundColor: '#f9f9f9'
    },
    welcomeText: {
      color: '#666',
      textAlign: 'center' as const,
      marginTop: '50px',
      fontSize: '16px'
    },
    message: {
      marginBottom: '12px',
      padding: '12px 16px',
      borderRadius: '8px',
      lineHeight: '1.4'
    },
    userMessage: {
      backgroundColor: '#007bff',
      color: 'white',
      marginLeft: '20%',
      marginRight: '0'
    },
    assistantMessage: {
      backgroundColor: '#fff',
      color: 'black',
      marginLeft: '0',
      marginRight: '20%',
      border: '1px solid #e5e5e5'
    },
    inputContainer: {
      display: 'flex' as const,
      gap: '8px',
      marginBottom: '16px'
    },
    input: {
      flex: 1,
      padding: '12px',
      border: '1px solid #ddd',
      borderRadius: '6px',
      fontSize: '16px',
      outline: 'none' as const
    },
    sendButton: {
      padding: '12px 24px',
      backgroundColor: '#007bff',
      color: 'white',
      border: 'none',
      borderRadius: '6px',
      cursor: 'pointer' as const,
      fontSize: '16px'
    },
    examplesContainer: {
      textAlign: 'center' as const
    },
    examplesTitle: {
      fontSize: '16px',
      fontWeight: 'bold' as const,
      marginBottom: '12px',
      color: '#333'
    },
    exampleButtons: {
      display: 'flex' as const,
      gap: '8px',
      flexWrap: 'wrap' as const,
      justifyContent: 'center' as const
    },
    exampleButton: {
      padding: '8px 16px',
      backgroundColor: '#f8f9fa',
      border: '1px solid #ddd',
      borderRadius: '6px',
      cursor: 'pointer' as const,
      fontSize: '14px',
      transition: 'background-color 0.2s'
    }
  };

  return (
    <div style={defaultStyles.container} className={className}>
      {/* Header */}
      <div style={defaultStyles.header}>
        <div>
          {header || (
            <>
              <h1 style={defaultStyles.title}>🧠 Jean Memory</h1>
              <div style={defaultStyles.userInfo}>
                Welcome back, <strong>{user?.name || user?.email}</strong>
              </div>
            </>
          )}
        </div>
        {showSignOut && (
          <button
            onClick={signOut}
            style={defaultStyles.signOutButton}
            title="Sign out"
          >
            Sign Out
          </button>
        )}
      </div>

      {/* Chat Area */}
      <div style={defaultStyles.chatArea}>
        {messages.length === 0 ? (
          <div style={defaultStyles.welcomeText}>
            {welcomeMessage}
          </div>
        ) : (
          messages.map((message, index) => (
            <div
              key={message.id || index}
              style={{
                ...defaultStyles.message,
                ...(message.role === 'user' 
                  ? defaultStyles.userMessage 
                  : defaultStyles.assistantMessage
                )
              }}
            >
              <strong>{message.role === 'user' ? 'You' : 'Jean'}:</strong>{' '}
              {message.content}
            </div>
          ))
        )}
        {isLoading && (
          <div style={{ textAlign: 'center', color: '#666', fontStyle: 'italic' }}>
            Jean is thinking...
          </div>
        )}
      </div>

      {/* Input Area */}
      <div style={defaultStyles.inputContainer}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          style={defaultStyles.input}
          disabled={isLoading}
        />
        <button
          onClick={handleSend}
          disabled={isLoading || !input.trim()}
          style={{
            ...defaultStyles.sendButton,
            opacity: (isLoading || !input.trim()) ? 0.6 : 1
          }}
        >
          Send
        </button>
      </div>

      {/* Example Prompts */}
      {showExamples && examplePrompts && examplePrompts.length > 0 && (
        <div style={defaultStyles.examplesContainer}>
          <div style={defaultStyles.examplesTitle}>Try these examples:</div>
          <div style={defaultStyles.exampleButtons}>
            {examplePrompts.map((example, index) => (
              <button
                key={index}
                onClick={() => setInput(example)}
                style={defaultStyles.exampleButton}
                onMouseEnter={(e) => {
                  e.currentTarget.style.backgroundColor = '#e9ecef';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#f8f9fa';
                }}
              >
                {example}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}