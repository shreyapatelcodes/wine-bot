/**
 * Quick action buttons for chat messages
 */

import {
  Wine,
  BookOpen,
  Archive,
  Camera,
  Bookmark,
  Plus,
  Info,
  Sparkles,
  Undo2,
  Check,
  X,
  CheckCircle,
  Heart,
} from 'lucide-react';
import type { ChatAction, ChatCard } from '../../types';

interface ActionButtonsProps {
  actions: ChatAction[];
  onAction: (action: ChatAction, cardContext?: ChatCard) => void;
  cardContext?: ChatCard;
  className?: string;
}

const actionIcons: Record<string, React.ReactNode> = {
  recommend: <Wine className="w-3.5 h-3.5" />,
  educate: <BookOpen className="w-3.5 h-3.5" />,
  cellar: <Archive className="w-3.5 h-3.5" />,
  photo: <Camera className="w-3.5 h-3.5" />,
  save: <Bookmark className="w-3.5 h-3.5" />,
  add_cellar: <Plus className="w-3.5 h-3.5" />,
  tell_more: <Info className="w-3.5 h-3.5" />,
  find_similar: <Sparkles className="w-3.5 h-3.5" />,
  view_cellar: <Archive className="w-3.5 h-3.5" />,
  undo: <Undo2 className="w-3.5 h-3.5" />,
  confirm: <Check className="w-3.5 h-3.5" />,
  cancel: <X className="w-3.5 h-3.5" />,
  tried: <CheckCircle className="w-3.5 h-3.5" />,
  want_to_try: <Heart className="w-3.5 h-3.5" />,
};

export function ActionButtons({
  actions,
  onAction,
  cardContext,
  className = '',
}: ActionButtonsProps) {
  if (!actions || actions.length === 0) return null;

  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {actions.map((action, index) => (
        <button
          key={`${action.type}-${index}`}
          onClick={() => onAction(action, cardContext)}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium
                     bg-white border border-gray-200 rounded-full
                     hover:bg-cream-dark hover:border-wine-200 hover:text-wine-700
                     transition-colors shadow-sm"
        >
          {actionIcons[action.type] || null}
          {action.label}
        </button>
      ))}
    </div>
  );
}
