/**
 * Cellar bottle card for display in chat
 */

import { Wine as WineIcon, Star, Package } from 'lucide-react';
import type { ChatCard, ChatAction } from '../../types';
import { ActionButtons } from './ActionButtons';

interface CellarCardProps {
  card: ChatCard;
  onAction?: (action: ChatAction, cardContext?: ChatCard) => void;
}

export function CellarCard({ card, onAction }: CellarCardProps) {
  const getWineTypeColor = (type?: string) => {
    switch (type) {
      case 'red':
        return 'text-red-700';
      case 'white':
        return 'text-amber-600';
      case 'rosé':
        return 'text-pink-600';
      case 'sparkling':
        return 'text-yellow-600';
      default:
        return 'text-gray-600';
    }
  };

  const getStatusBadge = (status?: string) => {
    switch (status) {
      case 'owned':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider bg-green-100 text-green-700 rounded">
            <Package className="w-3 h-3" />
            Owned
          </span>
        );
      case 'tried':
        return (
          <span className="inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider bg-purple-100 text-purple-700 rounded">
            <Star className="w-3 h-3" />
            Tried
          </span>
        );
      case 'wishlist':
        return (
          <span className="px-2 py-0.5 text-[10px] font-mono uppercase tracking-wider bg-amber-100 text-amber-700 rounded">
            Wishlist
          </span>
        );
      default:
        return null;
    }
  };

  const cardActions: ChatAction[] = [
    { type: 'tell_more', label: 'Details' },
  ];

  if (card.status === 'owned' && (card.quantity ?? 0) > 0) {
    cardActions.push({ type: 'decide', label: 'Drink tonight?' });
  }

  return (
    <div className="bg-white border border-gray-100 rounded-xl p-4 hover:shadow-md transition-all">
      <div className="flex gap-3">
        {/* Wine icon */}
        <div className="w-12 h-16 bg-cream rounded-lg flex items-center justify-center flex-shrink-0">
          <WineIcon className={`w-6 h-6 ${getWineTypeColor(card.wine_type)}`} />
        </div>

        <div className="flex-1 min-w-0">
          {/* Status and quantity */}
          <div className="flex items-center gap-2 mb-1">
            {getStatusBadge(card.status)}
            {card.quantity && card.quantity > 1 && (
              <span className="text-[10px] font-mono text-gray-500">
                x{card.quantity}
              </span>
            )}
          </div>

          {/* Wine name */}
          <h4 className="font-serif text-base text-gray-900 leading-tight truncate">
            {card.wine_name}
          </h4>

          {/* Producer and region */}
          <p className="font-mono text-[10px] uppercase tracking-wider text-gray-500 mt-0.5">
            {[card.producer, card.region].filter(Boolean).join(' \u2022 ')}
          </p>

          {/* Rating */}
          {card.rating && (
            <div className="flex items-center gap-1 mt-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <Star
                  key={star}
                  className={`w-3.5 h-3.5 ${
                    star <= card.rating!
                      ? 'fill-amber-400 text-amber-400'
                      : 'text-gray-300'
                  }`}
                />
              ))}
              <span className="text-xs text-gray-500 ml-1">{card.rating}/5</span>
            </div>
          )}
        </div>
      </div>

      {/* Actions */}
      {onAction && (
        <div className="mt-3 pt-3 border-t border-gray-50">
          <ActionButtons
            actions={cardActions}
            onAction={onAction}
            cardContext={card}
          />
        </div>
      )}
    </div>
  );
}
