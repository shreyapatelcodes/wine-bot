/**
 * Login modal component
 */

import { useState } from 'react';
import { X, Wine } from 'lucide-react';
import { GoogleLoginButton } from './GoogleLoginButton';

interface LoginModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export function LoginModal({ isOpen, onClose, onSuccess }: LoginModalProps) {
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleSuccess = () => {
    setError(null);
    onSuccess?.();
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-md mx-4 p-6">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Logo */}
        <div className="flex justify-center mb-6">
          <div className="w-16 h-16 bg-gradient-to-br from-wine-600 to-wine-800 rounded-2xl flex items-center justify-center">
            <Wine className="w-8 h-8 text-white" />
          </div>
        </div>

        {/* Title */}
        <h2 className="text-2xl font-semibold text-center text-gray-900 mb-2">
          Welcome to WineAI
        </h2>
        <p className="text-gray-500 text-center mb-6">
          Sign in to save bottles, manage your cellar, and get personalized recommendations.
        </p>

        {/* Error message */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        {/* Login buttons */}
        <div className="space-y-3">
          <GoogleLoginButton
            onSuccess={handleSuccess}
            onError={setError}
          />

          {/* Apple Sign-In placeholder */}
          <button
            disabled
            className="flex items-center justify-center gap-3 w-full px-4 py-3 bg-black text-white rounded-lg opacity-50 cursor-not-allowed"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
              <path d="M17.05 20.28c-.98.95-2.05.8-3.08.35-1.09-.46-2.09-.48-3.24 0-1.44.62-2.2.44-3.06-.35C2.79 15.25 3.51 7.59 9.05 7.31c1.35.07 2.29.74 3.08.8 1.18-.24 2.31-.93 3.57-.84 1.51.12 2.65.72 3.4 1.8-3.12 1.87-2.38 5.98.48 7.13-.57 1.5-1.31 2.99-2.54 4.09l.01-.01zM12.03 7.25c-.15-2.23 1.66-4.07 3.74-4.25.29 2.58-2.34 4.5-3.74 4.25z" />
            </svg>
            <span className="font-medium">Continue with Apple (Coming Soon)</span>
          </button>
        </div>

        {/* Terms */}
        <p className="mt-6 text-xs text-gray-400 text-center">
          By continuing, you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </div>
  );
}
