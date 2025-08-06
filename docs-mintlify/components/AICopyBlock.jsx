import React, { useState } from 'react';

export function AICopyBlock({ content, title = "AI Agent Instructions" }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="ai-copy-block" style={{
      position: 'relative',
      marginTop: '2rem',
      marginBottom: '2rem',
      padding: '1.5rem',
      background: 'linear-gradient(135deg, rgba(147, 51, 234, 0.1) 0%, rgba(79, 70, 229, 0.1) 100%)',
      borderRadius: '0.75rem',
      border: '1px solid rgba(147, 51, 234, 0.3)'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1rem'
      }}>
        <h3 style={{
          margin: 0,
          fontSize: '1.125rem',
          fontWeight: '600',
          color: 'var(--text-primary)'
        }}>
          🤖 {title}
        </h3>
        <button
          onClick={handleCopy}
          style={{
            padding: '0.5rem 1rem',
            background: copied ? '#10b981' : '#8b5cf6',
            color: 'white',
            border: 'none',
            borderRadius: '0.5rem',
            fontSize: '0.875rem',
            fontWeight: '500',
            cursor: 'pointer',
            transition: 'all 0.2s'
          }}
        >
          {copied ? '✓ Copied!' : 'Copy for AI'}
        </button>
      </div>
      <p style={{
        margin: 0,
        fontSize: '0.875rem',
        color: 'var(--text-secondary)',
        lineHeight: '1.5'
      }}>
        Click to copy complete implementation instructions that AI agents like Claude can execute directly.
      </p>
    </div>
  );
}