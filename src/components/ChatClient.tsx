'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import type { ChatMessage } from '@/lib/types/chat';

function makeMessage(role: ChatMessage['role'], content: string): ChatMessage {
  return {
    id: crypto.randomUUID(),
    role,
    content,
    createdAt: new Date().toISOString(),
  };
}

export function ChatClient() {
  const [input, setInput] = useState('Help me design AAIS version 1.');
  const [messages, setMessages] = useState<ChatMessage[]>([
    makeMessage('assistant', 'AAIS online. Give me a goal and I will help structure the build.'),
  ]);
  const [loading, setLoading] = useState(false);
  const [streamingId, setStreamingId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  async function submit() {
    const trimmed = input.trim();
    if (!trimmed || loading) return;

    const userMessage = makeMessage('user', trimmed);
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput('');
    setLoading(true);

    // Create a placeholder assistant message for streaming
    const assistantId = crypto.randomUUID();
    const assistantMessage: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      createdAt: new Date().toISOString(),
    };
    setMessages((current) => [...current, assistantMessage]);
    setStreamingId(assistantId);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: nextMessages, stream: true }),
      });

      if (!response.ok) {
        const data = (await response.json()) as { error?: string };
        throw new Error(data.error || 'Request failed');
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');

      const decoder = new TextDecoder();
      let accumulated = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const jsonStr = line.slice(6).trim();
          if (!jsonStr) continue;

          try {
            const parsed = JSON.parse(jsonStr) as {
              token?: string;
              done?: boolean;
              error?: string;
            };

            if (parsed.error) {
              accumulated += `\n\nError: ${parsed.error}`;
            } else if (parsed.done) {
              // Stream complete
            } else if (parsed.token) {
              accumulated += parsed.token;
            }

            // Update the assistant message in place
            setMessages((current) =>
              current.map((msg) =>
                msg.id === assistantId
                  ? { ...msg, content: accumulated || 'Thinking...' }
                  : msg,
              ),
            );
          } catch {
            // Skip malformed SSE lines
          }
        }
      }

      // Final update — if nothing was accumulated, show fallback
      if (!accumulated) {
        setMessages((current) =>
          current.map((msg) =>
            msg.id === assistantId ? { ...msg, content: 'No output.' } : msg,
          ),
        );
      }
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : 'Unknown client error';
      setMessages((current) =>
        current.map((msg) =>
          msg.id === assistantId ? { ...msg, content: `Error: ${errorMsg}` } : msg,
        ),
      );
    } finally {
      setLoading(false);
      setStreamingId(null);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <main style={{ maxWidth: 980, margin: '0 auto', padding: 24 }}>
      <div style={{ marginBottom: 20 }}>
        <h1 style={{ margin: 0, fontSize: 34 }}>AAIS</h1>
        <p style={{ color: 'var(--muted)', marginTop: 8 }}>
          Adaptive Autonomous Intelligence System — streaming chat, long-term memory, tool execution, and multi-step planning.
        </p>
      </div>

      <div
        style={{
          border: '1px solid var(--border)',
          borderRadius: 16,
          background: 'var(--panel)',
          padding: 16,
          minHeight: 420,
          maxHeight: '70vh',
          display: 'flex',
          flexDirection: 'column',
          gap: 12,
        }}
      >
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 12,
            flex: 1,
            overflowY: 'auto',
            paddingRight: 4,
          }}
        >
          {messages.map((message) => (
            <div
              key={message.id}
              style={{
                alignSelf: message.role === 'user' ? 'flex-end' : 'flex-start',
                maxWidth: '80%',
                background: message.role === 'user' ? 'var(--panel-2)' : '#10162d',
                border: '1px solid var(--border)',
                borderRadius: 14,
                padding: '12px 14px',
                whiteSpace: 'pre-wrap',
                lineHeight: 1.45,
              }}
            >
              <div style={{ fontSize: 12, color: 'var(--muted)', marginBottom: 6 }}>
                {message.role.toUpperCase()}
                {message.id === streamingId && (
                  <span style={{ marginLeft: 8, color: 'var(--accent)' }}>streaming...</span>
                )}
              </div>
              {message.content || (message.id === streamingId ? 'Thinking...' : '')}
            </div>
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div style={{ display: 'grid', gap: 10 }}>
          <textarea
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={handleKeyDown}
            rows={3}
            placeholder="Tell AAIS what to build... (Enter to send, Shift+Enter for newline)"
            style={{
              width: '100%',
              resize: 'vertical',
              borderRadius: 12,
              border: '1px solid var(--border)',
              background: '#0d1430',
              color: 'var(--text)',
              padding: 12,
            }}
          />
          <button
            onClick={submit}
            disabled={loading}
            style={{
              justifySelf: 'start',
              padding: '10px 16px',
              borderRadius: 12,
              border: '1px solid var(--border)',
              background: 'var(--accent)',
              color: '#061027',
              fontWeight: 700,
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.7 : 1,
            }}
          >
            {loading ? 'AAIS thinking...' : 'Send'}
          </button>
        </div>
      </div>
    </main>
  );
}
