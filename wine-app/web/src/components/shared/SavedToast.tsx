/**
 * Subtle toast notification for saved wines
 */

import { useEffect, useState } from 'react';
import { Check } from 'lucide-react';

interface SavedToastProps {
  isVisible: boolean;
  wineName?: string;
  onComplete: () => void;
}

export function SavedToast({ isVisible, wineName, onComplete }: SavedToastProps) {
  const [show, setShow] = useState(false);

  useEffect(() => {
    if (isVisible) {
      setShow(true);
      const timer = setTimeout(() => {
        setShow(false);
        setTimeout(onComplete, 300);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [isVisible, onComplete]);

  if (!isVisible && !show) return null;

  return (
    <div
      className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50 transition-all duration-300 ${
        show ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
      }`}
    >
      <div className="flex items-center gap-3 px-5 py-3 bg-white rounded-xl shadow-lg border border-gray-100">
        <div className="w-8 h-8 bg-wine-100 rounded-full flex items-center justify-center">
          <Check className="w-4 h-4 text-wine-600" />
        </div>
        <div>
          <p className="font-mono text-xs uppercase tracking-wider text-wine-600">Saved</p>
          {wineName && (
            <p className="text-sm text-gray-600 truncate max-w-[200px]">{wineName}</p>
          )}
        </div>
      </div>
    </div>
  );
}
