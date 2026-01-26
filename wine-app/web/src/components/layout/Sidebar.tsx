/**
 * Sidebar navigation component
 */

import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { MessageCircle, Package, Bookmark, User, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { LoginModal } from '../auth';

const navItems = [
  { path: '/', label: 'Sommelier AI', icon: MessageCircle },
  { path: '/cellar', label: 'Global Cellar', icon: Package },
  { path: '/saved', label: 'Curated Selections', icon: Bookmark },
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
      {/* Desktop sidebar */}
      <aside className="hidden md:flex fixed left-0 top-0 h-screen w-20 bg-white border-r border-gray-100 flex-col items-center py-8 z-50">
        {/* Logo */}
        <Link to="/" className="font-serif text-3xl text-wine-600 font-bold mb-12">
          V
        </Link>

        {/* Navigation */}
        <nav className="flex-1 flex flex-col items-center gap-8">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex flex-col items-center gap-3 group ${
                  isActive ? 'text-wine-600' : 'text-gray-400 hover:text-gray-600'
                }`}
                title={item.label}
              >
                <div
                  className={`p-2.5 rounded-xl transition-colors ${
                    isActive ? 'bg-wine-50' : 'group-hover:bg-gray-50'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                </div>
                <span className="vertical-text font-mono text-[10px] uppercase tracking-widest whitespace-nowrap">
                  {item.label}
                </span>
              </Link>
            );
          })}
        </nav>

        {/* User menu */}
        <div className="relative">
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
                  <div className="absolute left-full bottom-0 ml-2 w-48 bg-white rounded-xl shadow-lg border border-gray-100 py-1 z-50">
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
              className="p-2.5 rounded-xl bg-wine-600 text-white hover:bg-wine-700 transition-colors"
            >
              <User className="w-5 h-5" />
            </button>
          )}
        </div>
      </aside>

      {/* Mobile bottom navigation */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-100 z-50 safe-area-pb">
        <div className="flex items-center justify-around py-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex flex-col items-center gap-1 px-4 py-2 rounded-xl transition-colors ${
                  isActive
                    ? 'text-wine-600'
                    : 'text-gray-400 hover:text-gray-600'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="text-[10px] font-mono uppercase tracking-wide">
                  {item.label.split(' ')[0]}
                </span>
              </Link>
            );
          })}
          {isAuthenticated ? (
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex flex-col items-center gap-1 px-4 py-2"
            >
              {user?.avatar_url ? (
                <img
                  src={user.avatar_url}
                  alt={user.display_name || 'User'}
                  className="w-5 h-5 rounded-full"
                />
              ) : (
                <User className="w-5 h-5 text-gray-400" />
              )}
              <span className="text-[10px] font-mono uppercase tracking-wide text-gray-400">
                Profile
              </span>
            </button>
          ) : (
            <button
              onClick={() => setShowLoginModal(true)}
              className="flex flex-col items-center gap-1 px-4 py-2"
            >
              <User className="w-5 h-5 text-wine-600" />
              <span className="text-[10px] font-mono uppercase tracking-wide text-wine-600">
                Sign In
              </span>
            </button>
          )}
        </div>
      </nav>

      <LoginModal
        isOpen={showLoginModal}
        onClose={() => setShowLoginModal(false)}
      />
    </>
  );
}
