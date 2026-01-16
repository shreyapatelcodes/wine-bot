/**
 * Chat hook for managing conversation state
 */

import { useState, useCallback } from 'react';
import { api } from '../services/api';
import type { ChatMessage, WineRecommendation, RecommendationRequest } from '../types';

interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  sendMessage: (content: string, options?: Partial<RecommendationRequest>) => Promise<void>;
  clearChat: () => void;
}

function generateId(): string {
  return Math.random().toString(36).substring(2, 15);
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hello! I'm your wine sommelier. Tell me what you're looking for - whether it's a specific occasion, food pairing, or just exploring something new. I'll help you find the perfect wine.",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = useCallback(async (content: string, options?: Partial<RecommendationRequest>) => {
    // Add user message
    const userMessage: ChatMessage = {
      id: generateId(),
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      const response = await api.getRecommendations({
        description: content,
        ...options,
      });

      // Create assistant response
      let assistantContent: string;
      let recommendations: WineRecommendation[] | undefined;

      if (response.recommendations.length > 0) {
        assistantContent = `I found ${response.count} wine${response.count > 1 ? 's' : ''} that might be perfect for you:`;
        recommendations = response.recommendations;
      } else {
        assistantContent = "I'm still learning about wines. Currently, the recommendation engine is being set up. In the meantime, you can search for wines directly or tell me more about what you're looking for, and I'll do my best to help!";
      }

      const assistantMessage: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: assistantContent,
        timestamp: new Date().toISOString(),
        recommendations,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to get recommendations';
      setError(errorMessage);

      // Add error message to chat
      const errorChatMessage: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: `I'm sorry, I encountered an error: ${errorMessage}. Please try again.`,
        timestamp: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errorChatMessage]);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearChat = useCallback(() => {
    setMessages([
      {
        id: 'welcome',
        role: 'assistant',
        content: "Hello! I'm your wine sommelier. Tell me what you're looking for - whether it's a specific occasion, food pairing, or just exploring something new. I'll help you find the perfect wine.",
        timestamp: new Date().toISOString(),
      },
    ]);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    clearChat,
  };
}
