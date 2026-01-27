/**
 * Wine recommendation card component
 */

import { Bookmark, BookmarkCheck, Wine as WineIcon } from 'lucide-react';
import type { WineRecommendation, Wine } from '../../types';
import { useAuth } from '../../context/AuthContext';

interface WineCardProps {
  recommendation: WineRecommendation;
  onSave?: (wine: Wine) => void;
}

export function WineCard({ recommendation, onSave }: WineCardProps) {
  const { wine, explanation, is_saved, is_in_cellar } = recommendation;
  const { isAuthenticated } = useAuth();

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

  return (
    <div className="bg-white/50 border border-wine-600/10 rounded-xl p-5 hover:shadow-lg transition-all group">
      <div className="flex gap-4">
        {/* Wine image placeholder */}
        <div className="w-16 h-24 bg-cream rounded-lg flex items-center justify-center flex-shrink-0 overflow-hidden">
          <WineIcon className={`w-8 h-8 ${getWineTypeColor(wine.wine_type)}`} />
        </div>

        <div className="flex-1 min-w-0">
          {/* Wine type label */}
          <span className="font-mono text-[10px] uppercase tracking-wider text-wine-600">
            Recommendation
          </span>

          {/* Wine name */}
          <h3 className="font-serif text-lg text-gray-900 mt-1 leading-tight">
            {wine.name}
          </h3>

          {/* Location, vintage, price */}
          <p className="font-mono text-[10px] uppercase tracking-wider text-gray-500 mt-1">
            {[wine.region, wine.country].filter(Boolean).join(', ')}
            {wine.price_usd && ` \u2022 $${wine.price_usd.toFixed(0)}`}
          </p>
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
