/**
 * Top navigation component
 */

import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { MessageCircle, Wine, User, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { LoginModal } from '../auth';

const navItems = [
  { path: '/', label: 'Pip', icon: MessageCircle },
  { path: '/cellar', label: 'My Cellar', icon: Wine },
];

export function Sidebar() {
  const location = useLocation();
  const { user, isAuthenticated, logout } = useAuth();
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleLogout = async () => {
    await logout();
    setShowUserMenu(false);
  };

  return (
    <>
      {/* Top navigation bar */}
      <header className="fixed top-0 left-0 right-0 h-16 bg-white border-b border-gray-100 z-50">
        <div className="max-w-6xl mx-auto h-full px-4 md:px-6 flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="font-serif text-3xl text-wine-600 italic">
            P
          </Link>

          {/* Navigation */}
          <nav className="flex items-center gap-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl transition-colors ${
                    isActive
                      ? 'bg-wine-50 text-wine-600'
                      : 'text-gray-500 hover:bg-gray-50 hover:text-gray-700'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span className="font-mono text-xs uppercase tracking-wider hidden sm:inline">
                    {item.label}
                  </span>
                </Link>
              );
            })}

            {/* User menu */}
            <div className="relative ml-2">
              {isAuthenticated ? (
                <>
                  <button
                    onClick={() => setShowUserMenu(!showUserMenu)}
                    className="p-2 rounded-xl hover:bg-gray-50 transition-colors"
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
                </>
              ) : (
                <button
                  onClick={() => setShowLoginModal(true)}
                  className="flex items-center gap-2 px-4 py-2 rounded-xl bg-wine-600 text-white hover:bg-wine-700 transition-colors"
                >
                  <User className="w-4 h-4" />
                  <span className="font-mono text-xs uppercase tracking-wider hidden sm:inline">
                    Sign In
                  </span>
                </button>
              )}
            </div>
          </nav>
        </div>
      </header>

      <LoginModal
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
      />
    </>
  );
}
