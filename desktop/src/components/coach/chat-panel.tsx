'use client';

import { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Zap, MessageSquare, Bot } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn, safeDateFormat } from '@/lib/utils';
import { useTranslations } from '@/lib/i18n/config';
import { useThread, useAskCoach, useQuickAdvice } from '@/hooks/use-coach';
import type { ConversationMessage } from '@/lib/types/api';

const QUICK_PROMPTS = [
  'Comment améliorer mon sommeil ?',
  'Mon plan d\'entraînement est-il adapté ?',
  'Analyse mes dernières métriques',
  'Quels suppléments me recommandes-tu ?',
];

interface ChatPanelProps {
  threadId: string | null;
}

function MessageBubble({ message }: { message: ConversationMessage }) {
  const isUser = message.role === 'user';
  const isCoach = message.role === 'assistant';

  return (
    <div
      className={cn(
        'flex gap-3',
        isUser ? 'flex-row-reverse' : 'flex-row'
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'w-7 h-7 rounded-full flex items-center justify-center shrink-0 text-xs font-bold mt-1',
          isUser
            ? 'bg-soma-accent text-soma-bg'
            : 'bg-soma-border text-soma-text'
        )}
      >
        {isUser ? 'U' : <Bot size={14} />}
      </div>

      {/* Content */}
      <div className={cn('flex-1 min-w-0', isUser ? 'flex justify-end' : '')}>
        <div
          className={cn(
            'rounded-xl px-4 py-3 text-xs leading-relaxed max-w-[85%]',
            isUser
              ? 'bg-soma-accent text-soma-bg rounded-tr-sm'
              : 'bg-soma-surface border border-soma-border text-soma-text rounded-tl-sm'
          )}
        >
          {isCoach ? (
            <div className="prose prose-xs prose-invert max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {message.content}
              </ReactMarkdown>
            </div>
          ) : (
            <p>{message.content}</p>
          )}
        </div>
        {message.created_at && (
          <p
            className={cn(
              'text-[10px] text-soma-muted mt-1 px-1',
              isUser ? 'text-right' : ''
            )}
          >
            {safeDateFormat(message.created_at, 'HH:mm')}
          </p>
        )}
      </div>
    </div>
  );
}

export function ChatPanel({ threadId }: ChatPanelProps) {
  const t = useTranslations();
  const thread = useThread(threadId);
  const ask = useAskCoach();
  const quick = useQuickAdvice();

  const [input, setInput] = useState('');
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [thread.data?.messages]);

  async function handleSend(text?: string) {
    const question = text ?? input.trim();
    if (!question || !threadId || ask.isPending) return;

    if (!text) setInput('');

    await ask.mutateAsync({
      question,
      thread_id: threadId,
    });
  }

  async function handleQuickAdvice(topic: string) {
    await quick.mutateAsync({ topic });
  }

  if (!threadId) {
    return (
      <div className="flex flex-col h-full items-center justify-center gap-4 bg-soma-bg px-8">
        <MessageSquare size={40} className="text-soma-border" />
        <div className="text-center">
          <p className="text-sm font-medium text-soma-text">
            Aucune conversation sélectionnée
          </p>
          <p className="text-xs text-soma-muted mt-1">
            Sélectionnez ou créez une conversation dans le panneau gauche.
          </p>
        </div>

        {/* Quick advice section */}
        <div className="w-full max-w-md mt-4">
          <p className="text-xs text-soma-muted text-center mb-3 uppercase tracking-wider font-semibold">
            Conseil rapide
          </p>
          <div className="grid grid-cols-2 gap-2">
            {QUICK_PROMPTS.map((prompt) => (
              <button
                key={prompt}
                onClick={() => handleQuickAdvice(prompt)}
                disabled={quick.isPending}
                className="px-3 py-2 text-xs text-soma-muted border border-soma-border rounded-lg
                  hover:text-soma-text hover:border-soma-accent/50 transition-colors text-left
                  disabled:opacity-50"
              >
                <Zap size={10} className="inline mr-1 text-soma-accent" />
                {prompt}
              </button>
            ))}
          </div>
          {quick.data && (
            <div className="mt-4 p-3 bg-soma-surface border border-soma-border rounded-xl text-xs">
              <div className="flex items-center gap-1.5 mb-2">
                <Bot size={12} className="text-soma-accent" />
                <span className="text-soma-accent font-semibold text-[10px] uppercase tracking-wide">
                  Conseil rapide
                </span>
              </div>
              <div className="prose prose-xs prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {quick.data.advice ?? quick.data.answer ?? ''}
                </ReactMarkdown>
              </div>
            </div>
          )}
          {quick.isPending && (
            <div className="mt-4 flex items-center justify-center gap-2 text-xs text-soma-muted">
              <Loader2 size={12} className="animate-spin text-soma-accent" />
              Génération du conseil...
            </div>
          )}
        </div>
      </div>
    );
  }

  // Support both flat and nested thread response formats
  const threadTitle = thread.data?.title ?? thread.data?.thread?.title;
  const threadMsgCount = thread.data?.message_count ?? thread.data?.thread?.message_count;
  const messages: ConversationMessage[] = thread.data?.messages ?? [];

  return (
    <div className="flex flex-col h-full bg-soma-bg">
      {/* Thread title */}
      {threadTitle && (
        <div className="px-5 py-3 border-b border-soma-border shrink-0">
          <p className="text-sm font-semibold text-soma-text truncate">
            {threadTitle}
          </p>
          {threadMsgCount != null && (
            <p className="text-xs text-soma-muted">
              {threadMsgCount} message{threadMsgCount !== 1 ? 's' : ''}
            </p>
          )}
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">
        {thread.isLoading ? (
          <div className="space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className={cn('flex gap-3', i % 2 === 0 ? '' : 'flex-row-reverse')}>
                <div className="w-7 h-7 rounded-full bg-soma-border animate-pulse shrink-0" />
                <div className="h-16 bg-soma-border rounded-xl animate-pulse" style={{ width: `${40 + i * 15}%` }} />
              </div>
            ))}
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-3">
            <Bot size={32} className="text-soma-border" />
            <p className="text-xs text-soma-muted text-center">
              Posez votre première question au Coach SOMA.
            </p>
          </div>
        ) : (
          messages.map((msg, i) => <MessageBubble key={msg.id ?? i} message={msg} />)
        )}

        {/* Typing indicator */}
        {ask.isPending && (
          <div className="flex gap-3">
            <div className="w-7 h-7 rounded-full bg-soma-border flex items-center justify-center shrink-0">
              <Bot size={14} className="text-soma-text" />
            </div>
            <div className="bg-soma-surface border border-soma-border rounded-xl rounded-tl-sm px-4 py-3">
              <div className="flex gap-1 items-center">
                <span className="w-1.5 h-1.5 bg-soma-accent rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 bg-soma-accent rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 bg-soma-accent rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className="shrink-0 px-5 py-4 border-t border-soma-border">
        {/* Quick prompts */}
        <div className="flex gap-2 mb-3 flex-wrap">
          {QUICK_PROMPTS.slice(0, 2).map((p) => (
            <button
              key={p}
              onClick={() => handleSend(p)}
              disabled={ask.isPending}
              className="px-2.5 py-1 text-[10px] text-soma-muted border border-soma-border rounded-full
                hover:text-soma-text hover:border-soma-accent/50 transition-colors disabled:opacity-50"
            >
              {p}
            </button>
          ))}
        </div>

        <div className="flex gap-3 items-end">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder={t('coach.askPlaceholder')}
            rows={2}
            disabled={ask.isPending}
            className="flex-1 px-3 py-2.5 text-xs bg-soma-surface border border-soma-border rounded-xl
              text-soma-text placeholder-soma-muted focus:outline-none focus:border-soma-accent
              resize-none leading-relaxed disabled:opacity-60 transition-colors"
          />
          <button
            onClick={() => handleSend()}
            disabled={!input.trim() || ask.isPending}
            className={cn(
              'w-9 h-9 rounded-xl flex items-center justify-center transition-all shrink-0',
              input.trim() && !ask.isPending
                ? 'bg-soma-accent text-soma-bg hover:bg-soma-accent/90'
                : 'bg-soma-border text-soma-muted cursor-not-allowed'
            )}
          >
            {ask.isPending ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <Send size={14} />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
