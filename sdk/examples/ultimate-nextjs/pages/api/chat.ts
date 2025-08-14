/**
 * Jean Memory Node.js SDK - Next.js API Route Example
 * Shows how to create a context-aware API endpoint
 */
import { JeanClient } from '@jeanmemory/node';
import { OpenAIStream, StreamingTextResponse } from 'ai';
import OpenAI from 'openai';

// Create the clients
const jean = new JeanClient({ apiKey: process.env.JEAN_API_KEY! });
const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY! });

// Set the runtime to edge for best performance
export const runtime = 'edge';

export default async function POST(req: Request) {
  // 1. Get the user's message and token from the request body
  const { messages, userToken } = await req.json();
  const currentMessage = messages[messages.length - 1].content;

  // Ensure the user token is present
  if (!userToken) {
    return new Response('Unauthorized', { status: 401 });
  }

  // 2. Get context from Jean Memory
  const contextResponse = await jean.getContext({
    user_token: userToken,
    message: currentMessage
  });

  // 3. Engineer your final prompt
  const finalPrompt = `
    Using the following context, please answer the user's question.
    The context is a summary of the user's memories related to their question.

    Context:
    ---
    ${contextResponse.text}
    ---

    User Question: ${currentMessage}
  `;
  
  // 4. Call your LLM and stream the response
  const response = await openai.chat.completions.create({
    model: 'gpt-4-turbo',
    stream: true,
    messages: [
      { role: "system", content: "You are a helpful assistant." },
      { role: "user", content: finalPrompt },
    ],
  });

  const stream = OpenAIStream(response);
  return new StreamingTextResponse(stream);
}