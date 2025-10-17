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
  published?: boolean;
  preview_url?: string;
  subdomain?: string;
  deployment_url?: string;
  whatsapp_number?: string;
  seo_title?: string;
  seo_description?: string;
  theme_settings?: Record<string, any>;
  // new fields
  project_type?: 'html' | 'react';
  prompt?: string;
  template_id?: string;
  generation_status?: 'idle' | 'generating' | 'completed' | 'failed';
  generation_error?: string;
  last_generated_at?: string;
  files_count?: number;
  website_structure?: Record<string, any>;
  business_analysis?: Record<string, any>;
  validation_result?: Record<string, any>;
  generation_metadata?: Record<string, any>;
}

export interface ProjectCreateInput {
  name: string;
  description?: string;
  html_content?: string;
  css_content ?: string;
  js_content?: string;
  // new fields
  project_type?: 'html' | 'react';
  prompt?: string;
  template_id?: string;
}

export interface ProjectUpdateInput {
  name?: string;
  description?: string;
  html_content?: string;
  css_content?: string;
  js_content?: string;
  is_published?: boolean;
  published?: boolean;
  subdomain?: string;
  whatsapp_number?: string;
  seo_title?: string;
  seo_description?: string;
  theme_settings?: Record<string, any>;
  // new fields
  project_type?: 'html' | 'react';
  prompt?: string;
  template_id?: string;
  generation_status?: 'idle' | 'generating' | 'completed' | 'failed';
  generation_error?: string;
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

