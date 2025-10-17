'use client';

import { RefreshCw, ExternalLink, AlertCircle } from 'lucide-react';

interface ReactPreviewProps {
  previewUrl: string | null;
  isBuilding: boolean;
  error: string | null;
  onRebuild: () => void;
}

export default function ReactPreview({ previewUrl, isBuilding, error, onRebuild }: ReactPreviewProps) {
  if (isBuilding) {
    return (
      <div className="h-full bg-gray-900 flex items-center justify-center">
        <div className="text-center text-gray-300">
          <div className="inline-block w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mb-4"></div>
          <h3 className="text-lg font-medium mb-2">Building Preview</h3>
          <p className="text-sm text-gray-400 mb-4">
            This may take 5-10 seconds...
          </p>
          <div className="flex items-center justify-center gap-2 text-xs text-gray-500">
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse"></div>
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }}></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full bg-gray-900 flex items-center justify-center">
        <div className="text-center text-gray-300 max-w-md">
          <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-medium mb-2 text-red-400">Build Failed</h3>
          <p className="text-sm text-gray-400 mb-4">
            {error}
          </p>
          <button
            onClick={onRebuild}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors mx-auto"
          >
            <RefreshCw className="w-4 h-4" />
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!previewUrl) {
    return (
      <div className="h-full bg-gray-900 flex items-center justify-center">
        <div className="text-center text-gray-300">
          <div className="text-4xl mb-4">🚀</div>
          <h3 className="text-lg font-medium mb-2">Ready to Preview</h3>
          <p className="text-sm text-gray-400 mb-4">
            Click the "Build Preview" button to generate a live preview
          </p>
          <button
            onClick={onRebuild}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors mx-auto"
          >
            <RefreshCw className="w-4 h-4" />
            Build Preview
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-gray-900 flex flex-col">
      {/* Preview Header */}
      <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center gap-2 text-gray-300">
          <div className="w-2 h-2 bg-green-500 rounded-full"></div>
          <span className="text-sm font-medium">Live Preview</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onRebuild}
            className="flex items-center gap-1 px-3 py-1 text-xs text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors"
            title="Rebuild preview"
          >
            <RefreshCw className="w-3 h-3" />
            Rebuild
          </button>
          <a
            href={previewUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 px-3 py-1 text-xs text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors"
            title="Open in new tab"
          >
            <ExternalLink className="w-3 h-3" />
            Open
          </a>
        </div>
      </div>

      {/* Preview Iframe */}
      <div className="flex-1 bg-white">
        <iframe
          src={previewUrl}
          className="w-full h-full border-0"
          title="React Preview"
          sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
        />
      </div>

      {/* Preview Footer */}
      <div className="px-4 py-2 bg-gray-800 border-t border-gray-700 text-xs text-gray-500">
        <div className="flex items-center justify-between">
          <span>Preview expires in 1 hour</span>
          <span>Built with Vite</span>
        </div>
      </div>
    </div>
  );
}
