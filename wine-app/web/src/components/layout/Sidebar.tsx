/**
 * User menu component (top-right corner)
 */

import { useState } from 'react';
import { User, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { LoginModal } from '../auth';

export function Sidebar() {
  const { user, isAuthenticated, logout } = useAuth();
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = async () => {
    await logout();
    setShowUserMenu(false);
  };

  return (
    <>
      {/* User menu in top-right corner */}
      <div className="fixed top-4 right-4 z-50">
        {isAuthenticated ? (
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="p-2 rounded-xl bg-white/80 backdrop-blur-sm shadow-sm hover:bg-white transition-colors"
            >
              {user?.avatar_url ? (
                <img
                  src={user.avatar_url}
                  alt={user.display_name || 'User'}
                  className="w-8 h-8 rounded-full"
                />
              ) : (
                <div className="w-8 h-8 bg-wine-100 rounded-full flex items-center justify-center">
                  <User className="w-4 h-4 text-wine-600" />
                </div>
              )}
            </button>

            {showUserMenu && (
              <>
                <div
                  className="fixed inset-0"
                  onClick={() => setShowUserMenu(false)}
                />
                <div className="absolute right-0 top-full mt-2 w-48 bg-white rounded-xl shadow-lg border border-gray-100 py-1 z-50">
                  <div className="px-4 py-2 border-b border-gray-100">
                    <p className="font-medium text-gray-900 truncate text-sm">
                      {user?.display_name || 'User'}
                    </p>
                    <p className="text-xs text-gray-500 truncate">{user?.email}</p>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    Sign out
                  </button>
                </div>
              </>
            )}
          </div>
        ) : (
          <button
            onClick={() => setShowLoginModal(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-wine-600 text-white hover:bg-wine-700 transition-colors shadow-sm"
          >
            <User className="w-4 h-4" />
            <span className="font-mono text-xs uppercase tracking-wider hidden sm:inline">
              Sign In
            </span>
          </button>
        )}
      </div>

      <LoginModal
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
      />
    </>
  );
}
