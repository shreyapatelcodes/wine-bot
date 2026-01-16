/**
 * Card component for cellar bottles
 */

import { useState } from 'react';
import { Wine, MapPin, DollarSign, Star, Edit2, Trash2, Check, X, Minus, Plus } from 'lucide-react';
import type { CellarBottle, CellarBottleUpdate, CellarStatus } from '../../types';

interface CellarBottleCardProps {
  bottle: CellarBottle;
  onUpdate: (id: string, data: CellarBottleUpdate) => Promise<void>;
  onRemove: (id: string) => Promise<void>;
}

export function CellarBottleCard({ bottle, onUpdate, onRemove }: CellarBottleCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState<CellarBottleUpdate>({
    status: bottle.status,
    quantity: bottle.quantity,
    rating: bottle.rating || undefined,
    tasting_notes: bottle.tasting_notes || '',
  });

  // Get wine info from either catalog wine or custom fields
  const wineName = bottle.wine?.name || bottle.custom_wine_name || 'Unknown Wine';
  const wineProducer = bottle.wine?.producer || bottle.custom_wine_producer;
  const wineType = bottle.wine?.wine_type || bottle.custom_wine_type || 'red';
  const wineVintage = bottle.wine?.vintage || bottle.custom_wine_vintage;
  const wineVarietal = bottle.wine?.varietal;
  const wineRegion = bottle.wine?.region;
  const wineCountry = bottle.wine?.country;
  const winePrice = bottle.purchase_price || bottle.wine?.price_usd;

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

  const getStatusColor = (status: CellarStatus) => {
    switch (status) {
      case 'owned':
        return 'bg-green-100 text-green-700';
      case 'tried':
        return 'bg-blue-100 text-blue-700';
      case 'wishlist':
        return 'bg-purple-100 text-purple-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const handleSave = async () => {
    await onUpdate(bottle.id, editData);
    setIsEditing(false);
  };

  const handleCancel = () => {
    setEditData({
      status: bottle.status,
      quantity: bottle.quantity,
      rating: bottle.rating || undefined,
      tasting_notes: bottle.tasting_notes || '',
    });
    setIsEditing(false);
  };

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start gap-4">
        {/* Wine image or icon */}
        <div className="relative">
          {bottle.image_url ? (
            <img
              src={bottle.image_url}
              alt={wineName}
              className="w-16 h-20 object-cover rounded-lg"
            />
          ) : (
            <div className={`w-16 h-20 rounded-lg flex items-center justify-center ${getWineTypeColor(wineType)}`}>
              <Wine className="w-8 h-8" />
            </div>
          )}
          {/* Quantity badge */}
          {bottle.status === 'owned' && bottle.quantity > 1 && (
            <span className="absolute -top-2 -right-2 w-6 h-6 bg-wine-600 text-white text-xs font-bold rounded-full flex items-center justify-center">
              {bottle.quantity}
            </span>
          )}
        </div>

        {/* Wine details */}
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2">
            <div>
              <h3 className="font-semibold text-gray-900">{wineName}</h3>
              {wineProducer && (
                <p className="text-sm text-gray-500">{wineProducer}</p>
              )}
            </div>
            <span className={`text-xs px-2 py-1 rounded-full ${getStatusColor(bottle.status)}`}>
              {bottle.status}
            </span>
          </div>

          {/* Attributes */}
          <div className="flex flex-wrap items-center gap-2 mt-2">
            <span className={`text-xs px-2 py-1 rounded-full ${getWineTypeColor(wineType)}`}>
              {wineType}
            </span>
            {wineVintage && (
              <span className="text-xs text-gray-500">{wineVintage}</span>
            )}
            {wineVarietal && (
              <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                {wineVarietal}
              </span>
            )}
          </div>

          {/* Location and price */}
          <div className="flex flex-wrap items-center gap-4 mt-2 text-sm text-gray-500">
            {(wineRegion || wineCountry) && (
              <span className="flex items-center gap-1">
                <MapPin className="w-4 h-4" />
                {[wineRegion, wineCountry].filter(Boolean).join(', ')}
              </span>
            )}
            {winePrice && (
              <span className="flex items-center gap-1">
                <DollarSign className="w-4 h-4" />
                {winePrice.toFixed(2)}
              </span>
            )}
          </div>

          {/* Rating */}
          {bottle.rating && (
            <div className="flex items-center gap-1 mt-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <Star
                  key={star}
                  className={`w-4 h-4 ${
                    star <= bottle.rating!
                      ? 'text-yellow-400 fill-yellow-400'
                      : 'text-gray-200'
                  }`}
                />
              ))}
              <span className="text-sm text-gray-500 ml-1">({bottle.rating})</span>
            </div>
          )}

          {/* Tasting notes */}
          {bottle.tasting_notes && !isEditing && (
            <p className="text-sm text-gray-600 mt-2 italic">
              "{bottle.tasting_notes}"
            </p>
          )}

          {/* Edit form */}
          {isEditing && (
            <div className="mt-4 space-y-3 border-t pt-4">
              {/* Status */}
              <div>
                <label className="text-xs font-medium text-gray-500">Status</label>
                <div className="flex gap-2 mt-1">
                  {(['owned', 'tried', 'wishlist'] as CellarStatus[]).map((status) => (
                    <button
                      key={status}
                      onClick={() => setEditData({ ...editData, status })}
                      className={`px-3 py-1 text-xs rounded-full transition-colors ${
                        editData.status === status
                          ? getStatusColor(status)
                          : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
                      }`}
                    >
                      {status}
                    </button>
                  ))}
                </div>
              </div>

              {/* Quantity */}
              {editData.status === 'owned' && (
                <div>
                  <label className="text-xs font-medium text-gray-500">Quantity</label>
                  <div className="flex items-center gap-2 mt-1">
                    <button
                      onClick={() => setEditData({ ...editData, quantity: Math.max(1, (editData.quantity || 1) - 1) })}
                      className="p-1 bg-gray-100 rounded hover:bg-gray-200"
                    >
                      <Minus className="w-4 h-4" />
                    </button>
                    <span className="w-8 text-center font-medium">{editData.quantity || 1}</span>
                    <button
                      onClick={() => setEditData({ ...editData, quantity: (editData.quantity || 1) + 1 })}
                      className="p-1 bg-gray-100 rounded hover:bg-gray-200"
                    >
                      <Plus className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}

              {/* Rating */}
              <div>
                <label className="text-xs font-medium text-gray-500">Rating</label>
                <div className="flex items-center gap-1 mt-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button
                      key={star}
                      onClick={() => setEditData({ ...editData, rating: star })}
                      className="p-0.5"
                    >
                      <Star
                        className={`w-6 h-6 transition-colors ${
                          star <= (editData.rating || 0)
                            ? 'text-yellow-400 fill-yellow-400'
                            : 'text-gray-200 hover:text-yellow-300'
                        }`}
                      />
                    </button>
                  ))}
                  {editData.rating && (
                    <button
                      onClick={() => setEditData({ ...editData, rating: undefined })}
                      className="ml-2 text-xs text-gray-400 hover:text-gray-600"
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>

              {/* Tasting notes */}
              <div>
                <label className="text-xs font-medium text-gray-500">Tasting Notes</label>
                <textarea
                  value={editData.tasting_notes || ''}
                  onChange={(e) => setEditData({ ...editData, tasting_notes: e.target.value })}
                  placeholder="Add your tasting notes..."
                  rows={2}
                  className="w-full mt-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-wine-500/20 focus:border-wine-500"
                />
              </div>
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-2">
          {isEditing ? (
            <>
              <button
                onClick={handleSave}
                className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition-colors"
                title="Save"
              >
                <Check className="w-5 h-5" />
              </button>
              <button
                onClick={handleCancel}
                className="p-2 text-gray-500 hover:bg-gray-100 rounded-lg transition-colors"
                title="Cancel"
              >
                <X className="w-5 h-5" />
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => setIsEditing(true)}
                className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                title="Edit"
              >
                <Edit2 className="w-5 h-5" />
              </button>
              <button
                onClick={() => onRemove(bottle.id)}
                className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                title="Remove"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
