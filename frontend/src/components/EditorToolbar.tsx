'use client';

import { Eye, Code, MousePointerClick, Globe, Smartphone, Tablet, Monitor, RefreshCw, ExternalLink } from 'lucide-react';

export type DeviceMode = 'mobile' | 'tablet' | 'desktop';
export type EditorTab = 'preview' | 'code';
export type InteractionMode = 'edit' | 'browse';

interface EditorToolbarProps {
  activeTab: EditorTab;
  onTabChange: (tab: EditorTab) => void;
  /** Edit = click selects elements; Browse = normal site navigation */
  mode: InteractionMode;
  onModeChange: (mode: InteractionMode) => void;
  /** Selector script handshake done — Edit mode is unavailable until then */
  selectorReady: boolean;
  deviceMode: DeviceMode;
  onDeviceModeChange: (mode: DeviceMode) => void;
  onRebuild: () => void;
  previewUrl: string | null;
}

/**
 * Single compact toolbar above the preview/code panel: icon-only tabs on the
 * left, the Edit/Browse interaction mode + device + rebuild/open controls on
 * the right. Keyboard: E flips Edit/Browse, Esc clears the selection.
 */
export default function EditorToolbar({
  activeTab,
  onTabChange,
  mode,
  onModeChange,
  selectorReady,
  deviceMode,
  onDeviceModeChange,
  onRebuild,
  previewUrl,
}: EditorToolbarProps) {
  const tabClass = (active: boolean) =>
    `flex items-center justify-center p-2 border-b-2 transition-colors ${
      active
        ? 'border-blue-500 text-white bg-gray-900'
        : 'border-transparent text-gray-400 hover:text-white hover:bg-gray-700'
    }`;

  return (
    <div className="flex items-center justify-between bg-gray-800 border-b border-gray-700 pr-2">
      {/* Left: view tabs (icon-only) */}
      <div className="flex items-center">
        <button
          onClick={() => onTabChange('preview')}
          className={tabClass(activeTab === 'preview')}
          title="Preview"
        >
          <Eye className="w-4 h-4" />
        </button>
        <button
          onClick={() => onTabChange('code')}
          className={tabClass(activeTab === 'code')}
          title="Code files"
        >
          <Code className="w-4 h-4" />
        </button>
      </div>

      {/* Right: interaction mode + device + actions (preview only) */}
      <div className="flex items-center gap-1.5">
        {activeTab === 'preview' && (
          <>
            <div className="flex items-center bg-gray-900 rounded-md p-0.5" role="group" aria-label="Interaction mode">
              <button
                onClick={() => onModeChange('edit')}
                disabled={!selectorReady}
                className={`flex items-center gap-1 px-2 py-1 text-xs font-medium rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                  mode === 'edit'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
                title={selectorReady ? 'Edit mode — click elements to select them (E)' : 'Loading selector…'}
              >
                <MousePointerClick className="w-3.5 h-3.5" />
                Edit
              </button>
              <button
                onClick={() => onModeChange('browse')}
                className={`flex items-center gap-1 px-2 py-1 text-xs font-medium rounded transition-colors ${
                  mode === 'browse'
                    ? 'bg-gray-600 text-white'
                    : 'text-gray-400 hover:text-white'
                }`}
                title="Browse mode — interact with the site normally (E)"
              >
                <Globe className="w-3.5 h-3.5" />
                Browse
              </button>
            </div>

            <div className="flex items-center gap-0.5 bg-gray-900 rounded-md p-0.5">
              {(['mobile', 'tablet', 'desktop'] as DeviceMode[]).map((m) => {
                const Icon = m === 'mobile' ? Smartphone : m === 'tablet' ? Tablet : Monitor;
                return (
                  <button
                    key={m}
                    onClick={() => onDeviceModeChange(m)}
                    className={`flex items-center justify-center p-1.5 rounded transition-colors ${
                      deviceMode === m
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-400 hover:text-white hover:bg-gray-700'
                    }`}
                    title={`${m.charAt(0).toUpperCase() + m.slice(1)} preview`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                  </button>
                );
              })}
            </div>
          </>
        )}

        <button
          onClick={onRebuild}
          className="p-1.5 text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors"
          title="Rebuild preview"
        >
          <RefreshCw className="w-3.5 h-3.5" />
        </button>
        {previewUrl && (
          <a
            href={previewUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="p-1.5 text-gray-400 hover:text-white hover:bg-gray-700 rounded transition-colors"
            title="Open in new tab"
          >
            <ExternalLink className="w-3.5 h-3.5" />
          </a>
        )}
      </div>
    </div>
  );
}
