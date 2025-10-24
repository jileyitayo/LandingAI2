'use client';

import { useState, useEffect, useRef, memo } from 'react';
import { MessageSquare, Send, X, ChevronDown, ChevronRight, Loader2, AlertCircle } from 'lucide-react';
import { api } from '@/lib/api';
import { ChatMessage, SelectedElement, MessageType } from '@/types/chat.types';

interface ChatWindowProps {
  projectId: string;
  selectedElement: SelectedElement | null;
  onSelectedElementChange: (element: SelectedElement | null) => void;
  onSelectorModeChange: (enabled: boolean) => void;
  selectorEnabled: boolean;
  onEditSubmit: (prompt: string) => Promise<void>;
  isProcessing: boolean;
  inputRef?: React.RefObject<HTMLTextAreaElement>;
}

function ChatWindow({
  projectId,
  selectedElement,
  onSelectedElementChange,
  onSelectorModeChange,
  selectorEnabled,
  onEditSubmit,
  isProcessing,
  inputRef: externalInputRef
}: ChatWindowProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expandedMessages, setExpandedMessages] = useState<Set<string>>(new Set());
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const localInputRef = useRef<HTMLTextAreaElement>(null);

  // Use external ref if provided, otherwise use local ref
  const inputRef = externalInputRef || localInputRef;

  // Load chat history on mount
  useEffect(() => {
    loadChatHistory();
  }, [projectId]);

  // Auto-scroll to latest message
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const loadChatHistory = async () => {
    setIsLoading(true);
    try {
      const response = await api.generation.getChatHistory(projectId);
      setMessages(response.messages as any);
    } catch (err: any) {
      console.error('Failed to load chat history:', err);
      setError('Failed to load chat history');
    } finally {
      setIsLoading(false);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleInputFocus = () => {
    // Auto-enable selector when user focuses on input
    if (!selectorEnabled) {
      onSelectorModeChange(true);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputValue(e.target.value);
    // Auto-enable selector when user types
    if (e.target.value.trim() && !selectorEnabled) {
      onSelectorModeChange(true);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!inputValue.trim() || isProcessing) {
      return;
    }

    // Validate that a component is selected
    if (!selectedElement) {
      setError('Please select a component first by clicking on an element in the preview');
      return;
    }

    setError(null);

    try {
      // Call the edit submission handler from parent
      await onEditSubmit(inputValue.trim());

      // Clear input and selection after successful submit
      setInputValue('');
      onSelectedElementChange(null);

      // Reload chat history to get the new message
      await loadChatHistory();
    } catch (err: any) {
      console.error('Failed to submit edit:', err);
      setError(err.message || 'Failed to submit edit');
    }
  };

  const clearSelection = () => {
    onSelectedElementChange(null);
    setError(null);
  };

  const toggleMessageExpanded = (messageId: string) => {
    setExpandedMessages((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(messageId)) {
        newSet.delete(messageId);
      } else {
        newSet.add(messageId);
      }
      return newSet;
    });
  };

  const getMessageTypeColor = (type: MessageType) => {
    switch (type) {
      case 'generation':
        return 'bg-gray-700 border-gray-600';
      case 'edit':
        return 'bg-gray-700 border-purple-600';
      case 'question':
        return 'bg-gray-700 border-gray-600';
      default:
        return 'bg-gray-700 border-gray-600';
    }
  };

  const getMessageTypeBadgeColor = (type: MessageType) => {
    switch (type) {
      case 'generation':
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
      case 'edit':
        return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
      case 'question':
        return 'bg-gray-500/10 text-gray-400 border-gray-500/20';
      default:
        return 'bg-gray-500/10 text-gray-400 border-gray-500/20';
    }
  };

  const getMessageTypeLabel = (type: MessageType) => {
    switch (type) {
      case 'generation':
        return 'Website Generated';
      case 'edit':
        return 'Component Edited';
      case 'question':
        return 'Question';
      default:
        return 'Message';
    }
  };

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Header */}
      <div className="px-4 py-3 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center gap-2 mb-2">
          <MessageSquare className="w-4 h-4 text-blue-400" />
          <span className="text-sm font-medium text-white">Chat History</span>
        </div>

        {/* Selected Element Badge in Header */}
        {selectedElement && (
          <div className="bg-blue-900 border border-blue-700 rounded px-2 py-1 flex items-center justify-between">
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse"></div>
              <div className="text-xs text-blue-100 truncate">
                <span className="font-medium">
                  {selectedElement.component?.componentName || selectedElement.tagName}
                </span>
                {selectedElement.component?.elementName && (
                  <span className="text-blue-300"> → {selectedElement.component.elementName}</span>
                )}
              </div>
            </div>
            <button
              onClick={clearSelection}
              className="text-blue-300 hover:text-white transition-colors ml-2 flex-shrink-0"
              title="Clear selection"
            >
              <X className="w-3 h-3" />
            </button>
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
          </div>
        ) : messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm">
            No messages yet
          </div>
        ) : (
          messages.map((message) => (
            <div key={message.id} className="space-y-2">
              {/* Message Type Badge */}
              <div className="flex items-center justify-between">
                <span className={`text-xs px-2 py-1 rounded border ${getMessageTypeBadgeColor(message.message_type)}`}>
                  {getMessageTypeLabel(message.message_type)}
                </span>
                <span className="text-xs text-gray-500">
                  {new Date(message.created_at).toLocaleTimeString()}
                </span>
              </div>

              {/* User Message */}
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white text-sm font-medium flex-shrink-0">
                  U
                </div>
                <div className="flex-1">
                  <div className="bg-blue-500 text-white p-3 rounded-lg">
                    <p className="text-sm">{message.user_prompt}</p>
                  </div>
                </div>
              </div>

              {/* AI Response */}
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center text-white text-sm font-medium flex-shrink-0">
                  AI
                </div>
                <div className="flex-1">
                  <div className={`border p-3 rounded-lg ${getMessageTypeColor(message.message_type)}`}>
                    <p className="text-sm text-gray-100">{message.ai_response}</p>

                    {/* Show code changes for edit messages */}
                    {message.message_type === 'edit' && message.metadata?.file_path && (
                      <div className="mt-3">
                        <button
                          onClick={() => toggleMessageExpanded(message.id)}
                          className="flex items-center gap-2 text-xs text-gray-300 hover:text-white transition-colors"
                        >
                          {expandedMessages.has(message.id) ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                          <span className="font-medium">View Code Changes</span>
                          <span className="text-gray-400">({message.metadata.file_path?.split('/').pop() || 'File'})</span>
                        </button>

                        {expandedMessages.has(message.id) && (
                          <div className="mt-2 bg-gray-800 rounded border border-gray-600 p-3 space-y-2">
                            <div className="text-xs space-y-2">
                              {/* Component info */}
                              <div className="font-mono">
                                <div className="font-semibold text-blue-300 mb-1">
                                  Component: {message.metadata.selected_element?.component?.componentName || 'Unknown'}
                                </div>
                                <div className="text-gray-300">
                                  File: {message.metadata.file_path}
                                </div>
                              </div>

                              {/* Selected element info */}
                              {message.metadata.selected_element && (
                                <div className="pt-2 border-t border-gray-700">
                                  <div className="text-gray-400 mb-1">Selected Element:</div>
                                  <div className="font-mono text-gray-200">
                                    {message.metadata.selected_element.component?.elementName || message.metadata.selected_element.tagName}
                                  </div>
                                  {message.metadata.selected_element.textContent && (
                                    <div className="mt-1 text-gray-400 italic">
                                      "{message.metadata.selected_element.textContent.slice(0, 60)}{message.metadata.selected_element.textContent.length > 60 ? '...' : ''}"
                                    </div>
                                  )}
                                </div>
                              )}

                              {/* Edit ID for tracking */}
                              {message.metadata.edit_id && (
                                <div className="pt-2 border-t border-gray-700 text-gray-500">
                                  Edit ID: {message.metadata.edit_id}
                                </div>
                              )}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-700 bg-gray-800 p-4">

        {/* Error Message */}
        {error && (
          <div className="mb-3 p-3 bg-red-900 border border-red-700 rounded-lg flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-red-300 mt-0.5 flex-shrink-0" />
            <p className="text-sm text-red-100">{error}</p>
          </div>
        )}

        {/* Input Form */}
        <form onSubmit={handleSubmit}>
          <div className="flex gap-2">
            <textarea
              ref={inputRef}
              value={inputValue}
              onChange={handleInputChange}
              onFocus={handleInputFocus}
              placeholder={
                selectorEnabled
                  ? 'Describe your changes... (selector enabled)'
                  : 'Type to enable selector and describe changes...'
              }
              className="flex-1 bg-gray-900 text-white border border-gray-600 rounded-lg px-3 py-2 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
              rows={3}
              disabled={isProcessing}
            />
            <button
              type="submit"
              disabled={!inputValue.trim() || isProcessing || !selectedElement}
              className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="hidden sm:inline">Processing...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span className="hidden sm:inline">Submit</span>
                </>
              )}
            </button>
          </div>
        </form>

        {/* Helper Text */}
        <div className="mt-2 text-xs text-gray-400">
          {selectorEnabled ? (
            <span>✓ Selector enabled. Click an element in the preview to select it.</span>
          ) : (
            <span>Start typing to enable component selector</span>
          )}
        </div>
      </div>
    </div>
  );
}

// Export memoized version to prevent unnecessary re-renders
export default memo(ChatWindow);
