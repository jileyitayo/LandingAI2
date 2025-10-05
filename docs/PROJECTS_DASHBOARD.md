# Projects Dashboard Documentation

## Overview

The Projects Dashboard is the main interface for users to view, manage, and organize all their website projects. It provides a clean, card-based layout with search and filtering capabilities.

## Features

### 1. Projects Grid View
- **Card-based Layout**: Projects displayed in a responsive grid (1 column on mobile, 2 on tablet, 3 on desktop)
- **Visual Thumbnails**: Each project shows a preview image or generated placeholder
- **Project Information**: Name, description, last updated date, and published status
- **Hover Effects**: Smooth animations and edit button overlay on hover

### 2. Search and Filter
- **Search Bar**: Real-time search across project names and descriptions
- **Status Filter**: Filter projects by generation status:
  - All Projects
  - Completed
  - Generating
  - Failed
- **Dynamic Results**: Instant filtering without page reload

### 3. Project Actions

#### Primary Actions
- **Create New Project**: Quick access button to create new projects (`/dashboard/new`)
- **Edit Project**: Click anywhere on the card to edit the project
- **Delete Project**: Remove project with confirmation dialog
- **Duplicate Project**: Create a copy of existing project
- **View Live**: Open published projects in new tab

### 4. Empty States
- **No Projects**: Helpful message with CTA to create first project
- **No Search Results**: Clear feedback when filters return no results

## Technical Implementation

### Frontend Components

#### Dashboard Page (`/dashboard/page.tsx`)
```typescript
- Manages project state and filtering logic
- Handles API calls for fetching, deleting, and duplicating projects
- Implements search and filter UI
- Responsive navigation with user profile dropdown
```

#### ProjectCard Component (`/components/ProjectCard.tsx`)
```typescript
- Displays individual project information
- Handles project actions (edit, delete, duplicate, view)
- Shows loading states for async operations
- Responsive hover effects and status badges
```

### Backend API

#### Projects Router (`/api/v1/projects`)

**Endpoints:**

1. **GET /projects**
   - List all user projects
   - Query parameters:
     - `status_filter`: Filter by generation status
     - `search`: Search in name/description
     - `limit`: Pagination limit (default: 50)
     - `offset`: Pagination offset (default: 0)
   - Returns: Array of project list items

2. **GET /projects/{project_id}**
   - Get detailed project information
   - Includes full content (HTML, CSS, JS)
   - Returns: Complete project details

3. **PATCH /projects/{project_id}**
   - Update project properties
   - Accepts: name, description, content, settings
   - Returns: Success message with project ID

4. **DELETE /projects/{project_id}**
   - Delete project (with ownership verification)
   - Returns: Success message

5. **POST /projects/{project_id}/duplicate**
   - Create copy of project
   - Optional: custom name for duplicate
   - Returns: New project ID and name

### Database Schema

Projects table includes:
```sql
- id (UUID)
- user_id (UUID, FK to auth.users)
- name (TEXT)
- description (TEXT)
- html_content (TEXT)
- css_content (TEXT)
- js_content (TEXT)
- published (BOOLEAN)
- deployment_url (TEXT)
- generation_status (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

## User Flow

### Viewing Projects
1. User logs in and lands on `/dashboard`
2. Dashboard fetches and displays all user projects
3. Projects shown in grid layout with thumbnails

### Searching Projects
1. User types in search bar
2. Results filter in real-time
3. Search matches against name and description

### Creating Project
1. Click "New Project" button
2. Navigate to `/dashboard/new`
3. Enter prompt and generate website

### Editing Project
1. Click on any project card
2. Navigate to `/dashboard/projects/{id}`
3. Use project editor to modify content

### Deleting Project
1. Click trash icon on project card
2. Confirm deletion in dialog
3. Project removed from database and UI

### Duplicating Project
1. Click duplicate icon on project card
2. Copy created with "(Copy)" suffix
3. New project appears in dashboard

## API Client Integration

The frontend API client (`/lib/api.ts`) provides type-safe methods:

```typescript
// List projects
await api.projects.list();

// Get single project
await api.projects.get(projectId);

// Update project
await api.projects.update(projectId, { name: "New Name" });

// Delete project
await api.projects.delete(projectId);

// Duplicate project
await api.projects.duplicate(projectId, "Custom Name");
```

## Security

### Authentication
- All endpoints require valid JWT token
- Token automatically included in API requests
- Unauthorized requests redirect to login

### Authorization
- Projects owned by user only
- Ownership verified on all operations
- 403 Forbidden for unauthorized access

### Rate Limiting
- Future enhancement planned
- Will use Supabase rate limiting features

## Performance Considerations

### Frontend
- Client-side filtering for instant results
- Optimistic updates for better UX
- Lazy loading of project thumbnails
- Debounced search input (future enhancement)

### Backend
- Indexed queries on user_id
- Pagination support to limit payload
- Efficient database queries with Supabase
- Background task processing for heavy operations

## Future Enhancements

### Planned Features
1. **Sorting Options**
   - Sort by name, date, status
   - Ascending/descending order

2. **Bulk Actions**
   - Select multiple projects
   - Bulk delete, duplicate, or archive

3. **Project Templates**
   - Save project as template
   - Share templates with team

4. **Collaboration**
   - Share projects with other users
   - Team workspaces

5. **Advanced Filters**
   - Filter by tags
   - Filter by date range
   - Custom filter combinations

6. **Project Analytics**
   - View counts
   - Engagement metrics
   - Performance insights

7. **Export/Import**
   - Export project as ZIP
   - Import existing websites

## Styling Guidelines

### Design System
- **Colors**: Indigo primary, gray neutral
- **Spacing**: Consistent padding and margins
- **Typography**: Clear hierarchy with Tailwind
- **Animations**: Smooth transitions (200ms)

### Responsive Breakpoints
- **Mobile**: < 640px (1 column)
- **Tablet**: 640px - 1024px (2 columns)
- **Desktop**: > 1024px (3 columns)

### Accessibility
- Semantic HTML elements
- Keyboard navigation support
- ARIA labels on interactive elements
- Color contrast meets WCAG standards

## Error Handling

### Frontend Errors
- User-friendly error messages
- Console logging for debugging
- Alert dialogs for critical errors
- Graceful degradation

### Backend Errors
- HTTP status codes for different scenarios
- Detailed error messages in development
- Generic messages in production
- Logging for monitoring

## Testing

### Frontend Tests (Planned)
- Unit tests for filtering logic
- Integration tests for API calls
- E2E tests for user flows

### Backend Tests (Planned)
- Unit tests for router endpoints
- Integration tests with database
- Authorization tests
- Rate limit tests

## Deployment

### Frontend
- Next.js on Vercel
- Environment variables in `.env.local`
- Automatic deployments from main branch

### Backend
- FastAPI on Railway/Render
- Environment variables in platform
- Automatic deployments from main branch

## Troubleshooting

### Projects Not Loading
1. Check authentication token
2. Verify API connection
3. Check browser console for errors
4. Verify backend is running

### Search Not Working
1. Check search query length
2. Verify project data has searchable fields
3. Check browser console for errors

### Actions Failing
1. Verify user permissions
2. Check network connectivity
3. Verify backend API health
4. Check browser console for detailed errors

## Related Documentation

- [Authentication Flow](./AUTHENTICATION_FLOW.md)
- [AI Website Generation](./AI_TEMPLATE_GENERATION_SYSTEM.md)
- [Project Editor](./dashboard/projects/README.md)
- [API Integration](./FRONTEND_BACKEND_INTEGRATION.md)

