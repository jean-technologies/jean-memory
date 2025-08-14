/**
 * Memory Chat API Route
 * Demonstrates Node.js SDK + OpenAI integration with Jean Memory context
 */
import { JeanClient } from '../../../../sdk/node'
import { OpenAI } from 'openai'

// Initialize clients
const jean = new JeanClient({ 
  apiKey: process.env.JEAN_API_KEY! 
})

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY!
})

export const runtime = 'edge'

export default async function handler(req: Request) {
  if (req.method !== 'POST') {
    return new Response('Method not allowed', { status: 405 })
  }

  try {
    const { messages, userToken } = await req.json()
    const currentMessage = messages[messages.length - 1].content

    // Validate user token
    if (!userToken) {
      return new Response('Unauthorized - User token required', { status: 401 })
    }

    console.log('Getting context from Jean Memory...')
    
    // Get personalized context from Jean Memory
    const contextResponse = await jean.getContext({
      user_token: userToken,
      message: currentMessage,
      speed: 'balanced',    // Options: 'fast', 'balanced', 'comprehensive'  
      tool: 'jean_memory',  // Options: 'jean_memory', 'search_memory'
      format: 'enhanced'    // Options: 'simple', 'enhanced'
    })

    console.log('Context retrieved:', {
      text_length: contextResponse.text.length,
      enhanced: contextResponse.enhanced,
      memories_used: contextResponse.memories_used
    })

    // Engineer the final prompt with context
    const systemPrompt = `You are a helpful AI assistant with access to the user's personal memory and conversation history. 

Use the following context to provide personalized, relevant responses:

CONTEXT:
${contextResponse.text}

Instructions:
- Reference specific details from the user's context when relevant
- Build on previous conversations and shared experiences  
- Be conversational and natural
- If the context is empty or minimal, proceed with a standard helpful response`

    const finalMessages = [
      { role: 'system', content: systemPrompt },
      ...messages.slice(-5), // Keep last 5 messages for immediate context
    ]

    console.log('Calling OpenAI with enhanced context...')

    // Generate response with OpenAI
    const completion = await openai.chat.completions.create({
      model: 'gpt-4-turbo-preview',
      messages: finalMessages as any,
      max_tokens: 1000,
      temperature: 0.7,
      stream: false // For simplicity - can be made streaming later
    })

    const assistantResponse = completion.choices[0].message.content

    console.log('Response generated successfully')

    return Response.json({
      response: assistantResponse,
      context_used: contextResponse.text.length > 0,
      memories_accessed: contextResponse.memories_used,
      context_length: contextResponse.text.length
    })

  } catch (error) {
    console.error('Chat API error:', error)
    
    // Provide helpful error messages
    if (error instanceof Error) {
      if (error.message.includes('API key')) {
        return Response.json({
          error: 'Jean Memory API key invalid or missing',
          details: 'Check your JEAN_API_KEY environment variable'
        }, { status: 401 })
      }
      
      if (error.message.includes('OpenAI')) {
        return Response.json({
          error: 'OpenAI API key invalid or missing', 
          details: 'Check your OPENAI_API_KEY environment variable'
        }, { status: 401 })
      }
      
      if (error.message.includes('MCP')) {
        return Response.json({
          error: 'Jean Memory backend unavailable',
          details: 'The Jean Memory service may be down. Please try again later.'
        }, { status: 503 })
      }
    }

    return Response.json({
      error: 'Internal server error',
      details: error instanceof Error ? error.message : 'Unknown error occurred'
    }, { status: 500 })
  }
}