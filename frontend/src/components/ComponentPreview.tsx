'use client';

/**
 * ComponentPreview Component
 * 
 * A component for previewing individual components from the component library
 * with live content rendering and interactive controls.
 */

import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  ComponentVariation,
  TemplateContent,
  ComponentPreviewProps,
} from '@/lib/components/types';
import { validateComponent, validatePlaceholders } from '@/lib/components/schema';

interface ComponentPreviewState {
  loading: boolean;
  error: string | null;
  scale: number;
}

export default function ComponentPreview({
  component,
  content = {},
  className = '',
  width = '100%',
  height = 'auto',
  scale = 1,
  showControls = false,
  onContentChange,
}: ComponentPreviewProps) {
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [state, setState] = useState<ComponentPreviewState>({
    loading: true,
    error: null,
    scale,
  });

  // Validate component structure
  const validation = useMemo(() => {
    const componentValidation = validateComponent(component);
    
    if (!componentValidation.valid) {
      return componentValidation;
    }

    // Also validate placeholders
    const placeholderValidation = validatePlaceholders(
      component.html,
      component.content_bindings
    );

    return {
      valid: placeholderValidation.valid,
      errors: [...componentValidation.errors, ...placeholderValidation.errors],
      warnings: placeholderValidation.warnings,
    };
  }, [component]);

  // Render content into HTML
  const renderedHTML = useMemo(() => {
    if (!validation.valid) {
      return '';
    }

    let html = component.html;

    // Replace simple placeholders
    for (const [key, value] of Object.entries(content)) {
      if (typeof value === 'string') {
        html = html.replace(new RegExp(`\\{\\{${key}\\}\\}`, 'g'), value);
      }
    }

    // Handle array content (e.g., services, testimonials)
    const arrayPattern = /<!-- (\w+)_item_start -->(.*?)<!-- \1_item_end -->/gs;
    html = html.replace(arrayPattern, (match, key, template) => {
      const items = content[`${key}s`] || content[key];
      
      if (!Array.isArray(items)) {
        return match;
      }

      return items
        .map((item: Record<string, unknown>) => {
          let itemHtml = template;
          for (const [itemKey, itemValue] of Object.entries(item)) {
            itemHtml = itemHtml.replace(
              new RegExp(`\\{\\{${key}\\.${itemKey}\\}\\}`, 'g'),
              String(itemValue)
            );
          }
          return itemHtml;
        })
        .join('');
    });

    return html;
  }, [component, content, validation.valid]);

  // Generate complete HTML document for iframe
  const iframeDocument = useMemo(() => {
    if (!validation.valid) {
      return '';
    }

    return `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Component Preview</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
    }

    /* Component CSS */
    ${component.css}
  </style>
</head>
<body>
  ${renderedHTML}
</body>
</html>
    `.trim();
  }, [component.css, renderedHTML, validation.valid]);

  // Update iframe content
  useEffect(() => {
    if (!iframeRef.current) return;

    const iframe = iframeRef.current;
    const doc = iframe.contentDocument || iframe.contentWindow?.document;

    if (!doc) return;

    try {
      doc.open();
      doc.write(iframeDocument);
      doc.close();
      
      setState((prev) => ({ ...prev, loading: false, error: null }));
    } catch (error) {
      setState((prev) => ({
        ...prev,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to render component',
      }));
    }
  }, [iframeDocument]);

  // Handle scale change
  const handleScaleChange = (newScale: number) => {
    setState((prev) => ({ ...prev, scale: newScale }));
  };

  // Render validation errors
  if (!validation.valid) {
    return (
      <div className={`component-preview-error ${className}`}>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-red-800 font-semibold mb-2">Component Validation Error</h3>
          <ul className="list-disc list-inside text-red-700 text-sm space-y-1">
            {validation.errors.map((error, index) => (
              <li key={index}>{error}</li>
            ))}
          </ul>
        </div>
      </div>
    );
  }

  // Render loading state
  if (state.loading) {
    return (
      <div className={`component-preview-loading ${className}`}>
        <div className="flex items-center justify-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
          <span className="ml-3 text-gray-600">Loading preview...</span>
        </div>
      </div>
    );
  }

  // Render error state
  if (state.error) {
    return (
      <div className={`component-preview-error ${className}`}>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-red-800 font-semibold mb-2">Preview Error</h3>
          <p className="text-red-700 text-sm">{state.error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className={`component-preview ${className}`}>
      {/* Controls */}
      {showControls && (
        <div className="component-preview-controls bg-gray-100 border-b border-gray-300 p-3 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <span className="text-sm font-medium text-gray-700">
              {component.name}
            </span>
            {validation.warnings && validation.warnings.length > 0 && (
              <button
                type="button"
                className="text-xs text-yellow-600 hover:text-yellow-700"
                title={validation.warnings.join('\n')}
              >
                ⚠️ {validation.warnings.length} warning(s)
              </button>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <label className="text-xs text-gray-600 mr-2">Scale:</label>
            <button
              type="button"
              onClick={() => handleScaleChange(Math.max(0.25, state.scale - 0.25))}
              className="px-2 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50"
            >
              -
            </button>
            <span className="text-xs text-gray-700 w-12 text-center">
              {Math.round(state.scale * 100)}%
            </span>
            <button
              type="button"
              onClick={() => handleScaleChange(Math.min(2, state.scale + 0.25))}
              className="px-2 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50"
            >
              +
            </button>
            <button
              type="button"
              onClick={() => handleScaleChange(1)}
              className="px-2 py-1 text-xs bg-white border border-gray-300 rounded hover:bg-gray-50"
            >
              Reset
            </button>
          </div>
        </div>
      )}

      {/* Preview iframe */}
      <div 
        className="component-preview-container"
        style={{
          width,
          height,
          overflow: 'auto',
          background: '#ffffff',
        }}
      >
        <iframe
          ref={iframeRef}
          title={`Preview: ${component.name}`}
          className="w-full border-0"
          style={{
            transform: `scale(${state.scale})`,
            transformOrigin: 'top left',
            width: `${100 / state.scale}%`,
            height: height === 'auto' ? '100%' : `${100 / state.scale}%`,
          }}
          sandbox="allow-same-origin"
        />
      </div>

      {/* Component info */}
      {showControls && (
        <div className="component-preview-info bg-gray-50 border-t border-gray-300 p-3">
          <p className="text-xs text-gray-600">{component.description}</p>
          {component.tags && component.tags.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2">
              {component.tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-block px-2 py-0.5 text-xs bg-indigo-100 text-indigo-700 rounded"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * ComponentPreviewGrid Component
 * 
 * Displays multiple component previews in a grid layout
 */
interface ComponentPreviewGridProps {
  components: ComponentVariation[];
  content?: Record<string, TemplateContent>;
  onSelect?: (component: ComponentVariation) => void;
  columns?: number;
  className?: string;
}

export function ComponentPreviewGrid({
  components,
  content = {},
  onSelect,
  columns = 3,
  className = '',
}: ComponentPreviewGridProps) {
  return (
    <div
      className={`component-preview-grid grid gap-6 ${className}`}
      style={{
        gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
      }}
    >
      {components.map((component, index) => (
        <div
          key={index}
          className={`component-preview-item border border-gray-200 rounded-lg overflow-hidden ${
            onSelect ? 'cursor-pointer hover:border-indigo-500 hover:shadow-lg transition-all' : ''
          }`}
          onClick={() => onSelect?.(component)}
        >
          <ComponentPreview
            component={component}
            content={content[component.name] || {}}
            showControls={false}
            scale={0.5}
            height="200px"
          />
        </div>
      ))}
    </div>
  );
}

/**
 * ComponentPreviewModal Component
 * 
 * Full-screen modal for component preview
 */
interface ComponentPreviewModalProps {
  component: ComponentVariation;
  content?: TemplateContent;
  isOpen: boolean;
  onClose: () => void;
}

export function ComponentPreviewModal({
  component,
  content,
  isOpen,
  onClose,
}: ComponentPreviewModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-6xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-xl font-semibold">{component.name}</h2>
          <button
            type="button"
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Preview */}
        <div className="flex-1 overflow-auto">
          <ComponentPreview
            component={component}
            content={content}
            showControls={true}
            height="100%"
          />
        </div>
      </div>
    </div>
  );
}

