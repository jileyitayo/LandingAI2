# React Website Generator - Usage Guide

## Overview

The refactored React website generator provides a clean, modular architecture for generating complete React/TypeScript projects with full shadcn/ui components.

## Architecture

```
react_models.py              # Pydantic models
    ↓
react_website_generator.py   # Core generation logic
    ↓
react_file_manager.py        # File generation
    ↓
Generated React Project      # Complete, deployable project
```

## Quick Start

### 1. Basic Usage

```python
from app.services.react_website_generator import react_website_generator

# Generate a complete React website
result = react_website_generator.generate_website_structure(
    prompt="Create a modern website for a coffee shop with home, menu, and contact pages"
)

# Result contains:
# - website_structure: Complete site structure
# - business_analysis: Business requirements analysis
# - files: Dictionary of all generated files
```

### 2. API Endpoint Usage

**Generate React Website:**
```bash
POST /api/generate_react_website
Content-Type: application/json
Authorization: Bearer <token>

{
  "prompt": "Create a website for my photography studio",
  "project_name": "My Portfolio"
}
```

**Response:**
```json
{
  "project_id": "uuid-here",
  "status": "processing",
  "message": "React website generation started"
}
```

**Get Generated Website:**
```bash
GET /api/react_website/{project_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "project_id": "uuid-here",
  "website_structure": { ... },
  "business_analysis": { ... },
  "files": {
    "package.json": "...",
    "src/App.tsx": "...",
    "src/components/ui/button.tsx": "...",
    ...
  },
  "files_count": 35
}
```

## Generated Project Structure

Every generated project includes:

### Configuration Files (10 files)
- `package.json` - All dependencies configured
- `vite.config.ts` - Vite with path aliases
- `tsconfig.json` - Base TypeScript config
- `tsconfig.app.json` - App-specific config
- `tsconfig.node.json` - Node-specific config
- `tailwind.config.js` - Complete theme
- `postcss.config.js` - PostCSS setup
- `index.html` - Entry HTML
- `.gitignore` - Proper ignores
- `README.md` - Project documentation

### UI Components (5 files)
- `src/components/ui/button.tsx` - Full Button component
- `src/components/ui/card.tsx` - Complete Card component
- `src/components/ui/input.tsx` - Input component
- `src/components/ui/textarea.tsx` - Textarea component
- `src/lib/utils.ts` - Utility functions

### App Files (2 files)
- `src/App.tsx` - Main app with routing
- `src/main.tsx` - Entry point

### Styling (1 file)
- `src/index.css` - Tailwind with design tokens

### Dynamic Files
- `src/pages/*.tsx` - Generated based on business analysis
- `src/components/*.tsx` - Section components (Hero, Features, Contact, etc.)

## Component Types Available

The generator automatically creates these components based on your prompt:

| Component | Purpose | Props Example |
|-----------|---------|---------------|
| **Hero** | Main hero section with CTA | `title, subtitle, primaryCta` |
| **Features** | Grid of features/services | `title, features[]` |
| **About** | About section | `story, mission, vision` |
| **Contact** | Contact form + info | `email, phone, address` |
| **Testimonials** | Customer testimonials | `testimonials[]` |
| **CTA** | Call-to-action | `title, description, primaryCta` |
| **Stats** | Statistics/numbers | `stats[]` |

## Working with Generated Files

### Option 1: Download as ZIP
```python
import zipfile
from io import BytesIO

def create_project_zip(files: dict) -> BytesIO:
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path, content in files.items():
            zip_file.writestr(file_path, content)
    zip_buffer.seek(0)
    return zip_buffer
```

### Option 2: Write to Filesystem
```python
import os

def write_project_to_disk(files: dict, output_dir: str):
    for file_path, content in files.items():
        full_path = os.path.join(output_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
```

### Option 3: Deploy to Vercel
```python
from app.services.deployment import vercel_deployment

# Deploy generated files
deployment = vercel_deployment.deploy_project(
    project_name="my-coffee-shop",
    files=result["files"]
)
```

## Customization

### Adding New UI Components

1. **Add to `react_file_manager.py`:**
```python
def generate_ui_components(self):
    files = {}
    
    # ... existing components ...
    
    # Add new component
    files["src/components/ui/dialog.tsx"] = """
    // Your Dialog component here
    """
    
    return files
```

2. **Use in templates:**
```python
# In react_website_generator.py
imports.append("import { Dialog } from '@/components/ui/dialog'")
```

### Customizing Color Schemes

Colors are mapped in `react_file_manager.generate_style_files()`:
```python
color_map = {
    "blue": "221.2 83.2% 53.3%",
    "indigo": "239 84% 67%",
    "emerald": "142.1 76.2% 36.3%",
    # Add your custom colors
    "brand": "280 70% 55%",  # Custom brand color
}
```

### Adding New Section Components

1. **Add template method in `react_website_generator.py`:**
```python
def _get_pricing_template(self, comp_type: str, structure: WebsiteStructure) -> str:
    return """
    // Your pricing component template
    """
```

2. **Register in templates dict:**
```python
templates = {
    "hero": self._get_hero_template,
    "features": self._get_features_template,
    "pricing": self._get_pricing_template,  # New
    # ...
}
```

## Testing

### Unit Tests
```bash
cd backend
python3 tests/test_react_refactoring.py
```

### Integration Test
```bash
python3 tests/example_react_generation.py
```

### Full Test Suite
```bash
pytest tests/test_react_generation.py -v
```

## Debugging

### Enable Detailed Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now generate - you'll see detailed logs
result = react_website_generator.generate_website_structure(prompt)
```

### Inspect Generated Files
```python
result = react_website_generator.generate_website_structure(prompt)

# Check what files were generated
print(f"Generated {len(result['files'])} files:")
for filepath in sorted(result['files'].keys()):
    print(f"  - {filepath}")

# Inspect specific file
print(result['files']['src/components/ui/button.tsx'][:500])
```

### Validate Structure
```python
from app.services.react_models import WebsiteStructure

# Validate the structure
structure = WebsiteStructure(**result['website_structure'])
print(f"Website: {structure.name}")
print(f"Pages: {len(structure.pages)}")
for page in structure.pages:
    print(f"  - {page.name} ({page.path}): {len(page.components)} components")
```

## Best Practices

### 1. Prompts
- ✅ Be specific about business type and pages needed
- ✅ Mention desired features (contact form, testimonials, etc.)
- ✅ Include tone and style preferences
- ❌ Don't be too vague ("create a website")

**Good Prompt:**
```
Create a professional website for a boutique law firm specializing in family law. 
Include home, about, services, testimonials, and contact pages. 
The tone should be professional yet warm and approachable.
```

**Bad Prompt:**
```
make a website
```

### 2. Rate Limiting
Implement appropriate rate limits based on user tier:
```python
RATE_LIMITS = {
    "free": 3,      # 3 generations per day
    "pro": 50,      # 50 generations per day
    "enterprise": 1000
}
```

### 3. Caching
Cache business analysis for similar prompts:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_business_analysis(prompt: str):
    return business_analyzer.generate_business_analysis(prompt)
```

### 4. Error Handling
Always handle generation errors gracefully:
```python
try:
    result = react_website_generator.generate_website_structure(prompt)
except Exception as e:
    logger.error(f"Generation failed: {e}")
    # Update project status to failed
    # Notify user
```

## Performance

### Generation Time
- Business Analysis: ~2-5 seconds
- Structure Generation: ~3-7 seconds
- File Generation: ~1-2 seconds
- **Total: ~6-14 seconds**

### Optimization Tips
1. Use background tasks for generation
2. Stream results if possible
3. Cache common components
4. Implement queue system for high load

## Deployment

### Generated Project Deployment

After generating files, users can:

1. **Local Development:**
```bash
npm install
npm run dev
```

2. **Build for Production:**
```bash
npm run build
```

3. **Deploy to Vercel:**
```bash
vercel deploy
```

## Support

### Common Issues

**Issue: Missing dependencies**
- Solution: Ensure all dependencies are in `package.json`

**Issue: Import paths not resolving**
- Solution: Check `vite.config.ts` has correct path aliases

**Issue: Tailwind classes not working**
- Solution: Verify `tailwind.config.js` content paths

**Issue: TypeScript errors**
- Solution: Check `tsconfig.json` includes correct paths

## Examples

See complete examples in:
- `backend/tests/example_react_generation.py`
- `backend/tests/test_react_generation.py`

## Migration from Old Version

If you have existing code using the old structure:

**Before:**
```python
# Old code works without changes
result = react_website_generator.generate_website_structure(prompt)
```

**After:**
```python
# Same code, but now generates full shadcn/ui components!
result = react_website_generator.generate_website_structure(prompt)

# Access new features
ui_files = {k: v for k, v in result['files'].items() if 'ui/' in k}
print(f"UI components: {len(ui_files)}")
```

No breaking changes! The refactoring maintains backward compatibility.

---

**Need Help?** Check:
- `REACT_REFACTORING_SUMMARY.md` - What changed
- `README_REACT_GENERATION.md` - Detailed system docs
- `REACT_GENERATION_SUMMARY.md` - Implementation summary

