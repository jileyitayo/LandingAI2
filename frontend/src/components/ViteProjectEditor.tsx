import { useState, useEffect, useRef } from 'react';

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
}

export default function ViteProjectEditor({ projectId }: { projectId: string }) {
  const [selectedElement, setSelectedElement] = useState<SelectedElement | null>(null);
  const [selectorEnabled, setSelectorEnabled] = useState(false);
  const [editPrompt, setEditPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [selectorReady, setSelectorReady] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Listen for messages from iframe
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'SELECTOR_READY') {
        setSelectorReady(true);
        console.log('Selector script loaded in iframe');
      } else if (event.data.type === 'ELEMENT_SELECTED') {
        setSelectedElement(event.data.data);
        console.log('Element selected:', event.data.data);
      } else if (event.data.type === 'ELEMENT_RIGHT_CLICKED') {
        setSelectedElement(event.data.data);
        // Handle context menu at event.data.x, event.data.y
      }
    };

    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, []);

  // Toggle selector mode
  const toggleSelector = () => {
    if (!selectorReady) {
      alert('Selector not ready yet. Please wait...');
      return;
    }

    const newState = !selectorEnabled;
    setSelectorEnabled(newState);

    if (iframeRef.current?.contentWindow) {
      iframeRef.current.contentWindow.postMessage({
        type: newState ? 'ENABLE_SELECTOR' : 'DISABLE_SELECTOR',
      }, '*');
    }
  };

  // Handle edit submission
  const handleEdit = async () => {
    if (!selectedElement || !editPrompt) return;

    setIsLoading(true);
    try {
      const response = await fetch('/api/edit-vite-project', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          projectId,
          selectedElement,
          instruction: editPrompt,
        }),
      });

      const result = await response.json();
      
      if (result.success) {
        // Reload iframe to show changes
        if (iframeRef.current) {
          iframeRef.current.src = iframeRef.current.src;
        }
        setEditPrompt('');
        alert('Changes applied! Rebuilding project...');
      }
    } catch (error) {
      console.error('Edit failed:', error);
      alert('Failed to apply changes');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Toolbar */}
      <div className="absolute top-0 left-0 right-96 bg-white border-b px-4 py-3 flex items-center gap-3 z-10 shadow-sm">
        <button
          onClick={toggleSelector}
          disabled={!selectorReady}
          className={`px-4 py-2 rounded-lg font-medium transition-all ${
            selectorEnabled
              ? 'bg-blue-500 text-white shadow-md'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {selectorEnabled ? '✓ Selecting' : 'Enable Selector'}
        </button>

        {!selectorReady && (
          <span className="text-sm text-gray-500">Loading selector...</span>
        )}

        {isLoading && (
          <span className="text-sm text-blue-600">Processing changes...</span>
        )}
      </div>

      {/* Preview iframe */}
      <div className="flex-1 pt-14 pr-96">
        <iframe
          ref={iframeRef}
          src={`/preview/${projectId}`}
          className="w-full h-full border-0 bg-white"
          title="Project Preview"
        />
      </div>

      {/* Edit Panel */}
      <div className="fixed right-0 top-0 bottom-0 w-96 bg-white border-l shadow-xl pt-14 flex flex-col">
        <div className="flex-1 overflow-y-auto p-6">
          <h2 className="text-xl font-bold mb-4">Edit Element</h2>

          {selectedElement ? (
            <div className="space-y-4">
              {/* Element Info */}
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border border-blue-200">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <div className="font-mono text-sm font-bold text-blue-900">
                      {selectedElement.tagName}
                    </div>
                    {selectedElement.classList.length > 0 && (
                      <div className="text-xs text-blue-700 mt-1">
                        .{selectedElement.classList.join(' .')}
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => setSelectedElement(null)}
                    className="text-blue-400 hover:text-blue-600 text-xl"
                  >
                    ×
                  </button>
                </div>
                <div className="text-xs text-blue-600 font-mono mt-2 overflow-x-auto">
                  {selectedElement.selector}
                </div>
              </div>

              {/* Text Content Preview */}
              {selectedElement.textContent && (
                <div className="bg-gray-50 p-3 rounded border">
                  <div className="text-xs text-gray-500 mb-1">Content</div>
                  <div className="text-sm">{selectedElement.textContent}</div>
                </div>
              )}

              {/* Prompt Input */}
              <div>
                <label className="block text-sm font-semibold mb-2 text-gray-700">
                  What would you like to change?
                </label>
                <textarea
                  value={editPrompt}
                  onChange={(e) => setEditPrompt(e.target.value)}
                  placeholder="e.g., Make this button larger with a blue gradient background"
                  className="w-full h-28 p-3 border border-gray-300 rounded-lg resize-none text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <button
                onClick={handleEdit}
                disabled={!editPrompt || isLoading}
                className="w-full bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed font-semibold transition-all"
              >
                {isLoading ? 'Applying Changes...' : 'Apply Changes'}
              </button>

              {/* Computed Styles */}
              <details className="bg-gray-50 rounded-lg border">
                <summary className="p-3 cursor-pointer text-sm font-semibold text-gray-700">
                  Current Styles ({Object.keys(selectedElement.computedStyles).length})
                </summary>
                <div className="p-3 pt-0 max-h-64 overflow-y-auto">
                  {Object.entries(selectedElement.computedStyles).map(([key, value]) => (
                    <div key={key} className="flex justify-between text-xs py-1 font-mono border-b border-gray-200 last:border-0">
                      <span className="text-gray-600">{key}:</span>
                      <span className="text-gray-900 text-right ml-2 truncate">{value}</span>
                    </div>
                  ))}
                </div>
              </details>

              {/* Attributes */}
              {Object.keys(selectedElement.attributes).length > 0 && (
                <details className="bg-gray-50 rounded-lg border">
                  <summary className="p-3 cursor-pointer text-sm font-semibold text-gray-700">
                    Attributes ({Object.keys(selectedElement.attributes).length})
                  </summary>
                  <div className="p-3 pt-0">
                    {Object.entries(selectedElement.attributes).map(([key, value]) => (
                      <div key={key} className="text-xs py-1 font-mono">
                        <span className="text-blue-600">{key}</span>=
                        <span className="text-green-600">"{value}"</span>
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </div>
          ) : (
            <div className="text-center text-gray-400 mt-16">
              <div className="text-5xl mb-4">🎯</div>
              <p className="text-sm">
                Enable selector mode and click any element<br/>to start editing
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}