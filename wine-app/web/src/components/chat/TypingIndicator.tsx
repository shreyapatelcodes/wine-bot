/**
 * Typing indicator component for chat
 */

export function TypingIndicator() {
  return (
    <div className="flex gap-4 items-start">
      {/* P avatar */}
      <div className="w-10 h-10 rounded-full bg-wine-600 flex items-center justify-center flex-shrink-0">
        <span className="font-serif text-white text-lg">P</span>
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
    </div>
  );
}
