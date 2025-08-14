/**
 * Memory Chat App - Production Ready
 * Full-stack application using all three Jean Memory SDKs
 */
import { JeanProvider, JeanChat } from '../../../sdk/react'
import { useState } from 'react'
import { Settings, Github, ExternalLink } from 'lucide-react'

export default function Home() {
  const [showSettings, setShowSettings] = useState(false)
  const API_KEY = process.env.NEXT_PUBLIC_JEAN_API_KEY || 'jean_sk_your_key_here'
  
  return (
    <div className="h-screen w-screen bg-gray-50 dark:bg-gray-900 flex flex-col">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <span className="text-white font-bold text-sm">JM</span>
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900 dark:text-white">
                Memory Chat
              </h1>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                AI with persistent memory across all your conversations
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-3">
            <a 
              href="https://docs.jean-memory.com" 
              target="_blank"
              className="inline-flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              <ExternalLink size={16} />
              Docs
            </a>
            <a 
              href="https://github.com/jean-technologies/jean-memory" 
              target="_blank"
              className="inline-flex items-center gap-2 px-3 py-1.5 text-sm text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              <Github size={16} />
              GitHub
            </a>
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
            >
              <Settings size={18} />
            </button>
          </div>
        </div>
      </header>

      {/* Settings Panel */}
      {showSettings && (
        <div className="bg-yellow-50 dark:bg-yellow-900/20 border-b border-yellow-200 dark:border-yellow-700 px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 rounded-full bg-yellow-400"></div>
              <span className="text-sm text-yellow-800 dark:text-yellow-200">
                API Key: {API_KEY.substring(0, 12)}...
                {API_KEY === 'jean_sk_your_key_here' ? ' (Demo Mode)' : ' (Connected)'}
              </span>
            </div>
            <button
              onClick={() => setShowSettings(false)}
              className="text-yellow-600 dark:text-yellow-400 hover:text-yellow-800 dark:hover:text-yellow-200"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Main Chat Interface */}
      <div className="flex-1 overflow-hidden">
        <JeanProvider apiKey={API_KEY}>
          <JeanChat className="h-full" />
        </JeanProvider>
      </div>

      {/* Footer */}
      <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 px-6 py-3">
        <div className="flex justify-between items-center text-sm text-gray-500 dark:text-gray-400">
          <div>
            Powered by{' '}
            <a href="https://jean-memory.com" className="font-medium text-blue-600 dark:text-blue-400 hover:underline">
              Jean Memory
            </a>{' '}
            • This conversation is remembered across all your apps
          </div>
          <div className="flex items-center space-x-4">
            <span>React SDK v1.0.0</span>
            <span>•</span>
            <span>Node.js API</span>
          </div>
        </div>
      </footer>
    </div>
  )
}