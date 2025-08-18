# Jean Memory Voice Modality - Conversational AI Architecture

**Date:** August 7, 2025  
**Status:** Design Phase  
**Purpose:** Enable natural voice conversations with Jean Memory-powered AI agents

## Executive Summary

The Voice Modality feature extends Jean Memory SDK capabilities beyond text chat to support natural voice conversations. By introducing separate `JeanChat` and `JeanVoice` components, we provide developers with modality-specific configurations while maintaining the same 5-line integration simplicity. This enables use cases from voice assistants to therapy bots, educational tutors, and accessibility applications.

## Architecture Overview

### Component Separation Strategy

Instead of a single `modality` property, we separate into distinct components for better scalability:

```typescript
// Text Chat Component
<JeanChat 
  apiKey="jean_sk_..."
  systemPrompt="You are a helpful assistant"
  scope="all_memories"
/>

// Voice Conversation Component  
<JeanVoice
  apiKey="jean_sk_..."
  systemPrompt="You are a helpful assistant"
  scope="all_memories"
  voiceConfig={{
    provider: "elevenlabs",
    voiceId: "antoni",
    language: "en-US"
  }}
/>
```

This separation allows for modality-specific features without cluttering the API.

## Technology Stack Options

### 1. ElevenLabs Integration (Recommended for Quality)

**Pros:**
- Industry-leading voice quality
- Low latency streaming
- Voice cloning capabilities
- Multi-language support

**Implementation:**
```typescript
interface ElevenLabsConfig {
  provider: "elevenlabs";
  apiKey?: string;  // Optional, can use Jean Memory's pooled account
  voiceId: string;  // Voice selection
  modelId?: "eleven_turbo_v2" | "eleven_monolingual_v1";
  stability?: number;  // 0-1, voice consistency
  similarityBoost?: number;  // 0-1, voice clarity
  streamingLatency?: 0 | 1 | 2 | 3;  // Optimization level
}
```

### 2. Gemini Multimodal Live API (Best for Real-time)

**Pros:**
- Native multimodal understanding
- Real-time conversation flow
- Integrated with Google's LLM
- Handles interruptions naturally

**Implementation:**
```typescript
interface GeminiLiveConfig {
  provider: "gemini-live";
  model: "gemini-2.0-flash-exp";
  voice: "Puck" | "Charon" | "Kore" | "Fenrir";
  config: {
    generation_config?: {
      temperature?: number;
      maxOutputTokens?: number;
      candidateCount?: number;
    };
    speechConfig?: {
      voiceConfig?: { prebuiltVoiceConfig?: { voiceName: string } };
    };
  };
}
```

### 3. Pipecat Framework (Most Flexible)

**Pros:**
- Framework agnostic
- Supports multiple TTS/STT providers
- Pipeline-based architecture
- Open source

**Implementation:**
```typescript
interface PipecatConfig {
  provider: "pipecat";
  pipeline: {
    stt: "deepgram" | "whisper" | "azure";
    llm: "openai" | "anthropic" | "local";
    tts: "elevenlabs" | "azure" | "cartesia";
  };
  customPipeline?: PipecatPipeline;  // Advanced users
}
```

### 4. Web Speech API (Simplest)

**Pros:**
- No external dependencies
- Works in all modern browsers
- Free to use
- Good for MVPs

**Cons:**
- Limited voice options
- Quality varies by platform
- No advanced features

## Voice Component API

### JeanVoice Component

```typescript
import { JeanVoice } from '@jeanmemory/react';

function VoiceAssistant() {
  return (
    <JeanVoice
      apiKey="jean_sk_..."
      systemPrompt="You are a friendly voice assistant"
      scope="all_memories"
      voiceConfig={{
        provider: "elevenlabs",
        voiceId: "rachel",
        language: "en-US",
        streamingLatency: 1
      }}
      audioConfig={{
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }}
      onTranscript={(text) => console.log("User said:", text)}
      onResponse={(text) => console.log("Agent said:", text)}
      onError={(error) => console.error("Voice error:", error)}
    />
  );
}
```

### Python Voice SDK

```python
from jeanmemory import JeanVoice

agent = JeanVoice(
    api_key="jean_sk_...",
    system_prompt="You are a helpful voice assistant",
    scope="all_memories",
    voice_config={
        "provider": "elevenlabs",
        "voice_id": "antoni",
        "streaming_latency": 1
    }
)

# Start voice conversation
agent.start_conversation()
```

## Voice UI/UX Components

### Visual Feedback States

```typescript
<JeanVoice>
  {({ state, volume, transcript }) => (
    <div className="voice-interface">
      {/* Animated waveform during speech */}
      <VoiceWaveform 
        isListening={state === 'listening'}
        volume={volume}
      />
      
      {/* State indicators */}
      <VoiceState>
        {state === 'listening' && "Listening..."}
        {state === 'thinking' && "Thinking..."}
        {state === 'speaking' && "Speaking..."}
      </VoiceState>
      
      {/* Live transcript */}
      <TranscriptDisplay>
        {transcript}
      </TranscriptDisplay>
      
      {/* Push-to-talk or always-on toggle */}
      <VoiceControls />
    </div>
  )}
</JeanVoice>
```

## Technical Implementation

### Voice Pipeline Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Browser   │───▶│     STT     │───▶│ Jean Memory │───▶│     TTS     │
│ Microphone  │    │  (Speech-   │    │   LLM +     │    │  (Text-to   │
│   Input     │    │  to-Text)   │    │   Context   │    │   Speech)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                          │                    │                  │
                          ▼                    ▼                  ▼
                    Transcript           AI Response          Audio Stream
```

### Real-time Streaming Architecture

```typescript
class VoiceStreamManager {
  private mediaRecorder: MediaRecorder;
  private websocket: WebSocket;
  private audioContext: AudioContext;
  
  async startConversation(config: VoiceConfig) {
    // 1. Initialize WebSocket for bi-directional streaming
    this.websocket = new WebSocket(`wss://api.jeanmemory.com/voice/stream`);
    
    // 2. Start capturing microphone
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this.mediaRecorder = new MediaRecorder(stream);
    
    // 3. Stream audio chunks to server
    this.mediaRecorder.ondataavailable = (event) => {
      if (this.websocket.readyState === WebSocket.OPEN) {
        this.websocket.send(event.data);
      }
    };
    
    // 4. Receive and play TTS audio
    this.websocket.onmessage = async (event) => {
      const audioData = event.data;
      await this.playAudio(audioData);
    };
  }
}
```

### Voice Activity Detection (VAD)

```typescript
class VoiceActivityDetector {
  private analyser: AnalyserNode;
  private threshold: number = 40;  // dB
  
  detectSpeech(audioContext: AudioContext, stream: MediaStream): Observable<boolean> {
    this.analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(stream);
    source.connect(this.analyser);
    
    return new Observable(observer => {
      const dataArray = new Uint8Array(this.analyser.frequencyBinCount);
      
      const checkAudio = () => {
        this.analyser.getByteFrequencyData(dataArray);
        const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
        const isSpeaking = average > this.threshold;
        observer.next(isSpeaking);
        
        requestAnimationFrame(checkAudio);
      };
      
      checkAudio();
    });
  }
}
```

## Memory Integration for Voice

### Context-Aware Voice Responses

```python
class VoiceMemoryIntegration:
    def enhance_voice_response(self, transcript: str, user_context: dict) -> str:
        """Enhance voice responses with memory context"""
        
        # Voice-specific context additions
        voice_context = {
            "modality": "voice",
            "speaking_pace": user_context.get("preferred_speaking_pace", "normal"),
            "formality_level": user_context.get("voice_formality", "casual"),
            "audio_preferences": user_context.get("audio_preferences", {})
        }
        
        # Merge with memory context
        enhanced_prompt = f"""
        [VOICE CONVERSATION MODE]
        User prefers: {voice_context['speaking_pace']} pace, {voice_context['formality_level']} tone
        
        Previous context from memories:
        {user_context.get('relevant_memories', '')}
        
        User said: {transcript}
        
        Respond naturally as if speaking, using appropriate pauses and conversational flow.
        """
        
        return enhanced_prompt
```

### Voice-Specific Memory Storage

```typescript
interface VoiceMemory extends Memory {
  modality: "voice";
  audio_metadata?: {
    duration: number;
    emotion_detected?: string;
    speaker_confidence: number;
    background_noise_level?: number;
  };
  prosody?: {
    pace: "slow" | "normal" | "fast";
    pitch: "low" | "normal" | "high";
    emotion: string;
  };
}
```

## Voice Configuration Options

### Advanced Voice Settings

```typescript
interface AdvancedVoiceConfig {
  // Voice selection
  voice: {
    provider: "elevenlabs" | "gemini-live" | "pipecat";
    voiceId: string;
    language: string;
    accent?: string;
    age?: "child" | "young" | "adult" | "senior";
    gender?: "male" | "female" | "neutral";
  };
  
  // Speech recognition
  recognition: {
    language: string;
    alternatives?: number;
    profanityFilter?: boolean;
    wordTimestamps?: boolean;
    autoPunctuation?: boolean;
  };
  
  // Conversation flow
  conversation: {
    interruptionSensitivity: "low" | "medium" | "high";
    silenceTimeout: number;  // ms before considering speech ended
    maxSpeechLength?: number;  // seconds
    enableBackchanneling?: boolean;  // "uh-huh", "mm-hmm" responses
  };
  
  // Audio processing
  audio: {
    echoCancellation: boolean;
    noiseSuppression: boolean;
    autoGainControl: boolean;
    sampleRate?: number;
    channels?: 1 | 2;
  };
}
```

## Use Case Examples

### 1. Voice Therapy Assistant

```typescript
function TherapyVoiceBot() {
  return (
    <JeanVoice
      apiKey="jean_sk_..."
      systemPrompt="You are a compassionate therapy assistant trained in CBT"
      scope="all_memories"
      voiceConfig={{
        provider: "elevenlabs",
        voiceId: "therapist_voice",
        language: "en-US",
        streamingLatency: 1  // Prioritize low latency
      }}
      conversation={{
        interruptionSensitivity: "low",  // Let user speak freely
        silenceTimeout: 3000,  // Comfortable pauses
        enableBackchanneling: true  // Supportive sounds
      }}
      onEmotionDetected={(emotion) => {
        // Adjust response based on detected emotion
      }}
    />
  );
}
```

### 2. Language Learning Tutor

```typescript
function LanguageTutor() {
  return (
    <JeanVoice
      apiKey="jean_sk_..."
      systemPrompt="You are a patient Spanish language tutor"
      scope="app_specific"
      voiceConfig={{
        provider: "gemini-live",
        voice: "Kore",
        language: "es-ES"
      }}
      recognition={{
        language: "es-ES",
        alternatives: 3,  // Show pronunciation alternatives
        wordTimestamps: true  // For pronunciation feedback
      }}
      onPronunciationScore={(score) => {
        // Provide feedback on pronunciation
      }}
    />
  );
}
```

### 3. Accessibility Voice Interface

```typescript
function AccessibilityAssistant() {
  return (
    <JeanVoice
      apiKey="jean_sk_..."
      systemPrompt="You are an accessibility assistant helping with computer navigation"
      scope="all_memories"
      voiceConfig={{
        provider: "webspeech",  // Use built-in for compatibility
        language: navigator.language
      }}
      commands={{
        "open [app]": (app) => openApplication(app),
        "read [element]": (element) => readScreenElement(element),
        "click [button]": (button) => clickButton(button)
      }}
      accessibility={{
        announceStateChanges: true,
        verbosityLevel: "high",
        keyboardShortcuts: true
      }}
    />
  );
}
```

## Implementation Phases

### Phase 1: MVP Voice Support
- Basic Web Speech API integration
- Simple push-to-talk interface
- Text + Voice response
- Same memory integration as chat

### Phase 2: Advanced Providers
- ElevenLabs integration
- Streaming support
- Voice selection UI
- Interruption handling

### Phase 3: Real-time Conversations
- Gemini Live API integration
- Natural conversation flow
- Emotion detection
- Background noise handling

### Phase 4: Advanced Features
- Voice cloning (with consent)
- Multi-speaker support
- Sentiment analysis
- Conversation analytics

## Performance Considerations

### Latency Optimization

```typescript
class LatencyOptimizer {
  // Predictive TTS - start generating before user finishes
  async predictiveGeneration(partialTranscript: string) {
    if (this.isProbablyComplete(partialTranscript)) {
      // Start LLM generation early
      this.startGeneration(partialTranscript);
    }
  }
  
  // Audio chunking for faster first byte
  streamAudioChunks(audioData: ArrayBuffer) {
    const chunkSize = 1024;  // bytes
    for (let i = 0; i < audioData.byteLength; i += chunkSize) {
      const chunk = audioData.slice(i, i + chunkSize);
      this.playChunk(chunk);
    }
  }
  
  // Preload common responses
  async preloadCommonPhrases() {
    const phrases = ["I understand", "Could you tell me more", "That's interesting"];
    for (const phrase of phrases) {
      await this.cacheTTS(phrase);
    }
  }
}
```

### Resource Management

```typescript
class VoiceResourceManager {
  private maxConcurrentStreams = 3;
  private activeStreams = new Set<MediaStream>();
  
  async acquireAudioStream(): Promise<MediaStream> {
    // Reuse existing streams when possible
    if (this.activeStreams.size >= this.maxConcurrentStreams) {
      await this.releaseOldestStream();
    }
    
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    this.activeStreams.add(stream);
    return stream;
  }
  
  cleanup() {
    // Properly release all resources
    this.activeStreams.forEach(stream => {
      stream.getTracks().forEach(track => track.stop());
    });
    this.activeStreams.clear();
  }
}
```

## Privacy & Security

### Voice Data Handling

1. **No Permanent Storage**: Voice audio is not stored unless explicitly requested
2. **Transcription Only**: Only text transcripts are saved to memory
3. **Local Processing**: Where possible, use on-device speech recognition
4. **Encryption**: All voice streams use WebRTC encryption
5. **Consent UI**: Clear indication when microphone is active

### Privacy-Preserving Features

```typescript
interface VoicePrivacySettings {
  // Don't send audio to cloud
  localProcessingOnly?: boolean;
  
  // Mask sensitive information in transcripts
  redactSensitiveInfo?: boolean;
  
  // Don't save voice characteristics
  disableVoiceProfiling?: boolean;
  
  // Auto-stop recording after timeout
  maxRecordingDuration?: number;
  
  // Require push-to-talk
  disableAlwaysListening?: boolean;
}
```

## Metrics & Analytics

### Voice-Specific Metrics

```typescript
interface VoiceMetrics {
  // Conversation quality
  averageLatency: number;
  transcriptionAccuracy: number;
  interruptionRate: number;
  
  // User engagement
  averageSessionDuration: number;
  utterancesPerSession: number;
  completionRate: number;
  
  // Technical performance
  audioQuality: number;
  networkLatency: number;
  processingTime: number;
  
  // User satisfaction
  voiceNaturalness: number;
  responseRelevance: number;
  conversationFlow: number;
}
```

## Developer Experience

### Quick Start Examples

```typescript
// Minimal voice integration
<JeanVoice apiKey="jean_sk_..." />

// With custom voice
<JeanVoice 
  apiKey="jean_sk_..."
  voiceConfig={{ provider: "elevenlabs", voiceId: "sarah" }}
/>

// Full featured
<JeanVoice
  apiKey="jean_sk_..."
  systemPrompt="You are a helpful assistant"
  scope="all_memories"
  voiceConfig={{
    provider: "gemini-live",
    voice: "Puck"
  }}
  onTranscript={console.log}
  onResponse={console.log}
/>
```

## Conclusion

The Voice Modality feature extends Jean Memory's capabilities into natural conversation, enabling developers to build sophisticated voice-first AI applications with the same simplicity as text chat. By providing separate components for different modalities and supporting multiple voice technology providers, we give developers the flexibility to choose the right solution for their use case while maintaining the 5-line integration promise.

This positions Jean Memory as the complete solution for both text and voice AI applications, expanding our addressable market and use cases significantly.