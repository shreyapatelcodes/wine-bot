/**
 * Individual chat message component
 */

import { User, Bot } from 'lucide-react';
import type { ChatMessage as ChatMessageType } from '../../types';
import { WineCard } from './WineCard';

interface ChatMessageProps {
  message: ChatMessageType;
  onSaveWine?: (wineId: string) => void;
}

export function ChatMessage({ message, onSaveWine }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      <div
        className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser ? 'bg-wine-600' : 'bg-gray-100'
        }`}
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-gray-600" />
        )}
      </div>

      {/* Message content */}
      <div className={`flex-1 max-w-[80%] ${isUser ? 'text-right' : ''}`}>
        <div
          className={`inline-block px-4 py-2 rounded-2xl ${
            isUser
              ? 'bg-wine-600 text-white rounded-tr-sm'
              : 'bg-gray-100 text-gray-900 rounded-tl-sm'
          }`}
        >
          <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        </div>

        {/* Wine recommendations */}
        {message.recommendations && message.recommendations.length > 0 && (
          <div className="mt-3 space-y-3">
            {message.recommendations.map((rec) => (
              <WineCard
                key={rec.wine.id}
                recommendation={rec}
                onSave={onSaveWine}
              />
            ))}
          </div>
        )}

        {/* Timestamp */}
        <p className={`text-xs text-gray-400 mt-1 ${isUser ? 'text-right' : ''}`}>
          {new Date(message.timestamp).toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </p>
      </div>
    </div>
  );
}
