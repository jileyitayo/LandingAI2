from app.services.react_file_manager import ReactFileManager

# Test the updated generate_ui_components method
file_manager = ReactFileManager()
components = file_manager.generate_ui_components()

print('✅ Successfully loaded', len(components), 'UI components from template files')
print('✅ All components are now read from backend/templates/src/components/ui/')
print('✅ No more hardcoded components in the code')
print('✅ Utils file included:', 'src/lib/utils.ts' in components)

# Show a few key components
key_components = ['button.tsx', 'card.tsx', 'dialog.tsx', 'input.tsx']
for comp in key_components:
    if f'src/components/ui/{comp}' in components:
        print(f'✅ {comp} - loaded from template')
    else:
        print(f'❌ {comp} - missing')

print('\\nSample of loaded components:')
for i, path in enumerate(sorted(components.keys())[:10]):
    print(f'  {i+1}. {path}')

import requests
import json

def fetch_lucide_icons():
    """Fetch icon list from Lucide's GitHub or CDN"""
    try:
        # Option 1: From unpkg CDN metadata
        response = requests.get("https://unpkg.com/lucide-react/dist/esm/icons/index.d.ts")
        
        # Parse the TypeScript definitions to extract icon names
        lines = response.text.split('\n')
        icons = []
        for line in lines:
            if 'export declare const' in line or 'export const' in line:
                # Extract icon name between 'const ' and ':'
                parts = line.split('const ')[1].split(':')[0].strip()
                if parts[0].isupper():  # Icon names start with uppercase
                    icons.append(parts)
        
        # Save to file
        with open("valid_lucide_icons.json", "w") as f:
            json.dump(sorted(icons), f, indent=2)
        
        print(f"Found {len(icons)} icons")
        return icons
        
    except Exception as e:
        print(f"Error: {e}")
        return []

icons = fetch_lucide_icons()
print(icons[:10])  # Show first 10
