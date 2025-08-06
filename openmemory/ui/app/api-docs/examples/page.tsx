"use client";

import React, { useState } from 'react';
import { ArrowLeft, Code, Lightbulb, Users, MessageSquare, BookOpen, ShoppingCart, Heart, Briefcase, GraduationCap, Copy, Check, ChevronRight, Play } from 'lucide-react';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import ParticleNetwork from '@/components/landing/ParticleNetwork';
import { motion } from 'framer-motion';
import AICopyButton from '@/components/AICopyButton';
import { generateExamplesAIContent } from '@/utils/aiDocContent';

const CodeBlock = ({ code, lang = 'typescript', title }: { code: string; lang?: string; title?: string }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(code.trim());
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const lines = code.trim().split('\n');

  return (
    <div className="relative group my-4 bg-slate-900/70 backdrop-blur-sm rounded-lg border border-slate-700/50 shadow-lg">
      {title && (
        <div className="flex justify-between items-center text-xs text-slate-400 border-b border-slate-700/50">
          <div className="px-4 py-2">{title}</div>
          <div className="px-4 py-2 text-green-400">{lang}</div>
        </div>
      )}
      <div className="p-4 pr-12 text-sm font-mono overflow-x-auto">
        {lines.map((line, i) => {
          let styledLine: string = line;
          
          if (lang === 'typescript' || lang === 'javascript' || lang === 'tsx') {
            styledLine = styledLine.replace(/(\/\/.*$)/g, '<span class="text-slate-500">$&</span>');
            styledLine = styledLine.replace(/(".*?"|'.*?'|`.*?`)/g, '<span class="text-emerald-400">$&</span>');
            styledLine = styledLine.replace(/\b(const|let|var|function|return|if|import|from|export|async|await|class)\b/g, '<span class="text-pink-400">$&</span>');
          } else if (lang === 'python') {
            styledLine = styledLine.replace(/(#.*$)/g, '<span class="text-slate-500">$&</span>');
            styledLine = styledLine.replace(/(".*?"|'.*?')/g, '<span class="text-emerald-400">$&</span>');
            styledLine = styledLine.replace(/\b(from|import|def|return|if|class|async|await|for|in|print)\b/g, '<span class="text-pink-400">$&</span>');
          }
          
          return (
            <div key={i} className="flex items-start">
              <span className="text-right text-slate-600 select-none mr-4" style={{ minWidth: '2em' }}>
                {i + 1}
              </span>
              <code className="text-slate-200 whitespace-pre-wrap" dangerouslySetInnerHTML={{ __html: styledLine }} />
            </div>
          );
        })}
      </div>
      <button
        onClick={handleCopy}
        className="absolute top-4 right-2 p-2 rounded-md bg-slate-700/50 hover:bg-slate-700 transition-colors opacity-0 group-hover:opacity-100"
        aria-label="Copy code"
      >
        {copied ? <Check className="h-4 w-4 text-green-400" /> : <Copy className="h-4 w-4 text-slate-400" />}
      </button>
    </div>
  );
};

const ExampleCard = ({
  title,
  description,
  icon: Icon,
  gradient,
  tags,
  difficulty,
  code,
  language = 'typescript'
}: {
  title: string;
  description: string;
  icon: React.ElementType;
  gradient: string;
  tags: string[];
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  code: string;
  language?: string;
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const difficultyColors = {
    Beginner: 'bg-green-500/20 text-green-300 border-green-500/30',
    Intermediate: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
    Advanced: 'bg-red-500/20 text-red-300 border-red-500/30'
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={`rounded-xl border bg-gradient-to-br ${gradient} backdrop-blur-sm overflow-hidden`}
    >
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center">
            <div className="p-3 rounded-lg bg-white/10 backdrop-blur-sm">
              <Icon className="w-6 h-6" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold">{title}</h3>
              <p className="text-sm text-muted-foreground mt-1">{description}</p>
            </div>
          </div>
          <span className={`px-2 py-1 rounded-full text-xs font-medium border ${difficultyColors[difficulty]}`}>
            {difficulty}
          </span>
        </div>
        
        <div className="flex flex-wrap gap-2 mb-4">
          {tags.map((tag, i) => (
            <span key={i} className="px-2 py-1 bg-white/10 rounded-md text-xs">
              {tag}
            </span>
          ))}
        </div>
        
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center text-sm font-medium hover:text-blue-400 transition-colors"
        >
          <Play className="w-4 h-4 mr-2" />
          {isExpanded ? 'Hide Code' : 'View Code'}
          <ChevronRight className={`w-4 h-4 ml-1 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
        </button>
      </div>
      
      {isExpanded && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="border-t border-white/10">
            <CodeBlock code={code} lang={language} title={`${title} Implementation`} />
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

const UseCaseSection = ({
  title,
  description,
  examples
}: {
  title: string;
  description: string;
  examples: React.ReactNode;
}) => {
  return (
    <section className="mb-12">
      <h2 className="text-2xl font-bold mb-2">{title}</h2>
      <p className="text-muted-foreground mb-6">{description}</p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {examples}
      </div>
    </section>
  );
};

export default function ExamplesPage() {
  const educationExamples = [
    {
      title: "Personalized Math Tutor",
      description: "AI tutor that remembers student's learning style and progress",
      icon: GraduationCap,
      gradient: "from-blue-600/20 to-blue-800/10 border-blue-500/30",
      tags: ["Education", "React", "Real-time"],
      difficulty: "Beginner" as const,
      code: `import { useJeanAgent, SignInWithJean, JeanChat } from '@jeanmemory/react';

function MathTutor() {
  const { agent, signIn } = useJeanAgent({
    systemPrompt: \`You are a patient math tutor who:
    - Remembers the student's weak areas
    - Adapts explanations to their learning style
    - Tracks their progress over time
    - Provides personalized practice problems\`
  });

  if (!agent) return <SignInWithJean onSuccess={signIn} />;
  
  return (
    <div className="math-tutor-app">
      <h1>Personal Math Tutor</h1>
      <JeanChat agent={agent} />
    </div>
  );
}`
    },
    {
      title: "Language Learning Assistant",
      description: "Tracks vocabulary progress and conversation history",
      icon: BookOpen,
      gradient: "from-green-600/20 to-green-800/10 border-green-500/30",
      tags: ["Education", "Python", "Progress Tracking"],
      difficulty: "Intermediate" as const,
      code: `from jeanmemory import JeanAgent
import json

class LanguageLearningBot:
    def __init__(self):
        self.agent = JeanAgent(
            api_key="jean_sk_...",
            system_prompt=\"\"\"You are a language learning assistant who:
            - Tracks vocabulary the user has learned
            - Remembers their native language and target language
            - Adjusts difficulty based on their progress
            - Provides contextual examples from past conversations\"\"\"
        )
    
    def practice_conversation(self, topic):
        # Jean Memory automatically retrieves relevant past conversations
        response = self.agent.send_message(
            f"Let's practice {topic} in Spanish. "
            f"Use vocabulary I've learned before."
        )
        return response
    
    def review_progress(self):
        return self.agent.send_message(
            "What vocabulary have I mastered this week?"
        )

# Usage
bot = LanguageLearningBot()
bot.agent.authenticate()
print(bot.practice_conversation("ordering food"))
print(bot.review_progress())`
    }
  ];

  const businessExamples = [
    {
      title: "Customer Support Agent",
      description: "Remembers customer history and preferences",
      icon: Users,
      gradient: "from-purple-600/20 to-purple-800/10 border-purple-500/30",
      tags: ["Business", "Node.js", "CRM Integration"],
      difficulty: "Intermediate" as const,
      code: `import { JeanAgent } from '@jeanmemory/node';
import express from 'express';

const app = express();

// Initialize support agent
const supportAgent = new JeanAgent({
  apiKey: process.env.JEAN_API_KEY,
  systemPrompt: \`You are a customer support agent who:
  - Knows the customer's purchase history
  - Remembers past support tickets
  - Understands their preferences
  - Provides personalized solutions\`
});

app.post('/support/chat', async (req, res) => {
  const { customerId, message } = req.body;
  
  // Jean Memory handles customer context automatically
  const response = await supportAgent.sendMessage(message, {
    userId: customerId // Each customer has isolated memory
  });
  
  res.json({ response });
});

app.post('/support/ticket/resolve', async (req, res) => {
  const { customerId, resolution } = req.body;
  
  // Store the resolution for future reference
  await supportAgent.addMemory(
    \`Ticket resolved: \${resolution}\`,
    { userId: customerId }
  );
  
  res.json({ success: true });
});

app.listen(3000);`
    },
    {
      title: "Sales Assistant",
      description: "Tracks leads, conversations, and deal progress",
      icon: Briefcase,
      gradient: "from-orange-600/20 to-orange-800/10 border-orange-500/30",
      tags: ["Business", "Python", "CRM"],
      difficulty: "Advanced" as const,
      code: `from jeanmemory import JeanAgent
from datetime import datetime
import asyncio

class SalesAssistant:
    def __init__(self):
        self.agent = JeanAgent(
            api_key="jean_sk_...",
            system_prompt=\"\"\"You are a sales assistant who:
            - Tracks all interactions with each lead
            - Remembers their pain points and objections
            - Knows their budget and timeline
            - Suggests next best actions
            - Provides conversation summaries\"\"\"
        )
    
    async def log_call(self, lead_id, notes):
        \"\"\"Log a sales call with automatic summarization\"\"\"
        summary = await self.agent.send_message(
            f"Summarize this sales call and identify next steps: {notes}",
            user_id=lead_id
        )
        
        # Store the interaction
        await self.agent.add_memory(
            f"Call on {datetime.now()}: {summary}",
            tags=["sales-call", f"lead-{lead_id}"]
        )
        
        return summary
    
    async def get_lead_strategy(self, lead_id):
        \"\"\"Get personalized strategy for a lead\"\"\"
        return await self.agent.send_message(
            "Based on all interactions, what's the best approach "
            "to close this deal? What are their main concerns?",
            user_id=lead_id
        )
    
    async def find_similar_deals(self, criteria):
        \"\"\"Find similar successful deals\"\"\"
        return await self.agent.search_memory(
            f"successful deals with {criteria}",
            tags_filter=["closed-won"]
        )

# Usage
sales_bot = SalesAssistant()
await sales_bot.log_call("lead-123", "Interested in enterprise plan...")
strategy = await sales_bot.get_lead_strategy("lead-123")`
    }
  ];

  const healthcareExamples = [
    {
      title: "Mental Health Companion",
      description: "Provides continuous support with context awareness",
      icon: Heart,
      gradient: "from-pink-600/20 to-pink-800/10 border-pink-500/30",
      tags: ["Healthcare", "React", "Privacy-First"],
      difficulty: "Advanced" as const,
      code: `import { useJeanAgent, JeanChat } from '@jeanmemory/react';
import { useEffect, useState } from 'react';

function MentalHealthCompanion() {
  const { agent, signIn, user } = useJeanAgent({
    systemPrompt: \`You are a supportive mental health companion who:
    - Remembers past conversations and emotional patterns
    - Tracks mood changes over time
    - Provides personalized coping strategies
    - Never judges, always supports
    - Suggests professional help when appropriate
    
    Important: You are not a replacement for professional therapy.\`
  });
  
  const [moodToday, setMoodToday] = useState(null);
  
  useEffect(() => {
    if (agent && !moodToday) {
      // Check in on user's mood
      agent.sendMessage("How are you feeling today?")
        .then(response => {
          // Jean Memory stores this for pattern tracking
          console.log("Daily check-in recorded");
        });
    }
  }, [agent]);
  
  if (!agent) {
    return (
      <div className="welcome">
        <h2>Your Mental Health Journey</h2>
        <p>Your conversations are private and secure.</p>
        <SignInWithJean onSuccess={signIn} />
      </div>
    );
  }
  
  return (
    <div className="mental-health-app">
      <div className="mood-tracker">
        <h3>Daily Mood Check-In</h3>
        <MoodSelector onSelect={setMoodToday} />
      </div>
      
      <div className="chat-section">
        <JeanChat 
          agent={agent}
          placeholder="Share what's on your mind..."
        />
      </div>
      
      <div className="resources">
        <button onClick={() => agent.sendMessage("Show my mood patterns")}>
          View Patterns
        </button>
        <button onClick={() => agent.sendMessage("Suggest coping strategies")}>
          Coping Strategies
        </button>
      </div>
    </div>
  );
}`
    },
    {
      title: "Fitness Coach",
      description: "Personalized workout and nutrition tracking",
      icon: Heart,
      gradient: "from-red-600/20 to-red-800/10 border-red-500/30",
      tags: ["Healthcare", "Python", "Progress Tracking"],
      difficulty: "Intermediate" as const,
      code: `from jeanmemory import JeanAgent
from datetime import datetime, timedelta

class FitnessCoach:
    def __init__(self):
        self.agent = JeanAgent(
            api_key="jean_sk_...",
            system_prompt=\"\"\"You are a personal fitness coach who:
            - Remembers user's fitness goals and current level
            - Tracks workout history and progress
            - Knows dietary preferences and restrictions
            - Adjusts recommendations based on progress
            - Provides motivation based on past achievements\"\"\"
        )
    
    def log_workout(self, workout_details):
        \"\"\"Log a workout session\"\"\"
        self.agent.add_memory(
            f"Workout on {datetime.now()}: {workout_details}",
            tags=["workout", "fitness-log"]
        )
        
        # Get personalized feedback
        feedback = self.agent.send_message(
            f"I just completed: {workout_details}. "
            "How does this align with my goals?"
        )
        return feedback
    
    def get_workout_plan(self):
        \"\"\"Get personalized workout for today\"\"\"
        return self.agent.send_message(
            "What should I work on today? Consider my recent workouts "
            "and recovery needs."
        )
    
    def nutrition_advice(self, meal_description):
        \"\"\"Get nutrition feedback\"\"\"
        return self.agent.send_message(
            f"I'm planning to eat: {meal_description}. "
            "Does this align with my fitness goals?"
        )
    
    def weekly_progress(self):
        \"\"\"Get weekly progress summary\"\"\"
        return self.agent.send_message(
            "Summarize my fitness progress this week. "
            "What should I focus on next week?"
        )

# Usage
coach = FitnessCoach()
coach.agent.authenticate()

print(coach.get_workout_plan())
print(coach.log_workout("30 min run, 20 pushups, 30 squats"))
print(coach.nutrition_advice("Grilled chicken salad with quinoa"))
print(coach.weekly_progress())`
    }
  ];

  const developerExamples = [
    {
      title: "Code Review Assistant",
      description: "Remembers coding standards and past review feedback",
      icon: Code,
      gradient: "from-cyan-600/20 to-cyan-800/10 border-cyan-500/30",
      tags: ["Developer", "Node.js", "GitHub Integration"],
      difficulty: "Advanced" as const,
      code: `import { JeanAgent } from '@jeanmemory/node';
import { Octokit } from '@octokit/rest';

class CodeReviewBot {
  constructor() {
    this.agent = new JeanAgent({
      apiKey: process.env.JEAN_API_KEY,
      systemPrompt: \`You are a code review assistant who:
      - Remembers the team's coding standards
      - Knows common issues in this codebase
      - Tracks recurring problems by developer
      - Suggests improvements based on past reviews
      - Maintains consistency across the project\`
    });
    
    this.github = new Octokit({
      auth: process.env.GITHUB_TOKEN
    });
  }
  
  async reviewPullRequest(owner, repo, pr_number) {
    // Get PR details
    const { data: pr } = await this.github.pulls.get({
      owner, repo, pull_number: pr_number
    });
    
    // Get the diff
    const { data: files } = await this.github.pulls.listFiles({
      owner, repo, pull_number: pr_number
    });
    
    // Jean Memory knows the codebase patterns
    const review = await this.agent.sendMessage(\`
      Review this PR by \${pr.user.login}:
      Title: \${pr.title}
      Files changed: \${files.map(f => f.filename).join(', ')}
      
      Check for:
      - Consistency with our patterns
      - Common mistakes this developer makes
      - Security issues
      - Performance concerns
    \`);
    
    // Store the review for learning
    await this.agent.addMemory(
      \`PR #\${pr_number} review: \${review}\`,
      { tags: ['code-review', \`dev-\${pr.user.login}\`] }
    );
    
    // Post review comment
    await this.github.pulls.createReview({
      owner, repo,
      pull_number: pr_number,
      body: review,
      event: 'COMMENT'
    });
    
    return review;
  }
  
  async getDeveloperPatterns(username) {
    // Get patterns for specific developer
    return await this.agent.searchMemory(
      \`common issues and patterns for \${username}\`,
      { tags_filter: [\`dev-\${username}\`] }
    );
  }
}

// Usage
const reviewer = new CodeReviewBot();
await reviewer.reviewPullRequest('myorg', 'myrepo', 123);`
    },
    {
      title: "Documentation Generator",
      description: "Creates consistent docs based on codebase patterns",
      icon: BookOpen,
      gradient: "from-indigo-600/20 to-indigo-800/10 border-indigo-500/30",
      tags: ["Developer", "Python", "Automation"],
      difficulty: "Intermediate" as const,
      code: `from jeanmemory import JeanAgent
import ast
import os

class DocGenerator:
    def __init__(self):
        self.agent = JeanAgent(
            api_key="jean_sk_...",
            system_prompt=\"\"\"You are a documentation generator who:
            - Knows the project's documentation style
            - Remembers API patterns and conventions
            - Maintains consistency across all docs
            - Includes relevant examples from the codebase
            - Follows the team's writing guidelines\"\"\"
        )
    
    def document_function(self, function_code):
        \"\"\"Generate documentation for a function\"\"\"
        # Parse the function
        tree = ast.parse(function_code)
        func = tree.body[0]
        
        # Jean Memory knows your doc style
        doc = self.agent.send_message(f\"\"\"
        Generate documentation for this function:
        {function_code}
        
        Use our standard format with:
        - Brief description
        - Parameters with types
        - Return value
        - Example usage
        - Related functions
        \"\"\")
        
        return doc
    
    def generate_api_docs(self, endpoints):
        \"\"\"Generate API documentation\"\"\"
        docs = []
        for endpoint in endpoints:
            doc = self.agent.send_message(f\"\"\"
            Document this API endpoint:
            {endpoint['method']} {endpoint['path']}
            Handler: {endpoint['handler']}
            
            Include:
            - Description
            - Request/response formats
            - Authentication requirements
            - Example curl commands
            - Common errors
            \"\"\")
            docs.append(doc)
            
            # Store for consistency
            self.agent.add_memory(
                f"API doc for {endpoint['path']}: {doc}",
                tags=["api-docs", "documentation"]
            )
        
        return "\\n\\n".join(docs)
    
    def update_readme(self, project_path):
        \"\"\"Update README based on current code\"\"\"
        return self.agent.send_message(
            f"Update the README for {project_path} based on "
            "recent changes and our documentation standards"
        )

# Usage
doc_gen = DocGenerator()
doc_gen.agent.authenticate()

# Document a new function
code = '''
def calculate_similarity(text1, text2, method='cosine'):
    """Calculate semantic similarity between texts"""
    # Implementation here
    pass
'''
print(doc_gen.document_function(code))`
    }
  ];

  return (
    <div className="min-h-screen bg-background text-foreground relative">
      {/* Particle Background */}
      <div className="absolute inset-0 z-0">
        <ParticleNetwork id="examples-particles" className="h-full w-full" interactive={false} particleCount={60} />
      </div>

      <div className="relative z-10">
        {/* Header */}
        <header className="border-b border-white/10 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <Link href="/api-docs" className="flex items-center text-muted-foreground hover:text-foreground transition-colors">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to API Docs
              </Link>
              <div className="flex gap-2">
                <Link href="/api-docs/quickstart">
                  <Button variant="ghost" size="sm">Quick Start</Button>
                </Link>
                <Link href="https://github.com/jean-technologies/jean-memory/tree/main/examples">
                  <Button variant="ghost" size="sm">GitHub Examples</Button>
                </Link>
              </div>
            </div>
          </div>
        </header>

        {/* AI Quick Deploy Button */}
        <div className="fixed top-20 right-4 z-50">
          <AICopyButton 
            content={generateExamplesAIContent()} 
            title="Copy All Examples"
          />
        </div>

        {/* Main Content */}
        <section className="py-16 px-4 sm:px-6 lg:px-8">
          <div className="max-w-7xl mx-auto">
            {/* Title Section */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center mb-12"
            >
              <div className="inline-flex items-center px-4 py-2 rounded-full bg-yellow-500/20 border border-yellow-500/30 text-yellow-300 mb-6">
                <Lightbulb className="w-4 h-4 mr-2" />
                <span className="text-sm font-medium">Real-World Examples</span>
              </div>
              <h1 className="text-4xl sm:text-5xl font-bold mb-4 bg-gradient-to-r from-yellow-400 to-orange-400 bg-clip-text text-transparent">
                Example Applications
              </h1>
              <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
                Production-ready examples showing how to build personalized AI applications with Jean Memory
              </p>
            </motion.div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-12">
              <div className="p-4 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10 text-center">
                <div className="text-2xl font-bold text-blue-400">12+</div>
                <div className="text-sm text-muted-foreground">Complete Examples</div>
              </div>
              <div className="p-4 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10 text-center">
                <div className="text-2xl font-bold text-green-400">3</div>
                <div className="text-sm text-muted-foreground">Frameworks</div>
              </div>
              <div className="p-4 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10 text-center">
                <div className="text-2xl font-bold text-purple-400">5</div>
                <div className="text-sm text-muted-foreground">Industries</div>
              </div>
              <div className="p-4 rounded-lg bg-white/5 backdrop-blur-sm border border-white/10 text-center">
                <div className="text-2xl font-bold text-yellow-400">~50</div>
                <div className="text-sm text-muted-foreground">Lines of Code</div>
              </div>
            </div>

            {/* Education Examples */}
            <UseCaseSection
              title="🎓 Education & Learning"
              description="Build personalized tutors and learning assistants that adapt to each student"
              examples={educationExamples.map((example, i) => (
                <ExampleCard key={i} {...example} />
              ))}
            />

            {/* Business Examples */}
            <UseCaseSection
              title="💼 Business & Productivity"
              description="Create intelligent business tools that remember context and improve over time"
              examples={businessExamples.map((example, i) => (
                <ExampleCard key={i} {...example} />
              ))}
            />

            {/* Healthcare Examples */}
            <UseCaseSection
              title="❤️ Health & Wellness"
              description="Develop supportive health companions with continuous context awareness"
              examples={healthcareExamples.map((example, i) => (
                <ExampleCard key={i} {...example} />
              ))}
            />

            {/* Developer Tools */}
            <UseCaseSection
              title="Developer Tools"
              description="Build coding assistants that understand your codebase and patterns"
              examples={developerExamples.map((example, i) => (
                <ExampleCard key={i} {...example} />
              ))}
            />

            {/* More Examples CTA */}
            <section className="mt-16 p-8 rounded-xl bg-gradient-to-br from-blue-600/10 to-purple-600/10 border border-blue-500/30 text-center">
              <h2 className="text-2xl font-bold mb-4">Want More Examples?</h2>
              <p className="text-muted-foreground mb-6">
                Explore our GitHub repository for more complete examples, templates, and starter kits
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link href="https://github.com/jean-technologies/jean-memory/tree/main/examples" target="_blank">
                  <Button size="lg">
                    View GitHub Examples
                    <ChevronRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
                <Link href="/api-docs/quickstart">
                  <Button size="lg" variant="outline">
                    Start Building
                  </Button>
                </Link>
              </div>
            </section>

            {/* Community Examples */}
            <section className="mt-12 text-center">
              <p className="text-muted-foreground">
                Built something cool with Jean Memory?{' '}
                <Link href="https://github.com/jean-technologies/jean-memory/issues/new?labels=showcase" className="text-blue-400 hover:text-blue-300">
                  Share your project
                </Link>{' '}
                with the community!
              </p>
            </section>
          </div>
        </section>
      </div>
    </div>
  );
}