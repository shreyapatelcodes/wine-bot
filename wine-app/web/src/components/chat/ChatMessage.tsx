/**
 * Individual chat message component
 */

import { User } from 'lucide-react';
import type { ChatMessage as ChatMessageType } from '../../types';
import { WineCard } from './WineCard';

interface ChatMessageProps {
  message: ChatMessageType;
  onSaveWine?: (wineId: string) => void;
}

export function ChatMessage({ message, onSaveWine }: ChatMessageProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex gap-4 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      {isUser ? (
        <div className="w-10 h-10 rounded-full bg-cream-dark flex items-center justify-center flex-shrink-0">
          <User className="w-5 h-5 text-gray-600" />
        </div>
      ) : (
        <div className="w-10 h-10 rounded-full bg-wine-600 flex items-center justify-center flex-shrink-0">
          <span className="font-serif text-white text-lg">V</span>
        </div>
      )}

      {/* Message content */}
      <div className={`flex-1 max-w-[75%] flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Sender label and timestamp */}
        <div className={`flex items-center gap-3 mb-2 ${isUser ? 'flex-row-reverse' : ''}`}>
          <span className="font-mono text-[10px] uppercase tracking-wider text-gray-900 font-medium">
            {isUser ? 'You' : 'Sommelier AI'}
          </span>
          <span className="font-mono text-[10px] uppercase tracking-wider text-gray-400">
            {new Date(message.timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
        </div>

        {/* Message bubble */}
        <div
          className={`px-5 py-3 ${
            isUser
              ? 'bg-cream-dark text-gray-900 rounded-2xl rounded-tr-sm'
              : 'bg-white border border-gray-100 text-gray-800 rounded-2xl rounded-tl-sm shadow-sm'
          }`}
        >
          <p className={`text-sm leading-relaxed whitespace-pre-wrap ${!isUser ? 'font-serif italic' : ''}`}>
            {message.content}
          </p>
        </div>

        {/* Wine recommendations */}
        {message.recommendations && message.recommendations.length > 0 && (
          <div className="mt-4 space-y-3 w-full">
            {message.recommendations.map((rec) => (
              <WineCard
                key={rec.wine.id}
                recommendation={rec}
                onSave={onSaveWine}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
