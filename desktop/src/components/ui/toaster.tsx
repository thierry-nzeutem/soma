'use client';

import { useEffect, useState } from 'react';
import { cn } from '@/lib/utils';

export interface Toast {
  id: string;
  message: string;
  type?: 'success' | 'error' | 'info';
}

// Simple global toast queue
const toastQueue: Array<(toast: Toast) => void> = [];

export function showToast(message: string, type: Toast['type'] = 'info') {
  const toast: Toast = { id: Math.random().toString(36).slice(2), message, type };
  toastQueue.forEach((fn) => fn(toast));
}

export function Toaster() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    const handler = (toast: Toast) => {
      setToasts((prev) => [...prev, toast]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== toast.id));
      }, 4000);
    };
    toastQueue.push(handler);
    return () => {
      const idx = toastQueue.indexOf(handler);
      if (idx !== -1) toastQueue.splice(idx, 1);
    };
  }, []);

  if (!toasts.length) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={cn(
            'px-4 py-3 rounded-lg text-sm font-medium shadow-lg animate-fade-in',
            toast.type === 'error' && 'bg-soma-danger text-white',
            toast.type === 'success' && 'bg-soma-success text-black',
            toast.type === 'info' && 'bg-soma-surface border border-soma-border text-soma-text'
          )}
        >
          {toast.message}
        </div>
      ))}
    </div>
  );
}
