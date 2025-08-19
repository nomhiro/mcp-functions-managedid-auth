import React, { useState, useCallback, useEffect } from 'react';
import { AuthService } from '../services/authService';

interface ChatMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

const ChatInterface: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [authService] = useState(() => new AuthService(
    process.env.REACT_APP_FUNCTION_URL || 'http://localhost:7071'
  ));
  const [connectionStatus, setConnectionStatus] = useState<'checking' | 'connected' | 'error'>('checking');
  const [serverInfo, setServerInfo] = useState<any>(null);

  // Check backend connection on component mount
  useEffect(() => {
    const checkConnection = async () => {
      try {
        const healthResult = await authService.callHealthCheck();
        const authResult = await authService.testAuthentication();
        
        setServerInfo({ health: healthResult, auth: authResult });
        setConnectionStatus('connected');
      } catch (error) {
        console.error('Connection check failed:', error);
        setConnectionStatus('error');
      }
    };

    checkConnection();
  }, [authService]);

  const addMessage = useCallback((type: 'user' | 'assistant', content: string) => {
    const newMessage: ChatMessage = {
      id: Date.now().toString(),
      type,
      content,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, newMessage]);
  }, []);

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = inputMessage.trim();
    setInputMessage('');
    setIsLoading(true);

    // Add user message
    addMessage('user', userMessage);

    try {
      // Call MCP function through Azure Functions
      const response = await authService.callMCPFunction(userMessage);
      
      // Add assistant response
      addMessage('assistant', response.content || 'Sorry, I could not process your request.');
    } catch (error) {
      console.error('Error sending message:', error);
      addMessage('assistant', 'Sorry, there was an error processing your request. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto', padding: '20px' }}>
      <div style={{ 
        border: '1px solid #ddd', 
        borderRadius: '8px', 
        height: '500px', 
        overflow: 'auto', 
        padding: '16px',
        marginBottom: '16px',
        backgroundColor: '#f9f9f9'
      }}>
        {/* Connection Status */}
        <div style={{
          padding: '8px 12px',
          borderRadius: '4px',
          marginBottom: '16px',
          backgroundColor: connectionStatus === 'connected' ? '#d4edda' : connectionStatus === 'error' ? '#f8d7da' : '#fff3cd',
          border: `1px solid ${connectionStatus === 'connected' ? '#c3e6cb' : connectionStatus === 'error' ? '#f5c6cb' : '#ffeaa7'}`,
          fontSize: '14px'
        }}>
          <strong>Backend Status:</strong> 
          {connectionStatus === 'checking' && ' Checking connection...'}
          {connectionStatus === 'connected' && ' ✅ Connected'}
          {connectionStatus === 'error' && ' ❌ Connection Error (using mock mode)'}
          {serverInfo && (
            <details style={{ marginTop: '8px' }}>
              <summary style={{ cursor: 'pointer' }}>Server Details</summary>
              <pre style={{ fontSize: '12px', marginTop: '8px', overflow: 'auto' }}>
                {JSON.stringify(serverInfo, null, 2)}
              </pre>
            </details>
          )}
        </div>

        {messages.length === 0 && (
          <div style={{ color: '#666', textAlign: 'center', marginTop: '50px' }}>
            <p>MCP Chat with Azure Functions</p>
            <p>Try asking:</p>
            <ul style={{ textAlign: 'left', display: 'inline-block', marginTop: '16px' }}>
              <li>"What time is it?" (現在時刻取得MCPツール)</li>
              <li>"What's the weather like today?" (天気情報取得MCPツール)</li>
              <li>"現在の時刻を東京時間で教えて"</li>
              <li>"東京の天気はどうですか？"</li>
            </ul>
            <p style={{ fontSize: '12px', marginTop: '16px' }}>ローカル開発時はモック応答が返されます</p>
          </div>
        )}
        
        {messages.map((message) => (
          <div
            key={message.id}
            style={{
              marginBottom: '16px',
              padding: '12px',
              borderRadius: '8px',
              backgroundColor: message.type === 'user' ? '#e3f2fd' : '#f1f8e9',
              marginLeft: message.type === 'user' ? '20%' : '0',
              marginRight: message.type === 'assistant' ? '20%' : '0'
            }}
          >
            <div style={{ 
              fontSize: '12px', 
              color: '#666', 
              marginBottom: '4px',
              fontWeight: 'bold'
            }}>
              {message.type === 'user' ? 'You' : 'Assistant'}
            </div>
            <div style={{ whiteSpace: 'pre-wrap' }}>
              {message.content}
            </div>
            <div style={{ fontSize: '10px', color: '#999', marginTop: '4px' }}>
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div style={{ 
            padding: '12px', 
            color: '#666', 
            fontStyle: 'italic' 
          }}>
            Assistant is thinking...
          </div>
        )}
      </div>

      <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
        <textarea
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message here... (Press Enter to send)"
          disabled={isLoading}
          style={{
            flex: 1,
            padding: '12px',
            borderRadius: '4px',
            border: '1px solid #ddd',
            resize: 'vertical',
            minHeight: '60px'
          }}
        />
        <button
          onClick={handleSendMessage}
          disabled={isLoading || !inputMessage.trim()}
          style={{
            padding: '12px 24px',
            backgroundColor: isLoading ? '#6c757d' : '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: isLoading ? 'not-allowed' : 'pointer'
          }}
        >
          {isLoading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  );
};

export default ChatInterface;