/**
 * Chat page - main recommendation interface
 */

import { ChatContainer } from '../components/chat';

export function ChatPage() {
  return (
    <div className="h-screen flex flex-col">
      {/* Page header */}
      <header className="px-6 md:px-8 pt-8 pb-4">
        <div className="max-w-4xl mx-auto">
          <p className="font-mono text-xs uppercase tracking-widest text-gray-400 mb-2">
            AI Wine Agent / Sommelier Chat
          </p>
          <h1 className="font-serif italic text-4xl md:text-5xl text-wine-600">
            The Perfect Pour.
          </h1>
          <p className="font-mono text-xs uppercase tracking-wider text-gray-500 mt-4 max-w-lg">
            Tell us about what you're looking for — flavors, regions you enjoy, your budget, or what you'll be pairing it with.
          </p>
        </div>
      </header>

      {/* Chat container */}
      <div className="flex-1 px-6 md:px-8 pb-6 overflow-hidden">
        <div className="max-w-4xl mx-auto h-full">
          <ChatContainer />
        </div>
      </div>
    </div>
  );
}
