/**
 * Main chat container component
 */

import { useRef, useEffect } from 'react';
import { Trash2 } from 'lucide-react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { TypingIndicator } from './TypingIndicator';
import { useChat, useSavedBottles } from '../../hooks';
import { useAuth } from '../../context/AuthContext';

const quickSuggestions = [
  'Suggest a 2018 Bordeaux',
  'Wine for Sushi?',
  'Explain Tannins',
  'Under $30 reds',
];

export function ChatContainer() {
  const { messages, isLoading, sendMessage, clearChat } = useChat();
  const { saveBottle } = useSavedBottles();
  const { isAuthenticated } = useAuth();
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSaveWine = async (wineId: string) => {
    if (!isAuthenticated) return;
    try {
      await saveBottle({ wine_id: wineId });
    } catch (error) {
      console.error('Failed to save wine:', error);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto py-6 space-y-6">
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message}
            onSaveWine={handleSaveWine}
          />
        ))}
        {isLoading && <TypingIndicator />}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="bg-white border-t border-gray-100 p-4 md:p-6 rounded-t-2xl shadow-sm">
        <ChatInput onSend={sendMessage} isLoading={isLoading} />

        {/* Quick suggestions */}
        <div className="flex flex-wrap gap-2 mt-4 justify-center">
          {quickSuggestions.map((suggestion) => (
            <button
              key={suggestion}
              onClick={() => sendMessage(suggestion)}
              disabled={isLoading}
              className="font-mono text-[10px] uppercase tracking-wider px-4 py-2 border border-gray-200 rounded-full hover:bg-cream-dark hover:border-gray-300 transition-colors text-gray-500 disabled:opacity-50"
            >
              {suggestion}
            </button>
          ))}
        </div>

        {/* Clear chat button */}
        {messages.length > 1 && (
          <div className="flex justify-center mt-4">
            <button
              onClick={clearChat}
              className="flex items-center gap-2 text-xs text-gray-400 hover:text-gray-600 transition-colors"
            >
              <Trash2 className="w-3 h-3" />
              Clear conversation
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
