'use client';

import { useState, useEffect, useRef } from 'react';
import { Wand2, Eye, EyeOff, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';

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
    projectId: string;
    previewUrl: string | null;
    onRebuild: () => Promise<void>;
}

export default function VisualEditor({ projectId, previewUrl, onRebuild }: VisualEditorProps) {
    const [selectedElement, setSelectedElement] = useState<SelectedElement | null>(null);
    const [selectorEnabled, setSelectorEnabled] = useState(false);
    const [editPrompt, setEditPrompt] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [selectorReady, setSelectorReady] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const [lastEditSuccess, setLastEditSuccess] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const iframeRef = useRef<HTMLIFrameElement>(null);

    // Listen for messages from iframe
    useEffect(() => {
        const handleMessage = (event: MessageEvent) => {
            if (event.data.type === 'SELECTOR_READY') {
                setSelectorReady(true);
                console.log('Selector script loaded in iframe');
            } else if (event.data.type === 'ELEMENT_SELECTED') {
                setSelectedElement(event.data.data);
                setError(null);
                console.log('Element selected:', event.data.data);
            } else if (event.data.type === 'ELEMENT_RIGHT_CLICKED') {
                setSelectedElement(event.data.data);
                setError(null);
                // Handle context menu at event.data.x, event.data.y
            }
        };

        window.addEventListener('message', handleMessage);
        return () => window.removeEventListener('message', handleMessage);
    }, []);

    // Toggle selector mode
    const toggleSelector = () => {
        if (!selectorReady) {
            setError('Selector not ready yet. Please wait...');
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
        if (!selectedElement || !editPrompt.trim()) {
            setError('Please select an element and enter an instruction');
            return;
        }

        setIsProcessing(true);
        setError(null);
        setLastEditSuccess(false);

        try {
            // Dummy result for testing
            console.log('Editing component:', selectedElement, editPrompt);
            const result = await api.generation.editComponent(projectId, {
                selected_element: selectedElement,
                instruction: editPrompt.trim(),
            });
            // const result = {
            //     success: true,
            //     message: "Dummy: Component edited successfully.",
            //     updated_file: "src/components/DummyComponent.tsx",
            //     preview_url: null,
            // };

            if (result.success) {
                setLastEditSuccess(true);
                setEditPrompt('');
                setSelectedElement(null);

                // Rebuild preview to show changes
                await onRebuild();

                // Refresh iframe with cache busting
                if (iframeRef.current) {
                    const currentSrc = iframeRef.current.src;
                    const separator = currentSrc.includes('?') ? '&' : '?';
                    iframeRef.current.src = currentSrc + separator + 't=' + Date.now();
                }

                // Clear success state after 3 seconds
                setTimeout(() => setLastEditSuccess(false), 3000);
            } else {
                setError(result.message || 'Failed to apply changes');
            }
        } catch (error) {
            console.error('Edit failed:', error);
            setError('Failed to apply changes. Please try again.');
        } finally {
            setIsProcessing(false);
        }
    };

    // Clear selection
    const clearSelection = () => {
        setSelectedElement(null);
        setEditPrompt('');
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
                            disabled={!selectorReady || isLoading}
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

                        {isProcessing && (
                            <span className="text-sm text-blue-600 flex items-center gap-2">
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Processing changes...
                            </span>
                        )}

                        {lastEditSuccess && (
                            <span className="text-sm text-green-600 flex items-center gap-2">
                                <CheckCircle className="w-4 h-4" />
                                Changes applied successfully!
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

            {/* Right Panel - Edit Controls (30%) */}
            <div className="w-96 bg-white border-l border-gray-200 flex flex-col">
                <div className="p-4 border-b border-gray-200">
                    <h3 className="text-lg font-semibold text-gray-900">Visual Editor</h3>
                    <p className="text-sm text-gray-500 mt-1">
                        Click elements in the preview to edit them
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

                            {/* Edit Instruction */}
                            <div>
                                <label className="block text-sm font-semibold mb-2 text-gray-700">
                                    What would you like to change?
                                </label>
                                <textarea
                                    value={editPrompt}
                                    onChange={(e) => setEditPrompt(e.target.value)}
                                    placeholder="e.g., Make this button larger with a blue gradient background"
                                    className="w-full h-28 p-3 border border-gray-300 rounded-lg resize-none text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                                    disabled={isProcessing}
                                />
                            </div>

                            <button
                                onClick={handleEdit}
                                disabled={!editPrompt.trim() || isProcessing}
                                className="w-full bg-blue-500 text-white py-3 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed font-semibold transition-all flex items-center justify-center gap-2"
                            >
                                {isProcessing ? (
                                    <>
                                        <Loader2 className="w-4 h-4 animate-spin" />
                                        Applying Changes...
                                    </>
                                ) : (
                                    <>
                                        <Wand2 className="w-4 h-4" />
                                        Apply Changes
                                    </>
                                )}
                            </button>

                            {/* Element Details */}
                            <details className="bg-gray-50 rounded-lg border">
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
                        </div>
                    ) : (
                        <div className="text-center text-gray-400 mt-16">
                            <div className="text-5xl mb-4">🎯</div>
                            <p className="text-sm">
                                {selectorEnabled
                                    ? 'Click any element in the preview to start editing'
                                    : 'Enable selector mode and click any element to start editing'
                                }
                            </p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
