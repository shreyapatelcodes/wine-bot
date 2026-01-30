/**
 * Chat context for sharing chat state and actions across components
 */

import { createContext, useContext } from 'react';
import type { ReactNode } from 'react';
import { useChat } from '../hooks';
import type { ChatMessage, ChatAction, ChatCard } from '../types';

interface ChatContextType {
  messages: ChatMessage[];
  isLoading: boolean;
  expectsCards: boolean;
  error: string | null;
  sessionId: string | null;
  sendMessage: (content: string, imageBase64?: string) => Promise<void>;
  handleAction: (action: ChatAction, cardContext?: ChatCard) => Promise<void>;
  clearChat: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const chat = useChat();

  return (
    <ChatContext.Provider value={chat}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChatContext() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChatContext must be used within ChatProvider');
  }
  return context;
}
