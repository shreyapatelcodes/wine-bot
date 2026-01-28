/**
 * Wine recommendation card component
 */

import { Bookmark, BookmarkCheck, Wine as WineIcon, Camera, Star, Package } from 'lucide-react';
import type { WineRecommendation, Wine } from '../../types';
import { useAuth } from '../../context/AuthContext';

type CardType = 'wine' | 'identified_wine' | 'saved' | 'cellar';

interface WineCardProps {
  recommendation: WineRecommendation & {
    status?: string;
    quantity?: number;
    rating?: number;
  };
  cardType?: CardType;
  onSave?: (wine: Wine) => void;
}

export function WineCard({ recommendation, cardType = 'wine', onSave }: WineCardProps) {
  const { wine, explanation, is_saved, is_in_cellar, status, quantity, rating } = recommendation;
  const { isAuthenticated } = useAuth();
  const isCellar = cardType === 'cellar';

  const getWineTypeColor = (type: string) => {
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

  const getCardLabel = () => {
    switch (cardType) {
      case 'identified_wine':
        return 'Identified';
      case 'saved':
        return 'Saved';
      case 'cellar':
        return status === 'owned' ? 'Owned' : 'Tried';
      default:
        return 'Recommendation';
    }
  };

  const isIdentified = cardType === 'identified_wine';

  const getStatusColor = () => {
    if (cardType !== 'cellar') return 'text-wine-600';
    return status === 'owned' ? 'text-green-600' : 'text-purple-600';
  };

  return (
    <div className="bg-white/50 border border-wine-600/10 rounded-xl p-5 hover:shadow-lg transition-all group">
      <div className="flex gap-4">
        {/* Wine image placeholder */}
        <div className="w-16 h-24 bg-cream rounded-lg flex items-center justify-center flex-shrink-0 overflow-hidden">
          {isIdentified ? (
            <Camera className={`w-8 h-8 ${getWineTypeColor(wine.wine_type)}`} />
          ) : (
            <WineIcon className={`w-8 h-8 ${getWineTypeColor(wine.wine_type)}`} />
          )}
        </div>

        <div className="flex-1 min-w-0">
          {/* Card type label */}
          <div className="flex items-center gap-2">
            <span className={`font-mono text-[10px] uppercase tracking-wider ${isIdentified ? 'text-blue-600' : getStatusColor()}`}>
              {isCellar && status === 'owned' && <Package className="w-3 h-3 inline mr-1" />}
              {isCellar && status === 'tried' && <Star className="w-3 h-3 inline mr-1" />}
              {getCardLabel()}
            </span>
            {isCellar && quantity && quantity > 1 && (
              <span className="font-mono text-[10px] text-gray-500">
                x{quantity}
              </span>
            )}
          </div>

          {/* Wine name */}
          <h3 className="font-serif text-lg text-gray-900 mt-1 leading-tight">
            {wine.name}
          </h3>

          {/* Producer */}
          {wine.producer && (
            <p className="text-sm text-gray-600 mt-0.5">
              {wine.producer}
            </p>
          )}

          {/* Varietal, Region, Country */}
          <p className="font-mono text-[10px] uppercase tracking-wider text-gray-500 mt-1">
            {[wine.varietal, wine.region, wine.country].filter(Boolean).join(' · ')}
          </p>

          {/* Vintage and Price */}
          {(wine.vintage || wine.price_usd) && (
            <p className="font-mono text-[10px] uppercase tracking-wider text-gray-500 mt-0.5">
              {wine.vintage && `${wine.vintage}`}
              {wine.vintage && wine.price_usd && ' · '}
              {wine.price_usd && `$${wine.price_usd.toFixed(0)}`}
            </p>
          )}

          {/* Rating for cellar cards */}
          {isCellar && rating && (
            <div className="flex items-center gap-1 mt-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <Star
                  key={star}
                  className={`w-3.5 h-3.5 ${
                    star <= rating
                      ? 'fill-amber-400 text-amber-400'
                      : 'text-gray-300'
                  }`}
                />
              ))}
              <span className="text-xs text-gray-500 ml-1">{rating}/5</span>
            </div>
          )}
        </div>

        {/* Save button */}
        {isAuthenticated && onSave && !is_in_cellar && (
          <button
            onClick={() => onSave(wine)}
            className={`self-start p-2 rounded-xl transition-colors ${
              is_saved
                ? 'bg-wine-100 text-wine-600'
                : 'bg-gray-100 text-gray-400 hover:bg-wine-50 hover:text-wine-500'
            }`}
            title={is_saved ? 'Saved' : 'Save wine'}
          >
            {is_saved ? (
              <BookmarkCheck className="w-5 h-5" />
            ) : (
              <Bookmark className="w-5 h-5" />
            )}
          </button>
        )}
        {is_in_cellar && (
          <span className="self-start font-mono text-[10px] uppercase tracking-wider bg-green-100 text-green-700 px-3 py-1.5 rounded-lg">
            In Cellar
          </span>
        )}
      </div>

      {/* Explanation */}
      {explanation && (
        <p className="text-sm text-gray-600 mt-4 pt-4 border-t border-gray-100 leading-relaxed italic">
          "{explanation}"
        </p>
      )}
    </div>
  );
}
