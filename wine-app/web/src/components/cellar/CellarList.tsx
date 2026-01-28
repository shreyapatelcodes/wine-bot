/**
 * Cellar list component with filtering
 */

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Wine, Loader2, Package, CheckCircle } from 'lucide-react';
import { useCellar, useCellarStats } from '../../hooks';
import { CellarBottleCard } from './CellarBottleCard';
import type { CellarStatus } from '../../types';

const statusFilters: { value: CellarStatus; label: string; icon: React.ReactNode }[] = [
  { value: 'owned', label: 'Owned', icon: <Package className="w-4 h-4" /> },
  { value: 'tried', label: 'Tried', icon: <CheckCircle className="w-4 h-4" /> },
];

export function CellarList() {
  const navigate = useNavigate();
  const [statusFilter, setStatusFilter] = useState<CellarStatus>('owned');
  const { bottles, isLoading, error, updateBottle, removeBottle } = useCellar(statusFilter);
  const stats = useCellarStats();

  // Get count for each filter
  const getFilterCount = (value: CellarStatus): number => {
    if (value === 'owned') return stats.owned;
    if (value === 'tried') return stats.tried;
    return 0;
  };

  const handleBottleClick = (bottleId: string) => {
    navigate(`/wine/${bottleId}`);
  };

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
      {/* Filter tabs with badge counts */}
      <div className="flex flex-wrap gap-2">
        {statusFilters.map((filter) => {
          const count = getFilterCount(filter.value);
          return (
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
              {count > 0 && (
                <span className={`font-mono text-xs px-1.5 py-0.5 rounded-full ${
                  statusFilter === filter.value
                    ? 'bg-white/20 text-white'
                    : 'bg-gray-100 text-gray-500'
                }`}>
                  {count}
                </span>
              )}
            </button>
          );
        })}
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
              onClick={() => handleBottleClick(bottle.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
