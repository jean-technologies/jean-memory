/**
 * JeanChat.tsx: A simple, production-ready chat component for Jean Memory
 */
import React, { useState } from 'react';
import type { JeanAgent } from '../useJean';

interface JeanChatProps {
  agent: JeanAgent;
  className?: string;
  style?: React.CSSProperties;
}

export const JeanChat: React.FC<JeanChatProps> = ({ agent, className, style }) => {
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const newMessages = [...messages, { role: 'user', content: input }];
    setMessages(newMessages);
    setInput('');
    setIsLoading(true);

    try {
      const response = await agent.sendMessage(input);
      setMessages([...newMessages, { role: 'assistant', content: response }]);
    } catch (error) {
      setMessages([
        ...newMessages,
        { role: 'assistant', content: 'Sorry, I encountered an error.' },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={className} style={style}>
      <div style={{ height: '400px', overflowY: 'auto', border: '1px solid #ccc', padding: '10px', marginBottom: '10px' }}>
        {messages.map((msg, index) => (
          <div key={index} style={{ textAlign: msg.role === 'user' ? 'right' : 'left' }}>
            <p><strong>{msg.role}:</strong> {msg.content}</p>
          </div>
        ))}
        {isLoading && <p>Thinking...</p>}
      </div>
      <div style={{ display: 'flex' }}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          style={{ flexGrow: 1, padding: '5px' }}
        />
        <button onClick={handleSendMessage} style={{ marginLeft: '5px' }}>Send</button>
      </div>
    </div>
  );
};
