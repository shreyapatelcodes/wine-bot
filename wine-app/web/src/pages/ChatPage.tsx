/**
 * Chat page - main recommendation interface
 */

import { ChatContainer } from '../components/chat';

export function ChatPage() {
  return (
    <div className="max-w-3xl mx-auto px-4 py-6 h-[calc(100vh-4rem)]">
      <ChatContainer />
    </div>
  );
}
