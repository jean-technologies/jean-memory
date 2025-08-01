"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { materialLight } from "react-syntax-highlighter/dist/esm/styles/prism";

const codeSnippets = [
  {
    lang: "jsx",
    title: "React Chat App",
    code: `import { JeanChat, useJeanAgent } from '@jeanmemory/react';

function MathTutorApp() {
  const { agent, signIn } = useJeanAgent({
    systemPrompt: "You are a patient math tutor..."
  });

  if (!agent) return <SignInWithJean onSuccess={signIn} />;
  return <JeanChat agent={agent} />;
}`,
  },
  {
    lang: "python",
    title: "Python Voice Assistant",
    code: `from jeanmemory import JeanAgent

agent = JeanAgent(
    api_key="jean_sk_...",
    system_prompt="You are a supportive therapist",
    modality="voice"
)
agent.run()`,
  },
  {
    lang: "tsx",
    title: "Next.js Full-Stack App",
    code: `import { JeanAgent } from '@jeanmemory/node';

export default async function handler(req, res) {
  const agent = new JeanAgent({
    userToken: req.headers.authorization,
    systemPrompt: "You are an AI writing coach"
  });
  const response = await agent.process(req.body.message);
  res.json({ response });
}`,
  },
];

const AnimatedCodeBlock = () => {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setIndex((prevIndex) => (prevIndex + 1) % codeSnippets.length);
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const currentSnippet = codeSnippets[index];

  return (
    <div className="w-full max-w-3xl h-auto bg-gray-900/5 rounded-xl border border-gray-200 shadow-md overflow-hidden">
      <div className="flex items-center justify-between p-3 bg-gray-100 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 bg-red-400 rounded-full"></span>
          <span className="w-3 h-3 bg-yellow-400 rounded-full"></span>
          <span className="w-3 h-3 bg-green-400 rounded-full"></span>
        </div>
        <AnimatePresence mode="wait">
          <motion.div
            key={currentSnippet.title}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="text-sm text-gray-500 font-mono"
          >
            {currentSnippet.title}
          </motion.div>
        </AnimatePresence>
        <div className="w-12"></div>
      </div>
      <AnimatePresence mode="wait">
        <motion.div
          key={index}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.5 }}
          className="p-4"
        >
          <SyntaxHighlighter
            language={currentSnippet.lang}
            style={materialLight}
            customStyle={{
              background: "transparent",
              fontSize: "14px",
              lineHeight: "1.6",
            }}
            codeTagProps={{
              style: {
                fontFamily: '"Fira Code", "Dank Mono", monospace',
              },
            }}
          >
            {currentSnippet.code}
          </SyntaxHighlighter>
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

export default AnimatedCodeBlock;
