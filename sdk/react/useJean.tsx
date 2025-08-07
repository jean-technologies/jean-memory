/**
 * useJean.tsx: The primary React hook for interacting with Jean Memory
 *
 * This hook is the main entry point for the Jean Memory React SDK. It provides
 * a clean, easy-to-use interface for managing the user's authentication state,
 * sending messages to the Jean Memory API, and handling the responses.
 */
import { useState, useCallback } from 'react';

const JEAN_API_BASE = 'https://jean-memory-api-virginia.onrender.com';

export interface JeanUser {
  user_id: string;
  email: string;
  access_token: string;
}

export interface JeanAgent {
  user: JeanUser;
  sendMessage: (message: string) => Promise<string>;
}

interface UseJeanProps {
  user: JeanUser | null;
}

export const useJean = ({ user }: UseJeanProps) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(
    async (message: string) => {
      if (!user) {
        throw new Error('User is not authenticated.');
      }

      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(`${JEAN_API_BASE}/mcp/claude/messages/${user.user_id}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${user.access_token}`,
          },
          body: JSON.stringify({
            jsonrpc: '2.0',
            id: Date.now(),
            method: 'tools/call',
            params: {
              name: 'jean_memory',
              arguments: {
                user_message: message,
                is_new_conversation: true, // This should be managed in state
                needs_context: true,
              },
            },
          }),
        });

        if (!response.ok) {
          throw new Error('Failed to send message.');
        }

        const data = await response.json();
        return data.result.content[0].text;
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'An unknown error occurred';
        setError(errorMessage);
        throw new Error(errorMessage);
      } finally {
        setIsLoading(false);
      }
    },
    [user]
  );

  const agent: JeanAgent | null = user
    ? {
        user,
        sendMessage,
      }
    : null;

  return { agent, isLoading, error };
};
