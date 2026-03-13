'use client';

import { useState } from 'react';
import { Plus, MessageSquare, Loader2 } from 'lucide-react';
import { cn, safeDateFormat } from '@/lib/utils';
import { useTranslations } from '@/lib/i18n/config';
import { useCoachHistory, useCreateThread } from '@/hooks/use-coach';
import type { ConversationThread } from '@/lib/types/api';

interface ThreadListProps {
  activeThreadId: string | null;
  onSelectThread: (id: string) => void;
}

export function ThreadList({ activeThreadId, onSelectThread }: ThreadListProps) {
  const t = useTranslations();
  const history = useCoachHistory();
  const createThread = useCreateThread();
  const [showNewInput, setShowNewInput] = useState(false);
  const [newTitle, setNewTitle] = useState('');

  async function handleCreate() {
    if (!newTitle.trim()) return;
    try {
      const thread = await createThread.mutateAsync(newTitle.trim());
      setNewTitle('');
      setShowNewInput(false);
      const tid = thread?.thread_id ?? thread?.id;
      if (tid) {
        onSelectThread(tid);
      }
    } catch {
      // handled by mutation state
    }
  }

  const threads: ConversationThread[] = history.data?.threads ?? [];

  return (
    <div className="flex flex-col h-full bg-soma-surface border-r border-soma-border">
      {/* Header */}
      <div className="px-4 py-3 border-b border-soma-border shrink-0">
        <div className="flex items-center justify-between">
          <p className="text-xs font-semibold uppercase tracking-wider text-soma-muted">
            {t('coach.conversations')}
          </p>
          <button
            onClick={() => setShowNewInput((v) => !v)}
            className={cn(
              'w-6 h-6 rounded-md flex items-center justify-center transition-colors',
              'text-soma-muted hover:text-soma-accent hover:bg-soma-accent/10'
            )}
            title={t('coach.newThread')}
          >
            <Plus size={14} />
          </button>
        </div>

        {showNewInput && (
          <div className="mt-2 space-y-1.5">
            <input
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
              placeholder={t('coach.threadTitlePlaceholder')}
              autoFocus
              className="w-full px-2.5 py-1.5 text-xs bg-soma-bg border border-soma-border rounded-lg
                text-soma-text placeholder-soma-muted focus:outline-none focus:border-soma-accent"
            />
            <div className="flex gap-1.5">
              <button
                onClick={handleCreate}
                disabled={!newTitle.trim() || createThread.isPending}
                className="flex-1 py-1 text-xs font-medium bg-soma-accent text-soma-bg rounded-md
                  disabled:opacity-50 hover:bg-soma-accent/90 transition-colors"
              >
                {createThread.isPending ? (
                  <Loader2 size={11} className="animate-spin mx-auto" />
                ) : (
                  t('coach.create')
                )}
              </button>
              <button
                onClick={() => { setShowNewInput(false); setNewTitle(''); }}
                className="px-2 py-1 text-xs text-soma-muted hover:text-soma-text border border-soma-border rounded-md"
              >
                ✕
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Thread list */}
      <div className="flex-1 overflow-y-auto">
        {history.isLoading ? (
          <div className="space-y-1 p-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-12 bg-soma-border rounded-lg animate-pulse" />
            ))}
          </div>
        ) : threads.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-3 px-4 py-8">
            <MessageSquare size={28} className="text-soma-border" />
            <p className="text-xs text-soma-muted text-center leading-relaxed">
              Aucune conversation.{'\n'}Commencez par créer une nouvelle discussion.
            </p>
          </div>
        ) : (
          <div className="p-2 space-y-0.5">
            {threads.map((thread) => {
              const tid = thread.thread_id ?? thread.id ?? '';
              return (
              <button
                key={tid}
                onClick={() => onSelectThread(tid)}
                className={cn(
                  'w-full text-left px-3 py-2.5 rounded-lg transition-all group',
                  activeThreadId === tid
                    ? 'bg-soma-accent/10 border border-soma-accent/30'
                    : 'hover:bg-soma-bg/60 border border-transparent'
                )}
              >
                <p
                  className={cn(
                    'text-xs font-medium leading-snug line-clamp-1',
                    activeThreadId === tid
                      ? 'text-soma-accent'
                      : 'text-soma-text group-hover:text-soma-text'
                  )}
                >
                  {thread.title || t('coach.untitledThread')}
                </p>
                {thread.updated_at && (
                  <p className="text-[10px] text-soma-muted mt-0.5">
                    {safeDateFormat(thread.updated_at, "d MMM 'à' HH:mm")}
                  </p>
                )}
                {thread.message_count != null && (
                  <p className="text-[10px] text-soma-muted">
                    {thread.message_count} message{thread.message_count !== 1 ? 's' : ''}
                  </p>
                )}
              </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
