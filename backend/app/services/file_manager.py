# import os
# import json
# import zipfile
# from pathlib import Path
# from typing import Dict, Any
# # import aiofiles
# # from models.website import Website

# class FileManager:
#     def __init__(self):
#         self.websites_dir = Path("generated_websites")
#         self.websites_dir.mkdir(exist_ok=True)
    
#     async def save_react_website(self, website_name: str, files: Dict[str, str]) -> Dict[str, str]:
#         """Save React website files to filesystem"""
#         website_path = self.websites_dir / website_name
#         website_path.mkdir(exist_ok=True)
        
#         file_paths = {}
        
#         for file_path, content in files.items():
#             full_path = website_path / file_path
#             full_path.parent.mkdir(parents=True, exist_ok=True)
            
#             async with aiofiles.open(full_path, 'w', encoding='utf-8') as f:
#                 await f.write(content)
            
#             file_paths[file_path] = str(full_path)
        
#         # Save website metadata
#         metadata_path = website_path / "metadata.json"
#         async with aiofiles.open(metadata_path, 'w') as f:
#             await f.write(json.dumps({"files": file_paths}, indent=2))
        
#         return file_paths
    
#     async def load_react_website(self, website_name: str) -> Dict[str, Any]:
#         """Load React website data"""
#         website_path = self.websites_dir / website_name
#         metadata_path = website_path / "metadata.json"
        
#         if not metadata_path.exists():
#             raise FileNotFoundError(f"Website {website_name} not found")
        
#         async with aiofiles.open(metadata_path, 'r') as f:
#             metadata = json.loads(await f.read())
        
#         return metadata
    
#     async def save_component(self, website_name: str, component_name: str, component_code: str) -> str:
#         """Save a single React component"""
#         website_path = self.websites_dir / website_name
#         component_path = website_path / "src" / "components" / f"{component_name}.tsx"
        
#         component_path.parent.mkdir(parents=True, exist_ok=True)
        
#         async with aiofiles.open(component_path, 'w', encoding='utf-8') as f:
#             await f.write(component_code)
        
#         return str(component_path)
    
#     async def create_zip(self, website_name: str) -> str:
#         """Create a zip file of the React website"""
#         website_path = self.websites_dir / website_name
#         zip_path = self.websites_dir / f"{website_name}.zip"
        
#         with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
#             for root, dirs, files in os.walk(website_path):
#                 for file in files:
#                     if file != "metadata.json":  # Exclude metadata
#                         file_path = Path(root) / file
#                         arc_path = file_path.relative_to(website_path)
#                         zipf.write(file_path, arc_path)
        
#         return str(zip_path)