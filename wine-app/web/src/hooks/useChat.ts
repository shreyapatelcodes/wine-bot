/**
 * Chat hook for managing conversation state with Pip
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import type {
  ChatMessage,
  ChatResponse,
  ChatCard,
  ChatAction,
  IntentType,
} from '../types';

interface UseChatReturn {
  messages: ChatMessage[];
  isLoading: boolean;
  expectsCards: boolean;
  error: string | null;
  sessionId: string | null;
  sendMessage: (content: string, imageBase64?: string) => Promise<void>;
  handleAction: (action: ChatAction, cardContext?: ChatCard) => Promise<void>;
  clearChat: () => void;
}

// Keywords that suggest the response will include wine cards
const CARD_KEYWORDS = [
  'recommend', 'find', 'suggest', 'looking for', 'want a', 'need a',
  'cellar', 'saved', 'my wines', 'what wines',
  'show me', 'what do i have', 'identify', 'scan',
  'tried', 'want to try', 'wines to try',
];

function expectsCardsFromMessage(message: string): boolean {
  const lower = message.toLowerCase();
  return CARD_KEYWORDS.some(keyword => lower.includes(keyword));
}

function generateId(): string {
  return Math.random().toString(36).substring(2, 15);
}

function createWelcomeMessage(isAuthenticated: boolean): ChatMessage {
  const baseActions: ChatAction[] = [
    { type: 'recommend', label: 'Find a wine' },
    { type: 'educate', label: 'Learn about wine' },
    { type: 'photo', label: 'Scan a label' },
  ];

  const authActions: ChatAction[] = [
    { type: 'cellar', label: 'My Cellar' },
    { type: 'tried', label: 'Tried' },
    { type: 'want_to_try', label: 'Want to Try' },
  ];

  return {
    id: 'welcome',
    role: 'assistant',
    content: "Hey! I'm Pip, your wine guide. I can help you discover wines, answer questions, manage your collection, or identify bottles from photos. What are you in the mood for?",
    timestamp: new Date().toISOString(),
    actions: isAuthenticated ? [...baseActions, ...authActions] : baseActions,
  };
}

export function useChat(): UseChatReturn {
  const { isAuthenticated } = useAuth();
  const [messages, setMessages] = useState<ChatMessage[]>(() => [createWelcomeMessage(isAuthenticated)]);
  const [isLoading, setIsLoading] = useState(false);
  const [expectsCards, setExpectsCards] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);

  // Track conversation history for context
  const historyRef = useRef<Array<{ role: string; content: string }>>([]);

  // Update welcome message when auth state changes
  useEffect(() => {
    setMessages((prev) => {
      // Only update if the first message is the welcome message
      if (prev[0]?.id === 'welcome') {
        return [createWelcomeMessage(isAuthenticated), ...prev.slice(1)];
      }
      return prev;
    });
  }, [isAuthenticated]);

  const addMessage = useCallback((message: ChatMessage) => {
    setMessages((prev) => [...prev, message]);
    // Update history for context
    historyRef.current.push({
      role: message.role,
      content: message.content,
    });
    // Keep history manageable
    if (historyRef.current.length > 20) {
      historyRef.current = historyRef.current.slice(-20);
    }
  }, []);

  const sendMessage = useCallback(
    async (content: string, imageBase64?: string) => {
      // Add user message
      const userMessage: ChatMessage = {
        id: generateId(),
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      };
      addMessage(userMessage);
      setIsLoading(true);
      setExpectsCards(expectsCardsFromMessage(content) || !!imageBase64);
      setError(null);

      try {
        const response: ChatResponse = await api.chat({
          message: content,
          session_id: sessionId || undefined,
          image_base64: imageBase64,
          history: historyRef.current.slice(-10), // Send last 10 messages for context
        });

        // Store session ID for continuity
        if (response.session_id) {
          setSessionId(response.session_id);
        }

        // Create assistant message
        const assistantMessage: ChatMessage = {
          id: generateId(),
          role: 'assistant',
          content: response.response,
          timestamp: new Date().toISOString(),
          intent: response.intent as IntentType,
          cards: response.cards,
          actions: response.actions,
        };

        addMessage(assistantMessage);

        // Handle special cases
        if (response.requires_auth) {
          // Could trigger login modal here
          console.log('Auth required for this action');
        }

        if (response.error) {
          setError(response.error);
        }
      } catch (err) {
        const errorMessage =
          err instanceof Error ? err.message : 'Failed to send message';
        setError(errorMessage);

        // Add error message to chat
        const errorChatMessage: ChatMessage = {
          id: generateId(),
          role: 'assistant',
          content: `I'm having trouble connecting right now. Please try again.`,
          timestamp: new Date().toISOString(),
        };
        addMessage(errorChatMessage);
      } finally {
        setIsLoading(false);
        setExpectsCards(false);
      }
    },
    [sessionId, addMessage]
  );

  const handleAction = useCallback(
    async (action: ChatAction, cardContext?: ChatCard) => {
      // Handle different action types
      switch (action.type) {
        case 'recommend':
          await sendMessage('Help me find a wine');
          break;

        case 'educate':
          await sendMessage("I'd like to learn about wine");
          break;

        case 'learn_topic':
          // The label contains the topic to learn about
          if (action.label) {
            await sendMessage(`Tell me about ${action.label}`);
          }
          break;

        case 'cellar':
          await sendMessage("What's in my cellar?");
          break;

        case 'tried':
          await sendMessage("What wines have I tried?");
          break;

        case 'want_to_try':
          await sendMessage("What wines do I want to try?");
          break;

        case 'photo':
          // This should trigger the image upload UI
          // The actual image will be sent via sendMessage with imageBase64
          break;

        case 'save':
          if (cardContext?.wine_id) {
            await sendMessage(`Save the ${cardContext.wine_name || 'wine'}`);
          }
          break;

        case 'add_cellar':
          if (cardContext?.wine_name) {
            await sendMessage(`Add ${cardContext.wine_name} to my cellar`);
          } else {
            await sendMessage('Add this to my cellar');
          }
          break;

        case 'tell_more':
          if (cardContext?.wine_name) {
            await sendMessage(`Tell me more about ${cardContext.wine_name}`);
          }
          break;

        case 'find_similar':
          if (cardContext?.wine_name) {
            await sendMessage(`Find wines similar to ${cardContext.wine_name}`);
          }
          break;

        case 'view_cellar':
          await sendMessage('Show me my cellar');
          break;

        case 'undo':
          await sendMessage('Undo that');
          break;

        case 'confirm':
          await sendMessage('Yes, confirm');
          break;

        case 'cancel':
          await sendMessage("Actually, never mind");
          break;

        case 'recommend_new':
          await sendMessage('Recommend something new');
          break;

        case 'pick_from_cellar':
          await sendMessage('Pick from my cellar');
          break;

        case 'remove_bottle':
          if (cardContext?.wine_name) {
            await sendMessage(`Remove ${cardContext.wine_name} from my cellar`);
          } else {
            await sendMessage('Remove this from my cellar');
          }
          break;

        case 'confirm_tried':
          await sendMessage('Yes, move it to tried');
          break;

        case 'keep_owned':
          await sendMessage('No, keep it in my cellar');
          break;

        case 'mark_tried':
          if (cardContext?.wine_name) {
            await sendMessage(`I tried ${cardContext.wine_name}`);
          } else {
            await sendMessage('I tried this wine');
          }
          break;

        // Budget selection actions
        case 'budget_under_20':
          await sendMessage('Under $20');
          break;
        case 'budget_20_40':
          await sendMessage('$20-40');
          break;
        case 'budget_40_plus':
          await sendMessage('$40+');
          break;
        case 'budget_any':
          await sendMessage('No budget');
          break;

        // Food pairing actions
        case 'pairing_meat':
          await sendMessage('Meat or steak');
          break;
        case 'pairing_fish':
          await sendMessage('Fish or seafood');
          break;
        case 'pairing_pasta':
          await sendMessage('Pasta');
          break;
        case 'pairing_none':
          await sendMessage('No food pairing');
          break;

        // Wine type actions
        case 'type_red':
          await sendMessage('Red wine');
          break;
        case 'type_white':
          await sendMessage('White wine');
          break;
        case 'type_rose':
          await sendMessage('Rosé');
          break;
        case 'type_any':
          await sendMessage('Surprise me');
          break;

        default:
          // For any other action, send it as a message
          if (action.label) {
            await sendMessage(action.label);
          }
      }
    },
    [sendMessage]
  );

  const clearChat = useCallback(() => {
    setMessages([createWelcomeMessage(isAuthenticated)]);
    setError(null);
    setSessionId(null);
    historyRef.current = [];
  }, [isAuthenticated]);

  return {
    messages,
    isLoading,
    expectsCards,
    error,
    sessionId,
    sendMessage,
    handleAction,
    clearChat,
  };
}
