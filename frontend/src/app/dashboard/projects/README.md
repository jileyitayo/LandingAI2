# Website Preview System - Usage Guide

## Quick Start

### 1. Navigate to Project Editor

From the dashboard, click on any project card to open the editor:

```tsx
// Dashboard page
import ProjectCard from '@/components/ProjectCard';

const projects = await fetchProjects();

return (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
    {projects.map((project) => (
      <ProjectCard key={project.id} project={project} />
    ))}
  </div>
);
```

### 2. Editor URL Structure

```
/dashboard/projects/[id]
```

Example: `/dashboard/projects/abc-123-def-456`

## Features

### Editor Features

1. **Split View Layout**
   - Left: Code editor (HTML/CSS/JS tabs)
   - Right: Live preview with responsive controls

2. **Code Editor**
   - Syntax-friendly monospace font
   - Tab support (2 spaces)
   - Line count display
   - Auto-updating preview

3. **Preview Panel**
   - Sandboxed iframe for security
   - Desktop/Tablet/Mobile views
   - Fullscreen mode
   - Manual refresh capability

4. **Save System**
   - Auto-detect unsaved changes
   - Manual save button
   - Loading states during save

5. **Download**
   - Export complete HTML file
   - Embedded CSS and JavaScript
   - Proper document structure

## Using the Components

### WebsitePreview Component

Basic usage:

```tsx
import WebsitePreview from '@/components/WebsitePreview';

function MyComponent() {
  const [html, setHtml] = useState('<h1>Hello</h1>');
  const [css, setCss] = useState('h1 { color: blue; }');
  const [js, setJs] = useState('console.log("Hello");');

  return (
    <WebsitePreview
      html={html}
      css={css}
      js={js}
      isLoading={false}
    />
  );
}
```

### useProjectEditor Hook

Complete example:

```tsx
import { useProjectEditor } from '@/hooks/useProjectEditor';
import { api } from '@/lib/api';

function ProjectEditor({ projectId }: { projectId: string }) {
  const {
    project,
    editorState,
    isLoading,
    isSaving,
    error,
    updateCode,
    setActiveTab,
    saveProject,
    downloadProject,
  } = useProjectEditor({
    projectId,
    onLoad: async (id) => {
      const response = await api.get(`/projects/${id}`);
      return response.data;
    },
    onSave: async (data) => {
      await api.put(`/projects/${projectId}`, data);
    },
  });

  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;

  const { html_content, css_content, js_content, activeTab, hasUnsavedChanges } = editorState;

  return (
    <div>
      {/* Editor tabs */}
      <div>
        <button onClick={() => setActiveTab('html_content')}>HTML</button>
        <button onClick={() => setActiveTab('css_content')}>CSS</button>
        <button onClick={() => setActiveTab('js_content')}>JavaScript</button>
      </div>

      {/* Code editor */}
      <textarea
        value={activeTab === 'html_content' ? html_content : activeTab === 'css_content' ? css_content : js_content}
        onChange={(e) => updateCode(e.target.value)}
      />

      {/* Actions */}
      <button
        onClick={() => saveProject()}
        disabled={!hasUnsavedChanges}
      >
        Save {hasUnsavedChanges && '*'}
      </button>
      <button onClick={downloadProject}>Download</button>

      {/* Preview */}
      <WebsitePreview html_content={html_content} css_content={css_content} js_content={js_content} />
    </div>
  );
}
```

### ProjectCard Component

Display projects in a grid:

```tsx
import ProjectCard from '@/components/ProjectCard';

function ProjectList({ projects }: { projects: Project[] }) {
  const handleDelete = async (id: string) => {
    await api.delete(`/projects/${id}`);
    // Refresh list
  };

  return (
    <div className="grid grid-cols-3 gap-6">
      {projects.map((project) => (
        <ProjectCard
          key={project.id}
          project={project}
          onDelete={handleDelete}
        />
      ))}
    </div>
  );
}
```

## API Integration

### Required Endpoints

#### 1. Get Project

```typescript
GET /api/projects/:id

Response:
{
  id: string;
  name: string;
  description?: string;
  html: string;
  css: string;
  js: string;
  user_id: string;
  created_at: string;
  updated_at: string;
  is_published?: boolean;
  preview_url?: string;
}
```

#### 2. Update Project

```typescript
PUT /api/projects/:id

Body:
{
  html?: string;
  css?: string;
  js?: string;
  name?: string;
  description?: string;
  is_published?: boolean;
}

Response: Updated Project
```

#### 3. Delete Project

```typescript
DELETE /api/projects/:id

Response:
{
  success: boolean;
}
```

#### 4. List Projects

```typescript
GET /api/projects

Query params:
- limit: number
- offset: number
- sort: 'created_at' | 'updated_at' | 'name'
- order: 'asc' | 'desc'

Response:
{
  projects: Project[];
  total: number;
  limit: number;
  offset: number;
}
```

### Example API Client

```typescript
// lib/api.ts
export const projectsApi = {
  async getProject(id: string): Promise<Project> {
    const response = await api.get(`/projects/${id}`);
    return response.data;
  },

  async updateProject(
    id: string,
    data: ProjectUpdateInput
  ): Promise<Project> {
    const response = await api.put(`/projects/${id}`, data);
    return response.data;
  },

  async deleteProject(id: string): Promise<void> {
    await api.delete(`/projects/${id}`);
  },

  async listProjects(params?: {
    limit?: number;
    offset?: number;
    sort?: string;
    order?: string;
  }): Promise<{ projects: Project[]; total: number }> {
    const response = await api.get('/projects', { params });
    return response.data;
  },
};
```

## Security Considerations

### 1. Iframe Sandbox

The preview uses these sandbox attributes:

```tsx
<iframe sandbox="allow-scripts allow-same-origin" />
```

**What this prevents:**
- Form submissions
- Pop-ups
- Navigation to other pages
- Accessing parent window (mostly)

**What this allows:**
- JavaScript execution
- Same-origin requests
- DOM manipulation within iframe

### 2. JavaScript Error Handling

All user JavaScript is wrapped in a try-catch:

```javascript
(function() {
  try {
    // User code here
  } catch (error) {
    console.error('Preview JavaScript Error:', error);
  }
})();
```

### 3. Content Injection

Content is injected safely via iframe document API:

```typescript
const iframeDoc = iframe.contentDocument;
iframeDoc.open();
iframeDoc.write(fullHTML);
iframeDoc.close();
```

### 4. XSS Prevention

- No direct DOM manipulation from user input
- Isolated iframe execution context
- No access to parent window storage/cookies

## Keyboard Shortcuts

Future enhancements could include:

- `Ctrl/Cmd + S` - Save
- `Ctrl/Cmd + Shift + P` - Preview mode
- `Ctrl/Cmd + /` - Comment code
- `Ctrl/Cmd + D` - Download

## Performance Optimization

### 1. Debounce Preview Updates

```tsx
import { useMemo } from 'react';
import { debounce } from 'lodash';

const debouncedUpdate = useMemo(
  () => debounce((code: string) => {
    updateCode(code);
  }, 300),
  []
);
```

### 2. Code Splitting

```tsx
import dynamic from 'next/dynamic';

const WebsitePreview = dynamic(
  () => import('@/components/WebsitePreview'),
  { ssr: false }
);
```

### 3. Lazy Loading

Only load editor when needed:

```tsx
const ProjectEditor = lazy(() => import('./ProjectEditor'));

function Page() {
  return (
    <Suspense fallback={<Loading />}>
      <ProjectEditor />
    </Suspense>
  );
}
```

## Troubleshooting

### Preview Not Updating

**Issue:** Changes don't reflect in preview

**Solutions:**
1. Check browser console for errors
2. Verify iframe is rendering
3. Check network tab for API errors
4. Ensure `refreshKey` is updating

### Save Not Working

**Issue:** Save button stays disabled

**Solutions:**
1. Check `hasUnsavedChanges` state
2. Verify API endpoint is correct
3. Check browser console for errors
4. Verify auth token is valid

### Fullscreen Not Working

**Issue:** Fullscreen button doesn't work

**Solutions:**
1. Check browser support for Fullscreen API
2. Ensure HTTPS (required for fullscreen)
3. Check for security errors in console
4. Test in different browser

## Best Practices

### 1. Auto-Save

Implement auto-save with debouncing:

```tsx
useEffect(() => {
  const timer = setTimeout(() => {
    if (editorState.hasUnsavedChanges) {
      saveProject();
    }
  }, 5000);

  return () => clearTimeout(timer);
}, [editorState.html, editorState.css, editorState.js]);
```

### 2. Keyboard Shortcuts

Add keyboard shortcuts for common actions:

```tsx
useEffect(() => {
  const handleKeyDown = (e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 's') {
      e.preventDefault();
      saveProject();
    }
  };

  window.addEventListener('keydown', handleKeyDown);
  return () => window.removeEventListener('keydown', handleKeyDown);
}, [saveProject]);
```

### 3. Unsaved Changes Warning

Warn users before leaving with unsaved changes:

```tsx
useEffect(() => {
  const handleBeforeUnload = (e: BeforeUnloadEvent) => {
    if (editorState.hasUnsavedChanges) {
      e.preventDefault();
      e.returnValue = '';
    }
  };

  window.addEventListener('beforeunload', handleBeforeUnload);
  return () => window.removeEventListener('beforeunload', handleBeforeUnload);
}, [editorState.hasUnsavedChanges]);
```

### 4. Version History

Track changes with version history:

```tsx
const [versions, setVersions] = useState<Version[]>([]);

const createVersion = () => {
  const version: Version = {
    id: generateId(),
    html: editorState.html,
    css: editorState.css,
    js: editorState.js,
    created_at: new Date().toISOString(),
  };
  setVersions([version, ...versions]);
};
```

## Testing

### Unit Tests

```typescript
import { render, fireEvent } from '@testing-library/react';
import WebsitePreview from './WebsitePreview';

test('renders HTML content in iframe', () => {
  const { container } = render(
    <WebsitePreview html="<h1>Test</h1>" />
  );
  const iframe = container.querySelector('iframe');
  expect(iframe).toBeInTheDocument();
});

test('switches viewport sizes', () => {
  const { getByTitle } = render(<WebsitePreview />);
  
  fireEvent.click(getByTitle('Mobile view'));
  // Assert mobile viewport active
  
  fireEvent.click(getByTitle('Desktop view'));
  // Assert desktop viewport active
});
```

### Integration Tests

```typescript
test('saves project changes', async () => {
  const mockSave = jest.fn();
  
  const { getByRole, getByText } = render(
    <ProjectEditorPage />
  );
  
  const editor = getByRole('textbox');
  fireEvent.change(editor, { target: { value: '<h1>New</h1>' } });
  
  const saveButton = getByText('Save');
  fireEvent.click(saveButton);
  
  await waitFor(() => {
    expect(mockSave).toHaveBeenCalledWith({
      html: '<h1>New</h1>',
      css: expect.any(String),
      js: expect.any(String),
    });
  });
});
```

## Future Enhancements

1. **Monaco Editor Integration** - Professional code editor with IntelliSense
2. **Real-time Collaboration** - Multiple users editing simultaneously
3. **Version Control** - Git-like version history
4. **Template Library** - Pre-built components and layouts
5. **Asset Management** - Upload and manage images/files
6. **SEO Tools** - Meta tags, Open Graph, structured data
7. **Performance Monitoring** - Lighthouse integration
8. **Deploy Integration** - One-click deploy to hosting providers

