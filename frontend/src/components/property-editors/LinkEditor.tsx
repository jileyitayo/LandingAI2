'use client';

import { useState, useMemo, useEffect } from 'react';
import { Link as LinkIcon, ExternalLink, Info, ChevronDown, ChevronUp } from 'lucide-react';
import { toast } from 'sonner';

interface LinkEditorProps {
  href?: string;
  target?: string;
  rel?: string;
  onHrefChange?: (value: string) => void;
  onTargetChange?: (value: string) => void;
  onRelChange?: (value: string) => void;
  // Optional: Pass project files to extract available routes
  projectFiles?: Record<string, string>;
}

/**
 * Extracts route paths from App.tsx file
 * Parses React Router Route components to find available paths
 * Supports multiple formats:
 * - <Route path="/about" />
 * - <Route path={'/about'} />
 * - <Route path={`/about`} />
 * - <Route path={"/about"} />
 */
function extractRoutesFromApp(appContent: string): string[] {
  const routes: string[] = [];
  
  // Pattern 1: Standard quotes <Route path="/about" />
  const pattern1 = /<Route\s+path=["']([^"']+)["']/g;
  
  // Pattern 2: Curly braces with quotes <Route path={'/about'} />
  const pattern2 = /<Route\s+path=\{[`'"]([^`'"]+)[`'"]\}/g;
  
  // Pattern 3: Template literals <Route path={`/about`} />
  const pattern3 = /<Route\s+path=\{`([^`]+)`\}/g;
  
  let match;
  
  // Try all patterns
  while ((match = pattern1.exec(appContent)) !== null) {
    routes.push(match[1]);
  }
  
  while ((match = pattern2.exec(appContent)) !== null) {
    routes.push(match[1]);
  }
  
  while ((match = pattern3.exec(appContent)) !== null) {
    routes.push(match[1]);
  }
  
  // Remove duplicates and sort
  return [...new Set(routes)].sort();
}

export default function LinkEditor({
  href = '',
  target = '_self',
  rel = '',
  onHrefChange,
  onTargetChange,
  onRelChange,
  projectFiles,
}: LinkEditorProps) {
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [showInstructions, setShowInstructions] = useState(false);
  const [inputValue, setInputValue] = useState(href);

  // Extract available routes from App.tsx
  const availableRoutes = useMemo(() => {
    if (!projectFiles || !projectFiles['src/App.tsx']) {
      return [];
    }
    return extractRoutesFromApp(projectFiles['src/App.tsx']);
  }, [projectFiles]);

  /**
   * Validates if a link is valid
   * Valid formats:
   * - Empty string (no link)
   * - Relative path starting with / (e.g., /about)
   * - Hash link starting with # (e.g., #section)
   * - Full URL starting with http:// or https://
   * - Email link starting with mailto:
   * - Phone link starting with tel:
   */
  const validateLink = (link: string): boolean => {
    if (!link || link.trim() === '') {
      return true; // Empty is valid (no link)
    }
    
    const trimmedLink = link.trim();
    
    // Relative path (must start with /)
    if (trimmedLink.startsWith('/')) {
      // Check for valid path characters
      return /^\/[^\s]*$/.test(trimmedLink);
    }
    
    // Hash link (must start with #)
    if (trimmedLink.startsWith('#')) {
      return /^#[^\s]*$/.test(trimmedLink);
    }
    
    // Email link
    if (trimmedLink.startsWith('mailto:')) {
      const email = trimmedLink.substring(7);
      return email.length > 0 && !email.includes(' ');
    }
    
    // Phone link
    if (trimmedLink.startsWith('tel:')) {
      const phone = trimmedLink.substring(4);
      return phone.length > 0 && !phone.includes(' ');
    }
    
    // Full URL (must start with http:// or https://)
    if (trimmedLink.startsWith('http://') || trimmedLink.startsWith('https://')) {
      try {
        new URL(trimmedLink);
        return true;
      } catch {
        return false;
      }
    }
    
    // If it doesn't match any valid format, it's invalid
    return false;
  };

  // Check if current href is a route or external link
  const isExternalLink = useMemo(() => {
    if (!inputValue) return false;
    return inputValue.startsWith('http://') || 
           inputValue.startsWith('https://') || 
           inputValue.startsWith('mailto:') ||
           inputValue.startsWith('tel:');
  }, [inputValue]);

  // Filter routes based on input
  const filteredRoutes = useMemo(() => {
    if (!inputValue || inputValue.trim() === '') {
      return availableRoutes;
    }
    return availableRoutes.filter(route => 
      route.toLowerCase().includes(inputValue.toLowerCase())
    );
  }, [availableRoutes, inputValue]);

  // Handle route selection
  const handleRouteSelect = (route: string) => {
    setInputValue(route);
    if (onHrefChange) {
      onHrefChange(route);
    }
    setShowSuggestions(false);
  };

  // Handle input change
  const handleInputChange = (value: string) => {
    setInputValue(value);
    if (onHrefChange) {
      onHrefChange(value);
    }
    // Show suggestions if there are routes and input is not empty
    if (availableRoutes.length > 0 && value.trim() !== '') {
      setShowSuggestions(true);
    }
  };

  // Handle input blur - validate when user finishes typing
  const handleInputBlur = () => {
    if (inputValue && inputValue.trim() !== '') {
      const isValid = validateLink(inputValue);
      if (!isValid) {
        toast.error('Invalid Link', {
          description: 'Please enter a valid link. Use /path for pages, https:// for external sites, mailto: for email, or #section for anchors.',
          duration: 4000,
        });
      }
    }
  };

  // Update input value when href prop changes externally
  useEffect(() => {
    if (href !== inputValue) {
      setInputValue(href);
    }
  }, [href]);

  return (
    <div className="space-y-4">
      {/* Instructions */}
      <div className="bg-blue-900/20 border border-blue-700/50 rounded-lg p-3">
        <button
          onClick={() => setShowInstructions(!showInstructions)}
          className="w-full flex items-center justify-between text-left"
        >
          <div className="flex items-center gap-2 text-xs font-medium text-blue-300">
            <Info className="w-3 h-3" />
            How to set up links
          </div>
          {showInstructions ? (
            <ChevronUp className="w-3 h-3 text-blue-300" />
          ) : (
            <ChevronDown className="w-3 h-3 text-blue-300" />
          )}
        </button>
        {showInstructions && (
          <div className="mt-2 text-xs text-blue-200 space-y-1.5 pt-2 border-t border-blue-700/50">
            <p><strong>For internal pages:</strong> Use paths like <code className="bg-blue-900/50 px-1 rounded">/about</code> or <code className="bg-blue-900/50 px-1 rounded">/contact</code></p>
            <p><strong>For external sites:</strong> Use full URLs like <code className="bg-blue-900/50 px-1 rounded">https://example.com</code></p>
            <p><strong>For email:</strong> Use <code className="bg-blue-900/50 px-1 rounded">mailto:email@example.com</code></p>
            <p><strong>For sections:</strong> Use hash links like <code className="bg-blue-900/50 px-1 rounded">/#section</code></p>
            <p className="text-blue-300/80 mt-2">💡 Click on suggestions below to quickly select existing pages</p>
          </div>
        )}
      </div>

      {/* URL Input */}
      {onHrefChange && (
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-xs font-medium text-gray-400">
            <LinkIcon className="w-3 h-3" />
            URL or Path
          </label>
          <div className="relative">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => handleInputChange(e.target.value)}
              onBlur={handleInputBlur}
              onFocus={() => {
                if (availableRoutes.length > 0 && inputValue.trim() === '') {
                  setShowSuggestions(true);
                }
              }}
              placeholder={availableRoutes.length > 0 ? "Type or select a path..." : "https://example.com or /about"}
              className={`w-full px-3 py-2 bg-gray-800 border rounded text-sm text-gray-300 focus:outline-none ${
                inputValue && inputValue.trim() !== '' && !validateLink(inputValue)
                  ? 'border-red-500 focus:border-red-500'
                  : 'border-gray-700 focus:border-blue-500'
              }`}
            />
            {isExternalLink && (
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                <ExternalLink className="w-3 h-3 text-blue-400" />
              </div>
            )}
          </div>
          
          {/* Show validation error message */}
          {inputValue && inputValue.trim() !== '' && !validateLink(inputValue) && (
            <p className="text-xs text-red-400 flex items-center gap-1 mt-1">
              <Info className="w-3 h-3" />
              Invalid link format. Use /path, https://url, mailto:email, or #anchor
            </p>
          )}

          {/* Route Suggestions */}
          {showSuggestions && availableRoutes.length > 0 && (
            <div className="mt-2 border border-gray-700 rounded-lg bg-gray-800/95 overflow-hidden">
              <div className="px-3 py-2 bg-gray-750 border-b border-gray-700 flex items-center justify-between">
                <span className="text-xs font-medium text-gray-400">Available Pages</span>
                <button
                  onClick={() => setShowSuggestions(false)}
                  className="text-xs text-gray-500 hover:text-gray-300"
                >
                  Hide
                </button>
              </div>
              <div className="max-h-48 overflow-y-auto">
                {filteredRoutes.length > 0 ? (
                  filteredRoutes.map((route) => (
                    <button
                      key={route}
                      onClick={() => handleRouteSelect(route)}
                      className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-gray-700 hover:text-white transition-colors flex items-center gap-2"
                    >
                      <LinkIcon className="w-3 h-3 text-blue-400" />
                      <code className="text-xs">{route}</code>
                    </button>
                  ))
                ) : (
                  <div className="px-3 py-2 text-xs text-gray-500 text-center">
                    No matching pages found
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Show available routes hint when input is empty */}
          {!showSuggestions && availableRoutes.length > 0 && inputValue.trim() === '' && (
            <button
              onClick={() => setShowSuggestions(true)}
              className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
            >
              <LinkIcon className="w-3 h-3" />
              View {availableRoutes.length} available page{availableRoutes.length !== 1 ? 's' : ''}
            </button>
          )}
        </div>
      )}

      {/* Target */}
      {onTargetChange && (
        <div className="space-y-2">
          <label className="flex items-center gap-2 text-xs font-medium text-gray-400">
            <ExternalLink className="w-3 h-3" />
            Open Link In
          </label>
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={() => onTargetChange('_self')}
              className={`px-3 py-2 text-xs rounded border transition-colors ${
                target === '_self'
                  ? 'bg-blue-600 border-blue-500 text-white'
                  : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
              }`}
            >
              Same Tab
            </button>
            <button
              onClick={() => onTargetChange('_blank')}
              className={`px-3 py-2 text-xs rounded border transition-colors ${
                target === '_blank'
                  ? 'bg-blue-600 border-blue-500 text-white'
                  : 'bg-gray-800 border-gray-700 text-gray-300 hover:border-gray-600'
              }`}
            >
              New Tab
            </button>
          </div>
        </div>
      )}

      {/* Rel Attributes */}
      {onRelChange && target === '_blank' && (
        <div className="space-y-2">
          <label className="text-xs font-medium text-gray-400">Security</label>
          <div className="space-y-2">
            <label className="flex items-center gap-2 text-xs text-gray-300">
              <input
                type="checkbox"
                checked={rel.includes('noopener')}
                onChange={(e) => {
                  const newRel = e.target.checked
                    ? [...rel.split(' '), 'noopener'].filter(Boolean).join(' ')
                    : rel.replace('noopener', '').trim();
                  onRelChange(newRel);
                }}
                className="rounded border-gray-600"
              />
              noopener (recommended for security)
            </label>
            <label className="flex items-center gap-2 text-xs text-gray-300">
              <input
                type="checkbox"
                checked={rel.includes('noreferrer')}
                onChange={(e) => {
                  const newRel = e.target.checked
                    ? [...rel.split(' '), 'noreferrer'].filter(Boolean).join(' ')
                    : rel.replace('noreferrer', '').trim();
                  onRelChange(newRel);
                }}
                className="rounded border-gray-600"
              />
              noreferrer (hide referrer)
            </label>
          </div>
        </div>
      )}
    </div>
  );
}

