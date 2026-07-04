'use client';

import { useCallback, useEffect, useState } from 'react';
import { History, Loader2, RotateCcw, FileCode, CheckCircle2 } from 'lucide-react';
import { api } from '@/lib/api';

interface EditHistoryEntry {
  chat_message_id: string;
  instruction: string;
  edit_description: string | null;
  created_at: string;
  files: Array<{ file_path: string; is_reverted: boolean }>;
  is_reverted: boolean;
  can_revert: boolean;
}

interface EditHistoryPanelProps {
  projectId: string;
  /** Perform the revert (owner updates preview/files); return true on success. */
  onRevert: (chatMessageId: string) => Promise<boolean>;
  /** Compact styling for embedding outside the editor (e.g. settings page). */
  readOnly?: boolean;
}

/**
 * List of AI edits with one-click revert. Reverting restores every file the
 * edit touched to its pre-edit code (later edits to the same files are
 * overwritten — the confirm dialog warns about this).
 */
export default function EditHistoryPanel({ projectId, onRevert, readOnly = false }: EditHistoryPanelProps) {
  const [edits, setEdits] = useState<EditHistoryEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [revertingId, setRevertingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await api.generation.getEditHistory(projectId);
      setEdits(result.edits);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load history');
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleRevert = async (edit: EditHistoryEntry, isLatest: boolean) => {
    const fileList = edit.files.map((f) => f.file_path.split('/').pop()).join(', ');
    const warning = isLatest
      ? `Undo this edit? (${fileList})`
      : `Revert this edit? Later changes to the same file(s) will also be discarded. (${fileList})`;
    if (!window.confirm(warning)) return;

    setRevertingId(edit.chat_message_id);
    try {
      const ok = await onRevert(edit.chat_message_id);
      if (ok) await load();
    } finally {
      setRevertingId(null);
    }
  };

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {isLoading ? (
          <div className="flex items-center justify-center py-8 text-gray-500 text-sm gap-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            Loading history…
          </div>
        ) : error ? (
          <p className="text-sm text-red-400 text-center py-6">{error}</p>
        ) : edits.length === 0 ? (
          <div className="text-center py-8 px-4">
            <History className="w-8 h-8 text-gray-600 mx-auto mb-3" />
            <p className="text-sm text-gray-400">No edits yet</p>
            <p className="text-xs text-gray-500 mt-1">AI edits will appear here with one-click undo.</p>
          </div>
        ) : (
          edits.map((edit, index) => (
            <div
              key={edit.chat_message_id}
              className={`rounded-lg border p-3 ${
                edit.is_reverted
                  ? 'border-gray-700/60 bg-gray-800/30 opacity-60'
                  : 'border-gray-700 bg-gray-800/60'
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-sm text-gray-200 line-clamp-2">
                    {edit.edit_description || edit.instruction}
                  </p>
                  <p className="text-[11px] text-gray-500 mt-1">
                    {new Date(edit.created_at).toLocaleString()}
                  </p>
                  <div className="flex flex-wrap gap-1 mt-1.5">
                    {edit.files.map((f) => (
                      <span
                        key={f.file_path}
                        className="inline-flex items-center gap-1 text-[10px] text-gray-400 bg-gray-900/60 border border-gray-700 rounded px-1.5 py-0.5"
                      >
                        <FileCode className="w-2.5 h-2.5" />
                        {f.file_path.split('/').pop()}
                      </span>
                    ))}
                  </div>
                </div>

                {edit.is_reverted ? (
                  <span className="flex items-center gap-1 text-[11px] text-gray-500 flex-shrink-0">
                    <CheckCircle2 className="w-3 h-3" />
                    Reverted
                  </span>
                ) : (
                  !readOnly &&
                  edit.can_revert && (
                    <button
                      onClick={() => handleRevert(edit, index === 0)}
                      disabled={revertingId !== null}
                      className="flex items-center gap-1 px-2 py-1 text-[11px] text-gray-300 hover:text-white bg-gray-700/60 hover:bg-gray-600 rounded transition-colors disabled:opacity-50 flex-shrink-0"
                      title="Restore the code from before this edit"
                    >
                      {revertingId === edit.chat_message_id ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <RotateCcw className="w-3 h-3" />
                      )}
                      Revert
                    </button>
                  )
                )}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
