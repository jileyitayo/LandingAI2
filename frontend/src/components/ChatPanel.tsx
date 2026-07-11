'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { Sparkles, Loader2, X, Send, AlertCircle, RotateCcw } from 'lucide-react';
import { api } from '@/lib/api';
import { SelectedElement } from '@/types/chat.types';
import AttachmentButton, { Attachment } from './AttachmentButton';
import type { EditScope } from './EditSidebar';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  attachments?: Attachment[];
  isError?: boolean;
  /** Error came from the edit rate limit — render an upgrade hint */
  rateLimited?: boolean;
  createdAt: string;
  /** Backend chat message id — enables one-click undo for edit messages */
  chatMessageId?: string;
}

export interface ChatSendResult {
  success: boolean;
  description?: string;
  message?: string;
  chatMessageId?: string;
  /** True when the edit was rejected by the per-tier edit rate limit (429) */
  rateLimited?: boolean;
  /** The backend wants explicit confirmation before running the edit */
  needsConfirmation?: boolean;
  confirmation?: Record<string, any>;
}

interface ChatPanelProps {
  projectId: string;
  selectedElement: SelectedElement | null;
  selectedElements?: SelectedElement[];
  onSend: (
    instruction: string,
    scope: EditScope,
    attachments: Attachment[],
    onProgress?: (stage: string, detail: string) => void,
    options?: { confirmedTarget?: string; confirmedPage?: Record<string, any> }
  ) => Promise<ChatSendResult>;
  /** Revert an edit by chat message id; returns true on success. */
  onUndo?: (chatMessageId: string) => Promise<boolean>;
  onClearSelection: () => void;
  isApplyingEdit: boolean;
  /** Route currently shown in the preview iframe (e.g. '/about') */
  currentRoute?: string;
}

/**
 * Persistent AI chat: the primary editing surface. Always visible; works with
 * no selection (page scope). Selecting an element scopes the next message,
 * shown as a dismissible chip above the input.
 */
export default function ChatPanel({
  projectId,
  selectedElement,
  selectedElements = [],
  onSend,
  onUndo,
  onClearSelection,
  isApplyingEdit,
  currentRoute = '/',
}: ChatPanelProps) {
  const [undoingId, setUndoingId] = useState<string | null>(null);
  const [progressLabel, setProgressLabel] = useState<string>('Applying edit…');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  // A backend-requested confirmation (e.g. site-wide component edit) awaiting
  // the user's Confirm/Cancel; holds everything needed to resubmit
  const [pendingConfirmation, setPendingConfirmation] = useState<{
    instruction: string;
    scope: EditScope;
    attachments: Attachment[];
    message: string;
    confirmation: Record<string, any>;
  } | null>(null);
  const [isLoadingHistory, setIsLoadingHistory] = useState(true);
  const [input, setInput] = useState('');
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [editScope, setEditScope] = useState<EditScope>('element');
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Reset scope when selection changes
  useEffect(() => {
    setEditScope('element');
  }, [selectedElement?.selector]);

  // Auto-grow the input up to ~5 rows (effect-based so it also handles
  // paste, programmatic clears, and text that wraps without a keystroke)
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  }, [input]);

  // Load chat history on mount
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const history = await api.generation.getChatHistory(projectId);
        if (cancelled) return;
        const loaded: ChatMessage[] = [];
        for (const m of history.messages) {
          const atts = (m.metadata?.attachments ?? []) as Array<{
            media_id?: string; id?: string; url: string; media_type?: string;
          }>;
          loaded.push({
            id: `${m.id}-user`,
            role: 'user',
            content: m.user_prompt,
            attachments: atts.map((a) => ({
              id: a.media_id ?? a.id ?? a.url,
              url: a.url,
              mediaType: a.media_type ?? 'image',
              filename: null,
            })),
            createdAt: m.created_at,
          });
          loaded.push({
            id: `${m.id}-ai`,
            role: 'assistant',
            content: m.ai_response,
            createdAt: m.created_at,
            chatMessageId: m.message_type === 'edit' ? m.id : undefined,
          });
        }
        setMessages(loaded);
      } catch {
        // History is non-critical; the chat still works without it
      } finally {
        if (!cancelled) setIsLoadingHistory(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  // Keep scrolled to the latest message
  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages, isApplyingEdit]);

  const handleSend = useCallback(async () => {
    const instruction = input.trim();
    if (instruction.length < 5 || isApplyingEdit) return;

    const sentAttachments = attachments;
    const scope: EditScope = selectedElement ? editScope : 'page';
    setInput('');
    setAttachments([]);
    setProgressLabel('Applying edit…');
    setMessages((prev) => [
      ...prev,
      {
        id: `local-${Date.now()}`,
        role: 'user',
        content: instruction,
        attachments: sentAttachments,
        createdAt: new Date().toISOString(),
      },
    ]);

    const stageLabels: Record<string, string> = {
      analyzing: 'Understanding your request…',
      editing: 'Rewriting the code…',
      building: 'Building & verifying preview…',
      done: 'Finishing up…',
    };
    const result = await onSend(instruction, scope, sentAttachments, (stage, detail) => {
      setProgressLabel(detail || stageLabels[stage] || 'Applying edit…');
    });

    // Backend wants confirmation before running (multi-page edit): render
    // Confirm/Cancel instead of a result message — no edit has happened yet
    if (result.needsConfirmation && result.confirmation) {
      setPendingConfirmation({
        instruction,
        scope,
        attachments: sentAttachments,
        message: result.message || 'This edit affects multiple pages. Apply it site-wide?',
        confirmation: result.confirmation,
      });
      return;
    }

    setMessages((prev) => [
      ...prev,
      {
        id: `local-${Date.now()}-ai`,
        role: 'assistant',
        content: result.success
          ? result.description || result.message || 'Edit applied'
          : result.message || 'Edit failed',
        isError: !result.success,
        rateLimited: result.rateLimited,
        createdAt: new Date().toISOString(),
        chatMessageId: result.chatMessageId,
      },
    ]);
  }, [input, attachments, isApplyingEdit, selectedElement, editScope, onSend]);

  const handleConfirmPending = useCallback(async () => {
    if (!pendingConfirmation || isApplyingEdit) return;
    const pending = pendingConfirmation;
    setPendingConfirmation(null);
    setProgressLabel('Applying edit…');

    const stageLabels: Record<string, string> = {
      analyzing: 'Understanding your request…',
      editing: 'Rewriting the code…',
      building: 'Building & verifying preview…',
      done: 'Finishing up…',
    };
    const result = await onSend(
      pending.instruction,
      pending.scope,
      pending.attachments,
      (stage, detail) => setProgressLabel(detail || stageLabels[stage] || 'Applying edit…'),
      pending.confirmation.kind === 'create_page'
        ? { confirmedPage: pending.confirmation.new_page }
        : { confirmedTarget: pending.confirmation.target_file }
    );
    setMessages((prev) => [
      ...prev,
      {
        id: `local-${Date.now()}-ai`,
        role: 'assistant',
        content: result.success
          ? result.description || result.message || 'Edit applied'
          : result.message || 'Edit failed',
        isError: !result.success,
        rateLimited: result.rateLimited,
        createdAt: new Date().toISOString(),
        chatMessageId: result.chatMessageId,
      },
    ]);
  }, [pendingConfirmation, isApplyingEdit, onSend]);

  const handleCancelPending = useCallback(() => {
    setPendingConfirmation(null);
    setMessages((prev) => [
      ...prev,
      {
        id: `local-${Date.now()}-cancel`,
        role: 'assistant',
        content: 'Cancelled — nothing was changed.',
        createdAt: new Date().toISOString(),
      },
    ]);
  }, []);

  const handleUndo = useCallback(async (message: ChatMessage) => {
    if (!onUndo || !message.chatMessageId) return;
    if (!window.confirm('Undo this edit? The affected files will be restored to their previous state.')) return;
    setUndoingId(message.chatMessageId);
    try {
      const ok = await onUndo(message.chatMessageId);
      if (ok) {
        setMessages((prev) => [
          ...prev,
          {
            id: `local-${Date.now()}-undo`,
            role: 'assistant',
            content: `Reverted: ${message.content}`,
            createdAt: new Date().toISOString(),
          },
        ]);
      }
    } finally {
      setUndoingId(null);
    }
  }, [onUndo]);

  // The one message that gets an inline Undo button: the most recent
  // successful edit (reverts and errors don't qualify)
  const lastUndoableId = (() => {
    for (let i = messages.length - 1; i >= 0; i--) {
      const m = messages[i];
      if (m.role !== 'assistant') continue;
      if (m.isError || !m.chatMessageId) continue;
      if (m.content.startsWith('Reverted:')) return null;
      return m.id;
    }
    return null;
  })();

  // Scope chip: breadcrumb when an element is selected, the current route
  // otherwise — so you always know WHICH page a page-scope edit will touch
  const renderScopeChip = () => {
    const routeLabel = currentRoute === '/' ? 'Home' : currentRoute;
    if (!selectedElement) {
      return (
        <span
          className="inline-flex items-center px-2 py-0.5 bg-gray-800 border border-gray-600 rounded-full text-xs text-gray-300"
          title={`Edits apply to the ${routeLabel} page`}
        >
          {routeLabel}
        </span>
      );
    }

    const sectionLabel = selectedElement.component?.componentName || 'Section';
    const elementLabel = selectedElement.component?.elementName || selectedElement.tagName;
    const extraCount = selectedElements.length > 1 ? selectedElements.length : 0;

    const crumbClass = (active: boolean) =>
      `px-1.5 py-0.5 rounded text-xs font-medium transition-colors ${
        active
          ? 'bg-blue-500/30 text-blue-200 ring-1 ring-blue-400/50'
          : 'text-gray-400 hover:text-white hover:bg-gray-700/60'
      }`;

    return (
      <span className="inline-flex items-center gap-1 pl-1 pr-1 py-0.5 bg-gray-800 border border-gray-600 rounded-full">
        <button
          onClick={() => setEditScope('page')}
          className={crumbClass(editScope === 'page')}
          title={`Scope the edit to the whole ${routeLabel} page`}
        >
          {routeLabel}
        </button>
        <span className="text-gray-600 text-xs">›</span>
        <button onClick={() => setEditScope('section')} className={crumbClass(editScope === 'section')}>
          {sectionLabel}
        </button>
        <span className="text-gray-600 text-xs">›</span>
        <button onClick={() => setEditScope('element')} className={crumbClass(editScope === 'element')}>
          {elementLabel}
          {extraCount > 1 && <span className="ml-1 text-blue-300">+{extraCount - 1}</span>}
        </button>
        <button
          onClick={onClearSelection}
          className="p-0.5 text-gray-500 hover:text-white rounded-full hover:bg-gray-600 transition-colors"
          title="Clear selection (edit whole page)"
        >
          <X className="w-3 h-3" />
        </button>
      </span>
    );
  };

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Message list */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-3">
        {isLoadingHistory ? (
          <div className="flex items-center justify-center py-8 text-gray-500 text-sm gap-2">
            <Loader2 className="w-4 h-4 animate-spin" />
            Loading history…
          </div>
        ) : messages.length === 0 ? (
          <div className="text-center py-8 px-4">
            <Sparkles className="w-8 h-8 text-blue-400/60 mx-auto mb-3" />
            <p className="text-sm text-gray-400 mb-1">Describe any change you want</p>
            <p className="text-xs text-gray-500">
              Click an element in the preview to scope your edit, or just type to edit the whole
              page. Use + to attach images.
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : message.isError
                      ? 'bg-red-900/30 border border-red-700/50 text-red-200'
                      : 'bg-gray-800 border border-gray-700 text-gray-200'
                }`}
              >
                {message.attachments && message.attachments.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-1.5">
                    {message.attachments.map((a) => (
                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        key={a.id}
                        src={a.url}
                        alt={a.filename ?? 'attachment'}
                        className="h-14 w-14 rounded object-cover border border-white/20"
                      />
                    ))}
                  </div>
                )}
                {message.isError && (
                  <AlertCircle className="w-3.5 h-3.5 inline mr-1 -mt-0.5" />
                )}
                {message.content}
                {message.rateLimited && (
                  <div className="mt-1.5 pt-1.5 border-t border-red-700/40">
                    <a
                      href="/dashboard/profile"
                      className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-300 hover:text-amber-200 transition-colors"
                    >
                      <Sparkles className="w-3 h-3" />
                      Upgrade your plan for more edits
                    </a>
                  </div>
                )}
                {onUndo && message.id === lastUndoableId && (
                  <div className="mt-1.5 pt-1.5 border-t border-gray-700/60">
                    <button
                      onClick={() => handleUndo(message)}
                      disabled={undoingId !== null || isApplyingEdit}
                      className="flex items-center gap-1 text-[11px] text-gray-400 hover:text-white transition-colors disabled:opacity-50"
                      title="Restore the files this edit changed"
                    >
                      {undoingId === message.chatMessageId ? (
                        <Loader2 className="w-3 h-3 animate-spin" />
                      ) : (
                        <RotateCcw className="w-3 h-3" />
                      )}
                      Undo
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))
        )}

        {pendingConfirmation && (
          <div className="flex justify-start">
            <div className="max-w-[85%] bg-amber-900/20 border border-amber-700/50 rounded-lg px-3 py-2 text-sm text-amber-100">
              <div className="flex items-start gap-1.5">
                <AlertCircle className="w-3.5 h-3.5 mt-0.5 shrink-0 text-amber-300" />
                <span>{pendingConfirmation.message}</span>
              </div>
              <div className="flex gap-2 mt-2">
                <button
                  onClick={handleConfirmPending}
                  disabled={isApplyingEdit}
                  className="px-2.5 py-1 text-xs font-medium bg-amber-600 hover:bg-amber-500 text-white rounded transition-colors disabled:opacity-50"
                >
                  {pendingConfirmation.confirmation.kind === 'create_page' ? 'Create page' : 'Apply site-wide'}
                </button>
                <button
                  onClick={handleCancelPending}
                  disabled={isApplyingEdit}
                  className="px-2.5 py-1 text-xs font-medium bg-gray-700 hover:bg-gray-600 text-gray-200 rounded transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {isApplyingEdit && (
          <div className="flex justify-start">
            <div className="bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-gray-400 flex items-center gap-2">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              {progressLabel}
            </div>
          </div>
        )}
      </div>

      {/* Input area */}
      <div className="border-t border-gray-700 p-3 space-y-2">
        <div className="flex items-center gap-2">{renderScopeChip()}</div>

        <div className="flex items-end gap-2">
          <AttachmentButton
            attachments={attachments}
            onAttachmentsChange={setAttachments}
            projectId={projectId}
            disabled={isApplyingEdit}
          />
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
              }
            }}
            placeholder={
              selectedElement
                ? 'Describe your change… e.g. "Turn this into a carousel"'
                : 'Describe a change to this page… e.g. "Make the colors warmer"'
            }
            rows={1}
            disabled={isApplyingEdit}
            className="flex-1 px-3 py-2 bg-gray-900 border border-gray-600 rounded-lg text-sm text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none disabled:opacity-60"
          />
          <button
            onClick={handleSend}
            disabled={isApplyingEdit || input.trim().length < 5}
            className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 text-white transition-colors disabled:cursor-not-allowed flex-shrink-0"
            title="Send"
          >
            {isApplyingEdit ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
