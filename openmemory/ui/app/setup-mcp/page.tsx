"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useState } from "react";
import { Brain, ExternalLink, MessageCircle, Sparkles, ArrowRight, CheckCircle, Terminal, Copy } from "lucide-react";
import { Badge } from "@/components/ui/badge";

export default function SetupMCPPage() {
  const [supportForm, setSupportForm] = useState({
    name: '',
    email: '',
    message: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [copiedItem, setCopiedItem] = useState<string | null>(null);

  const handleSupportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      const response = await fetch('/api/support', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(supportForm),
      });

      if (!response.ok) {
        throw new Error('Failed to send support request');
      }

      setIsSubmitted(true);
      setSupportForm({ name: '', email: '', message: '' });
    } catch (error) {
      console.error('Error submitting support request:', error);
      // You could add error state here if needed
      alert('Failed to send message. Please try again or email jonathan@jeantechnologies.com directly.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const copyToClipboard = (text: string, item: string) => {
    navigator.clipboard.writeText(text);
    setCopiedItem(item);
    setTimeout(() => setCopiedItem(null), 2000);
  };

  return (
    <div className="container mx-auto max-w-4xl px-4 py-8">
      <div className="space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <h1 className="text-4xl font-bold flex items-center justify-center gap-3">
            <Brain className="h-10 w-10 text-purple-500" />
            How to Use Jean Memory
          </h1>
          <p className="text-xl text-zinc-400">
            Connect your personal memory to any AI assistant in seconds
          </p>
          <div className="flex justify-center gap-2">
            <Badge variant="secondary">One Simple Command</Badge>
            <Badge variant="secondary">Works Everywhere</Badge>
          </div>
        </div>

        {/* What This Does */}
        <Card className="border-purple-500/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-purple-500" />
              What This Does for You
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4">
              <div className="flex items-start gap-3">
                <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium">Your AI remembers everything about you</p>
                  <p className="text-sm text-zinc-400">Personal preferences, work history, goals, and important details</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium">Just talk naturally</p>
                  <p className="text-sm text-zinc-400">Say things like "Remember that I'm allergic to shellfish" or "What did I write about innovation?"</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-medium">Smarter conversations</p>
                  <p className="text-sm text-zinc-400">Your AI gives more personalized and relevant responses based on what it knows about you</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Simple Installation */}
        <Card className="border-green-500/20">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Terminal className="h-5 w-5 text-green-500" />
              Installation (30 seconds)
            </CardTitle>
            <CardDescription>
              Get your personalized install commands from your dashboard
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-blue-50 dark:bg-blue-950/20 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
              <p className="text-sm text-blue-800 dark:text-blue-200">
                <strong>Step 1:</strong> Sign up at <a href="/auth" className="underline hover:no-underline">jeanmemory.com</a>
              </p>
            </div>

            <div className="bg-green-50 dark:bg-green-950/20 p-4 rounded-lg border border-green-200 dark:border-green-800">
              <p className="text-sm text-green-800 dark:text-green-200">
                <strong>Step 2:</strong> Visit your <a href="/dashboard" className="underline hover:no-underline">dashboard</a> and find the "Quick Setup" section
              </p>
            </div>

            <div className="bg-purple-50 dark:bg-purple-950/20 p-4 rounded-lg border border-purple-200 dark:border-purple-800">
              <p className="text-sm text-purple-800 dark:text-purple-200">
                <strong>Step 3:</strong> Copy the install command for your AI app (Claude, Cursor, etc.) - it already has your user ID filled in!
              </p>
            </div>

            <div className="bg-zinc-50 dark:bg-zinc-950/20 p-4 rounded-lg border border-zinc-200 dark:border-zinc-800">
              <p className="text-sm text-zinc-800 dark:text-zinc-200">
                <strong>Step 4:</strong> Paste the command in your terminal and restart your AI app
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Example Conversations */}
        <Card>
          <CardHeader>
            <CardTitle>Example Conversations</CardTitle>
            <CardDescription>
              Here's how you'll talk to your AI assistant once connected
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="bg-zinc-900 p-4 rounded-lg">
                <p className="text-green-400 text-sm mb-1">You:</p>
                <p className="mb-3">"Remember that I prefer TypeScript over JavaScript for new projects"</p>
                <p className="text-blue-400 text-sm mb-1">AI:</p>
                <p className="text-sm text-zinc-300">✓ I'll remember your preference for TypeScript. This will help me give better coding advice!</p>
              </div>
              
              <div className="bg-zinc-900 p-4 rounded-lg">
                <p className="text-green-400 text-sm mb-1">You:</p>
                <p className="mb-3">"What did I write about innovation in my essays?"</p>
                <p className="text-blue-400 text-sm mb-1">AI:</p>
                <p className="text-sm text-zinc-300">Based on your essay "The Irreverent Act," you wrote about innovation requiring irreverence and challenging the status quo...</p>
              </div>

              <div className="bg-zinc-900 p-4 rounded-lg">
                <p className="text-green-400 text-sm mb-1">You:</p>
                <p className="mb-3">"Help me write a blog post about entrepreneurship"</p>
                <p className="text-blue-400 text-sm mb-1">AI:</p>
                <p className="text-sm text-zinc-300">I'll help you write that! Based on your previous writing about irreverence and 0-1 innovation, I'll make sure it reflects your unique perspective...</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Support */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageCircle className="h-5 w-5" />
              Need Help?
            </CardTitle>
            <CardDescription>
              Can't find Jean Memory in your AI assistant? Having trouble? We're here to help!
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isSubmitted ? (
              <div className="text-center py-8">
                <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">Message Sent!</h3>
                <p className="text-zinc-400">We'll get back to you within 24 hours.</p>
              </div>
            ) : (
              <form onSubmit={handleSupportSubmit} className="space-y-4">
                <div className="grid md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-1 block">Name</label>
                    <Input
                      value={supportForm.name}
                      onChange={(e) => setSupportForm({...supportForm, name: e.target.value})}
                      placeholder="Your name"
                      required
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-1 block">Email</label>
                    <Input
                      type="email"
                      value={supportForm.email}
                      onChange={(e) => setSupportForm({...supportForm, email: e.target.value})}
                      placeholder="your@email.com"
                      required
                    />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium mb-1 block">How can we help?</label>
                  <Textarea
                    value={supportForm.message}
                    onChange={(e) => setSupportForm({...supportForm, message: e.target.value})}
                    placeholder="I can't find Jean Memory in Claude Desktop..."
                    className="min-h-[100px]"
                    required
                  />
                </div>
                <Button type="submit" disabled={isSubmitting} className="w-full">
                  {isSubmitting ? "Sending..." : "Send Message"}
                  <ArrowRight className="h-4 w-4 ml-2" />
                </Button>
              </form>
            )}
          </CardContent>
        </Card>

        {/* Bottom CTA */}
        <Alert>
          <Sparkles className="h-4 w-4" />
          <AlertDescription>
            <strong>Ready to get started?</strong> Copy the command above, paste it in your terminal, and restart your AI app. Jean Memory will be waiting for you!
          </AlertDescription>
        </Alert>
      </div>
    </div>
  );
} 