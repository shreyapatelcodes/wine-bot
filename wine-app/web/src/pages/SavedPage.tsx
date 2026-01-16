/**
 * Saved bottles page
 */

import { useState } from 'react';
import { Bookmark, Lock } from 'lucide-react';
import { SavedBottlesList } from '../components/saved';
import { LoginModal } from '../components/auth';
import { useAuth } from '../context/AuthContext';

export function SavedPage() {
  const { isAuthenticated, isLoading } = useAuth();
  const [showLoginModal, setShowLoginModal] = useState(false);

  if (isLoading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-gray-200 rounded w-48" />
          <div className="h-4 bg-gray-200 rounded w-64" />
          <div className="h-32 bg-gray-200 rounded" />
          <div className="h-32 bg-gray-200 rounded" />
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
              Sign in to view saved bottles
            </h1>
            <p className="text-gray-500 mb-6">
              Save wines from recommendations to keep track of bottles you want to try.
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
    <div className="max-w-3xl mx-auto px-4 py-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="p-2 bg-wine-100 rounded-lg">
          <Bookmark className="w-5 h-5 text-wine-600" />
        </div>
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Saved Bottles</h1>
          <p className="text-sm text-gray-500">Wines you want to try</p>
        </div>
      </div>

      <SavedBottlesList />
    </div>
  );
}
