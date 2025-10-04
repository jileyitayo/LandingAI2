# AI Template Generation System

This document describes the AI-powered template generation system built for SiteSmith.

## Overview

The template generation system uses OpenAI's GPT-4 to automatically create website templates based on natural language descriptions. Users describe their business needs, and the AI selects appropriate components from the component library, customizes styles, and generates a complete template structure.

## Architecture

### Backend Components

#### 1. Template Generator Service (`app/services/template_generator.py`)

**Purpose**: Core template generation logic using OpenAI API

**Key Features**:
- OpenAI GPT-4 integration for template generation
- Few-shot learning using component samples
- Structured JSON output validation
- Preview HTML generation
- Error handling and retry logic

**Main Method**:
```python
generate_template(prompt: str, user_id: str, style_preferences: dict) -> dict
```

**System Prompt Strategy**:
The AI is instructed to:
1. Analyze business type from prompt
2. Select 4-7 appropriate sections from component library
3. Choose variations that fit the style
4. Generate `sections_config` JSON structure
5. Create `content_schema` defining required fields
6. Extract `style_config` (colors, fonts, spacing)

#### 2. Template Validator Service (`app/services/template_validator.py`)

**Purpose**: Validate generated template structures

**Key Functions**:
- `validate_template_structure()` - Complete template validation
- `validate_sections_config()` - Section configuration validation
- `validate_style_config()` - Style configuration validation
- `validate_content_schema()` - Content schema validation
- `validate_content_bindings()` - Cross-validate content requirements

**Validation Rules**:
- Required sections: header, hero, footer
- Maximum 12 sections per template
- Valid component types and variations only
- Required colors: primary, text, background
- Valid hex color codes
- All required content bindings must be present

#### 3. Templates Router (`app/routers/templates.py`)

**Purpose**: API endpoints for template operations

**Endpoints**:

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/templates/generate` | Generate new template from prompt |
| GET | `/api/v1/templates` | List templates (system + user's) |
| GET | `/api/v1/templates/{id}` | Get specific template |
| PATCH | `/api/v1/templates/{id}` | Update user template |
| DELETE | `/api/v1/templates/{id}` | Delete user template |
| GET | `/api/v1/templates/{id}/status` | Check generation status |

**Rate Limiting**:
- 3 template generations per hour for free tier users
- In-memory rate limiter (can be upgraded to Redis)

**Request/Response Models**:
- `GenerateTemplateRequest` - Input validation
- `TemplateResponse` - Complete template data
- `TemplateListItem` - Simplified list view
- `GenerationStatus` - Status checking
- `UpdateTemplateRequest` - Template updates

### Frontend Components

#### 1. Template Generation Hook (`hooks/useTemplateGeneration.ts`)

**Purpose**: Custom React hook for template generation state management

**Features**:
- Template generation API calls
- Status polling (for async generation)
- Error handling with retry logic
- Loading states
- Generated template state

**API**:
```typescript
const {
  generateTemplate,
  checkStatus,
  isGenerating,
  error,
  generatedTemplate,
  clearError
} = useTemplateGeneration();
```

#### 2. Template Generation Modal (`components/TemplateGenerationModal.tsx`)

**Purpose**: User interface for template generation

**Features**:
- Prompt input with character count (10-1000 chars)
- Example prompts for inspiration
- Business category selector
- Primary color picker
- Multi-stage UI (input → generating → preview)
- Progress indicators with stages
- Error display with helpful messages
- Generated template preview

**Stages**:
1. **Input** - User enters prompt and preferences
2. **Generating** - Shows progress with animated indicators
3. **Preview** - Displays generated template info
4. **Success** - Option to use template or generate another

**Prompt Examples**:
- "Modern restaurant with warm colors, menu showcase, and online ordering"
- "Professional consultancy with trust-building elements"
- "Creative portfolio with large image galleries"
- "Local artisan shop with product showcase and WhatsApp ordering"
- "Fitness studio with class schedules and membership options"
- "Real estate agency with property listings and contact forms"

#### 3. Dashboard Integration (`app/dashboard/page.tsx`)

**Updates**:
- Added "Generate with AI" button (primary action)
- "Browse Templates" button (secondary action)
- Modal integration with state management
- Responsive button layout

## Template Generation Flow

### 1. User Input
```
User describes website → Frontend validation → API request
```

### 2. Backend Processing
```
Rate limit check → OpenAI API call → JSON parsing → 
Structure validation → Preview generation → Database storage
```

### 3. Frontend Display
```
Poll status → Display preview → Navigate to editor
```

## Template Structure

A generated template contains:

```typescript
{
  id: string,
  name: string,
  description: string,
  sections_config: [
    {
      component_type: "header",
      variation: "logo-left",
      order: 0,
      config: {}
    },
    // ... more sections
  ],
  style_config: {
    colors: {
      primary: "#6366f1",
      secondary: "#8b5cf6",
      text: "#1f2937",
      heading: "#111827",
      background: "#ffffff",
      border: "#e5e7eb"
    },
    typography: {
      fontFamily: "'Inter', sans-serif",
      fontSize: "16px",
      lineHeight: "1.5"
    },
    spacing: {
      containerMaxWidth: "1200px",
      sm: "1rem",
      md: "1.5rem",
      lg: "2rem"
    }
  },
  content_schema: {
    business_name: {
      type: "text",
      required: true,
      placeholder: "Your Business Name"
    },
    // ... more content fields
  },
  preview_html: string,
  category: string,
  tags: string[],
  is_public: boolean,
  created_by: string,
  created_at: string
}
```

## Testing

### Backend Tests (`tests/test_template_generation.py`)

**Test Coverage**:

1. **Template Validator Tests**
   - Valid sections config
   - Missing required sections
   - Invalid component types
   - Empty sections
   - Valid style config
   - Missing required colors
   - Invalid hex colors
   - Valid content schema
   - Empty content schema
   - Invalid content types
   - Complete template structure

2. **Template Generator Tests**
   - Successful generation
   - Missing API key
   - Invalid JSON response
   - Component samples preparation
   - CSS variables generation

3. **Integration Tests**
   - Full generation flow

**Running Tests**:
```bash
cd backend
pytest tests/test_template_generation.py -v
```

## Configuration

### Environment Variables

Add to `.env` file:
```bash
# Required for template generation
OPENAI_API_KEY=your_openai_api_key_here
```

### OpenAI Settings

- Model: `gpt-4-turbo-preview`
- Temperature: `0.7`
- Max Tokens: `4000`
- Response Format: `json_object`

## Usage Examples

### Backend API

#### Generate Template
```bash
curl -X POST http://localhost:8000/api/v1/templates/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Modern restaurant with warm colors and menu showcase",
    "style_preferences": {
      "primaryColor": "#d97706"
    }
  }'
```

#### List Templates
```bash
curl http://localhost:8000/api/v1/templates \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Get Template
```bash
curl http://localhost:8000/api/v1/templates/{template_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Frontend

#### Using the Hook
```typescript
import { useTemplateGeneration } from '@/hooks/useTemplateGeneration';

function MyComponent() {
  const { generateTemplate, isGenerating, error } = useTemplateGeneration();

  const handleGenerate = async () => {
    const template = await generateTemplate({
      prompt: "Modern restaurant website",
      style_preferences: { primaryColor: "#d97706" }
    });
    
    if (template) {
      console.log("Template generated:", template.id);
    }
  };

  return (
    <button onClick={handleGenerate} disabled={isGenerating}>
      {isGenerating ? "Generating..." : "Generate Template"}
    </button>
  );
}
```

## Error Handling

### Rate Limiting
- **Error**: 429 Too Many Requests
- **Message**: "Rate limit exceeded. You have X generations remaining this hour."
- **Solution**: Wait until rate limit resets

### Invalid Prompt
- **Error**: 400 Bad Request
- **Message**: "Invalid request. Please check your prompt and try again."
- **Solution**: Ensure prompt is 10-1000 characters

### OpenAI API Errors
- **Error**: 500 Internal Server Error
- **Message**: "AI generation failed: [error details]"
- **Solution**: Check OpenAI API key and quota

### Validation Errors
- **Error**: 400 Bad Request
- **Message**: "Invalid template structure: [specific error]"
- **Solution**: Template failed validation; retry generation

## Future Enhancements

### Planned Features
1. **Async Generation**: Background task processing with WebSocket updates
2. **Template Variations**: Generate multiple variations from single prompt
3. **Style Transfer**: Apply styles from existing templates
4. **Component Recommendations**: AI suggestions for additional sections
5. **A/B Testing**: Generate alternative versions for testing
6. **Industry Templates**: Pre-trained models for specific industries
7. **Multi-language Support**: Generate templates in different languages
8. **Image Generation**: AI-generated placeholder images
9. **Content Generation**: AI-written sample content for sections

### Technical Improvements
1. **Redis Rate Limiting**: Distributed rate limiting
2. **Caching**: Cache component samples and common generations
3. **Monitoring**: Track generation success rates and errors
4. **Analytics**: User prompt analysis and improvement
5. **Version Control**: Track template versions and changes

## Troubleshooting

### Common Issues

#### 1. OpenAI API Key Not Set
```
Error: "OpenAI API key not configured"
Solution: Add OPENAI_API_KEY to .env file
```

#### 2. Rate Limit Exceeded
```
Error: "Rate limit exceeded"
Solution: Wait 1 hour or upgrade subscription tier
```

#### 3. Invalid Component Reference
```
Error: "Variation 'xyz' not found for component 'header'"
Solution: Check component_samples.json for available variations
```

#### 4. Missing Required Content Bindings
```
Error: "Missing required content bindings: logo_url"
Solution: Ensure content_schema includes all required fields from components
```

## Performance Metrics

### Expected Performance
- **Generation Time**: 5-15 seconds (depends on OpenAI API)
- **Success Rate**: >95% (with proper validation)
- **Rate Limit**: 3 generations/hour (free tier)
- **Token Usage**: ~2000-3000 tokens per generation

### Optimization Tips
1. Cache component samples in memory
2. Reuse OpenAI client connections
3. Implement request batching for multiple templates
4. Use background workers for async generation

## Security Considerations

### Authentication
- All endpoints require valid JWT token
- User ID extracted from authenticated session

### Authorization
- Users can only update/delete their own templates
- Public templates visible to all authenticated users

### Input Validation
- Prompt length limits (10-1000 chars)
- Style preferences validation
- Component type whitelisting
- SQL injection prevention (using Supabase client)

### Rate Limiting
- Per-user rate limits
- Prevents API abuse
- Configurable limits per subscription tier

## Monitoring and Logging

### Logged Events
- Template generation started
- Template generated successfully
- Template generation failed
- Template updated
- Template deleted
- Rate limit exceeded

### Metrics to Track
- Generation success rate
- Average generation time
- Most common business types
- Component usage frequency
- Error rates by type

## Contributing

When adding new features:

1. Update validation rules in `template_validator.py`
2. Add new tests in `test_template_generation.py`
3. Update API documentation
4. Update this document

## API Documentation

Full API documentation available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

