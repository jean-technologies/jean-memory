/**
 * Ultimate 5-Line Jean Memory Integration - React Example
 * Complete AI chatbot with personalized memory in 5 lines
 */
import { SignInWithJean, JeanChat, useJeanAgent } from 'jeanmemory-react';

function MathTutorApp() {
  const { agent, signIn } = useJeanAgent({
    systemPrompt: "You are a patient math tutor who explains concepts step by step"
  });

  if (!agent) return <SignInWithJean onSuccess={signIn} />;
  return <JeanChat agent={agent} />; // Powered by Assistant-UI
}

export default MathTutorApp;