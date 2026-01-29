/**
 * Persistent left rail showing user's wine lists
 */

import { useState } from 'react';
import { Heart, Package, Star, ChevronDown, ChevronRight, Wine as WineIcon, Lock } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useSavedBottles } from '../../hooks/useSavedBottles';
import { useCellar } from '../../hooks/useCellar';
import type { SavedBottle, CellarBottle } from '../../types';

interface ListSectionProps {
  title: string;
  icon: React.ReactNode;
  count: number;
  color: string;
  items: Array<{ id: string; name: string; producer?: string | null }>;
  isExpanded: boolean;
  onToggle: () => void;
  emptyAction?: {
    label: string;
    onClick: () => void;
  };
}

function ListSection({ title, icon, count, color, items, isExpanded, onToggle, emptyAction }: ListSectionProps) {
  return (
    <div className="mb-2">
      <button
        onClick={onToggle}
        className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-cream-dark/50 transition-colors text-left ${color}`}
      >
        {isExpanded ? (
          <ChevronDown className="w-3.5 h-3.5 text-gray-400" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 text-gray-400" />
        )}
        {icon}
        <span className="flex-1 font-medium text-sm text-gray-700">{title}</span>
        <span className="font-mono text-xs bg-gray-100 text-gray-500 px-1.5 py-0.5 rounded">
          {count}
        </span>
      </button>

      {isExpanded && items.length > 0 && (
        <div className="ml-6 mt-1 space-y-0.5">
          {items.slice(0, 5).map((item) => (
            <div
              key={item.id}
              className="px-3 py-1.5 text-sm text-gray-600 truncate hover:bg-cream-dark/30 rounded transition-colors cursor-default"
              title={`${item.name}${item.producer ? ` - ${item.producer}` : ''}`}
            >
              {item.name}
            </div>
          ))}
          {items.length > 5 && (
            <div className="px-3 py-1 text-xs text-gray-400 italic">
              +{items.length - 5} more
            </div>
          )}
        </div>
      )}

      {isExpanded && items.length === 0 && emptyAction && (
        <div className="ml-6 mt-1">
          <button
            onClick={emptyAction.onClick}
            className={`px-3 py-2 text-xs ${color} hover:bg-cream-dark/50 rounded transition-colors flex items-center gap-1`}
          >
            <span>{emptyAction.label}</span>
            <span className="text-gray-400">→</span>
          </button>
        </div>
      )}

      {isExpanded && items.length === 0 && !emptyAction && (
        <div className="ml-6 mt-1 px-3 py-2 text-xs text-gray-400 italic">
          No wines yet
        </div>
      )}
    </div>
  );
}

export function WineListsSidebar() {
  const { isAuthenticated } = useAuth();
  const { bottles: savedBottles, isLoading: savedLoading } = useSavedBottles();
  const { bottles: cellarBottles, isLoading: cellarLoading } = useCellar();

  const [expandedSections, setExpandedSections] = useState({
    wishlist: true,
    cellar: false,
    tried: false,
  });

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections((prev) => ({ ...prev, [section]: !prev[section] }));
  };

  // Focus the chat input when empty action is clicked
  const focusChatInput = () => {
    const chatInput = document.querySelector('textarea');
    if (chatInput) {
      chatInput.focus();
      chatInput.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  };

  // Transform data for display
  const wishlistItems = savedBottles.map((b: SavedBottle) => ({
    id: b.id,
    name: b.wine.name,
    producer: b.wine.producer,
  }));

  const cellarItems = cellarBottles
    .filter((b: CellarBottle) => b.status === 'owned')
    .map((b: CellarBottle) => ({
      id: b.id,
      name: b.wine?.name || b.custom_wine_name || 'Unknown',
      producer: b.wine?.producer || b.custom_wine_producer,
    }));

  const triedItems = cellarBottles
    .filter((b: CellarBottle) => b.status === 'tried')
    .map((b: CellarBottle) => ({
      id: b.id,
      name: b.wine?.name || b.custom_wine_name || 'Unknown',
      producer: b.wine?.producer || b.custom_wine_producer,
    }));

  const isLoading = savedLoading || cellarLoading;

  if (!isAuthenticated) {
    return (
      <aside className="w-56 flex-shrink-0 bg-cream-light/50 border-r border-gray-200/50 p-4 hidden lg:block">
        <div className="flex items-center gap-2 mb-4">
          <WineIcon className="w-5 h-5 text-wine-600" />
          <h2 className="font-serif text-lg text-gray-800">My Lists</h2>
        </div>
        <div className="flex flex-col items-center justify-center py-8 text-center">
          <Lock className="w-8 h-8 text-gray-300 mb-2" />
          <p className="text-sm text-gray-400">Sign in to track your wines</p>
        </div>
      </aside>
    );
  }

  return (
    <aside className="w-56 flex-shrink-0 bg-cream-light/50 border-r border-gray-200/50 p-4 hidden lg:block">
      <div className="flex items-center gap-2 mb-4">
        <WineIcon className="w-5 h-5 text-wine-600" />
        <h2 className="font-serif text-lg text-gray-800">My Lists</h2>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="animate-pulse">
              <div className="h-8 bg-gray-200/50 rounded-lg" />
            </div>
          ))}
        </div>
      ) : (
        <nav className="space-y-1">
          <ListSection
            title="Wishlist"
            icon={<Heart className="w-4 h-4 text-pink-500" />}
            count={wishlistItems.length}
            color="text-pink-600"
            items={wishlistItems}
            isExpanded={expandedSections.wishlist}
            onToggle={() => toggleSection('wishlist')}
            emptyAction={{
              label: "Find your first bottle",
              onClick: focusChatInput,
            }}
          />

          <ListSection
            title="Cellar"
            icon={<Package className="w-4 h-4 text-green-600" />}
            count={cellarItems.length}
            color="text-green-600"
            items={cellarItems}
            isExpanded={expandedSections.cellar}
            onToggle={() => toggleSection('cellar')}
            emptyAction={{
              label: "Add wines you own",
              onClick: focusChatInput,
            }}
          />

          <ListSection
            title="Tried"
            icon={<Star className="w-4 h-4 text-purple-500" />}
            count={triedItems.length}
            color="text-purple-600"
            items={triedItems}
            isExpanded={expandedSections.tried}
            onToggle={() => toggleSection('tried')}
            emptyAction={{
              label: "Rate a wine you've had",
              onClick: focusChatInput,
            }}
          />
        </nav>
      )}
    </aside>
  );
}
