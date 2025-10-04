/**
 * Component Library Type Definitions
 * 
 * This file defines the TypeScript types for the component library system,
 * ensuring type safety across the template generation and rendering process.
 */

/**
 * Supported component types in the library
 */
export enum ComponentType {
  HEADER = 'header',
  HERO = 'hero',
  SERVICES = 'services',
  ABOUT = 'about',
  CTA = 'cta',
  CONTACT = 'contact',
  TESTIMONIALS = 'testimonials',
  FOOTER = 'footer',
}

/**
 * Types for content bindings
 */
export enum ContentBindingType {
  TEXT = 'text',
  EMAIL = 'email',
  PHONE = 'phone',
  URL = 'url',
  IMAGE = 'image',
  VIDEO = 'video',
  ARRAY = 'array',
  COLOR = 'color',
}

/**
 * Content binding definition
 */
export interface ContentBinding {
  type: ContentBindingType;
  required: boolean;
  default?: string | string[] | Record<string, unknown>;
  placeholder?: string;
  validation?: Record<string, unknown>;
  itemSchema?: Record<string, string>; // For array types
}

/**
 * Component configuration options
 */
export interface ComponentConfig {
  // Background options
  background?: {
    type?: 'image' | 'color' | 'gradient' | 'video';
    value?: string;
    overlay?: boolean;
    overlayOpacity?: number;
    parallax?: boolean;
  };
  
  // Layout options
  layout?: string;
  alignment?: 'left' | 'center' | 'right';
  contentAlignment?: 'left' | 'center' | 'right';
  verticalAlignment?: 'top' | 'center' | 'bottom';
  
  // Style options
  columns?: number;
  cardStyle?: 'elevated' | 'bordered' | 'flat';
  iconStyle?: 'outlined' | 'solid';
  spacing?: 'compact' | 'normal' | 'comfortable' | 'spacious';
  minHeight?: string;
  
  // Feature flags
  sticky?: boolean;
  showBorder?: boolean;
  showWhatsApp?: boolean;
  showMap?: boolean;
  animation?: boolean;
  
  // Form options
  formFields?: string[];
  
  // Text options
  textColor?: 'auto' | 'light' | 'dark';
  
  // Other options
  imagePosition?: 'left' | 'right';
  iconPosition?: 'left' | 'right';
  style?: string;
  
  // Allow additional custom properties
  [key: string]: unknown;
}

/**
 * Component variation definition
 */
export interface ComponentVariation {
  name: string;
  description: string;
  html: string;
  css: string;
  config: ComponentConfig;
  content_bindings: Record<string, ContentBinding>;
  preview_image?: string;
  tags: string[];
}

/**
 * Section in a template (component instance)
 */
export interface TemplateSection {
  id: string;
  type: ComponentType;
  order: number;
  variation: string;
  html: string;
  css: string;
  config: ComponentConfig;
  content_bindings: Record<string, ContentBinding>;
}

/**
 * Style configuration for a template
 */
export interface StyleConfig {
  colorScheme: {
    primary: string;
    secondary?: string;
    accent?: string;
    background?: string;
    text?: string;
    heading?: string;
  };
  typography: {
    headingFont: string;
    bodyFont: string;
    baseFontSize?: string;
  };
  spacing: 'compact' | 'comfortable' | 'spacious';
  borderRadius?: 'none' | 'small' | 'medium' | 'large';
  customCSSVariables?: Record<string, string>;
}

/**
 * Content schema defining required fields for a template
 */
export interface ContentSchema {
  required_fields: Record<string, ContentBinding>;
  optional_fields?: Record<string, ContentBinding>;
}

/**
 * Complete template structure
 */
export interface Template {
  id: string;
  user_id?: string | null;
  name: string;
  description?: string;
  preview_image?: string;
  preview_html?: string;
  category?: 'business' | 'portfolio' | 'restaurant' | 'services' | 'custom';
  base_html?: string;
  base_css?: string;
  base_js?: string;
  is_system_template: boolean;
  is_active: boolean;
  is_public: boolean;
  generation_prompt?: string;
  style_config?: StyleConfig;
  sections_config: {
    sections: TemplateSection[];
  };
  content_schema?: ContentSchema;
  tags?: string[];
  use_count: number;
  generation_status: 'generating' | 'completed' | 'failed';
  generation_error?: string;
  created_at: string;
  updated_at: string;
}

/**
 * Component library metadata (summary info)
 */
export interface ComponentLibraryItem {
  name: string;
  description: string;
  tags: string[];
  preview_url?: string | null;
}

/**
 * Component library structure
 */
export type ComponentLibrary = {
  [K in ComponentType]: Record<string, ComponentLibraryItem>;
};

/**
 * Content data for rendering a template
 */
export interface TemplateContent {
  [key: string]: string | string[] | Record<string, unknown>;
}

/**
 * Rendered template output
 */
export interface RenderedTemplate {
  html: string;
  css: string;
  js?: string;
}

/**
 * Component validation result
 */
export interface ComponentValidationResult {
  valid: boolean;
  errors: string[];
  warnings?: string[];
}

/**
 * Template generation request
 */
export interface TemplateGenerationRequest {
  prompt: string;
  user_id: string;
  style_preferences?: {
    colorScheme?: string;
    typography?: string;
    layout?: string;
  };
  category?: string;
  tags?: string[];
}

/**
 * Template generation response
 */
export interface TemplateGenerationResponse {
  template_id: string;
  status: 'generating' | 'completed' | 'failed';
  message?: string;
  error?: string;
}

/**
 * Content generation request
 */
export interface ContentGenerationRequest {
  prompt: string;
  template_id: string;
  user_id: string;
}

/**
 * Content generation response
 */
export interface ContentGenerationResponse {
  project_id: string;
  status: 'generating' | 'completed' | 'failed';
  content?: TemplateContent;
  rendered?: RenderedTemplate;
  message?: string;
  error?: string;
}

/**
 * Component preview props
 */
export interface ComponentPreviewProps {
  component: ComponentVariation;
  content?: TemplateContent;
  className?: string;
  width?: number | string;
  height?: number | string;
  scale?: number;
  showControls?: boolean;
  onContentChange?: (content: TemplateContent) => void;
}

/**
 * Template preview props
 */
export interface TemplatePreviewProps {
  template: Template;
  content?: TemplateContent;
  className?: string;
  responsive?: 'desktop' | 'tablet' | 'mobile';
  showControls?: boolean;
  onContentChange?: (content: TemplateContent) => void;
}

/**
 * Component selector props
 */
export interface ComponentSelectorProps {
  componentType: ComponentType;
  selectedVariation?: string;
  onSelect: (variation: string) => void;
  showPreview?: boolean;
}

/**
 * Template card props
 */
export interface TemplateCardProps {
  template: Template;
  onSelect?: (template: Template) => void;
  onEdit?: (template: Template) => void;
  onDelete?: (template: Template) => void;
  onDuplicate?: (template: Template) => void;
  showActions?: boolean;
  className?: string;
}

/**
 * Component library response from API
 */
export interface ComponentLibraryResponse {
  components: ComponentLibrary;
  total_components: number;
  total_variations: number;
}

/**
 * Helper type for component type keys
 */
export type ComponentTypeKey = keyof typeof ComponentType;

/**
 * Helper type for content binding type keys
 */
export type ContentBindingTypeKey = keyof typeof ContentBindingType;

