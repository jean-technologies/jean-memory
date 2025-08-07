import React, { useState } from 'react';
import { Button } from 'mintlify/components';

const CopyToClipboard = () => {
  const [buttonText, setButtonText] = useState('Copy All Docs to Clipboard');

  const copyContent = async () => {
    try {
      const response = await fetch('/assets/consolidated-docs.md');
      const text = await response.text();
      await navigator.clipboard.writeText(text);
      setButtonText('Copied!');
      setTimeout(() => setButtonText('Copy All Docs to Clipboard'), 2000);
    } catch (err) {
      console.error('Failed to copy text: ', err);
      setButtonText('Failed to Copy');
      setTimeout(() => setButtonText('Copy All Docs to Clipboard'), 2000);
    }
  };

  return (
    <Button
      onClick={copyContent}
    >
      {buttonText}
    </Button>
  );
};

export default CopyToClipboard;
