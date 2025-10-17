import requests
import json
import base64
import time
from app.config import settings
from typing import Dict, Optional, Callable


class VercelDeployer:
    """Deploy a Vite + React project to Vercel from in-memory files."""
    
    def __init__(self):
        """
        Initialize the Vercel deployer.
        
        Args:
        """
        self.token = settings.vercel_api_token
        self.api_base = "https://api.vercel.com"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def deploy(
        self,
        project_files: Dict[str, str],
        project_name: str,
        team_id: Optional[str] = None
    ) -> Dict:
        """
        Deploy project files to Vercel.
        
        Args:
            project_files: Dictionary where keys are file paths and values are file contents
                          Example: {"package.json": "...", "src/App.jsx": "..."}
            project_name: Name for the Vercel project
            team_id: Optional team ID if deploying to a team
            
        Returns:
            Dictionary containing deployment information (URL, status, etc.)
        """
        # Prepare files for upload
        files = []
        deployment_project_response = None
        for path, content in project_files.items():
            # Encode file content to base64
            encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
            files.append({
                "file": path,
                "data": encoded_content,
                "encoding": "base64"
            })
        
        # Prepare deployment payload
        payload = {
            "name": project_name,
            "files": files,
            "projectSettings": {
                "framework": "vite",
                "buildCommand": "npm run build",
                "outputDirectory": "dist",
                "installCommand": "npm install"
            },
            "target": "production",
            "public": True
        }
        
        # Add team parameter if provided
        params = {}
        if team_id:
            params["teamId"] = team_id
        
        # Create deployment
        print(f"🚀 Starting deployment for project: {project_name}")
        print(f"📦 Uploading {len(files)} files...")
        
        response = requests.post(
            f"{self.api_base}/v13/deployments",
            headers=self.headers,
            json=payload,
            params=params
        )
        
        if response.status_code == 200:
            deployment = response.json()

            deployment_project_payload = {
                "ssoProtection": None,
                "passwordProtection": None,
                "publicSource": True, # Make the project publicly viewable
            }
            deployment_project_id = deployment.get("projectId")
            
            deployment_project_url = f"{self.api_base}/v9/projects/{deployment_project_id}"

            deployment_project_response = requests.patch(
                deployment_project_url,
                headers=self.headers,
                json=deployment_project_payload
            )
            
            if deployment_project_response and deployment_project_response.status_code not in [200, 201]:
                print(f"❌ Deployment project failed with status code: {deployment_project_response.status_code}")
                print(f"Error: {deployment_project_response.text}")
                raise Exception(f"Deployment project failed: {deployment_project_response.text}")
            else:
                print(f"✅ Deployment created successfully!")
                print(f"🔗 URL: https://{deployment.get('url')}")
                print(f"📊 Status: {deployment.get('readyState', 'BUILDING')}")
                return deployment
        else:
            print(f"❌ Deployment failed with status code: {deployment_project_response.status_code}")
            print(f"Error: {deployment_project_response.text}")
            raise Exception(f"Deployment failed: {response.text}")
    
    def get_deployment_status(self, deployment_id: str, team_id: Optional[str] = None) -> Dict:
        """
        Check the status of a deployment.
        
        Args:
            deployment_id: The deployment ID returned from deploy()
            team_id: Optional team ID if checking team deployment
            
        Returns:
            Dictionary with deployment status information
        """
        params = {}
        if team_id:
            params["teamId"] = team_id
        
        response = requests.get(
            f"{self.api_base}/v13/deployments/{deployment_id}",
            headers=self.headers,
            params=params
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to get deployment status: {response.text}")
    
    def wait_for_deployment(
        self,
        deployment_id: str,
        team_id: Optional[str] = None,
        check_interval: int = 5,
        timeout: int = 600,
        on_status_change: Optional[Callable[[str], None]] = None
    ) -> Dict:
        """
        Wait for a deployment to complete (or fail).
        
        Args:
            deployment_id: The deployment ID to monitor
            team_id: Optional team ID
            check_interval: Seconds between status checks (default: 5)
            timeout: Maximum seconds to wait (default: 600/10 minutes)
            on_status_change: Optional callback function when status changes
            
        Returns:
            Final deployment information
            
        Raises:
            TimeoutError: If deployment doesn't complete within timeout
            Exception: If deployment fails
        """
        start_time = time.time()
        last_status = None
        
        print(f"⏳ Waiting for deployment to complete (timeout: {timeout}s)...")
        
        while time.time() - start_time < timeout:
            deployment = self.get_deployment_status(deployment_id, team_id)
            current_status = deployment.get('readyState', 'UNKNOWN')
            
            # Notify on status change
            if current_status != last_status:
                if on_status_change:
                    on_status_change(current_status)
                else:
                    print(f"📊 Status: {current_status}")
                last_status = current_status
            
            # Check if deployment is complete
            if current_status == 'READY':
                print(f"✅ Deployment completed successfully!")
                print(f"🔗 Live URL: https://{deployment.get('url')}")
                return deployment
            
            # Check if deployment failed
            if current_status == 'ERROR':
                error_msg = deployment.get('error', {}).get('message', 'Unknown error')
                print(f"❌ Deployment failed: {error_msg}")
                raise Exception(f"Deployment failed: {error_msg}")
            
            # Check if deployment was canceled
            if current_status == 'CANCELED':
                print(f"⚠️ Deployment was canceled")
                raise Exception("Deployment was canceled")
            
            # Wait before next check
            time.sleep(check_interval)
        
        raise TimeoutError(f"Deployment did not complete within {timeout} seconds")



# Example usage
if __name__ == "__main__":
    # Example project files in memory
    project_files = {
        "package.json": json.dumps({
            "name": "vite-react-app",
            "private": True,
            "version": "0.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "preview": "vite preview"
            },
            "dependencies": {
                "react": "^18.2.0",
                "react-dom": "^18.2.0"
            },
            "devDependencies": {
                "@types/react": "^18.2.0",
                "@types/react-dom": "^18.2.0",
                "@vitejs/plugin-react": "^4.0.0",
                "vite": "^4.3.0"
            }
        }, indent=2),
        
        "vite.config.js": """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
})
""",
        
        "index.html": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Vite + React</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.jsx"></script>
  </body>
</html>
""",
        
        "src/main.jsx": """import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
""",
        
        "src/App.jsx": """import { useState } from 'react'
import './App.css'

function App() {
  const [count, setCount] = useState(0)

  return (
    <div className="App">
      <h1>Vite + React</h1>
      <div className="card">
        <button onClick={() => setCount((count) => count + 1)}>
          count is {count}
        </button>
      </div>
    </div>
  )
}

export default App
""",
        
        "src/App.css": """#root {
  max-width: 1280px;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
}

.card {
  padding: 2em;
}

button {
  border-radius: 8px;
  border: 1px solid transparent;
  padding: 0.6em 1.2em;
  font-size: 1em;
  font-weight: 500;
  font-family: inherit;
  background-color: #1a1a1a;
  cursor: pointer;
  transition: border-color 0.25s;
}

button:hover {
  border-color: #646cff;
}
""",
        
        "src/index.css": """body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
"""
    }
    
    # Deploy to Vercel
    deployer = VercelDeployer()
    
    try:
        deployment = deployer.deploy(
            project_files=project_files,
            project_name="my-vite-react-app"
        )
        
        # Optionally check deployment status
        deployment_id = deployment.get('id')
        status = deployer.get_deployment_status(deployment_id)
        print(f"\nDeployment Status: {status.get('readyState')}")

        # Wait for deployment to complete
        deployer.wait_for_deployment(deployment_id)
        
    except Exception as e:
        print(f"Deployment error: {e}")