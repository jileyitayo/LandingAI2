'use client';

import { useCallback, useEffect, useState } from 'react';
import { GripVertical, Loader2, Layers, ChevronDown, ChevronUp } from 'lucide-react';
import { api } from '@/lib/api';

interface Section {
  id: number;
  name: string;
  is_component: boolean;
}

interface PageStructure {
  page_file: string;
  page_name: string;
  sections: Section[];
}

interface PageStructurePanelProps {
  projectId: string;
  /** Apply a reorder; return the new preview URL on success (or null). */
  onReordered: (previewUrl: string | null) => void;
}

/**
 * Drag-to-reorder the sections of each page. Deterministic on the backend
 * (no LLM), build-verified, and undoable via edit history.
 */
export default function PageStructurePanel({ projectId, onReordered }: PageStructurePanelProps) {
  const [pages, setPages] = useState<PageStructure[]>([]);
  const [activePage, setActivePage] = useState<string | null>(null);
  const [order, setOrder] = useState<Section[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [dropTarget, setDropTarget] = useState<number | null>(null);

  const load = useCallback(async (preferredPage?: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await api.generation.getPageStructure(projectId);
      setPages(result.pages);
      if (result.pages.length > 0) {
        // Keep the current page selected across reloads when possible
        const target =
          result.pages.find((p) => p.page_file === preferredPage) ?? result.pages[0];
        setActivePage(target.page_file);
        setOrder(target.sections);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load page structure');
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    load();
  }, [load]);

  const selectPage = (pageFile: string) => {
    const page = pages.find((p) => p.page_file === pageFile);
    if (!page) return;
    setActivePage(pageFile);
    setOrder(page.sections);
  };

  // Move the item currently at `from` to position `to`, shifting the rest.
  const moveItem = (from: number, to: number) => {
    if (from === to || to < 0 || to >= order.length) return;
    const next = [...order];
    const [moved] = next.splice(from, 1);
    next.splice(to, 0, moved);
    setOrder(next);
  };

  const handleDrop = (targetIndex: number) => {
    if (dragIndex === null || dragIndex === targetIndex) {
      setDragIndex(null);
      return;
    }
    moveItem(dragIndex, targetIndex);
    setDragIndex(null);
  };

  const orderChanged = () => {
    const page = pages.find((p) => p.page_file === activePage);
    if (!page) return false;
    return page.sections.map((s) => s.id).join('|') !== order.map((s) => s.id).join('|');
  };

  const handleSave = async () => {
    if (!activePage || !orderChanged()) return;
    setIsSaving(true);
    setError(null);
    const targetPage = activePage;
    try {
      const result = await api.generation.reorderSections(
        projectId,
        targetPage,
        order.map((s) => s.id)
      );
      onReordered(result.preview_url ?? null);
      // Reload from the backend so block ids resync with the saved file — ids
      // are positional and get reassigned on save, so a stale baseline would
      // scramble the NEXT reorder.
      await load(targetPage);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Reorder failed');
      await load(targetPage);
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8 text-gray-500 text-sm gap-2">
        <Loader2 className="w-4 h-4 animate-spin" />
        Loading page structure…
      </div>
    );
  }

  if (error && pages.length === 0) {
    return <p className="text-sm text-red-400 text-center py-6">{error}</p>;
  }

  if (pages.length === 0) {
    return (
      <div className="text-center py-8 px-4">
        <Layers className="w-8 h-8 text-gray-600 mx-auto mb-3" />
        <p className="text-sm text-gray-400">No reorderable sections</p>
        <p className="text-xs text-gray-500 mt-1">
          Pages need at least two sections to reorder.
        </p>
      </div>
    );
  }

  return (
    <div className="p-3 space-y-3">
      {/* Page selector */}
      {pages.length > 1 && (
        <div className="relative">
          <select
            value={activePage ?? ''}
            onChange={(e) => selectPage(e.target.value)}
            className="w-full appearance-none bg-gray-900 border border-gray-700 rounded-lg px-3 py-2 pr-8 text-sm text-gray-200 focus:outline-none focus:border-blue-500"
          >
            {pages.map((p) => (
              <option key={p.page_file} value={p.page_file}>
                {p.page_name} page
              </option>
            ))}
          </select>
          <ChevronDown className="w-4 h-4 text-gray-500 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
        </div>
      )}

      <p className="text-xs text-gray-500">
        Drag the handle, or use the arrows, to reorder this page's sections.
      </p>

      <ul className="space-y-1.5">
        {order.map((section, index) => (
          <li
            key={section.id}
            draggable
            onDragStart={() => setDragIndex(index)}
            onDragOver={(e) => {
              e.preventDefault();
              if (dragIndex !== null && dragIndex !== index) setDropTarget(index);
            }}
            onDrop={() => {
              handleDrop(index);
              setDropTarget(null);
            }}
            onDragEnd={() => {
              setDragIndex(null);
              setDropTarget(null);
            }}
            className={`flex items-center gap-2 px-2 py-2 rounded-lg border transition-colors ${
              dragIndex === index
                ? 'border-blue-500 bg-blue-500/10 opacity-50'
                : dropTarget === index
                  ? 'border-blue-400 bg-blue-500/5'
                  : 'border-gray-700 bg-gray-800 hover:border-gray-600'
            }`}
          >
            <GripVertical className="w-4 h-4 text-gray-500 flex-shrink-0 cursor-grab active:cursor-grabbing" />
            <span className="text-[10px] text-gray-600 w-4 text-center flex-shrink-0">{index + 1}</span>
            <span className="text-sm text-gray-200 truncate flex-1">{section.name}</span>
            {!section.is_component && (
              <span className="text-[9px] text-gray-500 bg-gray-900/60 border border-gray-700 rounded px-1 py-0.5 flex-shrink-0">
                inline
              </span>
            )}
            <div className="flex flex-col flex-shrink-0">
              <button
                onClick={() => moveItem(index, index - 1)}
                disabled={index === 0}
                className="text-gray-500 hover:text-white disabled:opacity-20 disabled:hover:text-gray-500 transition-colors"
                title="Move up"
              >
                <ChevronUp className="w-4 h-4" />
              </button>
              <button
                onClick={() => moveItem(index, index + 1)}
                disabled={index === order.length - 1}
                className="text-gray-500 hover:text-white disabled:opacity-20 disabled:hover:text-gray-500 transition-colors"
                title="Move down"
              >
                <ChevronDown className="w-4 h-4" />
              </button>
            </div>
          </li>
        ))}
      </ul>

      {error && <p className="text-xs text-red-400">{error}</p>}

      <button
        onClick={handleSave}
        disabled={isSaving || !orderChanged()}
        className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 text-white text-sm font-medium rounded-lg transition-colors disabled:cursor-not-allowed"
      >
        {isSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
        {isSaving ? 'Applying…' : 'Apply new order'}
      </button>
    </div>
  );
}
