/**
 * Wine recommendation card component
 */

import { Bookmark, BookmarkCheck, Wine, MapPin, DollarSign } from 'lucide-react';
import type { WineRecommendation } from '../../types';
import { useAuth } from '../../context/AuthContext';

interface WineCardProps {
  recommendation: WineRecommendation;
  onSave?: (wineId: string) => void;
}

export function WineCard({ recommendation, onSave }: WineCardProps) {
  const { wine, explanation, is_saved, is_in_cellar } = recommendation;
  const { isAuthenticated } = useAuth();

  const getWineTypeColor = (type: string) => {
    switch (type) {
      case 'red':
        return 'bg-red-100 text-red-700';
      case 'white':
        return 'bg-amber-100 text-amber-700';
      case 'rosé':
        return 'bg-pink-100 text-pink-700';
      case 'sparkling':
        return 'bg-yellow-100 text-yellow-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-3">
        {/* Wine icon */}
        <div className={`p-2 rounded-lg ${getWineTypeColor(wine.wine_type)}`}>
          <Wine className="w-5 h-5" />
        </div>

        {/* Wine details */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h3 className="font-semibold text-gray-900 text-sm leading-tight">
                {wine.name}
              </h3>
              {wine.producer && (
                <p className="text-xs text-gray-500 mt-0.5">{wine.producer}</p>
              )}
            </div>

            {/* Save button */}
            {isAuthenticated && onSave && !is_in_cellar && (
              <button
                onClick={() => onSave(wine.id)}
                className={`p-1.5 rounded-lg transition-colors ${
                  is_saved
                    ? 'bg-wine-100 text-wine-600'
                    : 'bg-gray-100 text-gray-400 hover:bg-wine-50 hover:text-wine-500'
                }`}
                title={is_saved ? 'Saved' : 'Save wine'}
              >
                {is_saved ? (
                  <BookmarkCheck className="w-4 h-4" />
                ) : (
                  <Bookmark className="w-4 h-4" />
                )}
              </button>
            )}
            {is_in_cellar && (
              <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
                In Cellar
              </span>
            )}
          </div>

          {/* Wine attributes */}
          <div className="flex flex-wrap items-center gap-2 mt-2">
            <span className={`text-xs px-2 py-0.5 rounded-full ${getWineTypeColor(wine.wine_type)}`}>
              {wine.wine_type}
            </span>
            {wine.vintage && (
              <span className="text-xs text-gray-500">{wine.vintage}</span>
            )}
            {wine.varietal && (
              <span className="text-xs text-gray-500">{wine.varietal}</span>
            )}
          </div>

          {/* Location and price */}
          <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
            {(wine.region || wine.country) && (
              <span className="flex items-center gap-1">
                <MapPin className="w-3 h-3" />
                {[wine.region, wine.country].filter(Boolean).join(', ')}
              </span>
            )}
            {wine.price_usd && (
              <span className="flex items-center gap-1">
                <DollarSign className="w-3 h-3" />
                {wine.price_usd.toFixed(0)}
              </span>
            )}
          </div>

          {/* Explanation */}
          {explanation && (
            <p className="text-xs text-gray-600 mt-2 leading-relaxed">
              {explanation}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
