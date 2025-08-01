/**
 * Ultimate 5-Line Jean Memory Integration - Next.js API Route
 * Backend endpoint with Jean Memory context enhancement
 */
import { createJeanHandler } from '@jeanmemory/node';

export default createJeanHandler({
  apiKey: process.env.JEAN_API_KEY,
  systemPrompt: "You are an AI writing coach with access to user's writing history"
});