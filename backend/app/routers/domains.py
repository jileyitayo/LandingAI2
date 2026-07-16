"""
Custom Domains Router
API endpoints for connecting a custom domain to a deployed project (Pro tier).
Built on the Vercel Domains API via VercelDeployer.
"""

import re
import logging
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

from app.config import settings
from app.utils.auth import get_current_user
from app.utils.supabase_client import get_supabase_client
from app.utils.action_logger import log_action
from app.utils.entitlements import get_user_tier_name
from app.routers.deployment import verify_project_ownership
from app.services.deployments.vercel_deployer import (
    VercelDeployer,
    VercelDeploymentError,
    VercelDomainError,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["domains"])


# ============================================================================
# Request/Response Models
# ============================================================================

class SetDomainRequest(BaseModel):
    """Request to connect a custom domain to a project"""
    domain: str


class DnsRecord(BaseModel):
    """A DNS record the user must create at their DNS provider"""
    type: str  # "A" | "CNAME" | "TXT"
    name: str
    value: str


class DomainStatusResponse(BaseModel):
    """Custom domain state for a project"""
    domain: Optional[str] = None
    status: Optional[str] = None  # pending_dns | verified | error | None
    verified: bool = False
    misconfigured: bool = False
    dns_instructions: List[DnsRecord] = []
    error: Optional[str] = None
    checked_at: Optional[str] = None


# ============================================================================
# Helper Functions
# ============================================================================

# >=2 labels, letters-only TLD; each label <=63 chars, no leading/trailing hyphen
DOMAIN_REGEX = re.compile(
    r"^(?=.{4,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$"
)


def normalize_domain(raw: str) -> str:
    """
    Normalize user input to a bare lowercase hostname.

    Raises ValueError with a user-facing message on invalid input.
    """
    domain = (raw or "").strip().lower()
    domain = re.sub(r"^[a-z]+://", "", domain)
    domain = domain.split("/")[0].split("?")[0].split("#")[0]
    domain = domain.split("@")[-1].split(":")[0]
    domain = domain.rstrip(".")

    if not domain:
        raise ValueError("Please enter a domain name")

    try:
        domain = domain.encode("idna").decode("ascii")
    except (UnicodeError, UnicodeDecodeError):
        raise ValueError("That doesn't look like a valid domain name")

    if not DOMAIN_REGEX.match(domain):
        raise ValueError("That doesn't look like a valid domain name (e.g. example.com)")

    for suffix in settings.blocked_domain_suffixes:
        suffix = suffix.lower().lstrip(".")
        if domain == suffix or domain.endswith(f".{suffix}"):
            raise ValueError(f"Domains under {suffix} can't be connected")

    return domain


def _load_owned_project(project_id: str, user_id: str) -> dict:
    """Load a project row, 404 if missing, 403 if not owned by the user."""
    supabase = get_supabase_client()
    response = supabase.table("projects").select("*").eq("id", project_id).execute()
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    project = response.data[0]
    verify_project_ownership(project, user_id)
    return project


async def _resolve_vercel_project_id(project: dict, deployer: VercelDeployer) -> str:
    """
    Get the Vercel projectId for a published project, backfilling from the
    deployment for projects published before vercel_project_id was stored.
    """
    vercel_project_id = project.get("vercel_project_id")
    if vercel_project_id:
        return vercel_project_id

    deployment_id = project.get("deployment_id")
    if deployment_id:
        vercel_project_id = await deployer.get_deployment_project_id(deployment_id)
        if vercel_project_id:
            get_supabase_client().table("projects")\
                .update({"vercel_project_id": vercel_project_id})\
                .eq("id", project["id"]).execute()
            return vercel_project_id

    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Publish your site before connecting a domain"
    )


def _domain_error_to_http(e: VercelDomainError) -> HTTPException:
    """Map Vercel domain error codes to user-facing HTTP errors."""
    if e.code == "domain_already_in_use" or e.status_code == 409:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This domain is already connected to another site"
        )
    if e.code in ("invalid_domain", "forbidden", "domain_not_allowed") or e.status_code == 400:
        return HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="This domain can't be connected. Check the spelling and try again."
        )
    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=f"Domain provider error: {str(e)}"
    )


def _status_response(project: dict, live: Optional[dict] = None, error: Optional[str] = None) -> DomainStatusResponse:
    """Build the response from the project row plus an optional live check."""
    if live is not None:
        return DomainStatusResponse(
            domain=project.get("custom_domain"),
            status=live["status"],
            verified=live["verified"],
            misconfigured=live["misconfigured"],
            dns_instructions=[DnsRecord(**r) for r in live["dns_instructions"]],
            error=error,
            checked_at=datetime.utcnow().isoformat(),
        )
    return DomainStatusResponse(
        domain=project.get("custom_domain"),
        status=project.get("custom_domain_status"),
        error=error or project.get("custom_domain_error"),
        checked_at=project.get("custom_domain_updated_at"),
    )


def _update_domain_columns(project_id: str, **columns):
    supabase = get_supabase_client()
    columns["custom_domain_updated_at"] = datetime.utcnow().isoformat()
    supabase.table("projects").update(columns).eq("id", project_id).execute()


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/projects/{project_id}/domain", response_model=DomainStatusResponse)
@log_action(action_type='DOMAIN_ADD', target_resource_type='project')
async def set_custom_domain(
    project_id: str,
    request: SetDomainRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Connect a custom domain to a published project (Pro/Premium only).
    Acts as set/replace: an existing different domain is detached first.
    """
    user_id = current_user["id"]

    try:
        project = _load_owned_project(project_id, user_id)

        if get_user_tier_name(user_id) == "free":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Custom domains are available on Pro and Premium plans"
            )

        try:
            domain = normalize_domain(request.domain)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e)
            )

        if not project.get("deployment_id"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Publish your site before connecting a domain"
            )

        # Global uniqueness pre-check (the partial unique index in migration
        # 029 is the backstop against races)
        supabase = get_supabase_client()
        existing = supabase.table("projects").select("id")\
            .eq("custom_domain", domain)\
            .neq("id", project_id)\
            .execute()
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This domain is already connected to another site"
            )

        deployer = VercelDeployer()
        vercel_project_id = await _resolve_vercel_project_id(project, deployer)

        # Replacing a different domain: detach the old one first
        old_domain = project.get("custom_domain")
        if old_domain and old_domain != domain:
            try:
                await deployer.detach_custom_domain(vercel_project_id, old_domain)
            except Exception as e:
                logger.warning(f"Could not detach old domain {old_domain}: {e}")

        try:
            await deployer.attach_custom_domain(vercel_project_id, domain)
        except VercelDomainError as e:
            raise _domain_error_to_http(e)

        try:
            _update_domain_columns(
                project_id,
                custom_domain=domain,
                custom_domain_status="pending_dns",
                custom_domain_error=None,
            )
        except Exception as e:
            # Unique-violation race: someone claimed the domain concurrently
            if "23505" in str(e) or "duplicate" in str(e).lower() or "unique" in str(e).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="This domain is already connected to another site"
                )
            raise

        project["custom_domain"] = domain

        # Return a live status so the UI immediately has DNS instructions
        try:
            live = await deployer.get_domain_status(vercel_project_id, domain)
            if live["status"] != "pending_dns":
                _update_domain_columns(project_id, custom_domain_status=live["status"])
            return _status_response(project, live)
        except VercelDeploymentError as e:
            logger.warning(f"Live status check failed after attach: {e}")
            project["custom_domain_status"] = "pending_dns"
            return _status_response(project)

    except HTTPException:
        raise
    except VercelDeploymentError as e:
        logger.error(f"Error connecting domain for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Domain provider error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error connecting domain for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect domain. Please try again later."
        )


@router.get("/projects/{project_id}/domain", response_model=DomainStatusResponse)
async def get_custom_domain_status(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Custom domain status (poll target). Live-checks Vercel and refreshes the
    cached status; falls back to the cached value on Vercel errors. Not
    tier-gated so downgraded users can still see (and remove) their domain.
    """
    user_id = current_user["id"]

    try:
        project = _load_owned_project(project_id, user_id)

        domain = project.get("custom_domain")
        if not domain:
            return DomainStatusResponse()

        if not project.get("deployment_id"):
            # Unpublished: no Vercel project to check against
            return _status_response(
                project,
                error="Site is not published; the domain will reconnect on the next publish"
            )

        deployer = VercelDeployer()
        try:
            vercel_project_id = await _resolve_vercel_project_id(project, deployer)
            live = await deployer.get_domain_status(vercel_project_id, domain)

            if not live["attached"]:
                # Detached on Vercel's side (e.g. stale project) — re-attach
                try:
                    await deployer.attach_custom_domain(vercel_project_id, domain)
                    live = await deployer.get_domain_status(vercel_project_id, domain)
                except Exception as e:
                    logger.warning(f"Opportunistic re-attach of {domain} failed: {e}")

            if live["status"] != project.get("custom_domain_status"):
                _update_domain_columns(project_id, custom_domain_status=live["status"])
            return _status_response(project, live)

        except (VercelDeploymentError, HTTPException) as e:
            # Mirror deployment-status: fall back to cached state, don't 500
            detail = e.detail if isinstance(e, HTTPException) else str(e)
            logger.warning(f"Live domain check failed for project {project_id}: {detail}")
            return _status_response(project, error=f"Couldn't check domain status: {detail}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error checking domain for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check domain status. Please try again later."
        )


@router.delete("/projects/{project_id}/domain")
@log_action(action_type='DOMAIN_REMOVE', target_resource_type='project')
async def remove_custom_domain(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Disconnect a project's custom domain. Not tier-gated so downgraded users
    can clean up. Vercel-side detach is best-effort; the DB is always cleared.
    """
    user_id = current_user["id"]

    try:
        project = _load_owned_project(project_id, user_id)

        domain = project.get("custom_domain")
        if not domain:
            return {"message": "No custom domain configured", "project_id": project_id}

        if project.get("deployment_id"):
            try:
                deployer = VercelDeployer()
                vercel_project_id = await _resolve_vercel_project_id(project, deployer)
                await deployer.detach_custom_domain(vercel_project_id, domain)
            except (VercelDeploymentError, HTTPException) as e:
                detail = e.detail if isinstance(e, HTTPException) else str(e)
                logger.warning(f"Vercel detach of {domain} failed (clearing DB anyway): {detail}")

        _update_domain_columns(
            project_id,
            custom_domain=None,
            custom_domain_status=None,
            custom_domain_error=None,
        )

        return {"message": "Custom domain removed", "project_id": project_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error removing domain for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove domain. Please try again later."
        )
