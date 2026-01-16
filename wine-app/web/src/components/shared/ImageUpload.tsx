/**
 * Image upload component for bottle recognition
 */

import { useState, useRef, type ChangeEvent, type DragEvent } from 'react';
import { Upload, Camera, X, Loader2, Image as ImageIcon } from 'lucide-react';

interface ImageUploadProps {
  onImageSelect: (base64: string) => void;
  isLoading?: boolean;
  accept?: string;
}

export function ImageUpload({ onImageSelect, isLoading, accept = 'image/*' }: ImageUploadProps) {
  const [preview, setPreview] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const processFile = (file: File) => {
    if (!file.type.startsWith('image/')) {
      alert('Please select an image file');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const result = e.target?.result as string;
      setPreview(result);
      // Extract base64 data (remove data URL prefix)
      const base64 = result.split(',')[1];
      onImageSelect(base64);
    };
    reader.readAsDataURL(file);
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) {
      processFile(file);
    }
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const clearPreview = () => {
    setPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="w-full">
      {preview ? (
        <div className="relative rounded-xl overflow-hidden border border-gray-200">
          <img
            src={preview}
            alt="Preview"
            className="w-full h-64 object-contain bg-gray-50"
          />
          {!isLoading && (
            <button
              onClick={clearPreview}
              className="absolute top-2 right-2 p-1.5 bg-white/90 rounded-full text-gray-600 hover:bg-white hover:text-gray-900 transition-colors shadow-sm"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          {isLoading && (
            <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
              <div className="text-center text-white">
                <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2" />
                <p className="text-sm">Analyzing image...</p>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div
          onClick={() => fileInputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors ${
            isDragging
              ? 'border-wine-500 bg-wine-50'
              : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
          }`}
        >
          <div className="flex flex-col items-center gap-3">
            <div className={`p-3 rounded-full ${isDragging ? 'bg-wine-100' : 'bg-gray-100'}`}>
              <Upload className={`w-6 h-6 ${isDragging ? 'text-wine-600' : 'text-gray-400'}`} />
            </div>
            <div>
              <p className="font-medium text-gray-900">
                {isDragging ? 'Drop image here' : 'Upload wine bottle image'}
              </p>
              <p className="text-sm text-gray-500 mt-1">
                Drag and drop or click to select
              </p>
            </div>
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <ImageIcon className="w-4 h-4" />
              <span>JPG, PNG, HEIC up to 10MB</span>
            </div>
          </div>
        </div>
      )}

      <input
        ref={fileInputRef}
        type="file"
        accept={accept}
        onChange={handleFileChange}
        className="hidden"
      />

      {/* Mobile camera button */}
      {!preview && (
        <button
          onClick={() => {
            if (fileInputRef.current) {
              fileInputRef.current.setAttribute('capture', 'environment');
              fileInputRef.current.click();
              fileInputRef.current.removeAttribute('capture');
            }
          }}
          className="mt-3 w-full flex items-center justify-center gap-2 py-2 px-4 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors md:hidden"
        >
          <Camera className="w-4 h-4" />
          Take Photo
        </button>
      )}
    </div>
  );
}
