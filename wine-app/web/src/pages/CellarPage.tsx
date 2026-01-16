/**
 * Cellar management page
 */

import { useState } from 'react';
import { Package, Plus, Lock, Camera } from 'lucide-react';
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
      alert('Failed to analyze image. This feature will be available in Phase 4.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleAddFromScan = async (wine: Wine | null, customData?: { name: string; producer?: string }) => {
    if (wine) {
      await addBottle({ wine_id: wine.id, status: 'owned', quantity: 1 });
    } else if (customData) {
      await addBottle({
        custom_wine_name: customData.name,
        custom_wine_producer: customData.producer,
        status: 'owned',
        quantity: 1,
      });
    }
    setShowScanModal(false);
    setScanResult(null);
  };

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-48" />
          <div className="grid grid-cols-4 gap-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-24 bg-gray-200 rounded-xl" />
            ))}
          </div>
          <div className="h-32 bg-gray-200 rounded-xl" />
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <>
        <div className="max-w-3xl mx-auto px-4 py-12">
          <div className="text-center">
            <div className="w-16 h-16 bg-wine-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Lock className="w-8 h-8 text-wine-600" />
            </div>
            <h1 className="text-2xl font-semibold text-gray-900 mb-2">
              Sign in to manage your cellar
            </h1>
            <p className="text-gray-500 mb-6">
              Track your wine collection, add tasting notes, and more.
            </p>
            <button
              onClick={() => setShowLoginModal(true)}
              className="px-6 py-3 bg-wine-600 text-white font-medium rounded-lg hover:bg-wine-700 transition-colors"
            >
              Sign in to get started
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
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-wine-100 rounded-lg">
              <Package className="w-5 h-5 text-wine-600" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-gray-900">My Cellar</h1>
              <p className="text-sm text-gray-500">Manage your wine collection</p>
            </div>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setShowScanModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              <Camera className="w-4 h-4" />
              <span className="hidden sm:inline">Scan Label</span>
            </button>
            <button
              onClick={() => setShowAddModal(true)}
              className="flex items-center gap-2 px-4 py-2 bg-wine-600 text-white rounded-lg hover:bg-wine-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span className="hidden sm:inline">Add Bottle</span>
            </button>
          </div>
        </div>

        {/* Cellar list */}
        <CellarList />
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
          <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-lg mx-4 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Scan Wine Label
            </h2>

            {!scanResult ? (
              <>
                <ImageUpload
                  onImageSelect={handleImageScan}
                  isLoading={isAnalyzing}
                />
                <p className="text-xs text-gray-400 text-center mt-4">
                  Take a photo of the wine label to automatically identify the wine.
                  This feature will be fully available in Phase 4.
                </p>
              </>
            ) : (
              <div className="space-y-4">
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h3 className="font-medium text-gray-900">Detected Wine</h3>
                  <p className="text-sm text-gray-600 mt-1">
                    {scanResult.analysis.name || 'Unknown wine'}
                    {scanResult.analysis.vintage && ` (${scanResult.analysis.vintage})`}
                  </p>
                  {scanResult.analysis.producer && (
                    <p className="text-sm text-gray-500">{scanResult.analysis.producer}</p>
                  )}
                  <p className="text-xs text-gray-400 mt-2">
                    Confidence: {Math.round(scanResult.analysis.confidence * 100)}%
                  </p>
                </div>

                {scanResult.best_match ? (
                  <button
                    onClick={() => handleAddFromScan(scanResult.best_match)}
                    className="w-full py-2 bg-wine-600 text-white rounded-lg hover:bg-wine-700"
                  >
                    Add "{scanResult.best_match.name}" to Cellar
                  </button>
                ) : (
                  <button
                    onClick={() =>
                      handleAddFromScan(null, {
                        name: scanResult.analysis.name || 'Unknown Wine',
                        producer: scanResult.analysis.producer || undefined,
                      })
                    }
                    className="w-full py-2 bg-wine-600 text-white rounded-lg hover:bg-wine-700"
                  >
                    Add as Custom Wine
                  </button>
                )}

                <button
                  onClick={() => setScanResult(null)}
                  className="w-full py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200"
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
