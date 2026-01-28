/**
 * Typing indicator component for chat with skeleton cards
 */

import { WineCardSkeleton } from './WineCardSkeleton';

interface TypingIndicatorProps {
  showSkeletonCards?: boolean;
}

export function TypingIndicator({ showSkeletonCards = false }: TypingIndicatorProps) {
  return (
    <div className="flex gap-4 items-start">
      {/* Pip avatar */}
      <div className="w-10 h-10 rounded-full bg-wine-600 flex items-center justify-center flex-shrink-0">
        <span className="font-serif text-white text-lg">P</span>
      </div>

      {/* Content area */}
      <div className="flex-1 max-w-[85%] flex flex-col items-start">
        {/* Sender label */}
        <div className="flex items-center gap-3 mb-2">
          <span className="font-mono text-[10px] uppercase tracking-wider text-gray-900 font-medium">
            Pip
          </span>
          <span className="font-mono text-[10px] uppercase tracking-wider text-gray-400">
            typing...
          </span>
        </div>

        {/* Typing dots */}
        <div className="bg-white rounded-2xl rounded-tl-sm px-5 py-3 border border-gray-100 shadow-sm">
          <div className="flex gap-1.5">
            <span
              className="w-2 h-2 bg-wine-400 rounded-full animate-bounce"
              style={{ animationDelay: '0ms' }}
            />
            <span
              className="w-2 h-2 bg-wine-400 rounded-full animate-bounce"
              style={{ animationDelay: '150ms' }}
            />
            <span
              className="w-2 h-2 bg-wine-400 rounded-full animate-bounce"
              style={{ animationDelay: '300ms' }}
            />
          </div>
        </div>

        {/* Skeleton wine cards */}
        {showSkeletonCards && (
          <div className="mt-4 space-y-3 w-full">
            <WineCardSkeleton />
            <WineCardSkeleton />
          </div>
        )}
      </div>
    </div>
  );
}
