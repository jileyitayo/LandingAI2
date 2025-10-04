# Component Library (Frontend)

## Quick Start

```typescript
import ComponentPreview from '@/components/ComponentPreview';
import { ComponentVariation } from '@/lib/components/types';
import { validateComponent, validateTemplate } from '@/lib/components/schema';

// Preview a component
const component: ComponentVariation = { /* ... */ };
const content = { headline: "Hello", subheadline: "World" };

<ComponentPreview 
  component={component} 
  content={content}
  showControls={true}
/>

// Validate data
const validation = validateComponent(component);
if (!validation.valid) {
  console.error(validation.errors);
}
```

## Files

- **types.ts** - TypeScript type definitions
- **schema.ts** - Zod validation schemas and helpers
- **README.md** - This file

## Component Preview

The `ComponentPreview` component renders components in a sandboxed iframe:

```tsx
<ComponentPreview
  component={variation}
  content={contentData}
  showControls={true}
  scale={1}
  width="100%"
  height="auto"
/>
```

## Validation

```typescript
import { validateTemplate, validateTemplateContent } from '@/lib/components/schema';

// Validate structure
const result = validateTemplate(templateData);

// Validate content
const contentResult = validateTemplateContent(content, template.content_schema);
```

## Documentation

See `/docs/COMPONENT_LIBRARY.md` for complete documentation.

