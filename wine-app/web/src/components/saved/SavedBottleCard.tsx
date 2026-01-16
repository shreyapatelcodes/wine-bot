/**
 * Card component for saved bottles
 */

import { Trash2, ArrowRightCircle, Wine, MapPin, DollarSign, Calendar } from 'lucide-react';
import type { SavedBottle } from '../../types';

interface SavedBottleCardProps {
  bottle: SavedBottle;
  onRemove: (id: string) => void;
  onMoveToCellar: (id: string) => void;
  isRemoving?: boolean;
  isMoving?: boolean;
}

export function SavedBottleCard({
  bottle,
  onRemove,
  onMoveToCellar,
  isRemoving,
  isMoving,
}: SavedBottleCardProps) {
  const { wine } = bottle;

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
      <div className="flex items-start gap-4">
        {/* Wine icon */}
        <div className={`p-3 rounded-lg ${getWineTypeColor(wine.wine_type)}`}>
          <Wine className="w-6 h-6" />
        </div>

        {/* Wine details */}
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900">{wine.name}</h3>
          {wine.producer && (
            <p className="text-sm text-gray-500">{wine.producer}</p>
          )}

          {/* Attributes */}
          <div className="flex flex-wrap items-center gap-2 mt-2">
            <span className={`text-xs px-2 py-1 rounded-full ${getWineTypeColor(wine.wine_type)}`}>
              {wine.wine_type}
            </span>
            {wine.vintage && (
              <span className="text-xs text-gray-500">{wine.vintage}</span>
            )}
            {wine.varietal && (
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                {wine.varietal}
              </span>
            )}
          </div>

          {/* Location and price */}
          <div className="flex flex-wrap items-center gap-4 mt-2 text-sm text-gray-500">
            {(wine.region || wine.country) && (
              <span className="flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                {[wine.region, wine.country].filter(Boolean).join(', ')}
              </span>
            )}
            {wine.price_usd && (
              <span className="flex items-center gap-1">
                <DollarSign className="w-4 h-4" />
                {wine.price_usd.toFixed(2)}
              </span>
            )}
          </div>

          {/* Recommendation context */}
          {bottle.recommendation_context && (
            <p className="text-xs text-gray-500 mt-2 italic">
              "{bottle.recommendation_context}"
            </p>
          )}

          {/* Notes */}
          {bottle.notes && (
            <p className="text-sm text-gray-600 mt-2">{bottle.notes}</p>
          )}

          {/* Saved date */}
          <p className="flex items-center gap-1 text-xs text-gray-400 mt-2">
            <Calendar className="w-3 h-3" />
            Saved {new Date(bottle.saved_at).toLocaleDateString()}
          </p>
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-2">
          <button
            onClick={() => onMoveToCellar(bottle.id)}
            disabled={isMoving}
            className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors disabled:opacity-50"
            title="Move to Cellar"
          >
            <ArrowRightCircle className="w-5 h-5" />
          </button>
          <button
            onClick={() => onRemove(bottle.id)}
            disabled={isRemoving}
            className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
            title="Remove"
          >
            <Trash2 className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
