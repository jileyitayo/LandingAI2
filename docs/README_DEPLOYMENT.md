# Deployment Service

## Overview

The Deployment Service handles deploying projects to Vercel using the Vercel API v2. It generates static HTML/CSS/JS files from project content and manages the deployment lifecycle.

## Features

- ✅ Deploy projects to Vercel
- ✅ Generate static files from project content
- ✅ Handle custom subdomains
- ✅ Track deployment status
- ✅ Delete deployments
- ✅ Update database with deployment information
- ✅ Graceful error handling
- ✅ Comprehensive logging

## Usage

### Basic Deployment

```python
from app.services.vercel_deployer import VercelDeployer

# Initialize service
service = VercelDeployer()

# Deploy a project
result = await service.deploy_website(project_id="proj_123")
print(f"Deployed to: {result['deployment_url']}")
```

### Check Deployment Status

```python
# Get deployment status
status = await service.get_deployment_status(deployment_id="dpl_123")
print(f"Status: {status['state']}")
print(f"Ready: {status['ready']}")
```

### Delete Deployment

```python
# Delete a deployment
success = await service.delete_deployment(deployment_id="dpl_123")
print(f"Deleted: {success}")
```

## File Generation

The service automatically generates the following files:

### 1. index.html
- Full HTML document with proper structure
- Includes SEO meta tags (title, description)
- Links to styles.css and script.js
- Uses project's html_content

### 2. styles.css
- Contains project's css_content
- Linked from index.html

### 3. script.js
- Contains project's js_content
- Loaded at end of body in index.html

### 4. vercel.json
- Vercel configuration for static site deployment
- Defines build settings and routing

### 5. package.json
- Minimal configuration required by Vercel
- Uses project subdomain or sanitized name

## Configuration

Required environment variables:

```bash
# Vercel API token (required)
VERCEL_API_TOKEN=your_token_here

# Team ID (optional, for team accounts)
VERCEL_TEAM_ID=team_123
```

## Error Handling

The service handles various error scenarios:

### Configuration Errors
```python
# Missing API token
try:
    service = VercelDeployer()
except VercelDeploymentError as e:
    print(f"Configuration error: {e}")
```

### Deployment Errors
```python
# Deployment failure
try:
    result = await service.deploy_website(project_id)
except VercelDeploymentError as e:
    print(f"Deployment failed: {e}")
```

### Network Errors
- Automatic timeout handling (60s for deploy, 30s for status)
- Graceful handling of network failures
- Retry logic for status checks

## Database Updates

After successful deployment, the service updates the project:

```sql
UPDATE projects SET
  deployment_id = 'dpl_123',
  deployment_url = 'https://mysite.vercel.app',
  last_deployed_at = NOW(),
  published = true,
  updated_at = NOW()
WHERE id = 'proj_123';
```

## Logging

The service logs all operations:

```python
# Info level
logger.info(f"Fetching project {project_id} for deployment")
logger.info(f"Deployment created successfully: {deployment_url}")

# Warning level
logger.warning(f"Deployment {deployment_id} status check timed out")

# Error level
logger.error(f"Vercel deployment failed: {error_message}")
```

## API Response Examples

### Deploy Website
```json
{
  "deployment_id": "dpl_xxx",
  "deployment_url": "https://mysite-abc123.vercel.app",
  "status": "ready",
  "deployed_at": "2024-01-01T00:00:00Z"
}
```

### Get Deployment Status
```json
{
  "deployment_id": "dpl_xxx",
  "url": "mysite-abc123.vercel.app",
  "state": "READY",
  "created_at": "2024-01-01T00:00:00Z",
  "ready": true
}
```

## Testing

### Unit Tests

```python
import pytest
from app.services.vercel_deployer import VercelDeployer

@pytest.mark.asyncio
async def test_deploy_website():
    service = VercelDeployer()
    result = await service.deploy_website(project_id="test_proj")
    
    assert result["deployment_id"]
    assert result["deployment_url"]
    assert result["status"] == "ready"
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_full_deployment_lifecycle():
    service = VercelDeployer()
    
    # Deploy
    deploy_result = await service.deploy_website(project_id)
    deployment_id = deploy_result["deployment_id"]
    
    # Check status
    status = await service.get_deployment_status(deployment_id)
    assert status["ready"]
    
    # Delete
    success = await service.delete_deployment(deployment_id)
    assert success
```

## Limitations

1. **Static Sites Only**: Only deploys static HTML/CSS/JS
2. **Single Deployment**: Each project has one active deployment
3. **No Custom Domains**: Uses Vercel-generated URLs only
4. **No Environment Variables**: Static site with no build-time variables

## Future Improvements

1. **Multiple Environments**: Support staging and preview deployments
2. **Custom Domains**: Allow custom domain configuration
3. **Deployment History**: Track and manage deployment history
4. **Rollback**: Ability to rollback to previous deployments
5. **Build Hooks**: Support for pre/post-deployment hooks
6. **Analytics**: Integration with Vercel Analytics
7. **Performance Monitoring**: Track deployment performance metrics

## Troubleshooting

### Common Issues

**Issue**: "Vercel API token not configured"
- **Solution**: Add `VERCEL_API_TOKEN` to environment variables

**Issue**: "Deployment failed: Unauthorized"
- **Solution**: Verify token is valid and has deployment permissions

**Issue**: "Project must have HTML content"
- **Solution**: Ensure project has html_content before deploying

**Issue**: Deployment times out
- **Solution**: Check network connectivity and Vercel API status

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or set environment variable:

```bash
LOG_LEVEL=DEBUG
```

## Support

For issues or questions:
1. Check the logs for detailed error messages
2. Verify configuration (API token, project content)
3. Test with smaller projects first
4. Review Vercel API documentation
5. Check Vercel status page for outages

## Related Documentation

- [Vercel API Documentation](https://vercel.com/docs/rest-api)
- [Vercel Deployment Documentation](https://vercel.com/docs/deployments)
- [Project Deployment Guide](../../docs/VERCEL_DEPLOYMENT.md)

