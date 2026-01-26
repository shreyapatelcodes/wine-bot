/**
 * Cellar management page
 */

import { useState } from 'react';
import { Plus, Lock, Camera, Search, Sparkles, ArrowRight } from 'lucide-react';
import { CellarList, AddBottleModal } from '../components/cellar';
import { LoginModal } from '../components/auth';
import { ImageUpload } from '../components/shared';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { useCellar } from '../hooks';
import type { VisionMatchResponse, Wine } from '../types';

export function CellarPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const { addBottle } = useCellar();
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showScanModal, setShowScanModal] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [scanResult, setScanResult] = useState<VisionMatchResponse | null>(null);

  const handleImageScan = async (base64: string) => {
    setIsAnalyzing(true);
    try {
      const result = await api.matchImage(base64);
      setScanResult(result);
    } catch (error) {
      console.error('Failed to analyze image:', error);
      alert('Failed to analyze image. Please try again with a clearer photo of the wine label.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleAddFromScan = async (wine: Wine | null, customData?: { name: string; producer?: string; vintage?: number; varietal?: string; wine_type?: string; region?: string; country?: string }) => {
    if (wine) {
      await addBottle({ wine_id: wine.id, status: 'owned', quantity: 1 });
    } else if (customData) {
      await addBottle({
        custom_wine_name: customData.name,
        custom_wine_producer: customData.producer,
        custom_wine_vintage: customData.vintage,
        custom_wine_varietal: customData.varietal,
        custom_wine_type: customData.wine_type as 'red' | 'white' | 'rosé' | 'sparkling' | undefined,
        custom_wine_region: customData.region,
        custom_wine_country: customData.country,
        status: 'owned',
        quantity: 1,
      });
    }
    setShowScanModal(false);
    setScanResult(null);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen px-6 md:px-8 py-8">
        <div className="max-w-6xl mx-auto animate-pulse space-y-6">
          <div className="h-12 bg-cream-dark rounded-lg w-72" />
          <div className="h-6 bg-cream-dark rounded w-48" />
          <div className="flex gap-3">
            <div className="h-10 bg-cream-dark rounded-xl w-32" />
            <div className="h-10 bg-cream-dark rounded-xl w-32" />
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-24 bg-cream-dark rounded-xl" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <>
        <div className="h-screen flex flex-col items-center justify-center px-8">
          <div className="text-center max-w-md">
            <div className="w-20 h-20 bg-wine-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <Lock className="w-10 h-10 text-wine-600" />
            </div>
            <h1 className="font-serif italic text-3xl text-gray-900 mb-3">
              Your Collection Awaits
            </h1>
            <p className="text-gray-500 mb-8 leading-relaxed">
              Sign in to curate your personal wine cellar, track your collection, and receive personalized recommendations.
            </p>
            <button
              onClick={() => setShowLoginModal(true)}
              className="px-8 py-3 bg-wine-600 text-white font-medium rounded-xl hover:bg-wine-700 transition-colors"
            >
              Sign In
            </button>
          </div>
        </div>

        <LoginModal
          isOpen={showLoginModal}
          onClose={() => setShowLoginModal(false)}
        />
      </>
    );
  }

  return (
    <>
      <div className="min-h-screen">
        {/* Page header */}
        <header className="px-6 md:px-8 pt-8 pb-6">
          <div className="max-w-6xl mx-auto">
            <p className="font-mono text-xs uppercase tracking-widest text-gray-400 mb-2">
              AI Wine Agent / My Cellar
            </p>
            <h1 className="font-serif italic text-4xl md:text-5xl text-wine-600">
              My Personal Cellar.
            </h1>
            <p className="font-mono text-xs uppercase tracking-wider text-gray-500 mt-4 max-w-lg">
              A curated collection of your finest acquisitions. Manage your inventory and consult our agent for the perfect pairing.
            </p>

            {/* Action buttons */}
            <div className="flex flex-wrap gap-3 mt-6">
              <button
                onClick={() => setShowAddModal(true)}
                className="flex items-center gap-2 px-5 py-2.5 bg-white border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors"
              >
                <Plus className="w-4 h-4" />
                <span className="font-mono text-xs uppercase tracking-wider">Add Bottle</span>
              </button>
              <button
                onClick={() => setShowScanModal(true)}
                className="flex items-center gap-2 px-5 py-2.5 bg-white border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors"
              >
                <Camera className="w-4 h-4" />
                <span className="font-mono text-xs uppercase tracking-wider">Scan Label</span>
              </button>
              <button className="flex items-center gap-2 px-5 py-2.5 bg-white border border-gray-200 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors">
                <Search className="w-4 h-4" />
                <span className="font-mono text-xs uppercase tracking-wider">Search Collection</span>
              </button>
            </div>
          </div>
        </header>

        {/* AI suggestion banner */}
        <div className="px-6 md:px-8 mb-6">
          <div className="max-w-6xl mx-auto">
            <button className="w-full p-5 bg-gradient-to-r from-wine-600 to-wine-700 text-white rounded-xl flex items-center justify-between group hover:from-wine-700 hover:to-wine-800 transition-all shadow-lg shadow-wine-600/20">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                  <Sparkles className="w-6 h-6" />
                </div>
                <div className="text-left">
                  <h3 className="font-serif italic text-xl">What should I drink tonight?</h3>
                  <p className="text-wine-100 text-sm mt-1">Get a personalized recommendation from your cellar</p>
                </div>
              </div>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </button>
          </div>
        </div>

        {/* Cellar content */}
        <div className="px-6 md:px-8 pb-8">
          <div className="max-w-6xl mx-auto">
            <CellarList />
          </div>
        </div>
      </div>

      {/* Add bottle modal */}
      <AddBottleModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
      />

      {/* Scan label modal */}
      {showScanModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => {
              setShowScanModal(false);
              setScanResult(null);
            }}
          />
          <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg mx-4 p-6">
            <h2 className="font-serif text-xl text-gray-900 mb-4">
              Scan Wine Label
            </h2>

            {!scanResult ? (
              <>
                <ImageUpload
                  onImageSelect={handleImageScan}
                  isLoading={isAnalyzing}
                />
                <p className="text-xs text-gray-400 text-center mt-4 font-mono uppercase tracking-wider">
                  Take a photo of the wine label to automatically identify the wine.
                </p>
              </>
            ) : (
              <div className="space-y-4">
                <div className="p-4 bg-cream rounded-xl">
                  <p className="font-mono text-[10px] uppercase tracking-wider text-wine-600 mb-2">Detected Wine</p>
                  <p className="font-serif text-lg text-gray-900">
                    {scanResult.analysis.name || 'Unknown wine'}
                    {scanResult.analysis.vintage && ` (${scanResult.analysis.vintage})`}
                  </p>
                  {scanResult.analysis.producer && (
                    <p className="text-sm text-gray-500 mt-1">{scanResult.analysis.producer}</p>
                  )}
                  {(scanResult.analysis.varietal || scanResult.analysis.wine_type) && (
                    <p className="text-sm text-gray-500">
                      {[scanResult.analysis.varietal, scanResult.analysis.wine_type].filter(Boolean).join(' \u2022 ')}
                    </p>
                  )}
                  {(scanResult.analysis.region || scanResult.analysis.country) && (
                    <p className="text-sm text-gray-500">
                      {[scanResult.analysis.region, scanResult.analysis.country].filter(Boolean).join(', ')}
                    </p>
                  )}
                  <p className="font-mono text-[10px] uppercase tracking-wider text-gray-400 mt-3">
                    Confidence: {Math.round(scanResult.analysis.confidence * 100)}%
                  </p>
                </div>

                <button
                  onClick={() =>
                    handleAddFromScan(scanResult.best_match, {
                      name: scanResult.analysis.name || 'Unknown Wine',
                      producer: scanResult.analysis.producer || undefined,
                      vintage: scanResult.analysis.vintage || undefined,
                      varietal: scanResult.analysis.varietal || undefined,
                      wine_type: scanResult.analysis.wine_type || undefined,
                      region: scanResult.analysis.region || undefined,
                      country: scanResult.analysis.country || undefined,
                    })
                  }
                  className="w-full py-3 bg-wine-600 text-white rounded-xl hover:bg-wine-700 transition-colors font-mono text-sm uppercase tracking-wider"
                >
                  Add to Cellar
                </button>

                <button
                  onClick={() => setScanResult(null)}
                  className="w-full py-3 bg-cream text-gray-700 rounded-xl hover:bg-cream-dark transition-colors font-mono text-sm uppercase tracking-wider"
                >
                  Scan Different Image
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  );
}
