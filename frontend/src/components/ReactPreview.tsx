'use client';

import { useState, useEffect, useRef, memo } from 'react';
import { RefreshCw, ExternalLink, AlertCircle, Eye, EyeOff, X, ChevronRight, ChevronDown } from 'lucide-react';

interface SelectedElement {
    tagName: string;
    selector: string;
    path: string[];
    position: {
        top: number;
        left: number;
        width: number;
        height: number;
    };
    inlineStyles: Record<string, string>;
    computedStyles: Record<string, string>;
    classList: string[];
    textContent: string;
    innerHTML: string;
    attributes: Record<string, string>;
    hasChildren: boolean;
    childCount: number;
    outerHTML: string;
    component?: {
        tagName: string;
        selector: string;
        path: string[];
        position: {
            top: number;
            left: number;
            width: number;
            height: number;
        };
        attributes: Record<string, string>;
        isRoot: boolean;
        componentName: string | null;
        componentFile: string | null;
        elementName: string | null;
    };
}

interface ReactPreviewProps {
  previewUrl: string | null;
  isBuilding: boolean;
  error: string | null;
  onRebuild: () => void;
  selectedElement?: SelectedElement | null;
  onElementSelect?: (element: SelectedElement | null) => void;
  selectorEnabled?: boolean;
  onSelectorEnabledChange?: (enabled: boolean) => void;
}

function ReactPreview({
  previewUrl,
  isBuilding,
  error,
  onRebuild,
  selectedElement = null,
  onElementSelect,
  selectorEnabled = false,
  onSelectorEnabledChange
}: ReactPreviewProps) {
  const [selectorReady, setSelectorReady] = useState(false);
  const [showDetailsPanel, setShowDetailsPanel] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Listen for messages from iframe
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'SELECTOR_READY') {
        setSelectorReady(true);
        console.log('Selector script loaded in iframe');
        // Auto-enable selector when it's ready
        if (onSelectorEnabledChange && !selectorEnabled) {
          onSelectorEnabledChange(true);
        }
      } else if (event.data.type === 'ELEMENT_SELECTED') {
        if (onElementSelect) {
          onElementSelect(event.data.data);
        }
        console.log('Element selected:', event.data.data);
      } else if (event.data.type === 'ELEMENT_RIGHT_CLICKED') {
        if (onElementSelect) {
          onElementSelect(event.data.data);
        }
      } else if (event.data.type === 'PREVIEW_CLICKED') {
        // Auto-enable selector when user clicks in preview
        if (onSelectorEnabledChange && !selectorEnabled && selectorReady) {
          onSelectorEnabledChange(true);
        }
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [onElementSelect, onSelectorEnabledChange, selectorEnabled, selectorReady]);

  // Sync selector state with iframe
  useEffect(() => {
    if (iframeRef.current?.contentWindow && selectorReady) {
      iframeRef.current.contentWindow.postMessage({
        type: selectorEnabled ? 'ENABLE_SELECTOR' : 'DISABLE_SELECTOR',
      }, '*');
    }
  }, [selectorEnabled, selectorReady]);

  // Toggle selector mode
  const toggleSelector = () => {
    if (!selectorReady) {
      return;
    }
    if (onSelectorEnabledChange) {
      onSelectorEnabledChange(!selectorEnabled);
    }
  };

  // Clear selection
  const clearSelection = () => {
    if (onElementSelect) {
      onElementSelect(null);
    }
  };
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
    <div className="h-full bg-gray-900 flex">
      {/* Main Preview Area */}
      <div className={`flex-1 flex flex-col transition-all ${selectorEnabled && showDetailsPanel ? 'mr-0' : ''}`}>

        {/* Preview Header */}
        <div className="flex items-center justify-between px-4 py-2 bg-gray-800 border-b border-gray-700">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 text-gray-300">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <span className="text-sm font-medium">Live Preview</span>
            </div>
            {onSelectorEnabledChange && (
              <button
                onClick={toggleSelector}
                disabled={!selectorReady}
                className={`flex items-center gap-1 px-3 py-1 text-xs rounded transition-colors ${
                  selectorEnabled
                    ? 'bg-blue-500 text-white hover:bg-blue-600'
                    : 'text-gray-400 hover:text-white hover:bg-gray-700'
                } disabled:opacity-50 disabled:cursor-not-allowed`}
                title={selectorEnabled ? 'Disable selector' : 'Enable selector'}
              >
                {selectorEnabled ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                {selectorEnabled ? 'Selector On' : 'Enable Selector'}
              </button>
            )}
            {!selectorReady && selectorEnabled && (
              <span className="text-xs text-gray-500">Loading selector...</span>
            )}
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
        <div className={`flex-1 bg-white relative transition-all ${
          selectorEnabled ? 'ring-2 ring-blue-500 ring-inset' : ''
        }`}>
          <iframe
            ref={iframeRef}
            src={previewUrl}
            className={`w-full h-full border-0 ${
              selectorEnabled ? 'cursor-crosshair' : ''
            }`}
            title="React Preview"
            sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals allow-downloads"
          />
          {/* Selector Active Indicator */}
          {selectorEnabled && (
            <div className="absolute top-2 left-2 bg-blue-500 text-white text-xs px-2 py-1 rounded shadow-lg flex items-center gap-1 pointer-events-none">
              <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
              Click any element to edit
            </div>
          )}
        </div>

        {/* Preview Footer */}
        <div className="px-4 py-2 bg-gray-800 border-t border-gray-700 text-xs text-gray-500">
          <div className="flex items-center justify-between">
            <span>Preview expires in 1 hour</span>
            <span>Built with Vite</span>
          </div>
        </div>
      </div>

      {/* Closeable Details Panel (25% width) - Only shown when selector is enabled */}
      {selectorEnabled && showDetailsPanel && (
        <div className="w-1/4 bg-gray-800 border-l border-gray-700 flex flex-col">
          <div className="flex items-center justify-between p-3 border-b border-gray-700">
            <h3 className="text-sm font-semibold text-white">Component Details</h3>
            <button
              onClick={() => setShowDetailsPanel(false)}
              className="text-gray-400 hover:text-white transition-colors"
              title="Close panel"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="flex-1 overflow-y-auto p-4">
            {selectedElement ? (
              <div className="space-y-4">
                {/* Component Info - Prominently displayed */}
                <div className="bg-gradient-to-br from-blue-900 to-blue-800 p-4 rounded-lg border border-blue-600 shadow-sm">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      {/* Component Name */}
                      {selectedElement.component?.componentName ? (
                        <div>
                          <div className="text-xs text-blue-300 font-medium mb-1">COMPONENT</div>
                          <div className="font-bold text-lg text-white mb-1">
                            {selectedElement.component.componentName}
                          </div>
                          {selectedElement.component.componentFile && (
                            <div className="text-xs text-blue-200 font-mono bg-blue-950 px-2 py-1 rounded inline-block">
                              {selectedElement.component.componentFile}
                            </div>
                          )}
                        </div>
                      ) : (
                        <div>
                          <div className="text-xs text-amber-300 font-medium mb-1">WARNING</div>
                          <div className="text-sm text-amber-100">
                            No component data found
                          </div>
                          <div className="text-xs text-amber-200 mt-1">
                            Element: {selectedElement.tagName}
                          </div>
                        </div>
                      )}

                      {/* Element within component */}
                      {selectedElement.component?.elementName && (
                        <div className="mt-2 text-xs text-blue-200">
                          <span className="font-medium">Element:</span>{' '}
                          {selectedElement.component.elementName}
                        </div>
                      )}

                      {!selectedElement.component?.isRoot && selectedElement.component?.componentName && (
                        <div className="mt-2 text-xs text-blue-300">
                          Selected {selectedElement.tagName} inside {selectedElement.component.componentName}
                        </div>
                      )}
                    </div>
                    <button
                      onClick={clearSelection}
                      className="text-blue-300 hover:text-white text-xl ml-2"
                      title="Clear selection"
                    >
                      ×
                    </button>
                  </div>
                </div>

                {/* Text Content Preview */}
                {selectedElement.textContent && (
                  <div className="bg-gray-900 p-3 rounded border border-gray-700">
                    <div className="text-xs text-gray-400 mb-1">Content</div>
                    <div className="text-sm text-gray-100">{selectedElement.textContent}</div>
                  </div>
                )}

                {/* Element Details */}
                <details className="bg-gray-900 rounded-lg border border-gray-700">
                  <summary className="p-3 cursor-pointer text-sm font-semibold text-gray-300 hover:text-white">
                    Element Details
                  </summary>
                  <div className="p-3 pt-0 space-y-3">
                    {/* Computed Styles */}
                    <div>
                      <div className="text-xs font-medium text-gray-400 mb-2">Styles ({Object.keys(selectedElement.computedStyles).length})</div>
                      <div className="max-h-32 overflow-y-auto space-y-1">
                        {Object.entries(selectedElement.computedStyles).slice(0, 10).map(([key, value]) => (
                          <div key={key} className="flex justify-between text-xs py-1 font-mono border-b border-gray-800 last:border-0">
                            <span className="text-gray-400">{key}:</span>
                            <span className="text-gray-200 text-right ml-2 truncate">{value}</span>
                          </div>
                        ))}
                        {Object.keys(selectedElement.computedStyles).length > 10 && (
                          <div className="text-xs text-gray-500 italic">
                            ... and {Object.keys(selectedElement.computedStyles).length - 10} more
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Attributes */}
                    {Object.keys(selectedElement.attributes).length > 0 && (
                      <div>
                        <div className="text-xs font-medium text-gray-400 mb-2">Attributes ({Object.keys(selectedElement.attributes).length})</div>
                        <div className="space-y-1">
                          {Object.entries(selectedElement.attributes).map(([key, value]) => (
                            <div key={key} className="text-xs py-1 font-mono">
                              <span className="text-blue-400">{key}</span>=
                              <span className="text-green-400">"{value}"</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </details>

                {/* Note about editing */}
                <div className="bg-blue-950 border border-blue-800 rounded-lg p-3">
                  <p className="text-xs text-blue-200">
                    💡 Use the chat window on the left to describe changes you'd like to make to this component.
                  </p>
                </div>
              </div>
            ) : (
              <div className="text-center text-gray-400 mt-16">
                <div className="text-5xl mb-4">🎯</div>
                <p className="text-sm">
                  Click any element in the preview to view its details
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Show panel button when hidden */}
      {selectorEnabled && !showDetailsPanel && (
        <button
          onClick={() => setShowDetailsPanel(true)}
          className="absolute top-20 right-4 bg-blue-500 hover:bg-blue-600 text-white p-2 rounded-lg shadow-lg transition-colors z-10"
          title="Show component details"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}

// Export memoized version to prevent unnecessary re-renders
export default memo(ReactPreview);
