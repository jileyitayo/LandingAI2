# Vercel Deployment Integration

## Overview

This document describes the Vercel deployment integration for deploying projects to production using the Vercel API v2.

## Architecture

### Backend Components

1. **Deployment Service** (`app/services/vercel_deployer.py`)
   - `VercelDeployer`: Main service class for Vercel API integration
   - Handles authentication with Vercel API token
   - Generates static files from project content (HTML/CSS/JS)
   - Deploys React projects from database files
   - Manages deployment lifecycle

2. **Deployment Router** (`app/routers/deployment.py`)
   - RESTful API endpoints for deployment operations
   - Authentication and authorization checks
   - Error handling and logging

### API Endpoints

#### Deploy Project
```
POST /api/v1/projects/{project_id}/deploy
```

**Description:** Deploy a project to Vercel

**Requirements:**
- Project must exist and belong to the authenticated user
- Project must have HTML content
- Project generation must be complete (not in "generating" state)

**Request:**
- Headers: `Authorization: Bearer <token>`
- Path parameter: `project_id` (UUID)

**Response:**
```json
{
  "deployment_id": "dpl_xxx",
  "deployment_url": "https://mysite-abc123.vercel.app",
  "status": "ready",
  "deployed_at": "2024-01-01T00:00:00"
}
```

**Error Cases:**
- 401: Unauthorized (invalid or missing token)
- 403: Forbidden (user doesn't own project)
- 404: Project not found
- 400: Project has no content or generation in progress
- 500: Deployment failed

---

#### Delete Deployment
```
DELETE /api/v1/projects/{project_id}/deploy
```

**Description:** Delete a project's deployment from Vercel

**Requirements:**
- Project must exist and belong to the authenticated user
- Project must have an active deployment

**Request:**
- Headers: `Authorization: Bearer <token>`
- Path parameter: `project_id` (UUID)

**Response:**
```json
{
  "message": "Deployment deleted successfully",
  "project_id": "proj_xxx"
}
```

**Error Cases:**
- 401: Unauthorized
- 403: Forbidden
- 404: Project not found
- 400: No active deployment
- 500: Deletion failed

---

#### Get Deployment Status
```
GET /api/v1/projects/{project_id}/deployment-status
```

**Description:** Get the current deployment status of a project

**Request:**
- Headers: `Authorization: Bearer <token>`
- Path parameter: `project_id` (UUID)

**Response:**
```json
{
  "deployment_id": "dpl_xxx",
  "deployment_url": "https://mysite-abc123.vercel.app",
  "state": "READY",
  "ready": true,
  "last_deployed_at": "2024-01-01T00:00:00"
}
```

**Deployment States:**
- `NOT_DEPLOYED`: No deployment exists
- `BUILDING`: Deployment is building
- `READY`: Deployment is ready and live
- `ERROR`: Deployment failed
- `UNKNOWN`: Status could not be determined

**Error Cases:**
- 401: Unauthorized
- 403: Forbidden
- 404: Project not found
- 500: Status check failed

---

## Deployment Process

### 1. Static File Generation

The deployment service generates the following files from project content:

- **index.html**: Main HTML file
  - If project has full HTML document, uses it as-is
  - Otherwise, wraps content in proper HTML structure
  - Includes SEO meta tags (title, description)
  - Links to styles.css and script.js

- **styles.css**: CSS stylesheet from project's css_content

- **script.js**: JavaScript from project's js_content

- **vercel.json**: Vercel configuration
  ```json
  {
    "version": 2,
    "builds": [
      {
        "src": "index.html",
        "use": "@vercel/static"
      }
    ],
    "routes": [
      {
        "src": "/(.*)",
        "dest": "/$1"
      }
    ]
  }
  ```

- **package.json**: Required by Vercel (minimal configuration)

### 2. Deployment to Vercel

1. Service creates deployment payload with all files
2. Makes POST request to Vercel API `/v13/deployments`
3. Vercel processes and deploys the static site
4. Service waits for deployment to reach "READY" state
5. Deployment URL is returned

### 3. Database Update

After successful deployment:
- `deployment_id`: Vercel deployment ID
- `deployment_url`: Full HTTPS URL
- `last_deployed_at`: Timestamp
- `published`: Set to `true`
- `updated_at`: Updated timestamp

### 4. Subdomain Handling

- If project has a `subdomain` field, it's used as the project name
- Otherwise, project name is sanitized (lowercase, spaces to hyphens)
- Vercel generates a unique URL: `https://{name}-{hash}.vercel.app`

---

## Configuration

### Environment Variables

Required environment variables in `.env`:

```bash
# Vercel API Configuration
VERCEL_API_TOKEN=your_vercel_token_here
VERCEL_TEAM_ID=team_xxx  # Optional, for team accounts
```

### Getting Vercel API Token

1. Go to [Vercel Dashboard](https://vercel.com/account/tokens)
2. Click "Create Token"
3. Give it a name (e.g., "SiteSmith Deployment")
4. Set appropriate scope (deployment permissions)
5. Copy the token and add to `.env`

### Team ID (Optional)

If deploying to a team account:
1. Go to your team settings
2. Find your Team ID in the URL or settings
3. Add to `.env` as `VERCEL_TEAM_ID`

---

## Error Handling

### Graceful Error Handling

The deployment system handles errors gracefully:

1. **Configuration Errors**
   - Missing API token
   - Invalid token
   - Returns 500 with clear error message

2. **Project Errors**
   - Project not found
   - No content to deploy
   - Generation in progress
   - Returns 400/404 with specific error

3. **Vercel API Errors**
   - Rate limiting
   - API errors
   - Deployment failures
   - Returns 500 with error details

4. **Network Errors**
   - Timeouts (60s for deployment, 30s for status)
   - Connection failures
   - Retries for status checks

### Logging

All operations are logged:
- Info: Successful operations
- Warning: Non-critical issues (timeout on status check)
- Error: Failed operations with full error details

---

## Database Schema

### Projects Table Fields

```sql
-- Deployment-related fields
deployment_id TEXT,           -- Vercel deployment ID
deployment_url TEXT,          -- Full deployment URL
last_deployed_at TIMESTAMPTZ, -- Last deployment timestamp
published BOOLEAN,            -- Published status
subdomain TEXT UNIQUE,        -- Custom subdomain
```

### Action Logs

Deployment actions are logged using the action logger:
- `action_type`: DEPLOY, UNDEPLOY
- `target_resource_type`: project
- `target_resource_id`: project UUID

---

## Usage Examples

### Deploy a Project

```bash
curl -X POST \
  https://api.sitesmith.app/api/v1/projects/{project_id}/deploy \
  -H "Authorization: Bearer <token>"
```

### Check Deployment Status

```bash
curl -X GET \
  https://api.sitesmith.app/api/v1/projects/{project_id}/deployment-status \
  -H "Authorization: Bearer <token>"
```

### Delete Deployment

```bash
curl -X DELETE \
  https://api.sitesmith.app/api/v1/projects/{project_id}/deploy \
  -H "Authorization: Bearer <token>"
```

---

## Frontend Integration

### API Client Methods

Add to `frontend/src/lib/api.ts`:

```typescript
// Deploy project to Vercel
export async function deployProject(projectId: string) {
  const response = await fetch(`${API_URL}/projects/${projectId}/deploy`, {
    method: 'POST',
    headers: await getAuthHeaders(),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to deploy project');
  }
  
  return response.json();
}

// Get deployment status
export async function getDeploymentStatus(projectId: string) {
  const response = await fetch(`${API_URL}/projects/${projectId}/deployment-status`, {
    headers: await getAuthHeaders(),
  });
  
  if (!response.ok) {
    throw new Error('Failed to get deployment status');
  }
  
  return response.json();
}

// Delete deployment
export async function deleteDeployment(projectId: string) {
  const response = await fetch(`${API_URL}/projects/${projectId}/deploy`, {
    method: 'DELETE',
    headers: await getAuthHeaders(),
  });
  
  if (!response.ok) {
    throw new Error('Failed to delete deployment');
  }
  
  return response.json();
}
```

### UI Components

Example deployment button:

```typescript
const [deploying, setDeploying] = useState(false);
const [deploymentUrl, setDeploymentUrl] = useState<string | null>(null);

const handleDeploy = async () => {
  try {
    setDeploying(true);
    const result = await deployProject(projectId);
    setDeploymentUrl(result.deployment_url);
    toast.success('Deployed successfully!');
  } catch (error) {
    toast.error(error.message);
  } finally {
    setDeploying(false);
  }
};
```

---

## Testing

### Manual Testing

1. Create a project with HTML content
2. Deploy the project via API
3. Visit the deployment URL
4. Verify content is displayed correctly
5. Check deployment status
6. Delete deployment
7. Verify deployment is removed

### Automated Testing

Test cases to implement:

1. **Successful Deployment**
   - Create project with content
   - Deploy successfully
   - Verify deployment URL
   - Check database updated

2. **Deployment Errors**
   - Deploy without content (should fail)
   - Deploy during generation (should fail)
   - Deploy non-existent project (should fail)

3. **Status Checks**
   - Check deployed project status
   - Check non-deployed project status

4. **Deletion**
   - Delete existing deployment
   - Try to delete non-existent deployment

---

## Limitations and Future Improvements

### Current Limitations

1. **Static Sites Only**
   - Only deploys static HTML/CSS/JS
   - No server-side rendering
   - No backend API

2. **Single Deployment**
   - Each project has one deployment
   - No staging/preview deployments
   - No deployment history

3. **Basic Configuration**
   - No custom domain support
   - No environment variables
   - Limited Vercel features

### Future Improvements

1. **Multiple Environments**
   - Staging deployments
   - Preview deployments
   - Production deployments

2. **Custom Domains**
   - Support custom domains
   - SSL certificates
   - Domain verification

3. **Deployment History**
   - Track all deployments
   - Rollback to previous versions
   - Deployment logs

4. **Advanced Features**
   - Environment variables
   - Build hooks
   - Analytics integration
   - Performance monitoring

---

## Troubleshooting

### Common Issues

1. **"Vercel API token not configured"**
   - Add `VERCEL_API_TOKEN` to `.env`
   - Restart the backend server

2. **"Deployment failed: Unauthorized"**
   - Check token is valid
   - Verify token has deployment permissions
   - Regenerate token if needed

3. **"Project must have HTML content"**
   - Ensure project has content
   - Run generation first
   - Check `html_content` field is not null

4. **Deployment times out**
   - Check network connectivity
   - Verify Vercel API is accessible
   - Check Vercel status page

### Debug Mode

Enable debug logging:

```bash
LOG_LEVEL=DEBUG python -m uvicorn app.main:app
```

---

## Security Considerations

1. **API Token Security**
   - Never commit tokens to git
   - Use environment variables
   - Rotate tokens periodically

2. **User Authorization**
   - All endpoints require authentication
   - Project ownership verified
   - Action logging for audit trail

3. **Input Validation**
   - Project content sanitized
   - File names validated
   - JSON payloads validated

4. **Rate Limiting**
   - Consider implementing rate limits
   - Prevent abuse
   - Monitor deployment frequency

---

## Support

For issues or questions:
1. Check logs for error details
2. Verify configuration
3. Test with Vercel CLI first
4. Contact support with logs

