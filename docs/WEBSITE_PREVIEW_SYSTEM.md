# Website Preview System

## Overview

A secure, sandboxed website preview system that allows users to edit and preview HTML, CSS, and JavaScript in real-time with a VS Code-inspired interface.

## Components

### 1. WebsitePreview Component

**Location:** `frontend/src/components/WebsitePreview.tsx`

A fully-featured iframe-based preview component with security and responsiveness built-in.

#### Features

- **Sandboxed iframe** with `allow-scripts` and `allow-same-origin` attributes
- **Responsive viewport toggles**: Desktop, Tablet (768x1024), Mobile (375x667)
- **Full-screen mode** with native browser fullscreen API
- **Refresh capability** to reload the preview
- **Safe content injection** with error handling wrapper for JavaScript
- **Loading states** with animated spinner

#### Security

The iframe uses the `sandbox` attribute with minimal permissions:
- `allow-scripts`: Allows JavaScript execution
- `allow-same-origin`: Allows content to be treated as same-origin (necessary for iframe manipulation)

JavaScript is wrapped in a try-catch block to prevent errors from breaking the preview.

#### Usage

```tsx
import WebsitePreview from '@/components/WebsitePreview';

<WebsitePreview
  html="<h1>Hello World</h1>"
  css="h1 { color: blue; }"
  js="console.log('Hello');"
  isLoading={false}
/>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `html` | `string` | `''` | HTML content to display |
| `css` | `string` | `''` | CSS styles to apply |
| `js` | `string` | `''` | JavaScript code to execute |
| `isLoading` | `boolean` | `false` | Shows loading spinner |

### 2. Project Editor Page

**Location:** `frontend/src/app/dashboard/projects/[id]/page.tsx`

A split-view editor page that provides a complete IDE-like experience for editing websites.

#### Features

- **Split-view layout**: Editor on the left (50%), preview on the right (50%)
- **Tabbed editor**: Switch between HTML, CSS, and JavaScript
- **Real-time preview**: Changes reflect immediately in the preview pane
- **Unsaved changes tracking**: Visual indicator and disabled save button
- **Auto-save capability**: Save button enabled when changes detected
- **Download functionality**: Export complete HTML file with embedded CSS/JS
- **VS Code-inspired theme**: Dark mode with syntax highlighting colors
- **Responsive design**: Adapts to different screen sizes

#### Editor Features

- Monospace font with proper tab sizing
- Line count display
- File encoding indicator (UTF-8)
- Active tab highlighting
- Code area with syntax-friendly styling

#### Navigation

The page integrates with the dashboard:
- Back button to return to dashboard
- Project name display in header
- Unsaved changes indicator

#### Usage

The page is accessed via dynamic route:
```
/dashboard/projects/[id]
```

Where `[id]` is the project ID.

### 3. useProjectEditor Hook

**Location:** `frontend/src/hooks/useProjectEditor.ts`

A custom React hook that manages editor state and project operations.

#### Features

- **State management** for editor content (HTML, CSS, JS)
- **Change tracking** to detect unsaved modifications
- **Async operations** for loading and saving projects
- **Error handling** with error state management
- **Loading states** for better UX
- **Download functionality** with proper file formatting

#### Usage

```tsx
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
  projectId: '123',
  onLoad: async (id) => {
    const response = await api.get(`/projects/${id}`);
    return response.data;
  },
  onSave: async (data) => {
    await api.put(`/projects/123`, data);
  },
});
```

#### API

| Property | Type | Description |
|----------|------|-------------|
| `project` | `Project \| null` | Current project data |
| `editorState` | `EditorState` | Current editor state (code, active tab, changes) |
| `isLoading` | `boolean` | Loading state |
| `isSaving` | `boolean` | Saving state |
| `error` | `string \| null` | Error message if any |
| `updateCode` | `(code: string) => void` | Update code for active tab |
| `setActiveTab` | `(tab: EditorTab) => void` | Switch editor tab |
| `saveProject` | `() => Promise<boolean>` | Save current changes |
| `downloadProject` | `() => void` | Download as HTML file |

### 4. Type Definitions

**Location:** `frontend/src/types/project.types.ts`

Complete TypeScript definitions for the project system.

#### Types

- `Project`: Complete project data structure
- `ProjectCreateInput`: Data required to create a project
- `ProjectUpdateInput`: Data that can be updated in a project
- `EditorTab`: Type for editor tabs ('html' | 'css' | 'js')
- `ViewportSize`: Type for viewport sizes ('desktop' | 'tablet' | 'mobile')
- `EditorState`: Internal editor state structure

## Security Considerations

### 1. Iframe Sandboxing

The preview uses iframe sandbox attributes to isolate potentially dangerous code:

```tsx
sandbox="allow-scripts allow-same-origin"
```

This prevents:
- Navigation to other pages
- Form submissions
- Pop-ups and new windows
- Access to parent window (with some exceptions for same-origin)

### 2. JavaScript Error Handling

All user-provided JavaScript is wrapped in a try-catch block:

```javascript
(function() {
  try {
    // User code here
  } catch (error) {
    console.error('Preview JavaScript Error:', error);
  }
})();
```

This prevents unhandled errors from breaking the preview.

### 3. Content Security Policy

Consider adding CSP headers in the future:
```html
<meta http-equiv="Content-Security-Policy" content="default-src 'self' 'unsafe-inline' 'unsafe-eval'">
```

### 4. XSS Protection

- All HTML content is injected via iframe document API
- No direct DOM manipulation from user input
- JavaScript runs in isolated iframe context

## Best Practices

### 1. Debouncing Updates

For performance, consider debouncing preview updates:

```tsx
const debouncedHtml = useDebounce(html, 300);
<WebsitePreview html={debouncedHtml} />
```

### 2. Auto-save

Implement auto-save with debouncing:

```tsx
useEffect(() => {
  const timer = setTimeout(() => {
    if (hasUnsavedChanges) {
      saveProject();
    }
  }, 5000); // Auto-save after 5 seconds of inactivity

  return () => clearTimeout(timer);
}, [html, css, js]);
```

### 3. Version History

Consider implementing version history:
- Save snapshots on each manual save
- Allow reverting to previous versions
- Show diff between versions

### 4. Collaboration

For real-time collaboration:
- Use WebSockets for syncing changes
- Show cursor positions of other users
- Implement conflict resolution

## Future Enhancements

1. **Code Editor Improvements**
   - Syntax highlighting (integrate Monaco Editor or CodeMirror)
   - Auto-completion
   - Error highlighting
   - Code formatting (Prettier integration)

2. **Preview Enhancements**
   - Console output display
   - Network request monitoring
   - Performance metrics
   - Screenshot capture

3. **Collaboration Features**
   - Real-time multi-user editing
   - Comments and annotations
   - Share preview links

4. **Advanced Security**
   - CSP header configuration
   - Resource usage limits
   - Malicious code detection

5. **Mobile Optimization**
   - Touch-friendly controls
   - Swipe gestures for switching views
   - Virtual keyboard optimization

## API Integration

### Backend Endpoints Needed

```typescript
// Get project by ID
GET /api/projects/:id
Response: Project

// Update project
PUT /api/projects/:id
Body: { html, css, js }
Response: Project

// Create project
POST /api/projects
Body: { name, description, html, css, js }
Response: Project

// Delete project
DELETE /api/projects/:id
Response: { success: boolean }
```

### Example Integration

```typescript
// In page.tsx
const loadProject = async (id: string) => {
  const response = await api.get(`/projects/${id}`);
  return response.data;
};

const saveProject = async (data: { html: string; css: string; js: string }) => {
  await api.put(`/projects/${id}`, data);
};

const { project, editorState, saveProject } = useProjectEditor({
  projectId,
  onLoad: loadProject,
  onSave: saveProject,
});
```

## Testing

### Unit Tests

```typescript
// Test WebsitePreview rendering
test('renders preview with HTML content', () => {
  render(<WebsitePreview html="<h1>Test</h1>" />);
  // Assert iframe is rendered
});

// Test viewport switching
test('switches between viewport sizes', () => {
  const { getByTitle } = render(<WebsitePreview />);
  fireEvent.click(getByTitle('Mobile view'));
  // Assert mobile viewport is active
});
```

### Integration Tests

```typescript
// Test editor and preview interaction
test('updates preview when code changes', async () => {
  const { getByRole, container } = render(<ProjectEditorPage />);
  const editor = getByRole('textbox');
  
  fireEvent.change(editor, { target: { value: '<h1>Updated</h1>' } });
  
  // Wait for preview update
  await waitFor(() => {
    const iframe = container.querySelector('iframe');
    // Assert iframe content updated
  });
});
```

## Troubleshooting

### Preview Not Updating

**Issue:** Changes in editor don't reflect in preview

**Solutions:**
1. Check if `refreshKey` is incrementing correctly
2. Verify iframe `contentDocument` is accessible
3. Ensure no CORS issues with embedded resources

### Fullscreen Not Working

**Issue:** Fullscreen button doesn't enter fullscreen mode

**Solutions:**
1. Check browser support for Fullscreen API
2. Ensure user interaction triggered the request (not programmatic)
3. Check browser console for security errors

### JavaScript Errors in Preview

**Issue:** JavaScript code causes preview to break

**Solutions:**
1. Check try-catch wrapper is present
2. Verify sandbox attributes are correct
3. Check browser console for specific errors
4. Test code in isolated environment first

### Unsaved Changes Not Detected

**Issue:** Save button stays disabled despite changes

**Solutions:**
1. Verify comparison logic in useEffect
2. Check if project data loaded correctly
3. Ensure state updates are propagating
4. Debug with React DevTools

## Performance Optimization

### 1. Memoization

```tsx
const memoizedPreview = useMemo(
  () => <WebsitePreview html={html} css={css} js={js} />,
  [html, css, js]
);
```

### 2. Code Splitting

```tsx
const WebsitePreview = dynamic(() => import('@/components/WebsitePreview'), {
  ssr: false,
  loading: () => <div>Loading preview...</div>
});
```

### 3. Lazy Loading

```tsx
// Only load Monaco Editor when needed
const MonacoEditor = lazy(() => import('@monaco-editor/react'));
```

## Conclusion

This preview system provides a secure, user-friendly way to edit and preview websites in real-time. The sandboxed iframe approach ensures safety while maintaining functionality, and the VS Code-inspired design provides a familiar, professional experience.

