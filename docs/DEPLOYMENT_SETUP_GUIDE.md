# Vercel Deployment Setup Guide

This guide will help you set up the Vercel deployment integration for your SiteSmith application.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel API Token**: You'll need to generate an API token
3. **Backend Setup**: SiteSmith backend must be running
4. **Database**: Projects table must have deployment-related columns

## Step 1: Create Vercel API Token

1. Log in to your Vercel account
2. Navigate to [Account Settings > Tokens](https://vercel.com/account/tokens)
3. Click **"Create Token"**
4. Configure the token:
   - **Name**: `SiteSmith Deployment` (or any descriptive name)
   - **Scope**: Select appropriate scope (Deployments read/write)
   - **Expiration**: Choose based on your security needs
5. Click **"Create"**
6. **Important**: Copy the token immediately - it won't be shown again

## Step 2: Configure Environment Variables

### Backend Configuration

Create or update your backend `.env` file:

```bash
# Required: Vercel API Token
VERCEL_API_TOKEN=your_vercel_token_here

# Optional: Vercel Team ID (only needed for team accounts)
VERCEL_TEAM_ID=team_xxx
```

### Finding Your Team ID (if using team account)

1. Go to your team dashboard on Vercel
2. Check the URL: `https://vercel.com/teams/{team-slug}/...`
3. Or find it in team settings
4. Team IDs typically start with `team_`

### Other Required Environment Variables

Ensure these are also configured:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_key

# OpenAI (for generation)
OPENAI_API_KEY=sk-your_openai_key

# Application
APP_NAME=SiteSmith API
DEBUG=False
CORS_ORIGINS=http://localhost:3000
```

## Step 3: Verify Database Schema

Ensure your `projects` table has these columns:

```sql
-- Deployment-related columns
deployment_id TEXT,           -- Vercel deployment ID
deployment_url TEXT,          -- Full deployment URL
last_deployed_at TIMESTAMPTZ, -- Last deployment timestamp
published BOOLEAN,            -- Published status
subdomain TEXT UNIQUE,        -- Custom subdomain (optional)
```

If missing, run the migration:

```bash
cd backend
psql $DATABASE_URL -f migrations/001_initial_schema.sql
```

## Step 4: Start the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Verify the deployment endpoints are available:
- Visit http://localhost:8000/docs
- Check for `/api/v1/projects/{project_id}/deploy` endpoints

## Step 5: Test the Deployment

### Using the API

1. **Create a project with content**:
```bash
curl -X POST http://localhost:8000/api/v1/generate_website \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A simple landing page for a coffee shop",
    "project_name": "Coffee Shop"
  }'
```

2. **Wait for generation to complete**

3. **Deploy the project**:
```bash
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/deploy \
  -H "Authorization: Bearer YOUR_TOKEN"
```

4. **Check deployment status**:
```bash
curl http://localhost:8000/api/v1/projects/{project_id}/deployment-status \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Using the Frontend

1. Start the frontend:
```bash
cd frontend
npm install
npm run dev
```

2. Navigate to a project with content

3. Use the deployment button/functionality

## Step 6: Verify Deployment

1. **Check API Response**: Should receive deployment URL
2. **Visit Deployment URL**: Open the URL in your browser
3. **Verify Content**: Ensure your HTML/CSS/JS is rendered correctly
4. **Check Database**: Verify `deployment_url` and `deployment_id` are saved

## Troubleshooting

### Error: "Vercel API token not configured"

**Cause**: `VERCEL_API_TOKEN` not set in environment

**Solution**:
1. Check your `.env` file exists
2. Verify the token is correct
3. Restart the backend server

### Error: "Deployment failed: Unauthorized"

**Cause**: Invalid or expired token

**Solution**:
1. Generate a new token in Vercel
2. Update `.env` with new token
3. Verify token has deployment permissions

### Error: "Project must have HTML content"

**Cause**: Project has no content to deploy

**Solution**:
1. Generate website content first
2. Or manually add HTML content to the project
3. Ensure `html_content` is not null

### Error: "Project generation is still in progress"

**Cause**: Trying to deploy while generation is running

**Solution**:
1. Wait for generation to complete
2. Check generation status
3. Retry deployment after completion

### Deployment Times Out

**Causes**:
- Network connectivity issues
- Vercel API is down
- Large project size

**Solutions**:
1. Check your internet connection
2. Verify Vercel status: https://www.vercel-status.com/
3. Try with a smaller project first
4. Check firewall/proxy settings

### Content Not Displaying Correctly

**Causes**:
- Invalid HTML structure
- Missing CSS/JS links
- CORS issues

**Solutions**:
1. Validate HTML structure
2. Check browser console for errors
3. Verify CSS/JS files are generated
4. Review network requests

## Security Best Practices

### 1. Protect Your API Token

- ❌ **Never commit** `.env` file to git
- ❌ **Never expose** token in client-side code
- ❌ **Never log** the full token
- ✅ Use environment variables
- ✅ Rotate tokens periodically
- ✅ Use different tokens for dev/prod

### 2. Token Permissions

- Use tokens with minimal required permissions
- Create separate tokens for different environments
- Regularly audit token usage

### 3. Rate Limiting

Consider implementing rate limiting to prevent:
- Abuse of deployment endpoints
- Excessive API calls to Vercel
- Resource exhaustion

### 4. Validation

- Validate all project content before deployment
- Sanitize user input
- Check file sizes
- Limit deployment frequency

## Advanced Configuration

### Custom Subdomain Support

Enable custom subdomains by setting `subdomain` field on projects:

```bash
curl -X PATCH http://localhost:8000/api/v1/projects/{project_id} \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subdomain": "my-awesome-site"
  }'
```

The deployment will use this subdomain in the Vercel project name.

### Team Deployments

For team accounts, set `VERCEL_TEAM_ID`:

```bash
VERCEL_TEAM_ID=team_abc123xyz
```

All deployments will be under this team account.

### Production vs Development

Use different tokens for different environments:

```bash
# .env.development
VERCEL_API_TOKEN=dev_token_here

# .env.production
VERCEL_API_TOKEN=prod_token_here
```

## Monitoring and Logging

### Application Logs

The deployment service logs all operations:

```bash
# View logs
tail -f logs/app.log

# Search for deployment logs
grep "deployment" logs/app.log
```

### Vercel Dashboard

Monitor deployments in Vercel dashboard:
1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. View all deployments
3. Check build logs
4. Monitor analytics

### Action Logs

All deployment actions are logged in the `action_logs` table:

```sql
SELECT * FROM action_logs 
WHERE action_type IN ('DEPLOY', 'UNDEPLOY')
ORDER BY created_at DESC;
```

## Cost Considerations

### Vercel Pricing

- **Free Tier**: 100 GB bandwidth, unlimited deployments
- **Pro Tier**: $20/month, 1 TB bandwidth
- **Enterprise**: Custom pricing

### Deployment Limits

- Free tier: 100 deployments per day
- Consider implementing usage limits
- Monitor deployment frequency

### Optimization Tips

1. **Deploy only when necessary**: Don't deploy on every save
2. **Batch updates**: Group changes before deploying
3. **Delete old deployments**: Clean up unused deployments
4. **Use staging**: Test before production deployment

## Next Steps

1. **Integrate with Frontend**: Add deployment UI to your dashboard
2. **Add Deployment History**: Track all deployments
3. **Implement Rollback**: Add ability to rollback deployments
4. **Custom Domains**: Add support for custom domains
5. **Analytics**: Track deployment metrics
6. **Webhooks**: Listen for Vercel deployment events

## Resources

- [Vercel API Documentation](https://vercel.com/docs/rest-api)
- [Vercel Deployments Guide](https://vercel.com/docs/deployments)
- [SiteSmith Deployment Documentation](./VERCEL_DEPLOYMENT.md)
- [Deployment Service README](../backend/app/services/README_DEPLOYMENT.md)

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review application logs
3. Verify all configuration settings
4. Test with a minimal project first
5. Check Vercel status page
6. Review Vercel API documentation

## Appendix: Complete Environment Variables

```bash
# Backend .env file
APP_NAME=SiteSmith API
APP_VERSION=0.1.0
DEBUG=False

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=xxx

# OpenAI
OPENAI_API_KEY=sk-xxx

# Stripe (optional)
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Vercel (required for deployment)
VERCEL_API_TOKEN=xxx
VERCEL_TEAM_ID=team_xxx  # Optional

# CORS
CORS_ORIGINS=http://localhost:3000

# Logging
LOG_LEVEL=INFO

# Training Wheels (dev only)
TRAINING_WHEELS=False
```

