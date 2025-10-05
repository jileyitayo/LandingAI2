# AI Website Content Generation System

This document describes the AI-powered website content generation and rendering system built for SiteSmith.

## Overview

The content generation system uses OpenAI's GPT-4o-mini to automatically generate website content based on business descriptions and render complete websites using pre-designed templates. This is a template-based approach that separates template structure from content, enabling faster generation and better consistency.

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                    Generation Flow                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. User Prompt + Template Selection                       │
│                    ↓                                        │
│  2. Content Generator (OpenAI)                             │
│     - Extracts business info                               │
│     - Fills content schema                                 │
│     - Localizes for African market                         │
│                    ↓                                        │
│  3. Template Renderer                                       │
│     - Merges content with template                         │
│     - Replaces placeholders                                │
│     - Applies styles                                       │
│     - Generates HTML/CSS/JS                                │
│                    ↓                                        │
│  4. Complete Website                                        │
│     - Mobile-optimized                                     │
│     - WhatsApp integrated                                  │
│     - Production-ready                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Backend Services

### 1. Content Generator (`app/services/content_generator.py`)

**Purpose**: Generate website content using AI based on template requirements

**Key Features**:
- OpenAI GPT-4o-mini integration
- Template-aware content generation
- Content schema validation
- African market localization
- Business type detection

**Main Method**:
```python
async def generate_content(
    prompt: str,
    template_id: str,
    user_id: str
) -> Dict[str, Any]
```

**Process**:
1. Fetch template structure from database
2. Extract `sections_config`, `content_schema`, `style_config`
3. Build specialized system prompt for content generation
4. Call OpenAI API with business description
5. Parse and validate generated content
6. Return content matching content schema

**System Prompt Strategy**:
The AI is instructed to:
1. Extract business information (name, type, services, contact)
2. Generate content for each field in content_schema
3. Apply African market localization (WhatsApp, local payment methods)
4. Match tone to business type
5. Create compelling, conversion-focused copy
6. Ensure all required fields are filled

**Example Content Output**:
```json
{
  "content": {
    "business_name": "Tasty Bites Restaurant",
    "headline": "Authentic Nigerian Cuisine in Lagos",
    "subheadline": "Experience the flavors of home with our traditional dishes",
    "services": [
      {
        "title": "Jollof Rice Special",
        "description": "Our signature dish prepared with love",
        "icon": "utensils"
      }
    ],
    "business_email": "hello@tastybites.ng",
    "business_phone": "+234 803 123 4567",
    "whatsapp_number": "+2348031234567"
  },
  "metadata": {
    "business_type": "restaurant",
    "tone": "friendly",
    "target_audience": "Local food lovers and families"
  }
}
```

### 2. Template Renderer (`app/services/template_renderer.py`)

**Purpose**: Render complete websites by merging templates with content

**Key Features**:
- Component-based rendering
- Placeholder replacement ({{variable}})
- Array/loop handling ({{#items}}...{{/items}})
- CSS variable injection
- Style config application
- Mobile optimization
- HTML/CSS/JS minification
- WhatsApp float button integration

**Main Method**:
```python
def render_template(
    template: Dict[str, Any],
    content: Dict[str, Any]
) -> Dict[str, Any]
```

**Rendering Process**:
1. Sort sections by order
2. Render each section with component from library
3. Replace content placeholders
4. Apply style variables
5. Build complete HTML structure
6. Combine CSS (reset + base + components)
7. Add JavaScript utilities
8. Minify for production

**Placeholder System**:
- Simple: `{{business_name}}` → "Tasty Bites"
- Nested: `{{contact.email}}` → "hello@example.com"
- Arrays: `{{#services}}<div>{{title}}</div>{{/services}}`
- Config: `{{config.alignment}}` → "center"

**Output Structure**:
```json
{
  "html_content": "<!DOCTYPE html>...",
  "css_content": "/* Reset */ * { ... } /* Components */ ...",
  "js_content": "// Mobile menu ... // Smooth scroll ...",
  "metadata": {
    "sections_count": 7,
    "has_custom_js": true,
    "mobile_optimized": true
  }
}
```

### 3. AI Generator (`app/services/ai_generator.py`)

**Purpose**: Unified interface supporting both new and legacy flows

**Key Features**:
- Template-based generation (new flow)
- Legacy template generation (backwards compatibility)
- Content regeneration
- Prompt validation

**Flows**:

**New Flow** (Template-based):
```python
await ai_generator.generate_website(
    prompt="Restaurant serving Nigerian food",
    template_id="uuid-of-restaurant-template",
    user_id="user-uuid"
)
```

**Legacy Flow** (Template generation):
```python
await ai_generator.generate_website(
    prompt="Create a modern restaurant website",
    template_id=None,  # Triggers legacy flow
    user_id="user-uuid",
    style_preferences={"colors": {...}}
)
```

## API Endpoints

### Generation Router (`app/routers/generation.py`)

#### POST `/api/v1/generate`

Generate a complete website from prompt and template.

**Request**:
```json
{
  "prompt": "I run a small restaurant in Lagos serving traditional Nigerian food. We specialize in jollof rice, suya, and pepper soup. We offer dine-in and delivery via WhatsApp.",
  "template_id": "550e8400-e29b-41d4-a716-446655440000",
  "project_name": "Tasty Bites Website"
}
```

**Response** (202 Accepted):
```json
{
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "status": "generating",
  "message": "Website generation started. Check status endpoint for progress.",
  "html_preview_url": null
}
```

**Process**:
1. Validate template exists and is accessible
2. Check user rate limits (5/hour free, 100/hour pro)
3. Create project record in database
4. Increment generation count
5. Start background task for generation
6. Return project_id immediately

**Background Task**:
1. Generate content using `content_generator`
2. Fetch template structure
3. Render template using `template_renderer`
4. Save HTML/CSS/JS to project
5. Update status to "completed" or "failed"

#### GET `/api/v1/generation/{project_id}/status`

Check generation status.

**Response**:
```json
{
  "status": "completed",
  "project_id": "660e8400-e29b-41d4-a716-446655440001",
  "progress": 100,
  "message": "Website generated successfully",
  "error": null,
  "created_at": "2025-10-04T10:30:00Z",
  "completed_at": "2025-10-04T10:30:45Z"
}
```

**Status Values**:
- `idle`: Not started
- `generating`: In progress (30-60 seconds)
- `completed`: Successfully generated
- `failed`: Generation failed

#### GET `/api/v1/rate-limit`

Get current rate limit information.

**Response**:
```json
{
  "tier": "free",
  "limit": 5,
  "used": 2,
  "remaining": 3,
  "resets_at": "2025-10-04T11:30:00Z"
}
```

## Rate Limiting

### Implementation

Rate limits are stored in the `users` table:
- `current_period_generations`: Count in current period
- `current_period_start`: Period start timestamp
- `generation_count`: Total lifetime count

**Limits**:
- **Free tier**: 5 generations per hour
- **Pro tier**: 100 generations per hour

**Reset Logic**:
- Period: 1 hour (rolling)
- Automatic reset when period expires
- Counter resets to 0

**Rate Limit Headers**:
```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 3
X-RateLimit-Reset: 2025-10-04T11:30:00Z
```

**Error Response** (429 Too Many Requests):
```json
{
  "detail": "Rate limit exceeded. You have used 5/5 generations. Resets at 2025-10-04T11:30:00Z"
}
```

## Database Schema

### Projects Table (Updated)

```sql
CREATE TABLE public.projects (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id),
    name TEXT NOT NULL,
    description TEXT,
    prompt TEXT,  -- Original business description
    template_id TEXT,  -- Reference to template used
    
    -- Generated content
    html_content TEXT,
    css_content TEXT,
    js_content TEXT,
    
    -- Status tracking
    generation_status VARCHAR(20) DEFAULT 'idle',
    generation_error TEXT,
    last_generated_at TIMESTAMPTZ,
    
    -- ... other fields
);
```

### Users Table (Rate Limiting)

```sql
CREATE TABLE public.users (
    id UUID PRIMARY KEY,
    -- ... other fields
    
    -- Rate limiting
    generation_count INTEGER DEFAULT 0,  -- Total ever
    current_period_generations INTEGER DEFAULT 0,  -- Current period
    current_period_start DATE DEFAULT CURRENT_DATE,
    
    subscription_tier TEXT DEFAULT 'free',  -- 'free' | 'pro'
);
```

### RPC Function

```sql
CREATE FUNCTION increment_generation_count(user_id_param UUID)
RETURNS void AS $$
BEGIN
    UPDATE users
    SET 
        current_period_generations = current_period_generations + 1,
        generation_count = generation_count + 1
    WHERE id = user_id_param;
END;
$$ LANGUAGE plpgsql;
```

## African Market Optimization

### Localization Features

1. **WhatsApp Integration**:
   - Float button on all generated websites
   - WhatsApp number in international format
   - Click-to-chat functionality
   - Mobile-optimized placement

2. **Mobile-First Design**:
   - Responsive breakpoints
   - Touch-friendly buttons
   - Optimized images
   - Fast loading (minified assets)

3. **Content Localization**:
   - Local language greetings
   - Cultural references
   - Local payment methods (when relevant)
   - African business context

4. **Contact Methods**:
   - WhatsApp (primary)
   - Phone numbers in local format
   - Email
   - Physical location (if provided)

### Example Generated Content

For a restaurant:
```
Headline: "Authentic Nigerian Cuisine in the Heart of Lagos"
CTA: "Order via WhatsApp" → Opens WhatsApp chat
Phone: "+234 803 123 4567"
WhatsApp: "+2348031234567"
```

## Error Handling

### Content Generation Errors

```python
class ContentGenerationError(Exception):
    """Raised when content generation fails"""
    pass
```

**Common Errors**:
- Template not found
- OpenAI API failure
- Invalid content schema
- Missing required fields
- Rate limit exceeded

### Template Rendering Errors

```python
class TemplateRenderError(Exception):
    """Raised when template rendering fails"""
    pass
```

**Common Errors**:
- Component not found
- Invalid placeholder syntax
- Missing content fields
- CSS/JS processing errors

## Usage Examples

### Generate Website (Python)

```python
from app.services.ai_generator import ai_generator

# Generate website with template
result = await ai_generator.generate_website(
    prompt="""
    I own a beauty salon in Accra called "Glam Beauty".
    We offer hair styling, manicures, pedicures, and makeup.
    We serve walk-ins and appointments via WhatsApp.
    Contact: +233 20 123 4567
    """,
    template_id="beauty-salon-template-uuid",
    user_id="user-uuid"
)

print(result["html_content"])  # Complete HTML
print(result["css_content"])   # Complete CSS
print(result["js_content"])    # Complete JS
```

### Generate Website (API)

```bash
curl -X POST https://api.sitesmith.app/api/v1/generate \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Fashion boutique in Nairobi selling African prints",
    "template_id": "boutique-template-uuid",
    "project_name": "AfriStyles Boutique"
  }'
```

### Check Status

```bash
curl -X GET https://api.sitesmith.app/api/v1/generation/{project_id}/status \
  -H "Authorization: Bearer $TOKEN"
```

## Performance

### Generation Time

- **Content Generation**: 10-20 seconds
- **Template Rendering**: 1-3 seconds
- **Total**: 15-25 seconds average

### Optimization Techniques

1. **Background Processing**: Generation runs asynchronously
2. **Minification**: HTML/CSS/JS are minified
3. **Caching**: Component library cached in memory
4. **Lazy Loading**: Images loaded on demand
5. **Mobile Optimization**: Responsive images, touch events

## Testing

### Test Content Generation

```python
import pytest
from app.services.content_generator import content_generator

@pytest.mark.asyncio
async def test_content_generation():
    result = await content_generator.generate_content(
        prompt="Small bakery in Lagos",
        template_id="test-template-id",
        user_id="test-user-id"
    )
    
    assert "content" in result
    assert "business_name" in result["content"]
    assert result["content"]["business_name"]
```

### Test Template Rendering

```python
from app.services.template_renderer import template_renderer

def test_template_rendering():
    template = {
        "sections_config": {...},
        "style_config": {...}
    }
    content = {"business_name": "Test Business"}
    
    result = template_renderer.render_template(template, content)
    
    assert "html_content" in result
    assert "Test Business" in result["html_content"]
```

### Test Rate Limiting

```python
@pytest.mark.asyncio
async def test_rate_limit():
    # Make 5 requests (free tier limit)
    for i in range(5):
        response = await client.post("/api/v1/generate", json={...})
        assert response.status_code == 202
    
    # 6th request should be rate limited
    response = await client.post("/api/v1/generate", json={...})
    assert response.status_code == 429
```

## Migration Path

### From Legacy System

If you have existing projects using the old template generation system:

1. **Identify Legacy Projects**: Projects without `template_id`
2. **Extract Content**: Parse existing HTML for content
3. **Match to Template**: Find suitable template
4. **Regenerate**: Use new system with extracted content

```python
# Migration script example
async def migrate_legacy_project(project_id: str):
    project = await fetch_project(project_id)
    
    if not project["template_id"]:
        # Legacy project
        content = extract_content_from_html(project["html_content"])
        template_id = find_matching_template(project["category"])
        
        # Regenerate using new system
        result = await ai_generator.generate_website(
            prompt=reconstruct_prompt(content),
            template_id=template_id,
            user_id=project["user_id"]
        )
        
        await update_project(project_id, result)
```

## Future Enhancements

1. **Multi-language Support**: Generate content in multiple African languages
2. **Custom Fonts**: Support for local fonts and typography
3. **Advanced Styling**: More granular style customization
4. **A/B Testing**: Generate multiple variations
5. **SEO Optimization**: Automatic meta tags and structured data
6. **Analytics Integration**: Built-in analytics code
7. **Performance Monitoring**: Track generation times and success rates
8. **Content Editing**: Allow manual content editing post-generation

## Troubleshooting

### Common Issues

**Issue**: "Template not found"
- **Solution**: Verify template_id is correct and template is active

**Issue**: "Rate limit exceeded"
- **Solution**: Wait for rate limit reset or upgrade to Pro tier

**Issue**: "Content generation timeout"
- **Solution**: Retry request, OpenAI API may be slow

**Issue**: "Missing required fields"
- **Solution**: Check content_schema matches template requirements

## Support

For issues or questions:
- Documentation: `/docs/AI_CONTENT_GENERATION_SYSTEM.md`
- API Docs: `https://api.sitesmith.app/docs`
- Logs: Check application logs for detailed error messages

