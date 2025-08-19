import React from 'react';
import ChatInterface from './components/ChatInterface';

function App() {
  return (
    <div className="App">
      <header style={{ 
        backgroundColor: '#f8f9fa', 
        padding: '20px', 
        textAlign: 'center',
        borderBottom: '1px solid #dee2e6'
      }}>
        <h1>Azure Functions MCP Chat</h1>
        <p>Chat interface with Managed ID authentication</p>
      </header>
      <main style={{ padding: '20px' }}>
        <ChatInterface />
      </main>
    </div>
  );
}

export default App;