'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { Image as ImageIcon, Upload, Link as LinkIcon, Check, AlertCircle, Search, X, Loader2, Trash2 } from 'lucide-react';
import { api } from '@/lib/api';

interface ImageEditorProps {
  imageUrl?: string;
  imageAlt?: string;
  imageFit?: string;
  onImageUrlChange?: (value: string) => void;
  onImageAltChange?: (value: string) => void;
  onImageFitChange?: (value: string) => void;
  projectId?: string;
}

// const IMAGE_FIT_OPTIONS = [
//   { value: 'object-cover', label: 'Cover' },
//   { value: 'object-contain', label: 'Contain' },
//   { value: 'object-fill', label: 'Fill' },
//   { value: 'object-scale-down', label: 'Scale Down' },
//   { value: 'object-none', label: 'None' },
// ];

// Unsplash API types
interface UnsplashPhoto {
  id: string;
  urls: {
    regular: string;
    small: string;
    thumb: string;
  };
  alt_description: string | null;
  description: string | null;
  user: {
    name: string;
    username: string;
  };
}

interface UnsplashSearchResponse {
  results: UnsplashPhoto[];
  total: number;
  total_pages: number;
}

export default function ImageEditor({
  imageUrl = '',
  imageAlt = '',
  imageFit = 'object-cover',
  onImageUrlChange,
  onImageAltChange,
  onImageFitChange,
  projectId,
}: ImageEditorProps) {
  const [urlInput, setUrlInput] = useState(imageUrl);
  const [altInput, setAltInput] = useState(imageAlt);
  const [isValidUrl, setIsValidUrl] = useState(true);
  const [imageLoadError, setImageLoadError] = useState(false);
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const altDebounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  // Image selection modal state
  const [showImageModal, setShowImageModal] = useState(false);
  const [activeTab, setActiveTab] = useState<'link' | 'unsplash'>('link');
  const unsplashSearchInputRef = useRef<HTMLInputElement>(null);
  
  // Unsplash search state
  const [unsplashQuery, setUnsplashQuery] = useState('');
  const [unsplashResults, setUnsplashResults] = useState<UnsplashPhoto[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [unsplashError, setUnsplashError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [hasMoreResults, setHasMoreResults] = useState(false);
  const searchDebounceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const resultsContainerRef = useRef<HTMLDivElement>(null);

  // Upload state
  const uploadInputRef = useRef<HTMLInputElement>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);

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
      if (searchDebounceTimerRef.current) {
        clearTimeout(searchDebounceTimerRef.current);
      }
    };
  }, []);

  // Unsplash API search function
  const searchUnsplash = useCallback(async (query: string, page: number = 1) => {
    const apiKey = process.env.NEXT_PUBLIC_UNSPLASH_ACCESS_KEY;
    
    if (!apiKey) {
      setUnsplashError('Unsplash API key not configured. Please add NEXT_PUBLIC_UNSPLASH_ACCESS_KEY to your environment variables.');
      return;
    }

    if (!query.trim()) {
      setUnsplashResults([]);
      setHasMoreResults(false);
      return;
    }

    setIsSearching(true);
    setUnsplashError(null);

    try {
      const response = await fetch(
        `https://api.unsplash.com/search/photos?query=${encodeURIComponent(query)}&page=${page}&per_page=20&orientation=landscape`,
        {
          headers: {
            'Authorization': `Client-ID ${apiKey}`,
          },
        }
      );

      if (!response.ok) {
        throw new Error(`Unsplash API error: ${response.status} ${response.statusText}`);
      }

      const data: UnsplashSearchResponse = await response.json();
      
      if (page === 1) {
        setUnsplashResults(data.results);
        // Scroll to top when new search
        if (resultsContainerRef.current) {
          resultsContainerRef.current.scrollTop = 0;
        }
      } else {
        setUnsplashResults(prev => [...prev, ...data.results]);
      }
      
      setHasMoreResults(page < data.total_pages);
      setCurrentPage(page);
    } catch (error) {
      console.error('Unsplash search error:', error);
      setUnsplashError(error instanceof Error ? error.message : 'Failed to search Unsplash');
      setUnsplashResults([]);
    } finally {
      setIsSearching(false);
    }
  }, []);

  // Debounced Unsplash search
  const debouncedUnsplashSearch = useCallback((query: string) => {
    if (searchDebounceTimerRef.current) {
      clearTimeout(searchDebounceTimerRef.current);
    }
    
    searchDebounceTimerRef.current = setTimeout(() => {
      setCurrentPage(1);
      searchUnsplash(query, 1);
    }, 500); // Wait 500ms after user stops typing
  }, [searchUnsplash]);

  // Handle Unsplash search input
  const handleUnsplashSearchChange = (query: string) => {
    setUnsplashQuery(query);
    debouncedUnsplashSearch(query);
  };

  // Handle image selection from Unsplash
  const handleSelectUnsplashImage = (photo: UnsplashPhoto) => {
    // Use regular size for better quality
    const newImageUrl = photo.urls.regular;
    
    // Clear any pending debounce timers
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = null;
    }
    if (altDebounceTimerRef.current) {
      clearTimeout(altDebounceTimerRef.current);
      altDebounceTimerRef.current = null;
    }
    
    // Update local state
    setUrlInput(newImageUrl);
    setImageLoadError(false);
    setIsValidUrl(true); // Unsplash URLs are always valid
    
    // Set alt text from photo description if available
    const newAltText = photo.alt_description || photo.description || '';
    if (newAltText) {
      setAltInput(newAltText);
    }
    
    // Apply changes immediately (bypass debounce for instant feedback)
    // Call the change handlers directly to ensure they fire
    // Always send imageUrl - it's the primary property
    if (onImageUrlChange) {
      onImageUrlChange(newImageUrl);
    }
    // Only send alt text if it has a value AND is different from current
    // Backend fails if alt is empty or unchanged, so we skip it in those cases
    if (onImageAltChange && newAltText.trim() && newAltText.trim() !== (imageAlt || '').trim()) {
      onImageAltChange(newAltText);
    }
    
    // Keep modal open for browsing (Trello-style)
    // User can close manually or select another image
  };

  // Handle removing image
  const handleRemoveImage = () => {
    setUrlInput('');
    setAltInput('');
    setImageLoadError(false);
    if (onImageUrlChange) {
      onImageUrlChange('');
    }
    if (onImageAltChange) {
      onImageAltChange('');
    }
    setShowImageModal(false);
  };

  // Load more Unsplash results
  const loadMoreUnsplashResults = () => {
    if (!isSearching && hasMoreResults && unsplashQuery.trim()) {
      searchUnsplash(unsplashQuery, currentPage + 1);
    }
  };

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

  // Close modal on Escape key
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && showImageModal) {
        setShowImageModal(false);
      }
    };
    window.addEventListener('keydown', handleEscape);
    return () => window.removeEventListener('keydown', handleEscape);
  }, [showImageModal]);

  // Auto-focus Unsplash search when switching to Unsplash tab
  useEffect(() => {
    if (activeTab === 'unsplash' && showImageModal && unsplashSearchInputRef.current) {
      unsplashSearchInputRef.current.focus();
    }
  }, [activeTab, showImageModal]);

  // Open modal to Unsplash tab if no image is set
  const handleOpenImageModal = () => {
    setShowImageModal(true);
    if (!urlInput) {
      setActiveTab('unsplash');
    }
  };

  return (
    <div className="space-y-4">
      {/* Info banner */}
      <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-2">
        <div className="text-xs text-blue-300">
          ✨ Changes apply automatically as you type
        </div>
      </div>
      
      {/* Current Image Preview - Clickable to open modal */}
      <div className="space-y-2">
        <label className="text-xs font-medium text-gray-400">Image</label>
        <button
          onClick={handleOpenImageModal}
          className="w-full aspect-video bg-gray-800 rounded-lg overflow-hidden border border-gray-700 hover:border-blue-500 transition-all relative group"
        >
          {urlInput ? (
            !imageLoadError ? (
              <>
                <img
                  src={urlInput}
                  alt={altInput || 'Preview'}
                  className={`w-full h-full ${imageFit}`}
                  onError={() => setImageLoadError(true)}
                />
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/40 transition-colors flex items-center justify-center">
                  <div className="opacity-0 group-hover:opacity-100 transition-opacity text-white text-sm font-medium">
                    Change Image
                  </div>
                </div>
              </>
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center text-gray-500">
                <AlertCircle className="w-8 h-8 mb-2" />
                <p className="text-sm">Failed to load image</p>
                <p className="text-xs mt-1">Click to change</p>
              </div>
            )
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center text-gray-400">
              <ImageIcon className="w-12 h-12 mb-2 opacity-50" />
              <p className="text-sm">Click to add image</p>
            </div>
          )}
        </button>
        {urlInput && (
          <button
            onClick={handleRemoveImage}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-red-900/20 rounded border border-red-800/50 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Remove Image
          </button>
        )}
      </div>

      {/* Image Selection Modal - Trello Style */}
      {showImageModal && (
        <div 
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm"
          onClick={(e) => {
            // Close modal when clicking backdrop
            if (e.target === e.currentTarget) {
              setShowImageModal(false);
            }
          }}
        >
          <div 
            className="bg-gray-900 border border-gray-700 rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between p-4 border-b border-gray-700">
              <h3 className="text-lg font-semibold text-gray-200">Change Image</h3>
              <button
                onClick={() => setShowImageModal(false)}
                className="text-gray-400 hover:text-gray-200 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-gray-700">
              <button
                onClick={() => setActiveTab('link')}
                className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === 'link'
                    ? 'text-blue-400 border-b-2 border-blue-400 bg-gray-800/50'
                    : 'text-gray-400 hover:text-gray-300 hover:bg-gray-800/30'
                }`}
              >
                <div className="flex items-center justify-center gap-2">
                  <LinkIcon className="w-4 h-4" />
                  Link
                </div>
              </button>
              <button
                onClick={() => setActiveTab('unsplash')}
                className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                  activeTab === 'unsplash'
                    ? 'text-blue-400 border-b-2 border-blue-400 bg-gray-800/50'
                    : 'text-gray-400 hover:text-gray-300 hover:bg-gray-800/30'
                }`}
              >
                <div className="flex items-center justify-center gap-2">
                  <ImageIcon className="w-4 h-4" />
                  Unsplash
                </div>
              </button>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto p-4">
              {activeTab === 'link' && (
                <div className="space-y-4">
                  <div className="space-y-2">
                    <label className="flex items-center gap-2 text-sm font-medium text-gray-300">
                      <LinkIcon className="w-4 h-4" />
                      Image URL
                    </label>
                    <div className="relative">
                      <input
                        type="text"
                        value={urlInput}
                        onChange={(e) => handleUrlChange(e.target.value)}
                        onKeyDown={handleUrlKeyDown}
                        placeholder="https://example.com/image.jpg"
                        className={`w-full px-4 py-3 pr-10 bg-gray-800 border rounded-lg text-sm text-gray-300 focus:outline-none focus:ring-2 transition-all ${
                          !isValidUrl
                            ? 'border-red-500 focus:ring-red-500/50'
                            : hasUrlChanges
                            ? 'border-yellow-500 focus:ring-yellow-500/50'
                            : 'border-gray-700 focus:ring-blue-500/50'
                        }`}
                        autoFocus
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
                  
                  {/* Preview */}
                  {urlInput && isValidUrl && (
                    <div className="space-y-2">
                      <label className="text-sm font-medium text-gray-300">Preview</label>
                      <div className="aspect-video bg-gray-800 rounded-lg overflow-hidden border border-gray-700">
                        <img
                          src={urlInput}
                          alt={altInput || 'Preview'}
                          className={`w-full h-full ${imageFit}`}
                          onError={() => setImageLoadError(true)}
                        />
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'unsplash' && (
                <div className="space-y-4">
                  {/* Search Input */}
                  <div className="relative">
                    <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      ref={unsplashSearchInputRef}
                      type="text"
                      value={unsplashQuery}
                      onChange={(e) => handleUnsplashSearchChange(e.target.value)}
                      placeholder="Search Unsplash..."
                      className="w-full pl-12 pr-12 py-3 bg-gray-800 border border-gray-700 rounded-lg text-sm text-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500/50"
                    />
                    {unsplashQuery && (
                      <button
                        onClick={() => {
                          setUnsplashQuery('');
                          setUnsplashResults([]);
                        }}
                        className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-200 transition-colors"
                      >
                        <X className="w-5 h-5" />
                      </button>
                    )}
                  </div>

                  {/* Error Message */}
                  {unsplashError && (
                    <div className="p-3 bg-red-900/20 border border-red-700/50 rounded-lg text-sm text-red-400 flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 flex-shrink-0" />
                      <span>{unsplashError}</span>
                    </div>
                  )}

                  {/* Search Results */}
                  <div ref={resultsContainerRef} className="max-h-[500px] overflow-y-auto">
                    {isSearching && unsplashResults.length === 0 && (
                      <div className="flex items-center justify-center py-12">
                        <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
                        <span className="ml-3 text-sm text-gray-400">Searching...</span>
                      </div>
                    )}

                    {!isSearching && unsplashQuery && unsplashResults.length === 0 && !unsplashError && (
                      <div className="text-center py-12 text-sm text-gray-400">
                        No images found. Try a different search term.
                      </div>
                    )}

                    {unsplashResults.length > 0 && (
                      <>
                        <div className="grid grid-cols-3 gap-3">
                          {unsplashResults.map((photo) => (
                            <button
                              key={photo.id}
                              onClick={() => handleSelectUnsplashImage(photo)}
                              className="group relative aspect-video bg-gray-800 rounded-lg overflow-hidden border-2 border-transparent hover:border-blue-500 transition-all hover:scale-105"
                              title={photo.alt_description || photo.description || 'Unsplash image'}
                            >
                              <img
                                src={photo.urls.small}
                                alt={photo.alt_description || photo.description || ''}
                                className="w-full h-full object-cover"
                                loading="lazy"
                              />
                              <div className="absolute inset-0 bg-black/0 group-hover:bg-black/50 transition-colors flex items-center justify-center">
                                <Check className="w-8 h-8 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                              </div>
                            </button>
                          ))}
                        </div>

                        {/* Load More Button */}
                        {hasMoreResults && (
                          <div className="mt-4 flex justify-center">
                            <button
                              onClick={loadMoreUnsplashResults}
                              disabled={isSearching}
                              className="px-6 py-2 text-sm text-blue-400 hover:text-blue-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 border border-blue-500/50 rounded-lg hover:bg-blue-500/10 transition-colors"
                            >
                              {isSearching ? (
                                <>
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                  Loading...
                                </>
                              ) : (
                                'Load More'
                              )}
                            </button>
                          </div>
                        )}
                      </>
                    )}

                    {/* Initial State - No Search */}
                    {!unsplashQuery && unsplashResults.length === 0 && !isSearching && (
                      <div className="text-center py-12">
                        <ImageIcon className="w-16 h-16 text-gray-600 mx-auto mb-4" />
                        <p className="text-sm text-gray-400 mb-2">Search for images on Unsplash</p>
                        <p className="text-xs text-gray-500">Try searching for "nature", "business", "technology", etc.</p>
                      </div>
                    )}
                  </div>

                  {/* Attribution */}
                  {unsplashResults.length > 0 && (
                    <p className="text-xs text-gray-500 text-center pt-2 border-t border-gray-700">
                      Images from{' '}
                      <a
                        href="https://unsplash.com"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-400 hover:text-blue-300"
                      >
                        Unsplash
                      </a>
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end gap-3 p-4 border-t border-gray-700">
              <button
                onClick={() => setShowImageModal(false)}
                className="px-4 py-2 text-sm text-gray-300 hover:text-white transition-colors"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Upload Button */}
      <div className="relative space-y-1">
        <input
          ref={uploadInputRef}
          type="file"
          accept="image/png,image/jpeg,image/webp,image/gif"
          className="hidden"
          onChange={async (e) => {
            const file = e.target.files?.[0];
            if (!file) return;
            setUploadError(null);
            setIsUploading(true);
            try {
              const result = await api.media.upload(file, { projectId });
              setUrlInput(result.public_url);
              setImageLoadError(false);
              onImageUrlChange?.(result.public_url);
            } catch (err) {
              setUploadError(err instanceof Error ? err.message : 'Upload failed');
            } finally {
              setIsUploading(false);
              if (uploadInputRef.current) uploadInputRef.current.value = '';
            }
          }}
        />
        <button
          onClick={() => uploadInputRef.current?.click()}
          disabled={isUploading}
          className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gray-800 border border-gray-700 rounded transition-colors hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isUploading ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Upload className="w-4 h-4" />
          )}
          <span className="text-sm text-gray-300">
            {isUploading ? 'Uploading...' : 'Upload Image'}
          </span>
        </button>
        {uploadError && (
          <p className="text-xs text-red-400 flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            {uploadError}
          </p>
        )}
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
      {/* {onImageFitChange && (
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
      )} */}
    </div>
  );
}

