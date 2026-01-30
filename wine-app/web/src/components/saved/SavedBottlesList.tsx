/**
 * List component for wishlist bottles
 */

import { Heart, Loader2 } from 'lucide-react';
import { useSavedBottles } from '../../hooks';
import { SavedBottleCard } from './SavedBottleCard';

export function SavedBottlesList() {
  const {
    bottles,
    isLoading,
    error,
    removeBottle,
    isRemoving,
    moveToCellar,
    isMovingToCellar,
  } = useSavedBottles();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-pink-600 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500">{error}</p>
      </div>
    );
  }

  if (bottles.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="w-16 h-16 bg-pink-50 rounded-full flex items-center justify-center mx-auto mb-4">
          <Heart className="w-8 h-8 text-pink-300" />
        </div>
        <h3 className="text-lg font-medium text-gray-900 mb-1">Your wishlist is empty</h3>
        <p className="text-gray-500">
          Add wines you want to try and they'll show up here.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {bottles.map((bottle) => (
        <SavedBottleCard
          key={bottle.id}
          bottle={bottle}
          onRemove={removeBottle}
          onMoveToCellar={moveToCellar}
          isRemoving={isRemoving}
          isMoving={isMovingToCellar}
        />
      ))}
    </div>
  );
}
