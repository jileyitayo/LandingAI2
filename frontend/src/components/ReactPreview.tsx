'use client';

import { useState, useEffect, useRef, memo, forwardRef, useImperativeHandle } from 'react';
import { RefreshCw, ExternalLink, AlertCircle, Eye, EyeOff } from 'lucide-react';

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
  onElementsSelect?: (elements: SelectedElement[]) => void;
  selectorEnabled?: boolean;
  onSelectorEnabledChange?: (enabled: boolean) => void;
}

export interface ReactPreviewHandle {
  deselectElement: (selectorKey: string) => void;
  clearSelection: () => void;
  postToIframe: (message: Record<string, unknown>) => void;
}

const ReactPreview = forwardRef<ReactPreviewHandle, ReactPreviewProps>(function ReactPreview({
  previewUrl,
  isBuilding,
  error,
  onRebuild,
  selectedElement = null,
  onElementSelect,
  onElementsSelect,
  selectorEnabled = false,
  onSelectorEnabledChange
}: ReactPreviewProps, ref) {
  const [selectorReady, setSelectorReady] = useState(false);
  const [iframeLoaded, setIframeLoaded] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const previewContainerRef = useRef<HTMLDivElement>(null);
  // Last known selection, used to restore highlights after a preview rebuild
  const lastSelectionRef = useRef<SelectedElement[]>([]);

  // Keep latest props/state in refs so the message listener can be registered
  // exactly once — re-registering leaves gaps where iframe messages are lost
  const callbacksRef = useRef({ onElementSelect, onElementsSelect, onSelectorEnabledChange, selectorEnabled, selectorReady });
  callbacksRef.current = { onElementSelect, onElementsSelect, onSelectorEnabledChange, selectorEnabled, selectorReady };

  const postToIframe = (message: Record<string, unknown>) => {
    iframeRef.current?.contentWindow?.postMessage(message, '*');
  };

  useImperativeHandle(ref, () => ({
    deselectElement: (selectorKey: string) => {
      postToIframe({ type: 'DESELECT_ELEMENT', selector: selectorKey });
    },
    clearSelection: () => {
      postToIframe({ type: 'CLEAR_SELECTION' });
    },
    postToIframe,
  }));

  // Listen for messages from iframe — registered once, no teardown gaps
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      // Skip messages from browser extensions or other sources
      if (!event.data || typeof event.data !== 'object') {
        return;
      }
      const cb = callbacksRef.current;

      if (event.data.type === 'SELECTOR_READY' || event.data.type === 'SELECTOR_PONG') {
        setSelectorReady(true);
        // Auto-enable selector when it's ready
        if (cb.onSelectorEnabledChange && !cb.selectorEnabled) {
          cb.onSelectorEnabledChange(true);
        }
      } else if (event.data.type === 'ELEMENTS_SELECTED') {
        const elements: SelectedElement[] = Array.isArray(event.data.data) ? event.data.data : [];
        lastSelectionRef.current = elements;
        if (cb.onElementsSelect) {
          cb.onElementsSelect(elements);
        }
      } else if (event.data.type === 'ELEMENT_SELECTED') {
        // Legacy single-element path; multi-select consumers use ELEMENTS_SELECTED
        if (cb.onElementSelect && !cb.onElementsSelect) {
          cb.onElementSelect(event.data.data);
        }
      } else if (event.data.type === 'ELEMENT_RIGHT_CLICKED') {
        if (cb.onElementSelect) {
          cb.onElementSelect(event.data.data);
        }
      } else if (event.data.type === 'PREVIEW_CLICKED') {
        // Auto-enable selector when user clicks in preview
        if (cb.onSelectorEnabledChange && !cb.selectorEnabled && cb.selectorReady) {
          cb.onSelectorEnabledChange(true);
        }
      }
    };

    window.addEventListener('message', handleMessage);
    return () => {
      window.removeEventListener('message', handleMessage);
    };
  }, []);

  // Reset iframe loaded state when URL changes; the PING handshake below
  // re-establishes selector readiness automatically
  useEffect(() => {
    setIframeLoaded(false);
    setSelectorReady(false);
  }, [previewUrl]);

  // Parent-initiated handshake: ping the iframe until it answers. This
  // recovers readiness even if every SELECTOR_READY from the iframe was
  // missed (slow build, heavy render, tab switch).
  useEffect(() => {
    if (!iframeLoaded || selectorReady || !previewUrl) return;

    postToIframe({ type: 'PING' });
    const pingInterval = setInterval(() => {
      postToIframe({ type: 'PING' });
    }, 500);

    return () => clearInterval(pingInterval);
  }, [iframeLoaded, selectorReady, previewUrl]);

  // Once the selector is ready after a rebuild, restore the previous selection
  const prevReadyRef = useRef(false);
  useEffect(() => {
    if (selectorReady && !prevReadyRef.current && lastSelectionRef.current.length > 0) {
      postToIframe({
        type: 'RESTORE_SELECTION',
        selections: lastSelectionRef.current.map((sel) => ({
          elementSelector: (sel as SelectedElement & { elementSelector?: string | null }).elementSelector ?? sel.component?.elementName ?? null,
          componentFile: sel.component?.componentFile ?? null,
          tagName: sel.tagName,
          textContent: sel.textContent,
        })),
      });
    }
    prevReadyRef.current = selectorReady;
  }, [selectorReady]);

  // Handle iframe load event
  const handleIframeLoad = () => {
    setIframeLoaded(true);
  };

  // Sync selector state with iframe (only after iframe is loaded)
  useEffect(() => {
    if (iframeRef.current?.contentWindow && selectorReady && iframeLoaded) {
      const message = selectorEnabled ? 'ENABLE_SELECTOR' : 'DISABLE_SELECTOR';
      // console.log('[ReactPreview] Sending message to iframe:', message);
      iframeRef.current.contentWindow.postMessage({
        type: message,
      }, '*');
    } else {
      // console.log('[ReactPreview] Cannot send message - iframe not ready:', {
      // hasContentWindow: !!iframeRef.current?.contentWindow,
      //   selectorReady,
      //   iframeLoaded
      // });
    }
  }, [selectorEnabled, selectorReady, iframeLoaded]);

  // Re-enable selector when iframe gains focus or mouse enters preview area
  useEffect(() => {
    const iframe = iframeRef.current;
    const container = previewContainerRef.current;
    if (!iframe || !container) return;

    const reEnableSelector = () => {
      if (selectorEnabled && selectorReady && iframeLoaded && iframe.contentWindow) {
        // console.log('[ReactPreview] Re-enabling selector on focus/mouseenter');
        iframe.contentWindow.postMessage({
          type: 'ENABLE_SELECTOR',
        }, '*');
      }
    };

    const handleIframeFocus = () => {
      // console.log('Iframe focused');
      reEnableSelector();
    };

    const handleMouseEnter = () => {
      // console.log('Mouse entered preview area');
      reEnableSelector();
    };

    // Listen for focus on the iframe
    iframe.addEventListener('focus', handleIframeFocus);
    
    // Listen for mouse entering the preview container
    container.addEventListener('mouseenter', handleMouseEnter);
    
    // Also handle when the window regains focus (user comes back to tab)
    const handleWindowFocus = () => {
      // console.log('Window focused');
      reEnableSelector();
    };
    window.addEventListener('focus', handleWindowFocus);

    return () => {
      iframe.removeEventListener('focus', handleIframeFocus);
      container.removeEventListener('mouseenter', handleMouseEnter);
      window.removeEventListener('focus', handleWindowFocus);
    };
  }, [selectorEnabled, selectorReady, iframeLoaded]);

  // Toggle selector mode
  const toggleSelector = () => {
    if (!selectorReady) {
      return;
    }
    if (onSelectorEnabledChange) {
      onSelectorEnabledChange(!selectorEnabled);
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
    <div className="h-full bg-gray-900 flex flex-col">

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
        <div 
          ref={previewContainerRef}
          className={`flex-1 bg-white relative transition-all ${
            selectorEnabled ? 'ring-2 ring-blue-500 ring-inset' : ''
          }`}
        >
          <iframe
            ref={iframeRef}
            src={previewUrl}
            onLoad={handleIframeLoad}
            className={`w-full h-full border-0 ${
              selectorEnabled ? 'cursor-crosshair' : ''
            }`}
            title="React Preview"
            sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals"
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
  );
});

// Export memoized version to prevent unnecessary re-renders
export default memo(ReactPreview);
