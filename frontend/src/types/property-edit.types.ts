/**
 * Type definitions for the property editing system
 */

export type PropertyType =
  | 'text'
  | 'textColor'
  | 'backgroundColor'
  | 'borderColor'
  | 'fontSize'
  | 'fontWeight'
  | 'fontFamily'
  | 'lineHeight'
  | 'textAlign'
  | 'textTransform'
  | 'padding'
  | 'paddingTop'
  | 'paddingRight'
  | 'paddingBottom'
  | 'paddingLeft'
  | 'margin'
  | 'marginTop'
  | 'marginRight'
  | 'marginBottom'
  | 'marginLeft'
  | 'gap'
  | 'borderWidth'
  | 'borderStyle'
  | 'borderRadius'
  | 'width'
  | 'height'
  | 'minWidth'
  | 'minHeight'
  | 'maxWidth'
  | 'maxHeight'
  | 'display'
  | 'position'
  | 'flexDirection'
  | 'justifyContent'
  | 'alignItems'
  | 'flexWrap'
  | 'zIndex'
  | 'opacity'
  | 'boxShadow'
  | 'transition'
  | 'animation'
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

export type SpacingUnit = 'px' | 'rem' | 'em' | '%' | 'auto';
export type SizeUnit = 'px' | '%' | 'rem' | 'em' | 'vw' | 'vh' | 'auto';

export interface PropertyValue {
  type: PropertyType;
  value: string | number | boolean;
  unit?: SpacingUnit | SizeUnit;
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

export const TAILWIND_SPACING = [
  { value: '0', label: '0', px: '0px' },
  { value: '0.5', label: '0.5', px: '2px' },
  { value: '1', label: '1', px: '4px' },
  { value: '2', label: '2', px: '8px' },
  { value: '3', label: '3', px: '12px' },
  { value: '4', label: '4', px: '16px' },
  { value: '5', label: '5', px: '20px' },
  { value: '6', label: '6', px: '24px' },
  { value: '8', label: '8', px: '32px' },
  { value: '10', label: '10', px: '40px' },
  { value: '12', label: '12', px: '48px' },
  { value: '16', label: '16', px: '64px' },
  { value: '20', label: '20', px: '80px' },
  { value: '24', label: '24', px: '96px' },
  { value: '32', label: '32', px: '128px' },
] as const;

export const TAILWIND_SHADOWS = [
  { value: 'shadow-none', label: 'None', preview: 'none' },
  { value: 'shadow-sm', label: 'Small', preview: '0 1px 2px 0 rgb(0 0 0 / 0.05)' },
  { value: 'shadow', label: 'Base', preview: '0 1px 3px 0 rgb(0 0 0 / 0.1)' },
  { value: 'shadow-md', label: 'Medium', preview: '0 4px 6px -1px rgb(0 0 0 / 0.1)' },
  { value: 'shadow-lg', label: 'Large', preview: '0 10px 15px -3px rgb(0 0 0 / 0.1)' },
  { value: 'shadow-xl', label: 'Extra Large', preview: '0 20px 25px -5px rgb(0 0 0 / 0.1)' },
  { value: 'shadow-2xl', label: '2XL', preview: '0 25px 50px -12px rgb(0 0 0 / 0.25)' },
] as const;

export const TAILWIND_BORDER_RADIUS = [
  { value: 'rounded-none', label: 'None', px: '0px' },
  { value: 'rounded-sm', label: 'Small', px: '2px' },
  { value: 'rounded', label: 'Base', px: '4px' },
  { value: 'rounded-md', label: 'Medium', px: '6px' },
  { value: 'rounded-lg', label: 'Large', px: '8px' },
  { value: 'rounded-xl', label: 'XL', px: '12px' },
  { value: 'rounded-2xl', label: '2XL', px: '16px' },
  { value: 'rounded-3xl', label: '3XL', px: '24px' },
  { value: 'rounded-full', label: 'Full', px: '9999px' },
] as const;

