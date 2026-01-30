/**
 * Main chat container component for Pip wine assistant
 */

import { useRef, useEffect, useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { TypingIndicator } from './TypingIndicator';
import { SavedToast } from '../shared';
import { useSavedBottles } from '../../hooks';
import { useAuth } from '../../context/AuthContext';
import { useChatContext } from '../../context/ChatContext';
import type { Wine, ChatAction, ChatCard } from '../../types';

export function ChatContainer() {
  const { messages, isLoading, expectsCards, sendMessage, handleAction } = useChatContext();
  const { saveBottle } = useSavedBottles();
  const { isAuthenticated } = useAuth();
  const queryClient = useQueryClient();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showSavedToast, setShowSavedToast] = useState(false);
  const [savedWineName, setSavedWineName] = useState<string | undefined>();

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Invalidate cellar/saved queries when messages change (to catch backend updates)
  useEffect(() => {
    if (messages.length > 0 && isAuthenticated) {
      const lastMessage = messages[messages.length - 1];

      // If last message is from assistant with cellar-related intent, refetch
      if (lastMessage.role === 'assistant' && lastMessage.intent) {
        const cellarIntents = ['cellar_add', 'cellar_remove', 'rate', 'cellar_query'];

        if (cellarIntents.includes(lastMessage.intent)) {
          // Invalidate both cellar and saved bottles to ensure sidebar updates
          queryClient.invalidateQueries({ queryKey: ['cellar'] });
          queryClient.invalidateQueries({ queryKey: ['savedBottles'] });
        }
      }
    }
  }, [messages, isAuthenticated, queryClient]);

  const handleSaveWineClick = useCallback(
    async (wine: Wine) => {
      if (!isAuthenticated) return;
      try {
        await saveBottle({ wine_id: wine.id });
        setSavedWineName(wine.name);
        setShowSavedToast(true);
      } catch (error) {
        console.error('Failed to save wine:', error);
      }
    },
    [isAuthenticated, saveBottle]
  );

  const handleToastComplete = useCallback(() => {
    setShowSavedToast(false);
    setSavedWineName(undefined);
  }, []);

  const handleActionClick = useCallback(
    async (action: ChatAction, cardContext?: ChatCard) => {
      // Special handling for photo action - trigger file input
      if (action.type === 'photo') {
        fileInputRef.current?.click();
        return;
      }

      // Delegate to the hook's handler
      await handleAction(action, cardContext);
    },
    [handleAction]
  );

  const handleImageUpload = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;

      // Convert to base64
      const reader = new FileReader();
      reader.onload = async (e) => {
        const base64 = e.target?.result as string;
        // Send with a message
        await sendMessage('Identify this wine', base64);
      };
      reader.readAsDataURL(file);

      // Reset input
      if (event.target) {
        event.target.value = '';
      }
    },
    [sendMessage]
  );

  // Handle example query clicks
  const handleExampleQuery = useCallback(
    async (query: string) => {
      // Special handling for image upload query
      if (query.toLowerCase().includes('scan')) {
        fileInputRef.current?.click();
        return;
      }
      await sendMessage(query);
    },
    [sendMessage]
  );

  return (
    <>
      <div className="flex flex-col h-full">
        {/* Messages area */}
        <div className="flex-1 overflow-y-auto py-6 pb-24 space-y-6">
          {messages.map((message) => (
            <ChatMessage
              key={message.id}
              message={message}
              onSaveWine={handleSaveWineClick}
              onAction={handleActionClick}
              onExampleQuery={handleExampleQuery}
            />
          ))}
          {isLoading && <TypingIndicator showSkeletonCards={expectsCards} />}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area - fixed at bottom */}
        <div className="fixed bottom-0 left-0 right-0 p-4 pb-6 bg-gradient-to-t from-cream via-cream to-transparent">
          <div className="max-w-3xl mx-auto">
            <ChatInput
              onSend={sendMessage}
              onCameraClick={() => fileInputRef.current?.click()}
              isLoading={isLoading}
            />
          </div>

          {/* Hidden file input for image upload */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
            className="hidden"
          />
        </div>
      </div>

      {/* Saved toast notification */}
      <SavedToast
        isVisible={showSavedToast}
        wineName={savedWineName}
        onComplete={handleToastComplete}
      />
    </>
  );
}
