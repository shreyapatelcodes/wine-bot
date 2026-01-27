/**
 * Wine detail page - shows full wine information and allows editing
 */

import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Wine, Star, Trash2, MessageCircle, Edit2, Sparkles, Search, X, Plus, Minus } from 'lucide-react';
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
  const [isEditing, setIsEditing] = useState(false);

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
      // If clicking the same star, clear the rating
      if (bottle.rating === rating) {
        await updateBottle(id, { rating: undefined });
        setBottle({ ...bottle, rating: null });
      } else {
        await updateBottle(id, { rating });
        setBottle({ ...bottle, rating });
      }
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

  // Edit mode state
  const [editData, setEditData] = useState({
    status: bottle?.status || 'owned' as CellarStatus,
    quantity: bottle?.quantity || 1,
    rating: bottle?.rating || undefined as number | undefined,
    tasting_notes: bottle?.tasting_notes || '',
    custom_wine_name: '',
    custom_wine_producer: '',
    custom_wine_vintage: undefined as number | undefined,
    custom_wine_varietal: '',
    custom_wine_region: '',
    custom_wine_country: '',
  });

  // Initialize edit data when bottle loads
  useEffect(() => {
    if (bottle) {
      setEditData({
        status: bottle.status,
        quantity: bottle.quantity,
        rating: bottle.rating || undefined,
        tasting_notes: bottle.tasting_notes || '',
        custom_wine_name: bottle.custom_wine_name || bottle.wine?.name || '',
        custom_wine_producer: bottle.custom_wine_producer || bottle.wine?.producer || '',
        custom_wine_vintage: bottle.custom_wine_vintage || bottle.wine?.vintage || undefined,
        custom_wine_varietal: bottle.custom_wine_varietal || bottle.wine?.varietal || '',
        custom_wine_region: bottle.custom_wine_region || bottle.wine?.region || '',
        custom_wine_country: bottle.custom_wine_country || bottle.wine?.country || '',
      });
    }
  }, [bottle]);

  const handleStartEdit = () => {
    if (bottle) {
      setEditData({
        status: bottle.status,
        quantity: bottle.quantity,
        rating: bottle.rating || undefined,
        tasting_notes: bottle.tasting_notes || '',
        custom_wine_name: bottle.custom_wine_name || bottle.wine?.name || '',
        custom_wine_producer: bottle.custom_wine_producer || bottle.wine?.producer || '',
        custom_wine_vintage: bottle.custom_wine_vintage || bottle.wine?.vintage || undefined,
        custom_wine_varietal: bottle.custom_wine_varietal || bottle.wine?.varietal || '',
        custom_wine_region: bottle.custom_wine_region || bottle.wine?.region || '',
        custom_wine_country: bottle.custom_wine_country || bottle.wine?.country || '',
      });
      setIsEditing(true);
    }
  };

  const handleCancelEdit = () => {
    setIsEditing(false);
  };

  const handleSaveEdit = async () => {
    if (!bottle || !id) return;

    try {
      await updateBottle(id, {
        status: editData.status,
        quantity: editData.quantity,
        rating: editData.rating,
        tasting_notes: editData.tasting_notes || undefined,
        custom_wine_name: editData.custom_wine_name || undefined,
        custom_wine_producer: editData.custom_wine_producer || undefined,
        custom_wine_vintage: editData.custom_wine_vintage,
        custom_wine_varietal: editData.custom_wine_varietal || undefined,
        custom_wine_region: editData.custom_wine_region || undefined,
        custom_wine_country: editData.custom_wine_country || undefined,
      });

      // Update local state
      setBottle({
        ...bottle,
        status: editData.status,
        quantity: editData.quantity,
        rating: editData.rating || null,
        tasting_notes: editData.tasting_notes || null,
        custom_wine_name: editData.custom_wine_name || null,
        custom_wine_producer: editData.custom_wine_producer || null,
        custom_wine_vintage: editData.custom_wine_vintage || null,
        custom_wine_varietal: editData.custom_wine_varietal || null,
        custom_wine_region: editData.custom_wine_region || null,
        custom_wine_country: editData.custom_wine_country || null,
      });

      setIsEditing(false);
    } catch (err) {
      console.error('Failed to save changes:', err);
    }
  };

  const handleClearRating = async () => {
    if (!bottle || !id) return;

    try {
      // Send rating as undefined/null to clear it
      await updateBottle(id, { rating: undefined });
      setBottle({ ...bottle, rating: null });
    } catch (err) {
      console.error('Failed to clear rating:', err);
    }
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

            {/* Edit button */}
            <button
              onClick={handleStartEdit}
              className="absolute top-4 left-4 p-2 bg-white/80 backdrop-blur-sm rounded-xl text-gray-400 hover:text-wine-600 hover:bg-wine-50 transition-colors"
              title="Edit wine information"
            >
              <Edit2 className="w-5 h-5" />
            </button>

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
                <>
                  <span className="ml-3 font-mono text-sm text-gray-500">
                    {bottle.rating}/5
                  </span>
                  <button
                    onClick={handleClearRating}
                    disabled={isUpdating}
                    className="ml-2 text-xs text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    Clear
                  </button>
                </>
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

          {/* Your Notes */}
          <div className="mb-8">
            <label className="font-mono text-xs uppercase tracking-wider text-gray-500 block mb-3">
              Your Notes
            </label>
            <div className="bg-cream rounded-xl p-4">
              {bottle.tasting_notes ? (
                <p className="text-gray-700 italic">"{bottle.tasting_notes}"</p>
              ) : (
                <p className="text-gray-400 text-sm">No tasting notes yet. Tap edit to add your thoughts.</p>
              )}
            </div>
          </div>

          {/* The Story */}
          <div className="mb-8">
            <label className="font-mono text-xs uppercase tracking-wider text-gray-500 block mb-3">
              The Story
            </label>
            <div className="bg-cream rounded-xl p-4">
              <p className="text-gray-700 leading-relaxed">
                {wineMetadata?.characteristics?.length
                  ? `A wine known for its ${wineMetadata.characteristics.join(', ').toLowerCase()}.`
                  : "No story available for this wine yet. Ask Pip to learn more about this wine's history and character."}
              </p>
            </div>
          </div>

          {/* Sommelier's Tip */}
          <div className="mb-8">
            <label className="font-mono text-xs uppercase tracking-wider text-gray-500 flex items-center gap-2 mb-3">
              <Sparkles className="w-4 h-4 text-wine-500" />
              Sommelier's Tip
            </label>
            <div className="bg-wine-50 rounded-xl p-4 border border-wine-100">
              <p className="text-gray-700 italic">
                {wineMetadata?.flavor_notes?.length
                  ? `Expect notes of ${wineMetadata.flavor_notes.join(', ').toLowerCase()}. Best enjoyed at cellar temperature.`
                  : "Ask Pip for serving suggestions, decanting advice, and food pairings."}
              </p>
            </div>
          </div>

          {/* Purchase Options - only for Saved/wishlist wines */}
          {bottle.status === 'wishlist' && (
            <div className="mb-8">
              <button
                onClick={() => {
                  const searchQuery = encodeURIComponent(`${wineName} ${wineVintage || ''} wine buy`);
                  window.open(`https://www.google.com/search?q=${searchQuery}`, '_blank');
                }}
                className="w-full flex items-center justify-center gap-3 py-4 bg-cream text-gray-700 rounded-xl hover:bg-cream-dark transition-colors border border-gray-200"
              >
                <Search className="w-5 h-5" />
                <span className="font-mono text-sm uppercase tracking-wider">Find this wine</span>
              </button>
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

      {/* Edit Mode Overlay */}
      {isEditing && (
        <div className="fixed inset-0 z-50 bg-white overflow-y-auto">
          {/* Edit Header */}
          <header className="sticky top-0 bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between">
            <button
              onClick={handleCancelEdit}
              className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
            <h2 className="font-serif text-xl text-gray-900">Edit Wine</h2>
            <button
              onClick={handleSaveEdit}
              disabled={isUpdating}
              className="px-4 py-2 bg-wine-600 text-white text-sm font-medium rounded-lg hover:bg-wine-700 transition-colors disabled:opacity-50"
            >
              {isUpdating ? 'Saving...' : 'Save'}
            </button>
          </header>

          {/* Edit Form */}
          <div className="px-6 py-6 max-w-2xl mx-auto space-y-6">
            {/* Wine Name */}
            <div>
              <label className="font-mono text-xs uppercase tracking-wider text-gray-500 block mb-2">
                Wine Name
              </label>
              <input
                type="text"
                value={editData.custom_wine_name}
                onChange={(e) => setEditData({ ...editData, custom_wine_name: e.target.value })}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-wine-500 focus:border-transparent outline-none transition-all"
                placeholder="Enter wine name"
              />
            </div>

            {/* Producer */}
            <div>
              <label className="font-mono text-xs uppercase tracking-wider text-gray-500 block mb-2">
                Producer
              </label>
              <input
                type="text"
                value={editData.custom_wine_producer}
                onChange={(e) => setEditData({ ...editData, custom_wine_producer: e.target.value })}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-wine-500 focus:border-transparent outline-none transition-all"
                placeholder="Enter producer name"
              />
            </div>

            {/* Vintage */}
            <div>
              <label className="font-mono text-xs uppercase tracking-wider text-gray-500 block mb-2">
                Vintage
              </label>
              <input
                type="number"
                value={editData.custom_wine_vintage || ''}
                onChange={(e) => setEditData({ ...editData, custom_wine_vintage: e.target.value ? parseInt(e.target.value) : undefined })}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-wine-500 focus:border-transparent outline-none transition-all"
                placeholder="e.g., 2019"
                min="1900"
                max={new Date().getFullYear()}
              />
            </div>

            {/* Varietal */}
            <div>
              <label className="font-mono text-xs uppercase tracking-wider text-gray-500 block mb-2">
                Varietal
              </label>
              <input
                type="text"
                value={editData.custom_wine_varietal}
                onChange={(e) => setEditData({ ...editData, custom_wine_varietal: e.target.value })}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-wine-500 focus:border-transparent outline-none transition-all"
                placeholder="e.g., Cabernet Sauvignon"
              />
            </div>

            {/* Region & Country */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="font-mono text-xs uppercase tracking-wider text-gray-500 block mb-2">
                  Region
                </label>
                <input
                  type="text"
                  value={editData.custom_wine_region}
                  onChange={(e) => setEditData({ ...editData, custom_wine_region: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-wine-500 focus:border-transparent outline-none transition-all"
                  placeholder="e.g., Napa Valley"
                />
              </div>
              <div>
                <label className="font-mono text-xs uppercase tracking-wider text-gray-500 block mb-2">
                  Country
                </label>
                <input
                  type="text"
                  value={editData.custom_wine_country}
                  onChange={(e) => setEditData({ ...editData, custom_wine_country: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-wine-500 focus:border-transparent outline-none transition-all"
                  placeholder="e.g., USA"
                />
              </div>
            </div>

            {/* Status */}
            <div>
              <label className="font-mono text-xs uppercase tracking-wider text-gray-500 block mb-2">
                Collection Status
              </label>
              <div className="flex gap-2">
                {(['owned', 'tried', 'wishlist'] as CellarStatus[]).map((status) => {
                  const labels: Record<CellarStatus, string> = { owned: 'Owned', tried: 'Tried', wishlist: 'Saved' };
                  return (
                    <button
                      key={status}
                      onClick={() => setEditData({ ...editData, status })}
                      className={`flex-1 py-3 font-mono text-sm uppercase tracking-wider rounded-xl transition-all ${
                        editData.status === status
                          ? 'bg-wine-600 text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {labels[status]}
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Quantity - only for Owned wines */}
            {editData.status === 'owned' && (
              <div>
                <label className="font-mono text-xs uppercase tracking-wider text-gray-500 block mb-2">
                  Quantity
                </label>
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => setEditData({ ...editData, quantity: Math.max(1, editData.quantity - 1) })}
                    className="p-3 bg-gray-100 rounded-xl hover:bg-gray-200 transition-colors"
                  >
                    <Minus className="w-5 h-5 text-gray-600" />
                  </button>
                  <span className="font-mono text-xl text-gray-900 w-12 text-center">
                    {editData.quantity}
                  </span>
                  <button
                    onClick={() => setEditData({ ...editData, quantity: editData.quantity + 1 })}
                    className="p-3 bg-gray-100 rounded-xl hover:bg-gray-200 transition-colors"
                  >
                    <Plus className="w-5 h-5 text-gray-600" />
                  </button>
                </div>
              </div>
            )}

            {/* Rating */}
            <div>
              <label className="font-mono text-xs uppercase tracking-wider text-gray-500 block mb-2">
                Your Rating
              </label>
              <div className="flex items-center gap-2">
                {[1, 2, 3, 4, 5].map((star) => (
                  <button
                    key={star}
                    onClick={() => setEditData({ ...editData, rating: star })}
                    className="p-1"
                  >
                    <Star
                      className={`w-8 h-8 transition-colors ${
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
                    className="ml-2 text-xs text-gray-400 hover:text-gray-600 transition-colors"
                  >
                    Clear
                  </button>
                )}
              </div>
            </div>

            {/* Tasting Notes */}
            <div>
              <label className="font-mono text-xs uppercase tracking-wider text-gray-500 block mb-2">
                Your Notes
              </label>
              <textarea
                value={editData.tasting_notes}
                onChange={(e) => setEditData({ ...editData, tasting_notes: e.target.value })}
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-wine-500 focus:border-transparent outline-none transition-all resize-none"
                rows={4}
                placeholder="Add your tasting notes, occasion, or thoughts about this wine..."
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
