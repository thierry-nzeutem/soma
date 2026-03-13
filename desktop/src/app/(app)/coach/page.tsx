'use client';

import { useState } from 'react';
import { ThreadList } from '@/components/coach/thread-list';
import { ChatPanel } from '@/components/coach/chat-panel';
import { ContextPanel } from '@/components/coach/context-panel';
import { useEntitlement } from '@/hooks/use-entitlements';
import { FeatureCode } from '@/lib/entitlements';
import PaywallCard from '@/components/PaywallCard';

export default function CoachPage() {
  const canUseCoach = useEntitlement(FeatureCode.AI_COACH);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);

  if (!canUseCoach) {
    return <PaywallCard feature={FeatureCode.AI_COACH} />;
  }

  return (
    // 3-panel layout, full height, no scroll on container
    <div className="h-full flex overflow-hidden">
      {/* Left panel: thread list — 220px fixed */}
      <div className="w-full md:w-[220px] shrink-0 overflow-hidden">
        <ThreadList
          activeThreadId={activeThreadId}
          onSelectThread={setActiveThreadId}
        />
      </div>

      {/* Center panel: chat — flex grow */}
      <div className="flex flex-col md:flex-row-1 overflow-hidden">
        <ChatPanel threadId={activeThreadId} />
      </div>

      {/* Right panel: health context — 200px fixed */}
      <div className="hidden lg:block w-[200px] shrink-0 overflow-hidden">
        <ContextPanel />
      </div>
    </div>
  );
}
