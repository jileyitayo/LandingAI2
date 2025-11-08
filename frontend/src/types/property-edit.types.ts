/**
 * Type definitions for the property editing system
 */

export type PropertyType =
  | 'text'
  | 'color'  // Text color (maps to text-color-shade classes)
  | 'textColor'  // Deprecated: use 'color' instead
  | 'backgroundColor'
  | 'borderColor'
  | 'fontSize'
  | 'fontWeight'
  | 'fontFamily'
  | 'textAlign'
  | 'textTransform'
  | 'imageUrl'
  | 'imageFit'
  | 'imageAlt'
  | 'linkHref'
  | 'linkTarget'
  | 'visibility'
  | 'customClass';

export type ElementType =
  | 'Heading'
  | 'Text'
  | 'Button'
  | 'Link'
  | 'Image'
  | 'Container'
  | 'Section'
  | 'Input'
  | 'Icon'
  | 'Card'
  | 'List'
  | 'ListItem'
  | 'Other';

export interface PropertyValue {
  type: PropertyType;
  value: string | number | boolean;
}

export interface PropertyEditRequest {
  element_selector: string;
  component_file: string;
  properties: PropertyChange[];
  batch?: boolean; // If true, apply all changes at once
}

export interface PropertyChange {
  property: PropertyType;
  value: string | number | boolean;
  oldValue?: string | number | boolean;
  unit?: string;
}

export interface PropertyEditResponse {
  success: boolean;
  message: string;
  updated_file: string;
  changes_applied: PropertyChange[];
  preview_url?: string;
  new_code?: string;
  old_code?: string;
}

export interface DesignTokens {
  colors: {
    primary?: string;
    secondary?: string;
    accent?: string;
    text?: string;
    background?: string;
    border?: string;
    [key: string]: string | undefined;
  };
  fonts: {
    heading?: string;
    body?: string;
    mono?: string;
    [key: string]: string | undefined;
  };
  spacing: {
    sections?: string;
    containers?: string;
    elements?: string;
    [key: string]: string | undefined;
  };
  borderRadius: {
    sm?: string;
    md?: string;
    lg?: string;
    full?: string;
    [key: string]: string | undefined;
  };
  shadows: {
    sm?: string;
    md?: string;
    lg?: string;
    xl?: string;
    [key: string]: string | undefined;
  };
}

export interface PropertySuggestion {
  label: string;
  value: string;
  preview?: string; // For visual preview (e.g., color hex)
  category?: string;
  description?: string;
}

export interface EditableElement {
  selector: string;
  elementType: ElementType;
  elementName: string; // data-element value
  componentName?: string;
  componentFile?: string;
  textContent?: string;
  editableText: boolean;
  editableSrc: boolean;
  currentProperties: Partial<Record<PropertyType, string>>;
  availableProperties: PropertyType[];
  constraints?: PropertyConstraints;
}

export interface PropertyConstraints {
  text?: {
    maxLength?: number;
    minLength?: number;
    pattern?: string;
  };
  number?: {
    min?: number;
    max?: number;
    step?: number;
  };
  select?: {
    options: string[];
  };
}

export interface PageInfo {
  title: string;
  description: string;
  componentCount: number;
  elementCount: number;
  designTokens?: DesignTokens;
}

// Tailwind preset values
export const TAILWIND_COLORS = [
  'slate', 'gray', 'zinc', 'neutral', 'stone',
  'red', 'orange', 'amber', 'yellow', 'lime', 'green', 'emerald', 'teal', 'cyan',
  'sky', 'blue', 'indigo', 'violet', 'purple', 'fuchsia', 'pink', 'rose'
] as const;

export const TAILWIND_COLOR_SHADES = [
  '50', '100', '200', '300', '400', '500', '600', '700', '800', '900', '950'
] as const;

export const TAILWIND_FONT_SIZES = [
  'text-xs', 'text-sm', 'text-base', 'text-lg', 'text-xl',
  'text-2xl', 'text-3xl', 'text-4xl', 'text-5xl', 'text-6xl',
  'text-7xl', 'text-8xl', 'text-9xl'
] as const;

export const TAILWIND_FONT_WEIGHTS = [
  { value: 'font-thin', label: 'Thin', weight: 100 },
  { value: 'font-extralight', label: 'Extra Light', weight: 200 },
  { value: 'font-light', label: 'Light', weight: 300 },
  { value: 'font-normal', label: 'Normal', weight: 400 },
  { value: 'font-medium', label: 'Medium', weight: 500 },
  { value: 'font-semibold', label: 'Semibold', weight: 600 },
  { value: 'font-bold', label: 'Bold', weight: 700 },
  { value: 'font-extrabold', label: 'Extrabold', weight: 800 },
  { value: 'font-black', label: 'Black', weight: 900 },
] as const;


