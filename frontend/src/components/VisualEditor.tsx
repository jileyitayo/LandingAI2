'use client';

import { useState, useEffect, useRef } from 'react';
import { Eye, EyeOff, Loader2, AlertCircle, Wand2 } from 'lucide-react';

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
    // Component hierarchy (from enhanced selector)
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

interface VisualEditorProps {
    previewUrl: string | null;
    selectedElement: SelectedElement | null;
    onElementSelect: (element: SelectedElement | null) => void;
    selectorEnabled: boolean;
    onSelectorEnabledChange: (enabled: boolean) => void;
}

export default function VisualEditor({
    previewUrl,
    selectedElement,
    onElementSelect,
    selectorEnabled,
    onSelectorEnabledChange
}: VisualEditorProps) {
    const [selectorReady, setSelectorReady] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const iframeRef = useRef<HTMLIFrameElement>(null);

    // Listen for messages from iframe
    useEffect(() => {
        const handleMessage = (event: MessageEvent) => {
            if (event.data.type === 'SELECTOR_READY') {
                setSelectorReady(true);
                console.log('Selector script loaded in iframe');
            } else if (event.data.type === 'ELEMENT_SELECTED') {
                onElementSelect(event.data.data);
                setError(null);
                console.log('Element selected:', event.data.data);
            } else if (event.data.type === 'ELEMENT_RIGHT_CLICKED') {
                onElementSelect(event.data.data);
                setError(null);
                // Handle context menu at event.data.x, event.data.y
            }
        };

        window.addEventListener('message', handleMessage);
        return () => window.removeEventListener('message', handleMessage);
    }, [onElementSelect]);

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
            setError('Selector not ready yet. Please wait...');
            return;
        }

        onSelectorEnabledChange(!selectorEnabled);
    };

    // Clear selection
    const clearSelection = () => {
        onElementSelect(null);
        setError(null);
    };

    return (
        <div className="h-full flex bg-gray-50">
            {/* Left Panel - Preview (70%) */}
            <div className="flex-1 flex flex-col">
                {/* Toolbar */}
                <div className="flex items-center justify-between px-4 py-3 bg-white border-b border-gray-200">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={toggleSelector}
                            disabled={!selectorReady}
                            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${selectorEnabled
                                    ? 'bg-blue-500 text-white shadow-md'
                                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                } disabled:opacity-50 disabled:cursor-not-allowed`}
                        >
                            {selectorEnabled ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                            {selectorEnabled ? 'Disable Selector' : 'Enable Selector'}
                        </button>

                        {!selectorReady && (
                            <span className="text-sm text-gray-500 flex items-center gap-2">
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Loading selector...
                            </span>
                        )}
                    </div>

                    <div className="flex items-center gap-2">
                        {selectedElement && (
                            <button
                                onClick={clearSelection}
                                className="text-sm text-gray-500 hover:text-gray-700"
                            >
                                Clear Selection
                            </button>
                        )}
                    </div>
                </div>

                {/* Preview iframe */}
                <div className="flex-1 relative">
                    {previewUrl ? (
                        <iframe
                            ref={iframeRef}
                            src={previewUrl}
                            className="w-full h-full border-0 bg-white"
                            title="Project Preview"
                        />
                    ) : (
                        <div className="flex items-center justify-center h-full bg-gray-100">
                            <div className="text-center">
                                <Wand2 className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                                <p className="text-gray-500">Preview not available</p>
                                <p className="text-sm text-gray-400 mt-2">Build a preview first to start editing</p>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            {/* Right Panel - Component Details (30%) - Read-only - Only shown when selector is enabled */}
            {selectorEnabled && (
                <div className="w-96 bg-white border-l border-gray-200 flex flex-col">
                    <div className="p-4 border-b border-gray-200">
                        <h3 className="text-lg font-semibold text-gray-900">Component Details</h3>
                        <p className="text-sm text-gray-500 mt-1">
                            Selected component information
                        </p>
                    </div>

                    <div className="flex-1 overflow-y-auto p-4">
                        {error && (
                            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                                <div className="flex items-start gap-2">
                                    <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 flex-shrink-0" />
                                    <div>
                                        <p className="text-sm text-red-800 font-medium">Error</p>
                                        <p className="text-sm text-red-700">{error}</p>
                                    </div>
                                </div>
                            </div>
                        )}

                        {selectedElement ? (
                            <div className="space-y-4">
                                {/* Component Info - Prominently displayed */}
                                <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-4 rounded-lg border-2 border-blue-300 shadow-sm">
                                    <div className="flex items-start justify-between mb-3">
                                        <div className="flex-1">
                                            {/* Component Name */}
                                            {selectedElement.component?.componentName ? (
                                                <div>
                                                    <div className="text-xs text-blue-600 font-medium mb-1">COMPONENT</div>
                                                    <div className="font-bold text-lg text-blue-900 mb-1">
                                                        {selectedElement.component.componentName}
                                                    </div>
                                                    {selectedElement.component.componentFile && (
                                                        <div className="text-xs text-blue-700 font-mono bg-blue-50 px-2 py-1 rounded inline-block">
                                                            {selectedElement.component.componentFile}
                                                        </div>
                                                    )}
                                                </div>
                                            ) : (
                                                <div>
                                                    <div className="text-xs text-amber-600 font-medium mb-1">WARNING</div>
                                                    <div className="text-sm text-amber-800">
                                                        No component data found
                                                    </div>
                                                    <div className="text-xs text-amber-700 mt-1">
                                                        Element: {selectedElement.tagName}
                                                    </div>
                                                </div>
                                            )}

                                            {/* Element within component */}
                                            {selectedElement.component?.elementName && (
                                                <div className="mt-2 text-xs text-blue-600">
                                                    <span className="font-medium">Element:</span>{' '}
                                                    {selectedElement.component.elementName}
                                                </div>
                                            )}

                                            {!selectedElement.component?.isRoot && selectedElement.component?.componentName && (
                                                <div className="mt-2 text-xs text-blue-500">
                                                    Selected {selectedElement.tagName} inside {selectedElement.component.componentName}
                                                </div>
                                            )}
                                        </div>
                                        <button
                                            onClick={clearSelection}
                                            className="text-blue-400 hover:text-blue-600 text-xl ml-2"
                                            title="Clear selection"
                                        >
                                            ×
                                        </button>
                                    </div>
                                </div>

                                {/* Text Content Preview */}
                                {selectedElement.textContent && (
                                    <div className="bg-gray-50 p-3 rounded border">
                                        <div className="text-xs text-gray-500 mb-1">Content</div>
                                        <div className="text-sm text-gray-900">{selectedElement.textContent}</div>
                                    </div>
                                )}

                                {/* Element Details */}
                                <details className="bg-gray-50 rounded-lg border" open>
                                    <summary className="p-3 cursor-pointer text-sm font-semibold text-gray-700">
                                        Element Details
                                    </summary>
                                    <div className="p-3 pt-0 space-y-3">
                                        {/* Computed Styles */}
                                        <div>
                                            <div className="text-xs font-medium text-gray-600 mb-2">Styles</div>
                                            <div className="max-h-32 overflow-y-auto space-y-1">
                                                {Object.entries(selectedElement.computedStyles).map(([key, value]) => (
                                                    <div key={key} className="flex justify-between text-xs py-1 font-mono border-b border-gray-200 last:border-0">
                                                        <span className="text-gray-600">{key}:</span>
                                                        <span className="text-gray-900 text-right ml-2 truncate">{value}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Attributes */}
                                        {Object.keys(selectedElement.attributes).length > 0 && (
                                            <div>
                                                <div className="text-xs font-medium text-gray-600 mb-2">Attributes</div>
                                                <div className="space-y-1">
                                                    {Object.entries(selectedElement.attributes).map(([key, value]) => (
                                                        <div key={key} className="text-xs py-1 font-mono">
                                                            <span className="text-blue-600">{key}</span>=
                                                            <span className="text-green-600">"{value}"</span>
                                                        </div>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                </details>

                                {/* Note about editing */}
                                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                                    <p className="text-xs text-blue-800">
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
        </div>
    );
}
