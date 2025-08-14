/**
 * Jean Memory React SDK - Ultimate Example
 * Complete AI chatbot with personalized memory
 */
import { JeanProvider, JeanChat } from '@jeanmemory/react';

function MathTutorApp() {
  return (
    <JeanProvider apiKey={process.env.REACT_APP_JEAN_API_KEY!}>
      <JeanChat />
    </JeanProvider>
  );
}

export default MathTutorApp;