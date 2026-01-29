/**
 * Main chat container component for Pip wine assistant
 */

import { useRef, useEffect, useState, useCallback } from 'react';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { TypingIndicator } from './TypingIndicator';
import { SavedToast } from '../shared';
import { useChat, useSavedBottles } from '../../hooks';
import { useAuth } from '../../context/AuthContext';
import type { Wine, ChatAction, ChatCard } from '../../types';

export function ChatContainer() {
  const { messages, isLoading, expectsCards, sendMessage, handleAction } = useChat();
  const { saveBottle } = useSavedBottles();
  const { isAuthenticated } = useAuth();
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showSavedToast, setShowSavedToast] = useState(false);
  const [savedWineName, setSavedWineName] = useState<string | undefined>();

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

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
