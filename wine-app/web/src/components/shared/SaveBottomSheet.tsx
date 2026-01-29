/**
 * Bottom sheet for saving wine to collection with status picker
 */

import { useState } from 'react';
import { Wine, Package, CheckCircle, Loader2 } from 'lucide-react';
import { BottomSheet } from './BottomSheet';
import type { Wine as WineType, CellarStatus } from '../../types';

type StatusOption = {
  value: CellarStatus;
  label: string;
  description: string;
  icon: React.ReactNode;
  color: string;
};

const statusOptions: StatusOption[] = [
  {
    value: 'owned',
    label: 'Owned',
    description: 'I have this in my cellar',
    icon: <Package className="w-5 h-5" />,
    color: 'text-green-600 bg-green-50 border-green-200',
  },
  {
    value: 'tried',
    label: 'Tried',
    description: 'I\'ve tasted this wine',
    icon: <CheckCircle className="w-5 h-5" />,
    color: 'text-blue-600 bg-blue-50 border-blue-200',
  },
];

interface SaveBottomSheetProps {
  isOpen: boolean;
  onClose: () => void;
  wine: WineType | null;
  onSave: (wineId: string, status: CellarStatus) => Promise<void>;
  isSaving?: boolean;
}

export function SaveBottomSheet({ isOpen, onClose, wine, onSave, isSaving }: SaveBottomSheetProps) {
  const [selectedStatus, setSelectedStatus] = useState<CellarStatus>('owned');

  const handleSave = async () => {
    if (!wine) return;
    await onSave(wine.id, selectedStatus);
    onClose();
  };

  if (!wine) return null;

  return (
    <BottomSheet isOpen={isOpen} onClose={onClose} title="Save to Collection">
      {/* Wine preview */}
      <div className="flex items-center gap-4 p-4 bg-cream rounded-xl mb-6">
        <div className="w-16 h-20 bg-white rounded-lg flex items-center justify-center flex-shrink-0">
          <Wine className="w-8 h-8 text-wine-600" />
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="font-serif text-lg text-gray-900 truncate">{wine.name}</h3>
          {wine.producer && (
            <p className="text-sm text-gray-500 truncate">{wine.producer}</p>
          )}
          <p className="font-mono text-xs uppercase tracking-wider text-gray-400 mt-1">
            {wine.wine_type} {wine.vintage && `· ${wine.vintage}`}
          </p>
        </div>
      </div>

      {/* Status options */}
      <div className="space-y-3 mb-6">
        <label className="font-mono text-xs uppercase tracking-wider text-gray-500">
          Add to
        </label>
        {statusOptions.map((option) => (
          <button
            key={option.value}
            onClick={() => setSelectedStatus(option.value)}
            className={`w-full flex items-center gap-4 p-4 rounded-xl border-2 transition-all ${
              selectedStatus === option.value
                ? option.color
                : 'border-gray-100 hover:border-gray-200 bg-white'
            }`}
          >
            <div className={`p-2 rounded-lg ${
              selectedStatus === option.value ? 'bg-white/50' : 'bg-gray-100'
            }`}>
              {option.icon}
            </div>
            <div className="text-left flex-1">
              <p className="font-medium text-gray-900">{option.label}</p>
              <p className="text-sm text-gray-500">{option.description}</p>
            </div>
            {selectedStatus === option.value && (
              <div className="w-5 h-5 rounded-full bg-current flex items-center justify-center">
                <svg className="w-3 h-3 text-white" viewBox="0 0 12 12" fill="none">
                  <path d="M2 6L5 9L10 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
            )}
          </button>
        ))}
      </div>

      {/* Save button */}
      <button
        onClick={handleSave}
        disabled={isSaving}
        className="w-full py-4 bg-wine-600 text-white rounded-xl hover:bg-wine-700 transition-colors font-mono text-sm uppercase tracking-wider disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {isSaving ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Saving...
          </>
        ) : (
          'Save to Collection'
        )}
      </button>
    </BottomSheet>
  );
}
