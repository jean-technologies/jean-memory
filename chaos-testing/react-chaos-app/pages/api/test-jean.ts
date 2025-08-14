import { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' })
  }

  try {
    const { message, userToken, isNewConversation } = req.body

    // Import and use Node.js SDK
    const { JeanClient } = require('../../../../sdk/node/dist/index.js')
    const client = new JeanClient({ 
      apiKey: 'jean_sk_f3LqQ_2KMDLlD681e7cTEHAhMyhDXdbvct-cZR6Ryrk' 
    })

    const response = await client.getContext({
      user_token: userToken || 'mock_jwt_token',
      message: message,
      is_new_conversation: isNewConversation || false
    })

    return res.json({
      success: true,
      text: response.text,
      enhanced: response.enhanced,
      memories_used: response.memories_used
    })

  } catch (error) {
    console.error('Jean API error:', error)
    return res.status(500).json({ 
      error: error.message || 'Internal server error',
      success: false 
    })
  }
}