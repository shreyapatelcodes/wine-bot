/**
 * Card component for cellar bottles
 */

import { useState } from 'react';
import { Wine, Star, Edit2, Trash2, Check, X, Minus, Plus } from 'lucide-react';
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
  const wineRegion = bottle.wine?.region || bottle.custom_wine_region;
  const wineCountry = bottle.wine?.country || bottle.custom_wine_country;

  const getWineTypeColor = (type: string) => {
    switch (type) {
      case 'red':
        return 'text-red-600';
      case 'white':
        return 'text-amber-600';
      case 'rosé':
        return 'text-pink-500';
      case 'sparkling':
        return 'text-yellow-600';
      default:
        return 'text-gray-500';
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

  // Convert 5-star rating to points (rough approximation: 5 stars = 100pts, 4 = 90, etc.)
  const ratingToPoints = (rating: number) => Math.round(80 + rating * 4);

  return (
    <div className="relative bg-white border border-gray-100 rounded-xl overflow-hidden hover:shadow-lg transition-all group">
      {/* Wine image area */}
      <div className="relative h-48 bg-cream flex items-center justify-center">
        {bottle.image_url ? (
          <img
            src={bottle.image_url}
            alt={wineName}
            className="h-full object-contain"
          />
        ) : (
          <div className="w-24 h-32 bg-white/50 rounded-lg flex items-center justify-center">
            <Wine className={`w-12 h-12 ${getWineTypeColor(wineType)}`} />
          </div>
        )}

        {/* Point rating badge */}
        {bottle.rating && (
          <div className="absolute top-3 right-3 bg-white text-gray-900 font-mono text-xs px-2 py-1 rounded-lg shadow-sm border border-gray-100">
            {ratingToPoints(bottle.rating)} PTS
          </div>
        )}

        {/* Quantity badge */}
        {bottle.status === 'owned' && bottle.quantity > 1 && (
          <div className="absolute bottom-3 right-3 bg-wine-600 text-white font-mono text-xs px-2 py-1 rounded-lg">
            x{bottle.quantity}
          </div>
        )}
      </div>

      {/* Wine info */}
      <div className="p-4">
        {/* Type and vintage label */}
        <div className="flex items-center justify-between">
          <span className="font-mono text-[10px] uppercase tracking-wider text-wine-600">
            {wineType} {wineVintage && `\u2022 ${wineVintage}`}
          </span>
          {/* Star rating */}
          {bottle.rating && (
            <div className="flex items-center gap-0.5">
              {[1, 2, 3, 4, 5].map((star) => (
                <Star
                  key={star}
                  className={`w-3 h-3 ${
                    star <= bottle.rating!
                      ? 'text-yellow-400 fill-yellow-400'
                      : 'text-gray-200'
                  }`}
                />
              ))}
            </div>
          )}
        </div>

        {/* Wine name */}
        <h3 className="font-serif text-lg text-gray-900 mt-2 line-clamp-2 leading-tight">
          {wineName}
        </h3>

        {/* Producer */}
        {wineProducer && (
          <p className="text-sm text-gray-500 mt-1 truncate">{wineProducer}</p>
        )}

        {/* Region */}
        {(wineRegion || wineCountry) && (
          <p className="font-mono text-[10px] uppercase tracking-wider text-gray-400 mt-2">
            {[wineRegion, wineCountry].filter(Boolean).join(', ')}
          </p>
        )}

        {/* Tasting notes */}
        {bottle.tasting_notes && !isEditing && (
          <p className="text-xs text-gray-500 mt-3 italic line-clamp-2">
            "{bottle.tasting_notes}"
          </p>
        )}

        {/* Status tag and actions */}
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-gray-100">
          <span className={`font-mono text-[10px] uppercase tracking-wider px-2.5 py-1 rounded-lg ${getStatusColor(bottle.status)}`}>
            {bottle.status}
          </span>

          <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <button
              onClick={() => setIsEditing(true)}
              className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title="Edit"
            >
              <Edit2 className="w-4 h-4" />
            </button>
            <button
              onClick={() => onRemove(bottle.id)}
              className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
              title="Remove"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Edit modal overlay */}
      {isEditing && (
        <div className="absolute inset-0 bg-white z-10 p-4 overflow-y-auto">
          <div className="flex items-center justify-between mb-4">
            <h4 className="font-serif text-lg">Edit Bottle</h4>
            <div className="flex gap-1">
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
            </div>
          </div>

          <div className="space-y-4">
            {/* Status */}
            <div>
              <label className="font-mono text-[10px] uppercase tracking-wider text-gray-500">Status</label>
              <div className="flex gap-2 mt-2">
                {(['owned', 'tried', 'wishlist'] as CellarStatus[]).map((status) => (
                  <button
                    key={status}
                    onClick={() => setEditData({ ...editData, status })}
                    className={`px-3 py-1.5 font-mono text-[10px] uppercase tracking-wider rounded-lg transition-colors ${
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
                <label className="font-mono text-[10px] uppercase tracking-wider text-gray-500">Quantity</label>
                <div className="flex items-center gap-3 mt-2">
                  <button
                    onClick={() => setEditData({ ...editData, quantity: Math.max(1, (editData.quantity || 1) - 1) })}
                    className="p-2 bg-cream rounded-lg hover:bg-cream-dark"
                  >
                    <Minus className="w-4 h-4" />
                  </button>
                  <span className="w-8 text-center font-mono text-lg">{editData.quantity || 1}</span>
                  <button
                    onClick={() => setEditData({ ...editData, quantity: (editData.quantity || 1) + 1 })}
                    className="p-2 bg-cream rounded-lg hover:bg-cream-dark"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}

            {/* Rating */}
            <div>
              <label className="font-mono text-[10px] uppercase tracking-wider text-gray-500">Rating</label>
              <div className="flex items-center gap-1 mt-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => setEditData({ ...editData, rating: star })}
                    className="p-1"
                  >
                    <Star
                      className={`w-7 h-7 transition-colors ${
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
                    className="ml-2 font-mono text-[10px] uppercase tracking-wider text-gray-400 hover:text-gray-600"
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>

            {/* Tasting notes */}
            <div>
              <label className="font-mono text-[10px] uppercase tracking-wider text-gray-500">Tasting Notes</label>
              <textarea
                value={editData.tasting_notes || ''}
                onChange={(e) => setEditData({ ...editData, tasting_notes: e.target.value })}
                placeholder="Add your tasting notes..."
                rows={3}
                className="w-full mt-2 px-3 py-2 text-sm border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-wine-500/20 focus:border-wine-500 bg-cream-light"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
