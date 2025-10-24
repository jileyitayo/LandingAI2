'use client';

import { memo, useMemo } from 'react';

interface CodeViewerProps {
  fileName: string | null;
  content: string | null;
}

function CodeViewer({ fileName, content }: CodeViewerProps) {
  if (!fileName || !content) {
    return (
      <div className="h-full bg-gray-900 flex items-center justify-center">
        <div className="text-center text-gray-500">
          <div className="text-4xl mb-4">📁</div>
          <p className="text-lg mb-2">No file selected</p>
          <p className="text-sm">Select a file from the tree to view its content</p>
        </div>
      </div>
    );
  }

  // Memoize language detection to avoid recalculation
  const language = useMemo(() => {
    if (!fileName) return 'text';
    const extension = fileName.split('.').pop()?.toLowerCase();

    switch (extension) {
      case 'tsx':
      case 'jsx':
        return 'typescript';
      case 'ts':
      case 'js':
        return 'javascript';
      case 'css':
        return 'css';
      case 'json':
        return 'json';
      case 'html':
        return 'html';
      default:
        return 'text';
    }
  }, [fileName]);

  // Memoize file icon
  const fileIcon = useMemo(() => {
    if (!fileName) return '📄';
    const extension = fileName.split('.').pop()?.toLowerCase();

    switch (extension) {
      case 'tsx':
      case 'jsx':
        return '⚛️';
      case 'ts':
      case 'js':
        return '📄';
      case 'css':
        return '🎨';
      case 'json':
        return '📋';
      case 'html':
        return '🌐';
      default:
        return '📄';
    }
  }, [fileName]);

  // Memoize lines and line numbers to avoid recalculation on every render
  const lines = useMemo(() => content?.split('\n') || [], [content]);
  const lineNumbers = useMemo(() => Array.from({ length: lines.length }, (_, i) => i + 1), [lines.length]);

  return (
    <div className="h-full bg-gray-900 flex flex-col">
      {/* File Header */}
      <div className="flex items-center gap-2 px-4 py-2 bg-gray-800 border-b border-gray-700">
        <span className="text-lg">{fileIcon}</span>
        <span className="text-sm font-medium text-gray-300">{fileName}</span>
        <span className="text-xs text-gray-500 ml-auto">
          {language.toUpperCase()} • {lines.length} lines
        </span>
      </div>

      {/* Code Content */}
      <div className="flex-1 overflow-auto">
        <div className="flex">
          {/* Line Numbers */}
          <div className="bg-gray-800 text-gray-500 text-xs font-mono py-4 px-2 select-none border-r border-gray-700">
            {lineNumbers.map(lineNum => (
              <div key={lineNum} className="leading-6 text-right pr-2">
                {lineNum}
              </div>
            ))}
          </div>

          {/* Code Content */}
          <div className="flex-1">
            <pre className="text-sm text-gray-100 font-mono leading-6 p-4 overflow-x-auto">
              <code className={`language-${language}`}>
                {content}
              </code>
            </pre>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="px-4 py-2 bg-gray-800 border-t border-gray-700 text-xs text-gray-500">
        <div className="flex items-center justify-between">
          <span>UTF-8</span>
          <span>{content.length} characters</span>
        </div>
      </div>
    </div>
  );
}

// Export memoized version to prevent unnecessary re-renders
export default memo(CodeViewer);
