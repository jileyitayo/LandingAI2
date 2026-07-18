"""
Shared project ownership guard for routers.
"""

from fastapi import HTTPException, status


def get_owned_project(supabase, project_id: str, user_id: str, columns: str = "id, user_id") -> dict:
    """Fetch a project row and verify the caller owns it.

    Raises 404 "Project not found" / 403 "Access denied" — the same
    contract as the inline checks it replaces. Routes whose error
    messages or query shapes differ keep their own inline checks.
    """
    response = supabase.table("projects").select(columns).eq("id", project_id).execute()
    if not response.data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    project = response.data[0]
    if project["user_id"] != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return project
