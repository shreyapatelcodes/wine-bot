/**
 * Chat page - main recommendation interface
 */

import { ChatContainer } from '../components/chat';

export function ChatPage() {
  return (
    <div className="h-[calc(100vh-4rem)] flex flex-col">
      {/* Page header */}
      <header className="px-6 md:px-8 pt-4 pb-2">
        <div className="max-w-4xl mx-auto">
          <p className="font-mono text-[10px] uppercase tracking-widest text-gray-400 mb-1">
            AI Wine Agent / Pip
          </p>
          <h1 className="font-serif italic text-3xl md:text-4xl text-wine-600">
            Ask Pip.
          </h1>
          <p className="font-mono text-[10px] uppercase tracking-wider text-gray-500 mt-2 max-w-lg">
            Your personal sommelier. Ask about wines, get recommendations, or scan a label to learn more.
          </p>
        </div>
      </header>

      {/* Chat container */}
      <div className="flex-1 px-6 md:px-8 pb-4 overflow-hidden">
        <div className="max-w-4xl mx-auto h-full">
          <ChatContainer />
        </div>
      </div>
    </div>
  );
}
