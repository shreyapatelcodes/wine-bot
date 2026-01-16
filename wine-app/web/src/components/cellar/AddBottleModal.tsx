/**
 * Modal for adding bottles to cellar
 */

import { useState } from 'react';
import { X, Search, Wine, Plus, Loader2 } from 'lucide-react';
import { useWineSearch, useCellar } from '../../hooks';
import type { Wine as WineType, CellarBottleCreate, WineType as WineTypeValue } from '../../types';

interface AddBottleModalProps {
  isOpen: boolean;
  onClose: () => void;
}

type AddMode = 'search' | 'manual';

export function AddBottleModal({ isOpen, onClose }: AddBottleModalProps) {
  const [mode, setMode] = useState<AddMode>('search');
  const { query, setQuery, results, isLoading: isSearching } = useWineSearch();
  const { addBottle, isAdding } = useCellar();

  // Manual entry state
  const [manualData, setManualData] = useState<Partial<CellarBottleCreate>>({
    custom_wine_type: 'red',
    status: 'owned',
    quantity: 1,
  });

  if (!isOpen) return null;

  const handleSelectWine = async (wine: WineType) => {
    await addBottle({
      wine_id: wine.id,
      status: 'owned',
      quantity: 1,
    });
    onClose();
  };

  const handleManualAdd = async () => {
    if (!manualData.custom_wine_name) return;
    await addBottle(manualData as CellarBottleCreate);
    onClose();
  };

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
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-sm" onClick={onClose} />

      {/* Modal */}
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Add to Cellar</h2>
          <button
            onClick={onClose}
            className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Mode tabs */}
        <div className="flex border-b">
          <button
            onClick={() => setMode('search')}
            className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
              mode === 'search'
                ? 'text-wine-600 border-b-2 border-wine-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Search className="w-4 h-4 inline-block mr-2" />
            Search Catalog
          </button>
          <button
            onClick={() => setMode('manual')}
            className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
              mode === 'manual'
                ? 'text-wine-600 border-b-2 border-wine-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            <Plus className="w-4 h-4 inline-block mr-2" />
            Manual Entry
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {mode === 'search' ? (
            <div className="space-y-4">
              {/* Search input */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search wines by name, producer, or varietal..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-wine-500/20 focus:border-wine-500"
                />
              </div>

              {/* Search results */}
              {isSearching ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 text-wine-600 animate-spin" />
                </div>
              ) : results.length > 0 ? (
                <div className="space-y-2">
                  {results.map((wine) => (
                    <button
                      key={wine.id}
                      onClick={() => handleSelectWine(wine)}
                      disabled={isAdding}
                      className="w-full flex items-center gap-3 p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors text-left disabled:opacity-50"
                    >
                      <div className={`p-2 rounded-lg ${getWineTypeColor(wine.wine_type)}`}>
                        <Wine className="w-4 h-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-gray-900 truncate">{wine.name}</p>
                        <p className="text-sm text-gray-500 truncate">
                          {[wine.producer, wine.vintage, wine.varietal].filter(Boolean).join(' · ')}
                        </p>
                      </div>
                      {wine.price_usd && (
                        <span className="text-sm text-gray-500">${wine.price_usd.toFixed(0)}</span>
                      )}
                    </button>
                  ))}
                </div>
              ) : query.length >= 2 ? (
                <p className="text-center text-gray-500 py-8">
                  No wines found. Try a different search or add manually.
                </p>
              ) : (
                <p className="text-center text-gray-500 py-8">
                  Start typing to search the wine catalog.
                </p>
              )}
            </div>
          ) : (
            <div className="space-y-4">
              {/* Wine name */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Wine Name *
                </label>
                <input
                  type="text"
                  value={manualData.custom_wine_name || ''}
                  onChange={(e) => setManualData({ ...manualData, custom_wine_name: e.target.value })}
                  placeholder="e.g., Château Margaux"
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-wine-500/20 focus:border-wine-500"
                />
              </div>

              {/* Producer */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Producer
                </label>
                <input
                  type="text"
                  value={manualData.custom_wine_producer || ''}
                  onChange={(e) => setManualData({ ...manualData, custom_wine_producer: e.target.value })}
                  placeholder="e.g., Château Margaux"
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-wine-500/20 focus:border-wine-500"
                />
              </div>

              {/* Vintage and Type */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Vintage
                  </label>
                  <input
                    type="number"
                    value={manualData.custom_wine_vintage || ''}
                    onChange={(e) => setManualData({ ...manualData, custom_wine_vintage: e.target.value ? parseInt(e.target.value) : undefined })}
                    placeholder="2020"
                    min="1900"
                    max={new Date().getFullYear()}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-wine-500/20 focus:border-wine-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type
                  </label>
                  <select
                    value={manualData.custom_wine_type || 'red'}
                    onChange={(e) => setManualData({ ...manualData, custom_wine_type: e.target.value as WineTypeValue })}
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-wine-500/20 focus:border-wine-500"
                  >
                    <option value="red">Red</option>
                    <option value="white">White</option>
                    <option value="rosé">Rosé</option>
                    <option value="sparkling">Sparkling</option>
                  </select>
                </div>
              </div>

              {/* Quantity and Price */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Quantity
                  </label>
                  <input
                    type="number"
                    value={manualData.quantity || 1}
                    onChange={(e) => setManualData({ ...manualData, quantity: parseInt(e.target.value) || 1 })}
                    min="1"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-wine-500/20 focus:border-wine-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Price Paid
                  </label>
                  <input
                    type="number"
                    value={manualData.purchase_price || ''}
                    onChange={(e) => setManualData({ ...manualData, purchase_price: e.target.value ? parseFloat(e.target.value) : undefined })}
                    placeholder="0.00"
                    min="0"
                    step="0.01"
                    className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-wine-500/20 focus:border-wine-500"
                  />
                </div>
              </div>

              {/* Purchase location */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Where Purchased
                </label>
                <input
                  type="text"
                  value={manualData.purchase_location || ''}
                  onChange={(e) => setManualData({ ...manualData, purchase_location: e.target.value })}
                  placeholder="e.g., Total Wine"
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-wine-500/20 focus:border-wine-500"
                />
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        {mode === 'manual' && (
          <div className="p-4 border-t">
            <button
              onClick={handleManualAdd}
              disabled={!manualData.custom_wine_name || isAdding}
              className="w-full py-2 bg-wine-600 text-white rounded-lg font-medium hover:bg-wine-700 transition-colors disabled:bg-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed"
            >
              {isAdding ? (
                <Loader2 className="w-5 h-5 animate-spin mx-auto" />
              ) : (
                'Add to Cellar'
              )}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
