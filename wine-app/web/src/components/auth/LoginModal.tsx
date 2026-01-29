/**
 * Login modal component
 */

import { useState } from 'react';
import { X } from 'lucide-react';
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
      <div className="relative bg-cream-light rounded-xl shadow-2xl w-full max-w-md mx-4 p-8">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-wine-600 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Logo - styled "P" like the typing indicator */}
        <div className="flex justify-center mb-6">
          <div className="w-14 h-14 bg-wine-600 rounded-full flex items-center justify-center">
            <span className="font-serif text-white text-2xl italic">P</span>
          </div>
        </div>

        {/* Label */}
        <p className="font-mono text-[10px] uppercase tracking-widest text-gray-400 text-center mb-1">
          AI Wine Agent
        </p>

        {/* Title */}
        <h2 className="font-serif italic text-3xl text-center text-wine-600 mb-2">
          Welcome to Pip.
        </h2>
        <p className="font-mono text-[10px] uppercase tracking-wider text-gray-500 text-center mb-8 max-w-xs mx-auto">
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
        </div>

        {/* Terms */}
        <p className="mt-6 font-mono text-[10px] uppercase tracking-wider text-gray-400 text-center">
          By continuing, you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </div>
  );
}
