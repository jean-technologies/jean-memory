/**
 * Ultimate 5-Line Jean Memory Integration - Next.js Frontend
 * Complete chat interface with Jean Memory integration
 */
import { SignInWithJean, useJeanChat } from 'jeanmemory-react';

export default function Home() {
  const { messages, sendMessage, signIn, isAuthenticated } = useJeanChat({
    endpoint: '/api/chat'
  });

  if (!isAuthenticated) return <SignInWithJean onSuccess={signIn} />;
  return <ChatInterface messages={messages} onSend={sendMessage} />;
}