"use client";

import { memo } from "react";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/cjs/styles/prism";
import { Button } from "./button";
import { Check, Copy } from "lucide-react";
import { useCopyToClipboard } from "@/hooks/useCopyToClipboard";

interface CodeBlockProps {
  language: string;
  value: string;
}

export const CodeBlock = memo(({ language, value }: CodeBlockProps) => {
  const { isCopied, copyToClipboard } = useCopyToClipboard({ timeout: 2000 });

  const onCopy = () => {
    if (isCopied) return;
    copyToClipboard(value);
  };

  return (
    <div className="relative font-sans text-sm bg-[#1e1e1e] rounded-lg">
      <div className="flex items-center justify-between px-4 py-2 border-b border-gray-700">
        <span className="text-gray-300">{language}</span>
        <Button
            variant="ghost"
            size="icon"
            className="text-gray-300 hover:bg-gray-700 hover:text-white"
            onClick={onCopy}
        >
          {isCopied ? <Check size={16} /> : <Copy size={16} />}
          <span className="sr-only">Copy code</span>
        </Button>
      </div>
      <SyntaxHighlighter
        language={language}
        style={vscDarkPlus}
        customStyle={{
          margin: 0,
          borderRadius: "0 0 0.5rem 0.5rem",
          padding: "1rem",
          backgroundColor: "#1e1e1e",
        }}
        codeTagProps={{
            style: {
                fontFamily: "var(--font-mono)",
            }
        }}
      >
        {value}
      </SyntaxHighlighter>
    </div>
  );
});

CodeBlock.displayName = "CodeBlock";
