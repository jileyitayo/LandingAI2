'use client';

import { useState, useEffect, useRef } from 'react';
import { Monitor, Tablet, Smartphone, Maximize2, Minimize2, RotateCw } from 'lucide-react';

type ViewportSize = 'desktop' | 'tablet' | 'mobile';

interface WebsitePreviewProps {
  html?: string;
  css?: string;
  js?: string;
  isLoading?: boolean;
}

const viewportSizes = {
  desktop: { width: '100%', height: '100%', label: 'Desktop' },
  tablet: { width: '768px', height: '1024px', label: 'Tablet' },
  mobile: { width: '375px', height: '667px', label: 'Mobile' },
};

export default function WebsitePreviewHtml({ 
  html = '', 
  css = '', 
  js = '',
  isLoading = false 
}: WebsitePreviewProps) {
  const [viewport, setViewport] = useState<ViewportSize>('desktop');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  // Create complete HTML document with injected CSS and JS
  const fullHTML = `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    /* Reset styles */
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      line-height: 1.6;
      color: #333;
    }
    /* Injected CSS */
    ${css}
  </style>
</head>
<body>
  ${html}
  <script>
    // Error handling wrapper
    (function() {
      try {
        ${js}
      } catch (error) {
        console.error('Preview JavaScript Error:', error);
      }
    })();
  </script>
</body>
</html>
    `;

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
  };

  const toggleFullscreen = () => {
    if (!isFullscreen) {
      containerRef.current?.requestFullscreen?.();
      setIsFullscreen(true);
    } else {
      document.exitFullscreen?.();
      setIsFullscreen(false);
    }
  };

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  return (
    <div ref={containerRef} className="flex flex-col h-full bg-gray-50">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setViewport('desktop')}
            className={`p-2 rounded-lg transition-colors ${
              viewport === 'desktop'
                ? 'bg-blue-100 text-blue-600'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
            title="Desktop view"
          >
            <Monitor className="w-5 h-5" />
          </button>
          <button
            onClick={() => setViewport('tablet')}
            className={`p-2 rounded-lg transition-colors ${
              viewport === 'tablet'
                ? 'bg-blue-100 text-blue-600'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
            title="Tablet view"
          >
            <Tablet className="w-5 h-5" />
          </button>
          <button
            onClick={() => setViewport('mobile')}
            className={`p-2 rounded-lg transition-colors ${
              viewport === 'mobile'
                ? 'bg-blue-100 text-blue-600'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
            title="Mobile view"
          >
            <Smartphone className="w-5 h-5" />
          </button>

          <div className="ml-2 px-3 py-1 bg-gray-100 rounded-md text-sm text-gray-600">
            {viewportSizes[viewport].label}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="Refresh preview"
          >
            <RotateCw className="w-5 h-5" />
          </button>
          <button
            onClick={toggleFullscreen}
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title={isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}
          >
            {isFullscreen ? (
              <Minimize2 className="w-5 h-5" />
            ) : (
              <Maximize2 className="w-5 h-5" />
            )}
          </button>
        </div>
      </div>

      {/* Preview Area */}
      <div className="flex-1 flex items-center justify-center p-4 overflow-auto">
        <div
          className="bg-white rounded-lg shadow-lg transition-all duration-300 overflow-hidden"
          style={{
            width: viewportSizes[viewport].width,
            height: viewport === 'desktop' ? '100%' : viewportSizes[viewport].height,
            maxWidth: '100%',
            maxHeight: '100%',
          }}
        >
          {isLoading ? (
            <div className="flex items-center justify-center h-full bg-white">
              <div className="text-center">
                <div className="inline-block w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
                <p className="text-gray-600">Loading preview...</p>
              </div>
            </div>
          ) : (
            <iframe
              key={refreshKey}
              title="Website Preview"
              sandbox="allow-scripts allow-same-origin"
              className="w-full h-full border-0"
              style={{ backgroundColor: 'white' }}
              srcDoc={fullHTML}
            />
          )}
        </div>
      </div>
    </div>
  );
}

