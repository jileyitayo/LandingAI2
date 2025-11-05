# Realtime Editing Setup & Troubleshooting

## Quick Setup (3 Steps)

### 1. Run Database Migration

The realtime editing feature requires a new `preview_id` column in the `projects` table.

**Via Supabase Dashboard (Easiest):**
1. Go to your Supabase dashboard: https://supabase.com/dashboard
2. Select your project
3. Go to **SQL Editor** (left sidebar)
4. Click **New Query**
5. Paste the following SQL:

```sql
-- Add preview_id column to projects table
ALTER TABLE projects
ADD COLUMN IF NOT EXISTS preview_id TEXT;

-- Add index for faster lookups
CREATE INDEX IF NOT EXISTS idx_projects_preview_id ON projects(preview_id);

-- Add comment
COMMENT ON COLUMN projects.preview_id IS 'UUID of the active Vite preview build for this project';
```

6. Click **Run** (or press `Ctrl/Cmd + Enter`)
7. You should see: "Success. No rows returned"

**Or via script:**
```bash
cd backend
./run_migration_019.sh
```

### 2. Restart Backend Server

After running the migration, restart your FastAPI backend:

```bash
# Stop the current server (Ctrl+C)
# Then restart:
cd backend
uvicorn app.main:app --reload --port 8000
```

### 3. Test It Out!

1. Open an existing project or create a new React project
2. Click **Preview** tab to build the initial preview (5-10s)
3. Click **any element** in the preview to select it
4. Edit properties in the **Edit Sidebar** (left panel)
5. Changes should now apply in **~2-4 seconds** instead of 5-10 seconds! 🚀

## Troubleshooting 404 Errors

### Issue: "This page could not be found" after editing

**Cause:** One of these:
1. Database migration not run (no `preview_id` column)
2. Preview has expired (1 hour lifetime)
3. Preview directory was cleaned up

**Solution:**

1. **Check if migration ran:**
   - Open Supabase Dashboard → SQL Editor
   - Run: `SELECT column_name FROM information_schema.columns WHERE table_name = 'projects' AND column_name = 'preview_id';`
   - Should return: `preview_id`
   - If empty, run the migration above

2. **Check backend logs:**
   ```bash
   cd backend
   tail -50 uvicorn.log | grep "PROPERTY EDIT\|VITE PREVIEW"
   ```
   
   Look for:
   - ✅ `[PROPERTY EDIT] Existing preview_id from DB: abc-123` (good)
   - ❌ `[PROPERTY EDIT] Existing preview_id from DB: None` (migration needed)
   - ✅ `[PROPERTY EDIT] Preview updated successfully in 2.3s` (working)
   - ❌ `[PROPERTY EDIT] Preview not found or expired` (preview expired)

3. **If preview expired:**
   - Click **Rebuild** button in the preview header
   - This creates a new preview
   - Then try editing again

4. **Check browser console:**
   - Press `F12` to open DevTools
   - Go to **Console** tab
   - Look for:
     - `Backend returned new preview URL: /previews/builds/abc-123/dist/index.html`
     - `Setting preview URL to: http://localhost:8000/previews/builds/abc-123/dist/index.html?_t=1234567890`

### Issue: Changes are slow (still taking 5-10 seconds)

**Cause:** Preview is being recreated each time instead of updated.

**Solution:**

1. **Verify preview_id is being stored:**
   - Check backend logs for: `[PROPERTY EDIT] Storing new preview_id abc-123 in database`
   - Check database: `SELECT id, name, preview_id FROM projects WHERE id = 'your-project-id';`
   - `preview_id` should have a UUID value

2. **Verify preview directory exists:**
   ```bash
   cd backend/previews/builds
   ls -la
   # Should show directories with UUID names
   ```

3. **Check for errors in logs:**
   - Look for: `[VITE PREVIEW] Preview abc-123 not found in active previews`
   - If found, the preview expired - click **Rebuild**

### Issue: Backend errors

**Common Errors:**

1. **"column 'preview_id' does not exist"**
   - Solution: Run the database migration (step 1 above)

2. **"Preview not found or expired"**
   - Solution: Click **Rebuild** to create a new preview

3. **"Build failed"**
   - Check backend logs for Vite build errors
   - Usually syntax errors in the component code
   - Fix the code error and try again

## How It Works

### First Edit Workflow

```
User edits property
    ↓
Backend receives edit
    ↓
Checks DB for preview_id → None (first time)
    ↓
Creates new preview (~5-10s)
    ↓
Stores preview_id in database
    ↓
Returns preview_url to frontend
    ↓
Frontend loads new preview
```

### Subsequent Edits Workflow (Fast!)

```
User edits property
    ↓
Backend receives edit
    ↓
Checks DB for preview_id → Found!
    ↓
Updates existing preview files (~2-4s)
    ↓
Incremental Vite build (reuses cache)
    ↓
Returns same preview_url
    ↓
Frontend refreshes iframe with cache-busting
```

## Performance Expectations

| Operation | Time | Notes |
|-----------|------|-------|
| First preview build | 5-10s | Normal - full build required |
| First property edit | 5-10s | Creates preview if none exists |
| **Subsequent edits** | **2-4s** | ⚡ Fast incremental updates |
| Multiple rapid edits | 2-4s each | Each edit is fast |
| After 1 hour | 5-10s | Preview expires, new one created |

## Verification Checklist

Use this checklist to verify the setup:

- [ ] Database migration ran successfully
- [ ] `preview_id` column exists in `projects` table
- [ ] Backend server restarted after migration
- [ ] Can build preview (takes 5-10s)
- [ ] Preview displays correctly
- [ ] Can select elements by clicking
- [ ] Edit sidebar shows on element selection
- [ ] First property edit works (may take 5-10s)
- [ ] `preview_id` is stored in database after first edit
- [ ] Second property edit is faster (2-4s)
- [ ] Backend logs show "Preview updated successfully"
- [ ] No 404 errors in browser
- [ ] Changes reflect in preview after edit

## Need Help?

Check these resources:

1. **Backend Logs:**
   ```bash
   cd backend
   tail -f uvicorn.log
   ```

2. **Browser Console:**
   - Press `F12` → Console tab
   - Look for error messages

3. **Database:**
   - Supabase Dashboard → SQL Editor
   - Run: `SELECT * FROM projects WHERE id = 'your-project-id';`

4. **Preview Directory:**
   ```bash
   cd backend/previews/builds
   ls -la
   # Should show UUID directories
   # Check timestamps to see if they're recent
   ```

## Files Modified

For reference, these files were modified to implement realtime editing:

**Backend:**
- `backend/app/services/vite_preview_service.py` - Added `update_preview_files()` method
- `backend/app/routers/generation.py` - Updated property edit endpoint
- `backend/migrations/019_add_preview_id_to_projects.sql` - New migration

**Frontend:**
- `frontend/src/app/dashboard/projects/[id]/page.tsx` - Removed full rebuild, added debouncing

**Documentation:**
- `docs/REALTIME_EDITING_IMPLEMENTATION.md` - Technical details
- `REALTIME_EDITING_SETUP.md` - This file

