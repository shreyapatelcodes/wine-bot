/**
 * Wine detail page - shows full wine information and allows editing
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Wine, Star, Trash2, MessageCircle } from 'lucide-react';
import { api } from '../services/api';
import { useCellar } from '../hooks';
import type { CellarBottle, CellarStatus } from '../types';

type StatusLabel = 'Owned' | 'Tried' | 'Saved';

const REVERSE_STATUS_MAP: Record<StatusLabel, CellarStatus> = {
  Owned: 'owned',
  Tried: 'tried',
  Saved: 'wishlist',
};

export function WineDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { updateBottle, removeBottle, isUpdating } = useCellar();

  const [bottle, setBottle] = useState<CellarBottle | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    const fetchBottle = async () => {
      try {
        setIsLoading(true);
        const data = await api.getCellarBottle(id);
        setBottle(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load wine');
      } finally {
        setIsLoading(false);
      }
    };

    fetchBottle();
  }, [id]);

  const handleStatusChange = async (newStatus: CellarStatus) => {
    if (!bottle || !id) return;

    try {
      await updateBottle(id, { status: newStatus });
      setBottle({ ...bottle, status: newStatus });
    } catch (err) {
      console.error('Failed to update status:', err);
    }
  };

  const handleRatingChange = async (rating: number) => {
    if (!bottle || !id) return;

    try {
      await updateBottle(id, { rating });
      setBottle({ ...bottle, rating });
    } catch (err) {
      console.error('Failed to update rating:', err);
    }
  };

  const handleDelete = async () => {
    if (!id) return;

    if (window.confirm('Are you sure you want to remove this wine from your cellar?')) {
      try {
        await removeBottle(id);
        navigate('/cellar');
      } catch (err) {
        console.error('Failed to remove bottle:', err);
      }
    }
  };

  const handleAskPip = () => {
    const wineName = bottle?.wine?.name || bottle?.custom_wine_name || 'this wine';
    navigate(`/?ask=${encodeURIComponent(`Tell me more about ${wineName}`)}`);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen px-6 md:px-8 py-8">
        <div className="max-w-2xl mx-auto">
          <button
            onClick={() => navigate('/cellar')}
            className="flex items-center gap-2 text-gray-500 hover:text-gray-700 mb-6"
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="font-mono text-sm uppercase tracking-wider">Back to Cellar</span>
          </button>
          <div className="animate-pulse space-y-6">
            <div className="h-64 bg-cream-dark rounded-xl" />
            <div className="h-10 bg-cream-dark rounded w-64" />
            <div className="h-6 bg-cream-dark rounded w-48" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !bottle) {
    return (
      <div className="min-h-screen px-6 md:px-8 py-8">
        <div className="max-w-2xl mx-auto">
          <button
            onClick={() => navigate('/cellar')}
            className="flex items-center gap-2 text-gray-500 hover:text-gray-700 mb-8"
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="font-mono text-sm uppercase tracking-wider">Back to Cellar</span>
          </button>
          <div className="text-center py-16">
            <p className="text-gray-500">{error || 'Wine not found'}</p>
          </div>
        </div>
      </div>
    );
  }

  // Get wine info from either catalog wine or custom fields
  const wineName = bottle.wine?.name || bottle.custom_wine_name || 'Unknown Wine';
  const wineProducer = bottle.wine?.producer || bottle.custom_wine_producer;
  const wineType = bottle.wine?.wine_type || bottle.custom_wine_type || 'red';
  const wineVintage = bottle.wine?.vintage || bottle.custom_wine_vintage;
  const wineRegion = bottle.wine?.region || bottle.custom_wine_region;
  const wineCountry = bottle.wine?.country || bottle.custom_wine_country;
  const wineVarietal = bottle.wine?.varietal || bottle.custom_wine_varietal;
  const wineMetadata = bottle.wine?.wine_metadata || bottle.wine?.metadata || bottle.custom_wine_metadata;

  const getWineTypeColor = (type: string) => {
    switch (type) {
      case 'red': return 'text-red-600 bg-red-50';
      case 'white': return 'text-amber-600 bg-amber-50';
      case 'rosé': return 'text-pink-500 bg-pink-50';
      case 'sparkling': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-gray-500 bg-gray-50';
    }
  };

  return (
    <div className="min-h-screen pb-24">
      {/* Header */}
      <header className="px-6 md:px-8 pt-8 pb-6">
        <div className="max-w-2xl mx-auto">
          <button
            onClick={() => navigate('/cellar')}
            className="flex items-center gap-2 text-gray-500 hover:text-gray-700 mb-6"
          >
            <ArrowLeft className="w-5 h-5" />
            <span className="font-mono text-sm uppercase tracking-wider">Back to Cellar</span>
          </button>
        </div>
      </header>

      <div className="px-6 md:px-8">
        <div className="max-w-2xl mx-auto">
          {/* Wine Image */}
          <div className="relative h-64 bg-cream rounded-2xl flex items-center justify-center mb-8">
            {bottle.image_url ? (
              <img
                src={bottle.image_url}
                alt={wineName}
                className="h-full object-contain"
              />
            ) : (
              <div className="w-32 h-44 bg-white/50 rounded-lg flex items-center justify-center">
                <Wine className={`w-16 h-16 ${getWineTypeColor(wineType).split(' ')[0]}`} />
              </div>
            )}

            {/* Delete button */}
            <button
              onClick={handleDelete}
              className="absolute top-4 right-4 p-2 bg-white/80 backdrop-blur-sm rounded-xl text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
              title="Remove from cellar"
            >
              <Trash2 className="w-5 h-5" />
            </button>
          </div>

          {/* Wine Type Badge */}
          <span className={`inline-block font-mono text-xs uppercase tracking-wider px-3 py-1.5 rounded-lg mb-4 ${getWineTypeColor(wineType)}`}>
            {wineType} {wineVintage && `· ${wineVintage}`}
          </span>

          {/* Wine Name */}
          <h1 className="font-serif text-3xl md:text-4xl text-gray-900 mb-2">
            {wineName}
          </h1>

          {/* Producer */}
          {wineProducer && (
            <p className="text-lg text-gray-500 mb-2">{wineProducer}</p>
          )}

          {/* Region */}
          {(wineRegion || wineCountry) && (
            <p className="font-mono text-xs uppercase tracking-wider text-gray-400 mb-6">
              {[wineRegion, wineCountry].filter(Boolean).join(', ')}
            </p>
          )}

          {/* Collection State Control */}
          <div className="mb-8">
            <label className="font-mono text-xs uppercase tracking-wider text-gray-500 block mb-3">
              Collection Status
            </label>
            <div className="flex gap-2">
              {(['Owned', 'Tried', 'Saved'] as StatusLabel[]).map((label) => {
                const status = REVERSE_STATUS_MAP[label];
                const isActive = bottle.status === status;
                return (
                  <button
                    key={status}
                    onClick={() => handleStatusChange(status)}
                    disabled={isUpdating}
                    className={`flex-1 py-3 font-mono text-sm uppercase tracking-wider rounded-xl transition-all ${
                      isActive
                        ? 'bg-wine-600 text-white shadow-lg shadow-wine-600/20'
                        : 'bg-cream text-gray-600 hover:bg-cream-dark'
                    }`}
                  >
                    {label}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Rating */}
          <div className="mb-8">
            <label className="font-mono text-xs uppercase tracking-wider text-gray-500 block mb-3">
              Your Rating
            </label>
            <div className="flex items-center gap-2">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  onClick={() => handleRatingChange(star)}
                  disabled={isUpdating}
                  className="p-1"
                >
                  <Star
                    className={`w-8 h-8 transition-colors ${
                      star <= (bottle.rating || 0)
                        ? 'text-yellow-400 fill-yellow-400'
                        : 'text-gray-200 hover:text-yellow-300'
                    }`}
                  />
                </button>
              ))}
              {bottle.rating && (
                <span className="ml-3 font-mono text-sm text-gray-500">
                  {bottle.rating}/5
                </span>
              )}
            </div>
          </div>

          {/* Wine Details */}
          {(wineVarietal || wineMetadata) && (
            <div className="mb-8">
              <label className="font-mono text-xs uppercase tracking-wider text-gray-500 block mb-3">
                Wine Details
              </label>
              <div className="bg-cream rounded-xl p-4 space-y-3">
                {wineVarietal && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 text-sm">Varietal</span>
                    <span className="text-gray-900 text-sm font-medium">{wineVarietal}</span>
                  </div>
                )}
                {wineMetadata?.body && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 text-sm">Body</span>
                    <span className="text-gray-900 text-sm font-medium capitalize">{wineMetadata.body}</span>
                  </div>
                )}
                {wineMetadata?.acidity && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 text-sm">Acidity</span>
                    <span className="text-gray-900 text-sm font-medium capitalize">{wineMetadata.acidity}</span>
                  </div>
                )}
                {wineMetadata?.tannin && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 text-sm">Tannin</span>
                    <span className="text-gray-900 text-sm font-medium capitalize">{wineMetadata.tannin}</span>
                  </div>
                )}
                {wineMetadata?.sweetness && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 text-sm">Sweetness</span>
                    <span className="text-gray-900 text-sm font-medium capitalize">{wineMetadata.sweetness}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Tasting Notes */}
          {bottle.tasting_notes && (
            <div className="mb-8">
              <label className="font-mono text-xs uppercase tracking-wider text-gray-500 block mb-3">
                Your Notes
              </label>
              <div className="bg-cream rounded-xl p-4">
                <p className="text-gray-700 italic">"{bottle.tasting_notes}"</p>
              </div>
            </div>
          )}

          {/* Ask Pip Button */}
          <button
            onClick={handleAskPip}
            className="w-full flex items-center justify-center gap-3 py-4 bg-wine-600 text-white rounded-xl hover:bg-wine-700 transition-colors shadow-lg shadow-wine-600/20"
          >
            <MessageCircle className="w-5 h-5" />
            <span className="font-mono text-sm uppercase tracking-wider">Ask Pip about this wine</span>
          </button>
        </div>
      </div>
    </div>
  );
}
