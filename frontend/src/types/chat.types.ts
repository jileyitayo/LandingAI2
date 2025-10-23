/**
 * Chat message types for project chat functionality
 */

export type MessageType = 'generation' | 'edit' | 'question';

export interface ChatMessage {
  id: string;
  project_id: string;
  user_id: string;
  message_type: MessageType;
  user_prompt: string;
  ai_response: string;
  metadata: {
    file_path?: string;
    selected_element?: {
      tagName: string;
      textContent: string;
      component?: {
        componentName: string | null;
        componentFile: string | null;
        elementName: string | null;
        isRoot: boolean;
      };
    };
    old_code?: string;
    new_code?: string;
    edit_id?: string;
  };
  created_at: string;
  updated_at: string;
}

export interface ChatMessageRequest {
  message_type: MessageType;
  user_prompt: string;
  ai_response: string;
  metadata?: Record<string, any>;
}

export interface ChatHistoryResponse {
  messages: ChatMessage[];
  total_count: number;
}

export interface SelectedElement {
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
