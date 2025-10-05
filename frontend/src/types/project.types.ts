export interface Project {
  id: string;
  name: string;
  description?: string;
  html_content  : string;
  css_content: string;
  js_content: string;
  user_id: string;
  created_at: string;
  updated_at: string;
  is_published?: boolean;
  preview_url?: string;
}

export interface ProjectCreateInput {
  name: string;
  description?: string;
  html_content?: string;
  css_content ?: string;
  js_content?: string;
}

export interface ProjectUpdateInput {
  name?: string;
  description?: string;
  html_content?: string;
  css_content?: string;
  js_content?: string;
  is_published?: boolean;
}

export type EditorTab = 'html_content' | 'css_content' | 'js_content';

export type ViewportSize = 'desktop' | 'tablet' | 'mobile';

export interface EditorState {
  html_content: string;
  css_content: string;
  js_content: string;
  activeTab: EditorTab;
  hasUnsavedChanges: boolean;
}

