# Optimistic Updates Implementation

## Overview

This system provides **instant visual feedback** for property edits (< 50ms) while saving changes to the backend in the background.

## How It Works

### Traditional Flow (Slow - 2-4 seconds)
```
User changes property → API call → Update files → Rebuild preview → Refresh iframe → See change
```

### Optimistic Flow (Instant - < 50ms)
```
User changes property → Update iframe immediately (< 50ms) → [Background: Save to API after 500ms]
                     ↓
               See change instantly! ✨
```

## Architecture

### 1. Frontend: Optimistic Updates

**File:** `frontend/src/app/dashboard/projects/[id]/page.tsx`

When a property changes:

1. **Instant Update** - Sends `postMessage` to preview iframe to update DOM immediately
2. **Debounced Save** - Waits 500ms after last change, then saves to backend
3. **Error Handling** - Shows toast if backend save fails (but preview still shows change)

```typescript
// Step 1: Apply optimistic update to preview IMMEDIATELY (< 50ms)
const optimisticSuccess = applyOptimisticUpdate(
  selectedElement.elementSelector,
  property,
  value
);

// Step 2: Save to backend (debounced - waits 500ms after last change)
debouncedBackendSave(property, value, selectedElement);
```

### 2. Preview: Property Update Handler

**File:** `backend/previews/shared_template/selector-injection.js`

The preview iframe listens for `UPDATE_PROPERTY` messages and applies changes directly to the DOM:

```javascript
// Listen for instant update messages
window.addEventListener('message', function(event) {
  if (event.data.type === 'UPDATE_PROPERTY') {
    const { selector, property, value } = event.data;
    const element = document.querySelector(`[data-element="${selector}"]`);
    
    // Apply change instantly
    if (property === 'text') {
      element.textContent = value;
    } else if (property.startsWith('text') || property.startsWith('bg')) {
      updateTailwindClass(element, property, value);
    }
    // ... more property types
  }
});
```

### 3. Backend: Debounced Persistence

**File:** `backend/app/routers/generation.py`

Backend receives saves 500ms after the last change and:
1. Updates the file in the database
2. Updates the preview directory
3. Triggers incremental Vite build
4. Returns success/failure

## Performance Comparison

| Operation | Before | After | Improvement |
|-----------|--------|-------|-------------|
| Visual Feedback | 2-4s | **< 50ms** | **40-80x faster** 🚀 |
| Backend Save | 2-4s | 2-4s (background) | Same but feels instant |
| Multiple Edits | 6-12s (3 edits) | < 150ms + one save | **40-80x faster** 🚀 |

## Supported Properties

### Text Properties
- ✅ `text` - Text content
- ✅ `alt` - Alt text (images)

### Link Properties
- ✅ `href` - Link URLs
- ✅ `src` - Image sources

### Tailwind Classes
- ✅ `textColor` - Text colors (`text-blue-500`)
- ✅ `backgroundColor` - Background colors (`bg-gray-100`)
- ✅ `borderColor` - Border colors (`border-red-500`)
- ✅ `fontSize` - Font sizes (`text-xl`)
- ✅ `fontWeight` - Font weights (`font-bold`)
- ✅ `padding` - Padding (`p-4`)
- ✅ `margin` - Margin (`m-2`)

More properties can be easily added to the selector-injection.js handler.

## User Experience Flow

### Single Property Edit
```
1. User types "Hello World" in text field
   ↓ < 50ms
2. Preview updates to show "Hello World" ✨
   ↓ (user keeps editing)
3. User stops typing
   ↓ 500ms pause
4. Backend saves change (background) 💾
```

### Multiple Rapid Edits
```
1. User changes text color to blue
   ↓ < 50ms
2. Preview turns blue ✨
   ↓ (user immediately changes again)
3. User changes text color to red
   ↓ < 50ms
4. Preview turns red ✨
   ↓ (user stops)
5. 500ms pause
6. Backend saves final value (red) 💾
   (Only ONE backend call for multiple changes!)
```

## Error Handling

### Scenario: Backend Save Fails

```
1. User changes property
   ↓ < 50ms
2. Preview updates immediately ✅
   ↓ 500ms
3. Backend save fails ❌
   ↓
4. Toast shows: "Save Failed - Changes may not persist"
   ↓
Result: Preview still shows the change (optimistic)
        but user is warned it didn't save
```

**Why this is good:**
- User sees immediate feedback (good UX)
- User is warned about the failure
- Can retry or reload to see actual saved state

### Scenario: Preview Reload

```
1. User makes multiple optimistic edits
2. Backend saves in background ✅
3. User refreshes page
   ↓
Result: Changes persist! ✨
        (Because backend saved them)
```

## Debouncing Strategy

### Why 500ms?

- **Too short (< 200ms)**: Backend gets overwhelmed with requests
- **Too long (> 1s)**: Risk of losing changes if user navigates away
- **500ms (chosen)**: Sweet spot - feels instant but reduces API calls

### Batching Behavior

Multiple property changes within 500ms result in **ONE backend call**:

```
Time: 0ms    - User changes text color
Time: 100ms  - User changes font size
Time: 300ms  - User changes padding
Time: 800ms  - Backend saves all three changes at once ✅
```

## Visual Feedback

### 1. Instant Change
When property updates, the element gets a subtle green outline flash:

```javascript
element.style.outline = '2px solid #22c55e';
setTimeout(() => {
  element.style.outline = originalOutline;
}, 300);
```

### 2. Saving Indicator
A toast shows "Updating..." for 1 second to confirm the action:

```typescript
toast.success("Updating...", {
  description: `Changing ${property}`,
  duration: 1000,
});
```

### 3. Save Status
The sidebar header shows a pulsing dot when saving to backend:
- 🟡 Yellow pulse = Saving...
- 🟢 Green = Saved
- 🔴 Red = Error

## Implementation Details

### Message Protocol

**Frontend → Iframe:**
```javascript
{
  type: 'UPDATE_PROPERTY',
  selector: 'hero-title',
  property: 'text',
  value: 'New Title'
}
```

**Iframe → Frontend:**
```javascript
{
  type: 'PROPERTY_UPDATE_RESULT',
  success: true,
  selector: 'hero-title',
  property: 'text'
}
```

### State Management

```typescript
// Track pending saves
const pendingSaveRef = useRef<NodeJS.Timeout | null>(null);

// Clear previous timeout when new change comes
if (pendingSaveRef.current) {
  clearTimeout(pendingSaveRef.current);
}

// Schedule new save
pendingSaveRef.current = setTimeout(async () => {
  // Save to backend
}, 500);
```

## Limitations

### 1. Structural Changes Not Supported
Optimistic updates work for **content and styling** but not for:
- ❌ Adding/removing elements
- ❌ Changing component structure
- ❌ Complex nested prop updates

These require a full rebuild and don't benefit from optimistic updates.

### 2. Prop Values Need Special Handling
When editing a prop like `{title}`, we need to:
1. Update the prop at the source (parent component)
2. Reload the preview after backend save
3. Can't apply optimistically (needs full rebuild)

### 3. Preview Reload Resets Optimistic Changes
If the preview is rebuilt (e.g., after prop edit), optimistic changes are replaced by saved state.

**Solution:** Backend saves complete before rebuild, so changes persist.

## Testing Optimistic Updates

### Manual Test

1. **Open a React project**
2. **Build preview**
3. **Select a text element**
4. **Start typing in the Edit Sidebar text field**
5. **Expected behavior:**
   - Text updates in preview **as you type** (< 50ms per keystroke) ✨
   - After you stop typing (500ms), save indicator appears
   - Toast shows "Updating..." briefly
   - Changes persist on page reload

### Performance Test

Open browser DevTools → Console:

```javascript
// Time a property change
console.time('optimistic-update');
// Change a property in sidebar
// Check console after change appears
console.timeEnd('optimistic-update');
// Should show: "optimistic-update: 30ms" or similar
```

### Network Test

Open browser DevTools → Network:

1. Type rapidly in text field (5 character changes)
2. Check Network tab
3. **Expected:** Only ONE API call to `edit-properties`
4. **Time:** Happens 500ms after last keystroke

## Future Enhancements

### 1. Optimistic Prop Updates

Currently, prop edits require full rebuild. Could optimize:

```typescript
// For prop {title}
// 1. Update prop value at source instantly
// 2. Re-render just that component (partial HMR)
// 3. Full rebuild in background
```

### 2. Conflict Resolution

If multiple users edit the same project:

```typescript
// Detect conflicts
if (serverVersion > localVersion) {
  // Show dialog: "Someone else edited this. Merge or overwrite?"
}
```

### 3. Undo/Redo

With optimistic updates, could implement instant undo:

```typescript
// Keep history of changes
const history = [change1, change2, change3];

// Undo = rollback optimistic update + backend call
function undo() {
  const previousChange = history.pop();
  applyOptimisticUpdate(previousChange);
  debouncedBackendSave(previousChange);
}
```

## Troubleshooting

### Changes Don't Appear Instantly

**Check:**
1. Browser console for errors
2. Preview iframe loaded correctly
3. Element has `data-element` attribute
4. Property type is supported

**Debug:**
```javascript
// In browser console
console.log('Iframe:', document.querySelector('iframe[title="React Preview"]'));
// Should show iframe element, not null
```

### Changes Appear but Don't Save

**Check:**
1. Network tab for failed API calls
2. Backend logs for errors
3. Database migration ran (preview_id column exists)

**Solution:**
- Check `REALTIME_EDITING_SETUP.md` for migration steps

### Changes Revert on Page Reload

**Cause:** Backend save failed

**Solution:**
- Check browser console for "Save Failed" errors
- Check backend logs for errors
- Retry the edit

## Conclusion

Optimistic updates provide a **40-80x performance improvement** for interactive editing by:

1. ✅ Updating preview instantly (< 50ms)
2. ✅ Debouncing backend saves (500ms)
3. ✅ Batching multiple changes
4. ✅ Providing clear error feedback

This creates a **smooth, responsive editing experience** that feels like a native application while still persisting changes reliably to the backend.

