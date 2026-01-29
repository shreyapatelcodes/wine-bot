/**
 * Chat input component
 */

import { useState, useRef, type FormEvent, type KeyboardEvent } from 'react';
import { Loader2, ArrowRight, Camera } from 'lucide-react';

interface ChatInputProps {
  onSend: (message: string) => void;
  onCameraClick?: () => void;
  isLoading?: boolean;
  placeholder?: string;
}

export function ChatInput({ onSend, onCameraClick, isLoading, placeholder = "Ask about pairings, regions, or bottle IDs..." }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      onSend(message.trim());
      setMessage('');
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleInput = () => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 150)}px`;
    }
  };

  return (
    <form onSubmit={handleSubmit} className="relative bg-white rounded-full border border-gray-200 px-2 py-1.5 shadow-sm focus-within:ring-1 focus-within:ring-wine-500/20 focus-within:border-wine-500/30 transition-all">
      <div className="flex items-center gap-1">
        {/* Camera button */}
        {onCameraClick && (
          <button
            type="button"
            onClick={onCameraClick}
            disabled={isLoading}
            className="flex-shrink-0 p-2 text-gray-400 hover:text-wine-600 transition-colors rounded-full hover:bg-cream disabled:opacity-50"
            title="Scan wine label"
          >
            <Camera className="w-5 h-5" />
          </button>
        )}

        {/* Text input */}
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder={placeholder}
          disabled={isLoading}
          rows={1}
          className="flex-1 resize-none bg-transparent border-none px-2 py-2 text-sm focus:outline-none focus:ring-0 disabled:text-gray-400 placeholder:text-gray-400"
        />

        {/* Submit button */}
        <button
          type="submit"
          disabled={!message.trim() || isLoading}
          className={`flex-shrink-0 px-4 py-2 rounded-full flex items-center gap-2 transition-colors ${
            message.trim() && !isLoading
              ? 'bg-wine-600 text-white hover:bg-wine-700'
              : 'bg-gray-100 text-gray-400 cursor-not-allowed'
          }`}
        >
          {isLoading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <>
              <span className="font-mono text-[11px] uppercase tracking-wider">Consult Agent</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </>
          )}
        </button>
      </div>
    </form>
  );
}
