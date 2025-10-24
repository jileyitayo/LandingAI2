# React Project Editor Optimization Plan

## Current Analysis

### Main Issues Identified

- **ProjectEditorPage** (545 lines) - Too large, no memoization, multiple re-renders
- **FileTree** - Rebuilds entire tree structure on every render
- **CodeViewer** - Creates new line number arrays on every render, basic pre/code display
- **ReactPreview** - Heavy component with no memoization
- **ChatWindow** - No performance optimizations
- **Editing Workflow** - Requires manual selector activation, not intuitive
- **HTML/CSS/JS Editor** - ❌ Excluded from optimization (being deprecated)

## Optimization Implementation Plan

### Phase 1: Editing Workflow Optimization (High Impact, Low Effort) 🆕

#### 1.1 Auto-Activate Selector on Preview Click

**Current flow (clunky):**
```
Type in chat → Selector auto-enables
Click element in preview → Element selected
Continue typing → Submit edit
```

**Improved flow (intuitive):**
```
Click anywhere in preview → Selector auto-activates
Element immediately selected on click
Type in chat → Submit edit
```

**Implementation:**
- Add click listener to preview iframe
- Auto-enable selector on first preview interaction
- Show visual feedback (cursor change, highlight preview border)
- Keep selector enabled until user explicitly disables

#### 1.2 Smart Selector State Management

- Remember selector preference per session
- Auto-enable when entering React project
- Disable when leaving project
- Persist in sessionStorage

#### 1.3 Better Visual Feedback

- Preview border changes color when selector active (blue glow)
- Cursor changes to crosshair when hovering preview
- Toast notification: "Click any element to edit"
- Pulsing indicator on first load

#### 1.4 Keyboard Shortcuts for Editing

- `E` or `Click` → Enable selector
- `Esc` → Disable selector / Clear selection
- `Enter` in chat → Submit edit (when element selected)
- `Cmd/Ctrl + K` → Focus chat input

#### 1.5 Streamline Selection Panel

**Current:** Selection details in separate panel (can be closed)

**Improved:**
- Show selected element in chat window header
- Inline component badge in chat input area
- Less context switching

### Phase 2: Component Memoization (High Impact, Low Effort)

#### 2.1 Memoize All Child Components

- Wrap FileTree with React.memo
- Wrap CodeViewer with React.memo
- Wrap ReactPreview with React.memo
- Wrap ChatWindow with React.memo
- Wrap PublishButton with React.memo
- Wrap PublishModal with React.memo

#### 2.2 Memoize Callbacks in ProjectEditorPage

- `loadProject` - already using useCallback ✓
- `saveProject` - already using useCallback ✓
- `handlePublishSuccess` - add useCallback
- `handleUnpublishSuccess` - add useCallback
- `handleReactDownload` - add useCallback
- `loadReactFiles` - already using useCallback ✓
- `buildPreview` - already using useCallback ✓
- `handleEditSubmit` - add useCallback

#### 2.3 Add useMemo for Computed Values

**FileTree:**
- Memoize buildTree() result (depends on files prop)
- Memoize sorted tree nodes

**CodeViewer:**
- Memoize lineNumbers array (depends on content)
- Memoize getLanguage() result (depends on fileName)
- Memoize lines split operation

### Phase 3: Component Architecture (High Impact, Medium Effort)

#### 3.1 Extract React Editor Component

Create `ReactProjectEditor.tsx`:
- Move React-specific logic (lines 238-374) to dedicated component
- Keep main page as orchestrator/router
- Cleaner separation of concerns

#### 3.2 Extract Shared Components

- **EditorHeader.tsx** - Reusable header with back button, title, actions
- **EditorSidebar.tsx** - Chat window wrapper with consistent styling
- **EditorMainPanel.tsx** - Code/Preview panel wrapper

#### 3.3 Simplify ProjectEditorPage

- Becomes a router component (React vs HTML/CSS/JS)
- Only loads appropriate editor based on project type
- Much simpler, ~100 lines instead of 545

### Phase 4: CodeViewer Enhancement (Medium Impact, Medium Effort)

#### 4.1 Integrate Monaco Editor for Code Display

- Install `@monaco-editor/react`
- Replace the `<pre><code>` display with Monaco (read-only mode)
- Get syntax highlighting, code folding, minimap
- Still read-only, just better viewing experience

#### 4.2 Add Code Viewer Features

- Syntax highlighting for all file types (TSX, JSX, CSS, JSON, etc.)
- Code folding for large files
- Minimap for navigation
- Find in file (Ctrl+F)
- Copy to clipboard button
- "Open in VS Code" button (if available)

#### 4.3 Performance for Large Files

- Use Monaco's built-in virtualization
- Handles files with 10,000+ lines smoothly
- Only renders visible lines
- Lazy load file content when selected

### Phase 5: Build & Preview Optimization (High Impact, Medium Effort)

#### 5.1 Smart Auto-Build Strategy

**Current:** Auto-builds on every preview tab switch

**Improved:**
- Only auto-build on first preview activation
- Add manual "Rebuild" button (already exists)
- Add "Auto-rebuild on change" toggle
- Debounce rebuilds by 2 seconds

#### 5.2 Build Progress & Feedback

- Real-time build status indicator
- Progress bar if backend provides percentage
- Show build logs in collapsible panel
- Timestamp of last successful build
- Build duration display

#### 5.3 Build Caching & Optimization

- Track file changes with hash comparison
- Skip rebuild if no files changed since last build
- Show "Using cached build from 2m ago" message
- "Force Rebuild" button to clear cache
- Cache preview URLs

#### 5.4 Preview Error Handling

- Better error messages with file/line numbers
- Link to open file at error location in CodeViewer
- Suggestions for common build errors (missing deps, syntax errors)
- Copy error button for debugging
- "Report Issue" button

### Phase 6: FileTree Optimization (Low Impact, Medium Effort)

#### 6.1 Add File Search

- Search input at top of FileTree
- Filter files by name (fuzzy search)
- Keyboard navigation (Up/Down arrows, Enter to open)
- Highlight matching text
- Clear search button

#### 6.2 FileTree State Management

- Remember expanded folders in localStorage
- Remember last selected file per project
- Auto-expand to show selected file
- "Collapse All" / "Expand All" buttons
- Smart initial expansion (expand src/, components/)

#### 6.3 Virtual Scrolling (optional, for large projects)

- Use react-window for virtualization
- Only needed if project has 100+ files
- Renders only visible nodes
- Smooth scrolling even with 1000+ files

### Phase 7: State Management (Low Impact, Medium Effort)

#### 7.1 Create useReactProjectEditor Hook

Extract all React project state logic:

```typescript
const {
  files,
  selectedFile,
  setSelectedFile,
  previewUrl,
  isBuilding,
  buildError,
  buildPreview,
  loadFiles,
} = useReactProjectEditor(projectId);
```

#### 7.2 Create useElementSelector Hook

Extract selection logic:

```typescript
const {
  selectedElement,
  setSelectedElement,
  selectorEnabled,
  enableSelector, // NEW: explicit enable
  disableSelector, // NEW: explicit disable
  toggleSelector,
  clearSelection,
  autoEnableOnClick, // NEW: for auto-activation
} = useElementSelector();
```

#### 7.3 Use Reducer for Complex State

- Consolidate React project state into reducer
- Better state update batching
- Easier to debug state changes
- Time-travel debugging capability

## Implementation Priority

### 🔥 Week 1: Editing Workflow + Critical Performance (Days 1-3)
**Goal:** Much better UX + 30-40% reduction in re-renders

**Day 1 - Editing UX:**
- ✅ Add auto-activate selector on preview click
- ✅ Add visual feedback (blue border, cursor change)
- ✅ Add keyboard shortcuts (E, Esc, Enter)
- ✅ Show selection in chat header

**Day 2 - Performance:**
- ✅ Memoize FileTree, CodeViewer, ReactPreview, ChatWindow
- ✅ Add useMemo for buildTree in FileTree
- ✅ Add useMemo for lineNumbers in CodeViewer
- ✅ Add useCallback for all handlers

**Day 3 - Testing:**
- ✅ Test and measure performance improvements
- ✅ Test new editing workflow
- ✅ Fix any broken functionality
- ✅ Update documentation

### 🚀 Week 2: Architecture Improvements (Days 4-7)
**Goal:** Better maintainability, cleaner code

**Day 4:**
- ✅ Create EditorHeader component
- ✅ Create ReactProjectEditor component
- ✅ Extract shared layouts

**Day 5:**
- ✅ Simplify ProjectEditorPage to be a router
- ✅ Move React logic to ReactProjectEditor
- ✅ Test all functionality

**Day 6-7:**
- ✅ Create useReactProjectEditor hook
- ✅ Create useElementSelector hook (with auto-enable)
- ✅ Refactor components to use new hooks

### ⚡ Week 3: Enhanced Code Viewing (Days 8-10)
**Goal:** Better developer experience

**Day 8:**
- ✅ Install Monaco Editor
- ✅ Create MonacoCodeViewer component (read-only)
- ✅ Replace CodeViewer with Monaco version

**Day 9:**
- ✅ Add syntax highlighting for all file types
- ✅ Add copy to clipboard
- ✅ Add find in file
- ✅ Add code folding

**Day 10:**
- ✅ Test with large files
- ✅ Optimize Monaco config
- ✅ Add minimap
- ✅ Lazy load file contents

### 🎯 Week 4: Build & Preview Polish (Days 11-14)
**Goal:** Smoother build experience

**Day 11:**
- ✅ Improve auto-build logic (only first time)
- ✅ Add build progress indicators
- ✅ Add build caching

**Day 12:**
- ✅ Better error messages
- ✅ Link errors to file locations
- ✅ Add build duration display

**Day 13:**
- ✅ File search in FileTree
- ✅ Remember expanded folders
- ✅ Keyboard navigation

**Day 14:**
- ✅ Final testing
- ✅ Performance measurements
- ✅ Documentation updates

## Files to Create

### New Components:
- `frontend/src/components/editor/ReactProjectEditor.tsx`
- `frontend/src/components/editor/EditorHeader.tsx`
- `frontend/src/components/editor/EditorSidebar.tsx`
- `frontend/src/components/editor/EditorMainPanel.tsx`
- `frontend/src/components/editor/MonacoCodeViewer.tsx`
- `frontend/src/components/editor/BuildProgress.tsx`
- `frontend/src/components/editor/SelectorActivator.tsx` 🆕

### New Hooks:
- `frontend/src/hooks/useReactProjectEditor.ts`
- `frontend/src/hooks/useElementSelector.ts` (enhanced with auto-enable)
- `frontend/src/hooks/useBuildManager.ts`
- `frontend/src/hooks/useKeyboardShortcuts.ts` 🆕

## Files to Modify

- ✅ `frontend/src/app/dashboard/projects/[id]/page.tsx` - Simplify to router
- ✅ `frontend/src/components/FileTree.tsx` - Add memoization, search
- ✅ `frontend/src/components/CodeViewer.tsx` - Migrate to Monaco
- ✅ `frontend/src/components/ReactPreview.tsx` - Add memoization + auto-activate selector 🆕
- ✅ `frontend/src/components/ChatWindow.tsx` - Add memoization + show selection in header 🆕

## Success Metrics

### Performance Targets:
- ✅ 50% reduction in re-renders (measured with React DevTools Profiler)
- ✅ <100ms typing latency when typing in chat
- ✅ <50ms when switching files in FileTree
- ✅ <3s preview build time (backend dependent)
- ✅ Smooth 60fps scrolling in all panels

### User Experience:
- ✅ One-click editing workflow (click preview → selector active)
- ✅ Keyboard shortcuts for common actions
- ✅ Visual feedback for selector state
- ✅ Syntax highlighting in code viewer
- ✅ Instant file switching (<50ms)
- ✅ Clear build progress/status
- ✅ Better error messages

### Editing Workflow Improvements:
- ✅ 50% fewer clicks to make an edit
- ✅ Clearer visual feedback for selector state
- ✅ Less mental overhead (auto-enable)
- ✅ Keyboard-friendly workflow