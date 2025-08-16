import React, { useState } from 'react';

const CopyToClipboard = () => {
  const [buttonText, setButtonText] = useState('Copy All Docs for AI');
  const [isLoading, setIsLoading] = useState(false);

  const copyContent = async () => {
    setIsLoading(true);
    try {
      // Fetch the consolidated documentation from the static file
      const response = await fetch('/static/consolidated-docs.md');
      if (!response.ok) {
        throw new Error('Failed to fetch documentation');
      }
      const consolidatedDocs = await response.text();
      
      await navigator.clipboard.writeText(consolidatedDocs);
      setButtonText('Copied!');
      setTimeout(() => {
        setButtonText('Copy All Docs for AI');
        setIsLoading(false);
      }, 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
      setButtonText('Failed to Copy');
      setTimeout(() => {
        setButtonText('Copy All Docs for AI');
        setIsLoading(false);
      }, 2000);
    }
  };

  return (
    <div className="not-prose my-6">
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg border border-blue-200 dark:border-blue-800 p-6">
        <div className="flex items-start space-x-4">
          <div className="flex-shrink-0">
            <div className="flex items-center justify-center w-10 h-10 bg-blue-100 dark:bg-blue-800 rounded-lg">
              <svg className="w-5 h-5 text-blue-600 dark:text-blue-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              Skip the reading, start building
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
              Don't like reading docs? Copy all our documentation below and paste it into your AI coding tool (Cursor, Claude Code, etc.) with instructions for what you'd like to build.
            </p>
            <button
              onClick={copyContent}
              disabled={isLoading}
              className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
            >
              {isLoading && (
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              )}
              {buttonText}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CopyToClipboard;
