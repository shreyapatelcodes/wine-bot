/**
 * Cellar list component with filtering
 */

import { useState } from 'react';
import { Wine, Loader2, Package, CheckCircle, Heart } from 'lucide-react';
import { useCellar, useCellarStats } from '../../hooks';
import { CellarBottleCard } from './CellarBottleCard';
import type { CellarStatus } from '../../types';

const statusFilters: { value: CellarStatus | undefined; label: string; icon: React.ReactNode }[] = [
  { value: undefined, label: 'All', icon: <Wine className="w-4 h-4" /> },
  { value: 'owned', label: 'Owned', icon: <Package className="w-4 h-4" /> },
  { value: 'tried', label: 'Tried', icon: <CheckCircle className="w-4 h-4" /> },
  { value: 'wishlist', label: 'Wishlist', icon: <Heart className="w-4 h-4" /> },
];

export function CellarList() {
  const [statusFilter, setStatusFilter] = useState<CellarStatus | undefined>(undefined);
  const { bottles, isLoading, error, updateBottle, removeBottle } = useCellar(statusFilter);
  const stats = useCellarStats();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 text-wine-600 animate-spin" />
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

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-4 border border-gray-200">
          <p className="text-2xl font-bold text-gray-900">{stats.totalBottles}</p>
          <p className="text-sm text-gray-500">Total Bottles</p>
        </div>
        <div className="bg-green-50 rounded-xl p-4 border border-green-200">
          <p className="text-2xl font-bold text-green-700">{stats.owned}</p>
          <p className="text-sm text-green-600">Owned</p>
        </div>
        <div className="bg-blue-50 rounded-xl p-4 border border-blue-200">
          <p className="text-2xl font-bold text-blue-700">{stats.tried}</p>
          <p className="text-sm text-blue-600">Tried</p>
        </div>
        <div className="bg-purple-50 rounded-xl p-4 border border-purple-200">
          <p className="text-2xl font-bold text-purple-700">{stats.wishlist}</p>
          <p className="text-sm text-purple-600">Wishlist</p>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex flex-wrap gap-2">
        {statusFilters.map((filter) => (
          <button
            key={filter.label}
            onClick={() => setStatusFilter(filter.value)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              statusFilter === filter.value
                ? 'bg-wine-600 text-white'
                : 'bg-white text-gray-600 hover:bg-gray-100 border border-gray-200'
            }`}
          >
            {filter.icon}
            {filter.label}
          </button>
        ))}
      </div>

      {/* Bottles list */}
      {bottles.length === 0 ? (
        <div className="text-center py-12">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Wine className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-gray-900 mb-1">
            {statusFilter ? `No ${statusFilter} bottles` : 'Your cellar is empty'}
          </h3>
          <p className="text-gray-500">
            {statusFilter
              ? `You don't have any bottles marked as "${statusFilter}" yet.`
              : 'Add bottles to your cellar to keep track of your collection.'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {bottles.map((bottle) => (
            <CellarBottleCard
              key={bottle.id}
              bottle={bottle}
              onUpdate={updateBottle}
              onRemove={removeBottle}
            />
          ))}
        </div>
      )}
    </div>
  );
}
