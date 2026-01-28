/**
 * Individual chat message component with support for cards and actions
 */

import { User } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import type { ChatMessage as ChatMessageType, Wine, ChatAction, ChatCard } from '../../types';
import { WineCard } from './WineCard';
import { CellarCard } from './CellarCard';
import { ActionButtons } from './ActionButtons';

interface ChatMessageProps {
  message: ChatMessageType;
  onSaveWine?: (wine: Wine) => void;
  onAction?: (action: ChatAction, cardContext?: ChatCard) => void;
}

export function ChatMessage({ message, onSaveWine, onAction }: ChatMessageProps) {
  const isUser = message.role === 'user';

  // Render cards based on type
  const renderCards = () => {
    if (!message.cards || message.cards.length === 0) return null;

    return (
      <div className="mt-4 space-y-3 w-full">
        {message.cards.map((card, index) => {
          if (card.type === 'wine' || card.type === 'identified_wine' || card.type === 'saved') {
            // Convert card to WineRecommendation format for WineCard
            const wineRec = {
              wine: {
                id: card.wine_id || `temp-${index}`,
                name: card.wine_name || 'Unknown Wine',
                producer: card.producer || null,
                vintage: card.vintage || null,
                wine_type: card.wine_type || 'red',
                varietal: card.varietal || null,
                country: card.country || null,
                region: card.region || null,
                price_usd: card.price_usd || null,
              } as Wine,
              explanation: card.explanation || '',
              relevance_score: card.relevance_score || 0,
              is_saved: card.type === 'saved' ? true : (card.is_saved || false),
              is_in_cellar: card.is_in_cellar || false,
            };

            return (
              <div key={`${card.wine_id || card.saved_id}-${index}`}>
                <WineCard
                  recommendation={wineRec}
                  cardType={card.type}
                  onSave={onSaveWine}
                />
                {/* Card-specific actions for identified wines */}
                {card.type === 'identified_wine' && onAction && (
                  <div className="mt-3 ml-20">
                    <ActionButtons
                      actions={[
                        { type: 'add_cellar', label: 'Add to cellar' },
                        { type: 'tell_more', label: 'Tell me more' },
                        { type: 'find_similar', label: 'Find similar' },
                      ]}
                      onAction={onAction}
                      cardContext={card}
                    />
                  </div>
                )}
                {/* Card-specific actions for saved wines */}
                {card.type === 'saved' && onAction && (
                  <div className="mt-3 ml-20">
                    <ActionButtons
                      actions={[
                        { type: 'add_cellar', label: 'Add to cellar' },
                        { type: 'tell_more', label: 'Tell me more' },
                      ]}
                      onAction={onAction}
                      cardContext={card}
                    />
                  </div>
                )}
              </div>
            );
          }

          if (card.type === 'cellar') {
            return (
              <CellarCard
                key={`${card.bottle_id}-${index}`}
                card={card}
                onAction={onAction}
              />
            );
          }

          return null;
        })}
      </div>
    );
  };

  // Render legacy recommendations (backward compatibility)
  const renderRecommendations = () => {
    if (!message.recommendations || message.recommendations.length === 0) return null;
    if (message.cards && message.cards.length > 0) return null; // Don't double-render

    return (
      <div className="mt-4 space-y-3 w-full">
        {message.recommendations.map((rec) => (
          <WineCard
            key={rec.wine.id}
            recommendation={rec}
            onSave={onSaveWine}
          />
        ))}
      </div>
    );
  };

  return (
    <div className={`flex gap-4 ${isUser ? 'flex-row-reverse' : ''}`}>
      {/* Avatar */}
      {isUser ? (
        <div className="w-10 h-10 rounded-full bg-cream-dark flex items-center justify-center flex-shrink-0">
          <User className="w-5 h-5 text-gray-600" />
        </div>
      ) : (
        <div className="w-10 h-10 rounded-full bg-wine-600 flex items-center justify-center flex-shrink-0">
          <span className="font-serif text-white text-lg">P</span>
        </div>
      )}

      {/* Message content */}
      <div className={`flex-1 max-w-[85%] flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Sender label and timestamp */}
        <div className={`flex items-center gap-3 mb-2 ${isUser ? 'flex-row-reverse' : ''}`}>
          <span className="font-mono text-[10px] uppercase tracking-wider text-gray-900 font-medium">
            {isUser ? 'You' : 'Pip'}
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
          {isUser ? (
            <p className="text-sm leading-relaxed whitespace-pre-wrap">
              {message.content}
            </p>
          ) : (
            <div className="text-sm leading-relaxed font-serif prose prose-sm prose-gray max-w-none">
              <ReactMarkdown
                components={{
                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                  strong: ({ children }) => <strong className="font-semibold text-gray-900">{children}</strong>,
                  ol: ({ children }) => <ol className="list-decimal list-inside mb-2 space-y-1">{children}</ol>,
                  ul: ({ children }) => <ul className="list-disc list-inside mb-2 space-y-1">{children}</ul>,
                  li: ({ children }) => <li className="text-gray-700">{children}</li>,
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Cards (new system) */}
        {renderCards()}

        {/* Legacy recommendations */}
        {renderRecommendations()}

        {/* Action buttons */}
        {!isUser && message.actions && message.actions.length > 0 && onAction && (
          <div className="mt-3">
            <ActionButtons
              actions={message.actions}
              onAction={onAction}
            />
          </div>
        )}
      </div>
    </div>
  );
}
