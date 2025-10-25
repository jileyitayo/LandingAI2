"""
React File Manager
Manages all file generation for React projects including configs, UI components, and utilities.
"""

import json
from typing import Dict
from app.services.react_models import WebsiteStructure
import os
from pathlib import Path
# UI components are now read from template files instead of hardcoded


class ReactFileManager:
    """Handles generation of all React project files"""
    
    def generate_config_files(self, structure: WebsiteStructure) -> Dict[str, str]:
        """Generate configuration files (package.json, tsconfig, etc.)"""
        
        files = {}
        
        # package.json
        files["package.json"] = json.dumps({
            "name": structure.name.lower().replace(" ", "-"),
            "private": True,
            "version": "0.0.0",
            "type": "module",
            "scripts": {
                "dev": "vite",
                "build": "vite build",
                "lint": "eslint .",
                "preview": "vite preview"
            },
            "dependencies": {
                "react": "^19.1.1",
                "@types/node": "^20.0.0",
                "react-dom": "^19.1.1",
                "react-router-dom": "^6.8.0",
                "@tanstack/react-query": "^5.0.0",
                "lucide-react": "^0.462.0",
                "class-variance-authority": "^0.7.0",
                "clsx": "^2.0.0",
                "tailwind-merge": "^2.0.0",
                "@radix-ui/react-slot": "^1.0.2",
                "@radix-ui/react-label": "^2.0.2",
                "@radix-ui/react-select": "^2.0.0",
                "@radix-ui/react-dialog": "^1.0.5",
                "@radix-ui/react-avatar": "^1.0.4",
                "@radix-ui/react-separator": "^1.0.3",
                "@radix-ui/react-switch": "^1.0.3",
                "@radix-ui/react-progress": "^1.0.3",
                "@radix-ui/react-accordion": "^1.1.2",
                "@radix-ui/react-tabs": "^1.0.4",
                "@radix-ui/react-tooltip": "^1.0.7",
                "@radix-ui/react-popover": "^1.0.7",
                "@radix-ui/react-alert-dialog": "^1.0.5",
                "@radix-ui/react-dropdown-menu": "^2.0.6",
                "@radix-ui/react-toggle": "^1.0.3",
                "@radix-ui/react-toggle-group": "^1.0.4",
                "@radix-ui/react-radio-group": "^1.1.3",
                "@radix-ui/react-context-menu": "^2.1.5",
                "sonner": "^1.3.1"
            },
            "devDependencies": {
                "@eslint/js": "^9.36.0",
                "@types/react": "^19.1.13",
                "@types/react-dom": "^19.1.9",
                "@vitejs/plugin-react": "^5.0.3",
                "autoprefixer": "^10.4.0",
                "eslint": "^9.36.0",
                "eslint-plugin-react-hooks": "^5.2.0",
                "eslint-plugin-react-refresh": "^0.4.20",
                "globals": "^16.4.0",
                "postcss": "^8.4.0",
                "tailwindcss": "^3.4.0",
                "typescript": "~5.8.3",
                "typescript-eslint": "^8.44.0",
                "vite": "^7.1.7"
            }
        }, indent=2)
        
        # vite.config.ts
        files["vite.config.ts"] = """import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  base: './',
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'esbuild',
  },
  server: {
    port: 3000,
    host: true,
  },
})
"""
        
        # tsconfig.json
        files["tsconfig.json"] = json.dumps({
            "files": [],
            "references": [
                {"path": "./tsconfig.app.json"},
                {"path": "./tsconfig.node.json"}
            ]
        }, indent=2)
        
        # tsconfig.app.json
        files["tsconfig.app.json"] = json.dumps({
            "compilerOptions": {
                "target": "ES2020",
                "useDefineForClassFields": True,
                "lib": ["ES2020", "DOM", "DOM.Iterable"],
                "module": "ESNext",
                "skipLibCheck": True,
                "moduleResolution": "bundler",
                "allowImportingTsExtensions": True,
                "isolatedModules": True,
                "moduleDetection": "force",
                "noEmit": True,
                "jsx": "react-jsx",
                "strict": True,
                "noUnusedLocals": True,
                "noUnusedParameters": True,
                "noFallthroughCasesInSwitch": True,
                "baseUrl": ".",
                "paths": {
                    "@/*": ["./src/*"]
                }
            },
            "include": ["src"]
        }, indent=2)
        
        # tsconfig.node.json
        files["tsconfig.node.json"] = json.dumps({
            "compilerOptions": {
                "target": "ES2022",
                "lib": ["ES2023"],
                "module": "ESNext",
                "skipLibCheck": True,
                "moduleResolution": "bundler",
                "allowSyntheticDefaultImports": True,
                "strict": True,
                "noEmit": True,
                "types": ["node"]
            },
            "include": ["vite.config.ts"]
        }, indent=2)
        
        # tailwind.config.js
        files["tailwind.config.js"] = """/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
    },
  },
  plugins: [],
}
"""
        
        # postcss.config.js
        files["postcss.config.js"] = """export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
"""
        
        # index.html
        files["index.html"] = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{structure.name}</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""
        
        # .gitignore
        files[".gitignore"] = """# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*
pnpm-debug.log*
lerna-debug.log*

node_modules
dist
dist-ssr
*.local

# Editor directories and files
.vscode/*
!.vscode/extensions.json
.idea
.DS_Store
*.suo
*.ntvs*
*.njsproj
*.sln
*.sw?
"""
        
        # README.md
        files["README.md"] = f"""# {structure.name}

{structure.description}

## Getting Started

### Prerequisites
- Node.js 18+ 
- npm or yarn

### Installation

\`\`\`bash
npm install
\`\`\`

### Development

\`\`\`bash
npm run dev
\`\`\`

Visit http://localhost:5173

### Build

\`\`\`bash
npm run build
\`\`\`

### Preview Production Build

\`\`\`bash
npm run preview
\`\`\`

## Tech Stack

- React 19
- TypeScript
- Vite
- Tailwind CSS
- React Router
- shadcn/ui components

## Project Structure

\`\`\`
src/
├── components/     # Reusable components
├── pages/          # Page components
├── lib/            # Utility functions
└── App.tsx         # Main app component
\`\`\`

## License

MIT
"""
        
        return files
    
    def generate_ui_components(self) -> Dict[str, str]:
        """Generate shadcn/ui components by reading from template files"""
        
        files = {}

        # Path to the UI components template directory
        # more permanent is to read from Database
        template_ui_path = Path("templates/src/components/ui")

        allowed_components = ["button", "card", "input", "textarea", "label", "select", "dialog", "badge", "alert", "avatar", "separator", "switch", "progress", "skeleton", "accordion", "tabs", "tooltip", "popover", "dropdown-menu", "toggle", "radio-group", "table", "sonner"]
        
        # Read all UI component files from the template directory
        if template_ui_path.exists():
            for component_file in template_ui_path.glob("*.tsx"):
                try:
                    if component_file.name in allowed_components:
                      with open(component_file, 'r', encoding='utf-8') as f:
                          content = f.read()
                          # Store with the correct path structure for the generated project
                          files[f"src/components/ui/{component_file.name}"] = content
                except Exception as e:
                    print(f"Warning: Could not read {component_file}: {e}")
        
        # Also read the utils file
        utils_path = Path("templates/src/lib/utils.ts")
        if utils_path.exists():
            try:
                with open(utils_path, 'r', encoding='utf-8') as f:
                    files["src/lib/utils.ts"] = f.read()
            except Exception as e:
                print(f"Warning: Could not read utils.ts: {e}")
                # Fallback to hardcoded utils if file doesn't exist
                files["src/lib/utils.ts"] = '''import { type ClassValue, clsx } from "clsx"
                import { twMerge } from "tailwind-merge"

                export function cn(...inputs: ClassValue[]) {
                  return twMerge(clsx(inputs))
                }
                '''
        else:
            # Fallback to hardcoded utils if file doesn't exist
            # retrieve from a stable project with all the components
            pass
        
        return files
    
    def generate_app_files(self, structure: WebsiteStructure) -> Dict[str, str]:
        """Generate App.tsx, main.tsx, and routing"""
        
        files = {}
        
        # Generate imports for all pages
        page_imports = []
        routes = []
        
        for page in structure.pages:
            page_name = page.name.replace(" ", "")
            page_filename = page.name.lower().replace(" ", "-")
            page_imports.append(f"import {page_name} from './pages/{page_filename}'")
            routes.append(f'          <Route path="{page.path}" element={{<{page_name} />}} />')
        
        # App.tsx
        files["src/App.tsx"] = f'''import {{ BrowserRouter, Routes, Route }} from 'react-router-dom'
{chr(10).join(page_imports)}

const App = () => (
  <BrowserRouter>
    <Routes>
{chr(10).join(routes)}
    </Routes>
  </BrowserRouter>
)

export default App
'''
        
        # main.tsx
        files["src/main.tsx"] = '''import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
'''
        
        return files
    
    def generate_style_files(self, structure: WebsiteStructure) -> Dict[str, str]:
        """Generate CSS files"""
        
        files = {}
        
        # Get primary color from structure
        color = structure.color_scheme or "blue"
        
        # Map color names to HSL values
        color_map = {
            "blue": "221.2 83.2% 53.3%",
            "indigo": "239 84% 67%",
            "emerald": "142.1 76.2% 36.3%",
            "green": "142.1 76.2% 36.3%",
            "purple": "262.1 83.3% 57.8%",
            "pink": "330 81% 60%",
            "red": "0 72% 51%",
            "orange": "24.6 95% 53.1%",
        }
        
        primary_color = color_map.get(color.lower(), color_map["blue"])
        
        files["src/index.css"] = f'''@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {{
  :root {{
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 222.2 84% 4.9%;
    --primary: {primary_color};
    --primary-foreground: 210 40% 98%;
    --secondary: 210 40% 96.1%;
    --secondary-foreground: 222.2 47.4% 11.2%;
    --muted: 210 40% 96.1%;
    --muted-foreground: 215.4 16.3% 46.9%;
    --accent: 210 40% 96.1%;
    --accent-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 210 40% 98%;
    --border: 214.3 31.8% 91.4%;
    --input: 214.3 31.8% 91.4%;
    --ring: {primary_color};
    --radius: 0.5rem;
  }}

  .dark {{
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
    --card: 222.2 84% 4.9%;
    --card-foreground: 210 40% 98%;
    --popover: 222.2 84% 4.9%;
    --popover-foreground: 210 40% 98%;
    --primary: {primary_color};
    --primary-foreground: 222.2 47.4% 11.2%;
    --secondary: 217.2 32.6% 17.5%;
    --secondary-foreground: 210 40% 98%;
    --muted: 217.2 32.6% 17.5%;
    --muted-foreground: 215 20.2% 65.1%;
    --accent: 217.2 32.6% 17.5%;
    --accent-foreground: 210 40% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 210 40% 98%;
    --border: 217.2 32.6% 17.5%;
    --input: 217.2 32.6% 17.5%;
    --ring: {primary_color};
  }}
}}

@layer base {{
  * {{
    @apply border-border;
  }}
  body {{
    @apply bg-background text-foreground;
  }}
}}
'''
        
        return files


# Create singleton instance
react_file_manager = ReactFileManager()
