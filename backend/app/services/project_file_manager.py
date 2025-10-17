"""
Project File Manager Service
Handles saving, fetching, and updating project files in Supabase
"""

import hashlib
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from app.utils.supabase_client import get_supabase_client

logger = logging.getLogger(__name__)


class ProjectFileManager:
    """Manages project files in Supabase database"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    @staticmethod
    def _calculate_hash(content: str) -> str:
        """Calculate SHA-256 hash of file content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    @staticmethod
    def _get_file_type(file_path: str) -> str:
        """Determine file type from path"""
        if '/components/ui/' in file_path:
            return 'ui_component'
        elif '/components/' in file_path:
            return 'component'
        elif '/pages/' in file_path:
            return 'page'
        elif file_path.endswith(('.json', '.ts', '.js')) and '/' not in file_path.replace('src/', ''):
            return 'config'
        elif file_path.endswith('.css'):
            return 'style'
        elif file_path == 'package.json':
            return 'package'
        else:
            return 'other'
    
    async def save_project_files(
        self, 
        project_id: str, 
        files: Dict[str, str],
        overwrite: bool = True
    ) -> Dict[str, Any]:
        """
        Save all project files to database
        
        Args:
            project_id: The project UUID
            files: Dictionary mapping file paths to file contents
            overwrite: If True, replace existing files. If False, keep existing.
        
        Returns:
            Dictionary with stats: {inserted: int, updated: int, skipped: int}
        """
        logger.info(f"[FILE MANAGER] Saving {len(files)} files for project {project_id}")
        
        stats = {
            "inserted": 0,
            "updated": 0,
            "skipped": 0,
            "total_size": 0
        }
        
        # Prepare file records
        file_records = []
        for file_path, content in files.items():
            file_size = len(content.encode('utf-8'))
            file_type = self._get_file_type(file_path)
            content_hash = self._calculate_hash(content)
            
            file_records.append({
                "project_id": project_id,
                "file_path": file_path,
                "file_content": content,
                "file_type": file_type,
                "file_size": file_size,
                "content_hash": content_hash,
                "is_generated": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            })
            
            stats["total_size"] += file_size
        
        if overwrite:
            # Delete existing files for this project
            logger.info(f"[FILE MANAGER] Deleting existing files for project {project_id}")
            self.supabase.table("project_files")\
                .delete()\
                .eq("project_id", project_id)\
                .execute()
            
            # Insert all files in batch
            logger.info(f"[FILE MANAGER] Inserting {len(file_records)} files...")
            response = self.supabase.table("project_files")\
                .insert(file_records)\
                .execute()
            
            stats["inserted"] = len(response.data) if response.data else 0
        else:
            # Upsert approach - update if exists, insert if not
            for record in file_records:
                try:
                    # Check if file exists
                    existing = self.supabase.table("project_files")\
                        .select("id, content_hash")\
                        .eq("project_id", project_id)\
                        .eq("file_path", record["file_path"])\
                        .execute()
                    
                    if existing.data:
                        # File exists - check if content changed
                        if existing.data[0]["content_hash"] != record["content_hash"]:
                            # Update file
                            self.supabase.table("project_files")\
                                .update({
                                    "file_content": record["file_content"],
                                    "file_size": record["file_size"],
                                    "content_hash": record["content_hash"],
                                    "updated_at": record["updated_at"]
                                })\
                                .eq("id", existing.data[0]["id"])\
                                .execute()
                            stats["updated"] += 1
                        else:
                            stats["skipped"] += 1
                    else:
                        # Insert new file
                        self.supabase.table("project_files")\
                            .insert(record)\
                            .execute()
                        stats["inserted"] += 1
                        
                except Exception as e:
                    logger.error(f"[FILE MANAGER] Error saving file {record['file_path']}: {str(e)}")
                    raise
        
        logger.info(f"[FILE MANAGER] ✓ Saved files - Inserted: {stats['inserted']}, "
                   f"Updated: {stats['updated']}, Skipped: {stats['skipped']}, "
                   f"Total size: {stats['total_size'] / 1024:.2f} KB")
        
        return stats
    
    async def get_project_files(
        self, 
        project_id: str,
        file_paths: Optional[List[str]] = None
    ) -> Dict[str, str]:
        """
        Fetch project files from database
        
        Args:
            project_id: The project UUID
            file_paths: Optional list of specific file paths to fetch. If None, fetch all.
        
        Returns:
            Dictionary mapping file paths to file contents
        """
        logger.info(f"[FILE MANAGER] Fetching files for project {project_id}")
        
        # Build query
        query = self.supabase.table("project_files")\
            .select("file_path, file_content")\
            .eq("project_id", project_id)
        
        # Filter by specific paths if provided
        if file_paths:
            query = query.in_("file_path", file_paths)
        
        # Execute query
        response = query.execute()
        
        if not response.data:
            logger.warning(f"[FILE MANAGER] No files found for project {project_id}")
            return {}
        
        # Convert to dictionary
        files = {
            record["file_path"]: record["file_content"]
            for record in response.data
        }
        
        logger.info(f"[FILE MANAGER] ✓ Fetched {len(files)} files")
        return files
    
    async def get_file_metadata(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Get metadata for all files in a project (without content)
        
        Args:
            project_id: The project UUID
        
        Returns:
            List of file metadata dictionaries
        """
        response = self.supabase.table("project_files")\
            .select("id, file_path, file_type, file_size, content_hash, created_at, updated_at")\
            .eq("project_id", project_id)\
            .order("file_path")\
            .execute()
        
        return response.data if response.data else []
    
    async def update_single_file(
        self,
        project_id: str,
        file_path: str,
        new_content: str
    ) -> bool:
        """
        Update a single file's content
        
        Args:
            project_id: The project UUID
            file_path: Path of file to update
            new_content: New file content
        
        Returns:
            True if updated, False if file doesn't exist
        """
        content_hash = self._calculate_hash(new_content)
        file_size = len(new_content.encode('utf-8'))
        
        response = self.supabase.table("project_files")\
            .update({
                "file_content": new_content,
                "file_size": file_size,
                "content_hash": content_hash,
                "updated_at": datetime.utcnow().isoformat()
            })\
            .eq("project_id", project_id)\
            .eq("file_path", file_path)\
            .execute()
        
        return bool(response.data)
    
    async def delete_files(
        self,
        project_id: str,
        file_paths: Optional[List[str]] = None
    ) -> int:
        """
        Delete files from a project
        
        Args:
            project_id: The project UUID
            file_paths: Optional list of specific file paths to delete. If None, delete all.
        
        Returns:
            Number of files deleted
        """
        query = self.supabase.table("project_files")\
            .delete()\
            .eq("project_id", project_id)
        
        if file_paths:
            query = query.in_("file_path", file_paths)
        
        response = query.execute()
        return len(response.data) if response.data else 0


# Singleton instance
project_file_manager = ProjectFileManager()