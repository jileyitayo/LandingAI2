'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Image as ImageIcon, Upload, Link as LinkIcon, Check, AlertCircle } from 'lucide-react';

interface ImageEditorProps {
  imageUrl?: string;
  imageAlt?: string;
  imageFit?: string;
  onImageUrlChange?: (value: string) => void;
  onImageAltChange?: (value: string) => void;
  onImageFitChange?: (value: string) => void;
}

const IMAGE_FIT_OPTIONS = [
  { value: 'object-cover', label: 'Cover' },
  { value: 'object-contain', label: 'Contain' },
  { value: 'object-fill', label: 'Fill' },
  { value: 'object-scale-down', label: 'Scale Down' },
  { value: 'object-none', label: 'None' },
];

export default function ImageEditor({
  imageUrl = '',
  imageAlt = '',
  imageFit = 'object-cover',
  onImageUrlChange,
  onImageAltChange,
  onImageFitChange,
}: ImageEditorProps) {
  const [urlInput, setUrlInput] = useState(imageUrl);
  const [altInput, setAltInput] = useState(imageAlt);
  const [isValidUrl, setIsValidUrl] = useState(true);
  const [imageLoadError, setImageLoadError] = useState(false);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const altDebounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Update local values when props change
  useEffect(() => {
    setUrlInput(imageUrl);
  }, [imageUrl]);

  useEffect(() => {
    setAltInput(imageAlt);
  }, [imageAlt]);

  // Validate URL format
  const validateUrl = (url: string): boolean => {
    if (!url) return true; // Empty is valid
    try {
      new URL(url);
      return true;
    } catch {
      // Check if it's a relative path
      return url.startsWith('/') || url.startsWith('./');
    }
  };

  // Debounced URL change for real-time updates
  // Reduced debounce delay for faster real-time preview updates
  const debouncedUrlChange = useCallback((newUrl: string) => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    
    const isValid = validateUrl(newUrl);
    setIsValidUrl(isValid);
    
    if (!isValid) return;
    
    // Apply immediately for real-time preview updates (optimistic update handles instant feedback)
    // Still debounce the backend save, but trigger the change callback immediately
    if (onImageUrlChange && newUrl !== imageUrl) {
      onImageUrlChange(newUrl);
    }
    
    // No need for debounce here since optimistic updates provide instant feedback
    // The backend save is already debounced in handlePropertyChange
  }, [imageUrl, onImageUrlChange]);

  // Debounced alt text change
  const debouncedAltChange = useCallback((newAlt: string) => {
    if (altDebounceTimerRef.current) {
      clearTimeout(altDebounceTimerRef.current);
    }
    
    altDebounceTimerRef.current = setTimeout(() => {
      if (onImageAltChange && newAlt !== imageAlt) {
        onImageAltChange(newAlt);
      }
    }, 800); // Wait 800ms after last keystroke
  }, [imageAlt, onImageAltChange]);

  // Cleanup timers
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
      if (altDebounceTimerRef.current) {
        clearTimeout(altDebounceTimerRef.current);
      }
    };
  }, []);

  // Handle URL input change
  const handleUrlChange = (newUrl: string) => {
    setUrlInput(newUrl);
    setImageLoadError(false);
    debouncedUrlChange(newUrl);
  };

  // Handle Enter key to apply immediately
  const handleUrlKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
      const isValid = validateUrl(urlInput);
      setIsValidUrl(isValid);
      if (isValid && onImageUrlChange) {
        onImageUrlChange(urlInput);
      }
    }
  };

  // Handle alt text change
  const handleAltChange = (newAlt: string) => {
    setAltInput(newAlt);
    debouncedAltChange(newAlt);
  };

  // Handle alt text Enter key
  const handleAltKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      if (altDebounceTimerRef.current) {
        clearTimeout(altDebounceTimerRef.current);
      }
      if (onImageAltChange) {
        onImageAltChange(altInput);
      }
    }
  };

  const hasUrlChanges = urlInput !== imageUrl;
  const hasAltChanges = altInput !== imageAlt;

  return (
    <div className="space-y-4">
      {/* Info banner */}
      <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-2">
        <div className="text-xs text-blue-300">
          ✨ Changes apply automatically as you type
        </div>
      </div>
      {/* Current Image Preview */}
      {urlInput && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-400">Preview</label>
          <div className="aspect-video bg-gray-800 rounded-lg overflow-hidden border border-gray-700 relative">
            {!imageLoadError ? (
              <img
                src={urlInput}
                alt={altInput || 'Preview'}
                className={`w-full h-full ${imageFit}`}
                onError={() => setImageLoadError(true)}
              />
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center text-gray-500">
                <AlertCircle className="w-8 h-8 mb-2" />
                <p className="text-sm">Failed to load image</p>
                <p className="text-xs mt-1">Check the URL</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Image URL Input */}
      {onImageUrlChange && (
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-xs font-medium text-gray-400">
            <LinkIcon className="w-3 h-3" />
            Image URL
          </label>
          <div className="relative">
            <input
              type="text"
              value={urlInput}
              onChange={(e) => handleUrlChange(e.target.value)}
              onKeyDown={handleUrlKeyDown}
              placeholder="https://example.com/image.jpg"
              className={`w-full px-3 py-2 pr-10 bg-gray-800 border rounded text-sm text-gray-300 focus:outline-none focus:ring-2 transition-all ${
                !isValidUrl
                  ? 'border-red-500 focus:ring-red-500/50'
                  : hasUrlChanges
                  ? 'border-yellow-500 focus:ring-yellow-500/50'
                  : 'border-gray-700 focus:ring-blue-500/50'
              }`}
            />
            {hasUrlChanges && isValidUrl && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                <div className="w-2 h-2 bg-yellow-500 rounded-full animate-pulse" />
              </div>
            )}
          </div>
          {!isValidUrl && (
            <p className="text-xs text-red-400 flex items-center gap-1">
              <AlertCircle className="w-3 h-3" />
              Please enter a valid URL
            </p>
          )}
          {hasUrlChanges && isValidUrl && (
            <p className="text-xs text-blue-400">
              Press Enter or wait 1 second to apply changes
            </p>
          )}
        </div>
      )}

      {/* Upload Button - Coming soon */}
      <div className="relative">
        <button 
          disabled
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gray-800 border border-gray-700 rounded transition-colors opacity-50 cursor-not-allowed"
        >
          <Upload className="w-4 h-4" />
          <span className="text-sm text-gray-300">Upload Image (Coming Soon)</span>
        </button>
      </div>

      {/* Alt Text */}
      {onImageAltChange && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-400">Alt Text (Accessibility)</label>
          <input
            type="text"
            value={altInput}
            onChange={(e) => handleAltChange(e.target.value)}
            onKeyDown={handleAltKeyDown}
            placeholder="Describe the image for screen readers"
            className={`w-full px-3 py-2 bg-gray-800 border rounded text-sm text-gray-300 focus:outline-none focus:ring-2 transition-all ${
              hasAltChanges
                ? 'border-yellow-500 focus:ring-yellow-500/50'
                : 'border-gray-700 focus:ring-blue-500/50'
            }`}
          />
          {hasAltChanges && (
            <p className="text-xs text-blue-400">Saving as you type...</p>
          )}
        </div>
      )}

      {/* Image Fit */}
      {onImageFitChange && (
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-xs font-medium text-gray-400">
            <ImageIcon className="w-3 h-3" />
            Object Fit
          </label>
          <div className="grid grid-cols-3 gap-2">
            {IMAGE_FIT_OPTIONS.map((fit) => (
              <button
                key={fit.value}
                onClick={() => onImageFitChange(fit.value)}
                className={`px-3 py-2 text-xs rounded border transition-all ${
                  imageFit === fit.value
                    ? 'bg-blue-600 border-blue-500 text-white shadow-lg scale-105'
                    : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-blue-400 hover:bg-gray-750 hover:scale-105'
                }`}
              >
                {fit.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

