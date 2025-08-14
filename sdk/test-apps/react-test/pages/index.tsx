/**
 * Jean Memory React SDK Test App
 * Tests the 5-line integration promise
 */
import { JeanProvider, JeanChat } from '../../../react'

export default function Home() {
  // This should be your actual API key for testing
  const API_KEY = process.env.NEXT_PUBLIC_JEAN_API_KEY || 'jean_sk_test_key_here'
  
  return (
    <div className="h-screen w-screen">
      <JeanProvider apiKey={API_KEY}>
        <div className="h-full flex flex-col">
          {/* Header */}
          <div className="bg-white border-b border-gray-200 p-4">
            <h1 className="text-2xl font-bold text-gray-900">
              Jean Memory React SDK Test
            </h1>
            <p className="text-gray-600">
              Testing the 5-line integration: JeanProvider + JeanChat
            </p>
          </div>
          
          {/* Chat Interface */}
          <div className="flex-1">
            <JeanChat />
          </div>
        </div>
      </JeanProvider>
    </div>
  )
}