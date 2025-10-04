/**
 * Component Library Validation Schemas
 * 
 * This file contains validation schemas for component structures,
 * ensuring data integrity and type safety throughout the system.
 */

import { z } from 'zod';

/**
 * Content Binding Type Schema
 */
export const ContentBindingTypeSchema = z.enum([
  'text',
  'email',
  'phone',
  'url',
  'image',
  'video',
  'array',
  'color',
]);

/**
 * Content Binding Schema
 */
export const ContentBindingSchema = z.object({
  type: ContentBindingTypeSchema,
  required: z.boolean().default(false),
  default: z.union([
    z.string(),
    z.array(z.unknown()),
    z.record(z.string(), z.unknown()),
  ]).optional(),
  placeholder: z.string().optional(),
  validation: z.record(z.string(), z.unknown()).optional(),
  itemSchema: z.record(z.string(), z.unknown()).optional(),
});

/**
 * Component Config Schema
 */
export const ComponentConfigSchema = z.object({
  // Background options
  background: z.object({
    type: z.enum(['image', 'color', 'gradient', 'video']).optional(),
    value: z.string().optional(),
    overlay: z.boolean().optional(),
    overlayOpacity: z.number().min(0).max(1).optional(),
    parallax: z.boolean().optional(),
  }).optional(),
  
  // Layout options
  layout: z.string().optional(),
  alignment: z.enum(['left', 'center', 'right']).optional(),
  contentAlignment: z.enum(['left', 'center', 'right']).optional(),
  verticalAlignment: z.enum(['top', 'center', 'bottom']).optional(),
  
  // Style options
  columns: z.number().int().positive().optional(),
  cardStyle: z.enum(['elevated', 'bordered', 'flat']).optional(),
  iconStyle: z.enum(['outlined', 'solid']).optional(),
  spacing: z.enum(['compact', 'normal', 'comfortable', 'spacious']).optional(),
  minHeight: z.string().optional(),
  
  // Feature flags
  sticky: z.boolean().optional(),
  showBorder: z.boolean().optional(),
  showWhatsApp: z.boolean().optional(),
  showMap: z.boolean().optional(),
  animation: z.boolean().optional(),
  
  // Form options
  formFields: z.array(z.string()).optional(),
  
  // Text options
  textColor: z.enum(['auto', 'light', 'dark']).optional(),
  
  // Other options
  imagePosition: z.enum(['left', 'right']).optional(),
  iconPosition: z.enum(['left', 'right']).optional(),
  style: z.string().optional(),
}).passthrough(); // Allow additional properties

/**
 * Component Variation Schema
 */
export const ComponentVariationSchema = z.object({
  name: z.string().min(1),
  description: z.string(),
  html: z.string().min(1),
  css: z.string(),
  config: ComponentConfigSchema,
  content_bindings: z.record(z.string(), ContentBindingSchema),
  preview_image: z.string().url().optional(),
  tags: z.array(z.string()).default([]),
});

/**
 * Component Type Schema
 */
export const ComponentTypeSchema = z.enum([
  'header',
  'hero',
  'services',
  'about',
  'cta',
  'contact',
  'testimonials',
  'footer',
]);

/**
 * Template Section Schema
 */
export const TemplateSectionSchema = z.object({
  id: z.string(),
  type: ComponentTypeSchema,
  order: z.number().int().nonnegative(),
  variation: z.string(),
  html: z.string(),
  css: z.string(),
  config: ComponentConfigSchema,
  content_bindings: z.record(z.string(), ContentBindingSchema),
});

/**
 * Style Config Schema
 */
export const StyleConfigSchema = z.object({
  colorScheme: z.object({
    primary: z.string(),
    secondary: z.string().optional(),
    accent: z.string().optional(),
    background: z.string().optional(),
    text: z.string().optional(),
    heading: z.string().optional(),
  }),
  typography: z.object({
    headingFont: z.string(),
    bodyFont: z.string(),
    baseFontSize: z.string().optional(),
  }),
  spacing: z.enum(['compact', 'comfortable', 'spacious']),
  borderRadius: z.enum(['none', 'small', 'medium', 'large']).optional(),
  customCSSVariables: z.record(z.string(), z.unknown()).optional(),
});

/**
 * Content Schema
 */
export const ContentSchemaSchema = z.object({
  required_fields: z.record(z.string(), ContentBindingSchema),
  optional_fields: z.record(z.string(), ContentBindingSchema).optional(),
});

/**
 * Template Category Schema
 */
export const TemplateCategorySchema = z.enum([
  'business',
  'portfolio',
  'restaurant',
  'services',
  'custom',
]);

/**
 * Template Generation Status Schema
 */
export const GenerationStatusSchema = z.enum([
  'generating',
  'completed',
  'failed',
]);

/**
 * Complete Template Schema
 */
export const TemplateSchema = z.object({
  id: z.string().uuid(),
  user_id: z.string().uuid().nullable().optional(),
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional(),
  preview_image: z.string().url().optional(),
  preview_html: z.string().optional(),
  category: TemplateCategorySchema.optional(),
  base_html: z.string().optional(),
  base_css: z.string().optional(),
  base_js: z.string().optional(),
  is_system_template: z.boolean().default(false),
  is_active: z.boolean().default(true),
  is_public: z.boolean().default(false),
  generation_prompt: z.string().optional(),
  style_config: StyleConfigSchema.optional(),
  sections_config: z.object({
    sections: z.array(TemplateSectionSchema),
  }),
  content_schema: ContentSchemaSchema.optional(),
  tags: z.array(z.string()).optional(),
  use_count: z.number().int().nonnegative().default(0),
  generation_status: GenerationStatusSchema,
  generation_error: z.string().optional(),
  created_at: z.string().datetime(),
  updated_at: z.string().datetime(),
});

/**
 * Template Content Schema (flexible)
 */
export const TemplateContentSchema = z.record(z.string(),
  z.union([
    z.string(),
    z.array(z.unknown()),
    z.record(z.string(), z.unknown()),
  ])
);

/**
 * Rendered Template Schema
 */
export const RenderedTemplateSchema = z.object({
  html: z.string(),
  css: z.string(),
  js: z.string().optional(),
});

/**
 * Template Generation Request Schema
 */
export const TemplateGenerationRequestSchema = z.object({
  prompt: z.string().min(10).max(1000),
  user_id: z.string().uuid(),
  style_preferences: z.object({
    colorScheme: z.string().optional(),
    typography: z.string().optional(),
    layout: z.string().optional(),
  }).optional(),
  category: TemplateCategorySchema.optional(),
  tags: z.array(z.string()).optional(),
});

/**
 * Template Generation Response Schema
 */
export const TemplateGenerationResponseSchema = z.object({
  template_id: z.string().uuid(),
  status: GenerationStatusSchema,
  message: z.string().optional(),
  error: z.string().optional(),
});

/**
 * Content Generation Request Schema
 */
export const ContentGenerationRequestSchema = z.object({
  prompt: z.string().min(10).max(2000),
  template_id: z.string().uuid(),
  user_id: z.string().uuid(),
});

/**
 * Content Generation Response Schema
 */
export const ContentGenerationResponseSchema = z.object({
  project_id: z.string().uuid(),
  status: GenerationStatusSchema,
  content: TemplateContentSchema.optional(),
  rendered: RenderedTemplateSchema.optional(),
  message: z.string().optional(),
  error: z.string().optional(),
});

/**
 * Component Library Item Schema
 */
export const ComponentLibraryItemSchema = z.object({
  name: z.string(),
  description: z.string(),
  tags: z.array(z.string()),
  preview_url: z.string().url().nullable().optional(),
});

/**
 * Component Library Schema
 */
export const ComponentLibrarySchema = z.record(
  ComponentTypeSchema,
  z.record(z.string(), ComponentLibraryItemSchema)
);

/**
 * Validation helper functions
 */

/**
 * Validate component structure
 */
export function validateComponent(component: unknown) {
  try {
    ComponentVariationSchema.parse(component);
    return { valid: true, errors: [] };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return {
        valid: false,
        errors: error.issues.map((e) => `${e.path.join('.')}: ${e.message}`),
      };
    }
    return {
      valid: false,
      errors: ['Unknown validation error'],
    };
  }
}

/**
 * Validate template structure
 */
export function validateTemplate(template: unknown) {
  try {
    TemplateSchema.parse(template);
    return { valid: true, errors: [] };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return {
        valid: false,
        errors: error.issues.map((e) => `${e.path.join('.')}: ${e.message}`),
      };
    }
    return {
      valid: false,
      errors: ['Unknown validation error'],
    };
  }
}

/**
 * Validate template content against schema
 */
export function validateTemplateContent(
  content: unknown,
  schema: z.infer<typeof ContentSchemaSchema>
) {
  const errors: string[] = [];
  const warnings: string[] = [];

  if (typeof content !== 'object' || content === null) {
    return {
      valid: false,
      errors: ['Content must be an object'],
      warnings: [],
    };
  }

  const contentObj = content as Record<string, unknown>;

  // Check required fields
  for (const [field, binding] of Object.entries(schema.required_fields)) {
    if (binding.required && !(field in contentObj)) {
      errors.push(`Missing required field: ${field}`);
    }
  }

  // Check field types
  for (const [field, value] of Object.entries(contentObj)) {
    const binding =
      schema.required_fields[field] || schema.optional_fields?.[field];

    if (!binding) {
      warnings.push(`Unknown field: ${field}`);
      continue;
    }

    // Basic type checking
    if (binding.type === 'email' && typeof value === 'string') {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(value)) {
        errors.push(`Invalid email format: ${field}`);
      }
    } else if (binding.type === 'url' && typeof value === 'string') {
      try {
        new URL(value);
      } catch {
        errors.push(`Invalid URL format: ${field}`);
      }
    } else if (binding.type === 'array' && !Array.isArray(value)) {
      errors.push(`Field ${field} must be an array`);
    }
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
  };
}

/**
 * Validate sections config
 */
export function validateSectionsConfig(sections: unknown) {
  try {
    z.array(TemplateSectionSchema).parse(sections);
    return { valid: true, errors: [] };
  } catch (error) {
    if (error instanceof z.ZodError) {
      return {
        valid: false,
        errors: error.issues.map((e) => `${e.path.join('.')}: ${e.message}`),
      };
    }
    return {
      valid: false,
      errors: ['Unknown validation error'],
    };
  }
}

/**
 * Check if component placeholders match content bindings
 */
export function validatePlaceholders(html: string, bindings: Record<string, unknown>): {
  valid: boolean;
  errors: string[];
  warnings: string[];
} {
  const errors: string[] = [];
  const warnings: string[] = [];

  // Find all placeholders in HTML
  const placeholderRegex = /\{\{(\w+(?:\.\w+)?)\}\}/g;
  const placeholders = new Set<string>();
  let match;

  while ((match = placeholderRegex.exec(html)) !== null) {
    placeholders.add(match[1]);
  }

  // Check if all placeholders have bindings
  for (const placeholder of placeholders) {
    const key = placeholder.split('.')[0]; // Get root key for nested placeholders
    if (!(key in bindings)) {
      errors.push(`Placeholder {{${placeholder}}} not defined in content_bindings`);
    }
  }

  // Check if all bindings are used
  for (const binding of Object.keys(bindings)) {
    if (!placeholders.has(binding) && !html.includes(`${binding}_item_start`)) {
      warnings.push(`Content binding '${binding}' is defined but not used in HTML`);
    }
  }

  return {
    valid: errors.length === 0,
    errors,
    warnings,
  };
}

/**
 * Export all schemas for external use
 */
export const schemas = {
  ContentBinding: ContentBindingSchema,
  ComponentConfig: ComponentConfigSchema,
  ComponentVariation: ComponentVariationSchema,
  ComponentType: ComponentTypeSchema,
  TemplateSection: TemplateSectionSchema,
  StyleConfig: StyleConfigSchema,
  ContentSchema: ContentSchemaSchema,
  TemplateCategory: TemplateCategorySchema,
  GenerationStatus: GenerationStatusSchema,
  Template: TemplateSchema,
  TemplateContent: TemplateContentSchema,
  RenderedTemplate: RenderedTemplateSchema,
  TemplateGenerationRequest: TemplateGenerationRequestSchema,
  TemplateGenerationResponse: TemplateGenerationResponseSchema,
  ContentGenerationRequest: ContentGenerationRequestSchema,
  ContentGenerationResponse: ContentGenerationResponseSchema,
  ComponentLibraryItem: ComponentLibraryItemSchema,
  ComponentLibrary: ComponentLibrarySchema,
};

