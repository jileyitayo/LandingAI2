"""
Script to add src/components/ui/sheet.tsx to all projects
Loops through all projects and adds the sheet component if not already present
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.supabase_client import get_supabase_client
from app.services.project_file_manager import project_file_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Sheet.tsx template content
SHEET_TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "src" / "components" / "ui" / "sheet.tsx"
SHEET_FILE_PATH = "src/components/ui/sheet.tsx"


async def add_sheet_to_projects():
    """
    Main function to add sheet.tsx to all projects
    """
    try:
        # Read the sheet template
        logger.info(f"Reading sheet template from {SHEET_TEMPLATE_PATH}")
        with open(SHEET_TEMPLATE_PATH, 'r') as f:
            sheet_content = f.read()

        logger.info(f" Sheet template loaded ({len(sheet_content)} bytes)")

        # Get Supabase client
        supabase = get_supabase_client()

        # Fetch all projects
        logger.info("Fetching all projects from database...")
        response = supabase.table("projects").select("id, name, project_type").execute()

        if not response.data:
            logger.warning("No projects found in database")
            return

        projects = response.data
        logger.info(f" Found {len(projects)} projects")

        # Statistics
        stats = {
            "total": len(projects),
            "added": 0,
            "skipped": 0,
            "errors": 0,
            "not_react": 0
        }

        # Process each project
        for i, project in enumerate(projects, 1):
            project_id = project["id"]
            project_name = project["name"]
            project_type = project.get("project_type", "")

            logger.info(f"\n[{i}/{len(projects)}] Processing project: {project_name} ({project_id})")

            # Skip non-React projects
            if project_type != "react":
                logger.info(f"  � Skipping - not a React project (type: {project_type})")
                stats["not_react"] += 1
                continue

            try:
                # Check if sheet.tsx already exists in project files
                existing_files = await project_file_manager.get_project_files(
                    project_id=project_id,
                    file_paths=[SHEET_FILE_PATH]
                )

                if SHEET_FILE_PATH in existing_files:
                    logger.info(f"   Sheet component already exists - skipping")
                    stats["skipped"] += 1
                else:
                    # Add the sheet component
                    logger.info(f"  + Adding sheet component...")
                    result = await project_file_manager.save_project_file(
                        project_id=project_id,
                        file_path=SHEET_FILE_PATH,
                        file_content=sheet_content,
                        overwrite=False
                    )

                    if result["inserted"]:
                        logger.info(f"   Successfully added sheet component")
                        stats["added"] += 1
                    else:
                        logger.warning(f"  � Failed to add sheet component")
                        stats["errors"] += 1

            except Exception as e:
                logger.error(f"   Error processing project: {str(e)}")
                stats["errors"] += 1

        # Print summary
        logger.info("\n" + "="*60)
        logger.info("SUMMARY")
        logger.info("="*60)
        logger.info(f"Total projects: {stats['total']}")
        logger.info(f"React projects: {stats['total'] - stats['not_react']}")
        logger.info(f"Sheet component added: {stats['added']}")
        logger.info(f"Already exists (skipped): {stats['skipped']}")
        logger.info(f"Non-React projects (skipped): {stats['not_react']}")
        logger.info(f"Errors: {stats['errors']}")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        raise


if __name__ == "__main__":
    logger.info("Starting script to add sheet.tsx to all projects...")
    asyncio.run(add_sheet_to_projects())
    logger.info("Script completed!")
