/**
 * Jean Memory React SDK - Next.js Frontend Example
 * Complete chat interface with Jean Memory integration
 */
import { JeanProvider, JeanChat } from '@jeanmemory/react';

export default function Home() {
  return (
    <JeanProvider apiKey={process.env.NEXT_PUBLIC_JEAN_API_KEY!}>
      <div style={{ height: '100vh' }}>
        <JeanChat />
      </div>
    </JeanProvider>
  );
}