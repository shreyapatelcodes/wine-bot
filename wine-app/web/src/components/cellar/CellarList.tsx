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
    <div className="space-y-8">
      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-5 border border-gray-100">
          <p className="font-mono text-[10px] uppercase tracking-wider text-gray-500">Total</p>
          <p className="font-serif text-4xl text-gray-900 mt-1">{stats.totalBottles}</p>
        </div>
        <div className="bg-white rounded-xl p-5 border border-gray-100">
          <p className="font-mono text-[10px] uppercase tracking-wider text-green-600">Owned</p>
          <p className="font-serif text-4xl text-green-700 mt-1">{stats.owned}</p>
        </div>
        <div className="bg-white rounded-xl p-5 border border-gray-100">
          <p className="font-mono text-[10px] uppercase tracking-wider text-blue-600">Tried</p>
          <p className="font-serif text-4xl text-blue-700 mt-1">{stats.tried}</p>
        </div>
        <div className="bg-white rounded-xl p-5 border border-gray-100">
          <p className="font-mono text-[10px] uppercase tracking-wider text-purple-600">Wishlist</p>
          <p className="font-serif text-4xl text-purple-700 mt-1">{stats.wishlist}</p>
        </div>
      </div>

      {/* Filter tabs */}
      <div className="flex flex-wrap gap-2">
        {statusFilters.map((filter) => (
          <button
            key={filter.label}
            onClick={() => setStatusFilter(filter.value)}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl transition-colors ${
              statusFilter === filter.value
                ? 'bg-wine-600 text-white'
                : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
            }`}
          >
            {filter.icon}
            <span className="font-mono text-xs uppercase tracking-wider">{filter.label}</span>
          </button>
        ))}
      </div>

      {/* Bottles grid */}
      {bottles.length === 0 ? (
        <div className="text-center py-16">
          <div className="w-20 h-20 bg-cream-dark rounded-full flex items-center justify-center mx-auto mb-6">
            <Wine className="w-10 h-10 text-gray-400" />
          </div>
          <h3 className="font-serif italic text-xl text-gray-900 mb-2">
            {statusFilter ? `No ${statusFilter} bottles` : 'Your cellar is empty'}
          </h3>
          <p className="text-gray-500 text-sm">
            {statusFilter
              ? `You don't have any bottles marked as "${statusFilter}" yet.`
              : 'Add bottles to your cellar to keep track of your collection.'}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
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
