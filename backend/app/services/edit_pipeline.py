"""
Edit Pipeline Service
The AI edit engine behind the /edit endpoints: page-file resolution,
build-verify-repair loop, page creation, the main edit pipeline, and the
property-edit queue handler.
"""

import asyncio
import json
import logging
import re
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import HTTPException, status

from app.config import settings
from app.utils.supabase_client import get_supabase_client
from app.utils.action_logger import ActionLogger
from app.utils.image_loader import fetch_images_as_data_urls
from app.services.project_file_manager import project_file_manager
from app.services.vite_preview_service import vite_preview_service
from app.services.component_editor_service import component_editor_service
from app.services import component_library
from app.services.validators.error_fixer import error_fixer
from app.services.validators.build_tester import BuildError, BuildTester
from app.services.direct_code_editor import direct_code_editor
from app.services.component_relationship_tracker import ComponentRelationshipTracker
from app.services.intent_checker import URL_RE
from app.services.site_ingestion import extract_site_design, to_prompt_block, WEAK_CONFIDENCE
from app.services.quota_service import check_user_rate_limit, log_ai_call
from app.models.generation import (
    ComponentEditRequest,
    ComponentEditResponse,
    PropertyChange,
    PropertyEditRequest,
    PropertyEditResponse,
)

logger = logging.getLogger(__name__)


def _find_page_file(files: Dict[str, str]) -> Optional[str]:
    """Pick the page file to target for a no-selection (whole page) edit."""
    page_files = sorted(f for f in files if f.startswith("src/pages/") and f.endswith(".tsx"))
    # Prefer the landing page regardless of casing (Home.tsx, home.tsx, index.tsx, ...)
    for name in ("home.tsx", "index.tsx", "landing.tsx", "main.tsx"):
        for f in page_files:
            if f.rsplit("/", 1)[-1].lower() == name:
                return f
    if page_files:
        return page_files[0]
    if "src/App.tsx" in files:
        return "src/App.tsx"
    return None


def _page_file_for_route(route, website_structure: dict, files: Dict[str, str]):
    """
    Resolve the preview's current route to its page file via
    website_structure.pages (same kebab naming rule as generate_app_files).
    """
    if not route:
        return None
    for page in (website_structure or {}).get("pages", []) or []:
        if page.get("path") == route and page.get("name"):
            candidate = f"src/pages/{page['name'].lower().replace(' ', '-')}.tsx"
            if candidate in files:
                return candidate
    return None


def _pages_importing(component_file: str, files: Dict[str, str]) -> List[str]:
    """Page files that import the given component (blast radius of a component edit)."""
    name = component_file.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    pattern = re.compile(rf"from\s+['\"](?:@/components/|\./components/|\.\./components/){name}['\"]")
    return [
        p for p, content in files.items()
        if p.startswith("src/pages/") and pattern.search(content)
    ]


async def _build_verify_with_repairs(
    project_id: str,
    files: Dict[str, str],
    new_codes: Dict[str, str],
    max_repair_attempts: int = 2,
    cost_tracker=None,
) -> tuple:
    """
    Build the candidate project (files + new_codes) via the preview service,
    feeding build errors back to the LLM for up to `max_repair_attempts`
    repairs. Mutates new_codes to stay in sync with any repairs.

    Returns (preview_result_or_None, candidate_files).
    """
    candidate_files = {**files, **new_codes}
    preview_result = None
    build_output = ""
    build_tester = BuildTester()

    for attempt in range(max_repair_attempts + 1):
        try:
            preview_result = await asyncio.to_thread(
                vite_preview_service.create_preview, project_id, candidate_files
            )
            break
        except Exception as build_exc:
            build_output = str(build_exc)
            logger.warning(f"[BUILD VERIFY] Candidate build failed (attempt {attempt + 1}): {build_output[:500]}")
            if attempt >= max_repair_attempts:
                break

            parsed_errors = build_tester._parse_build_errors(build_output)
            # Keep only errors that resolve to a real project file — the parser
            # sometimes attributes vite output to bogus paths like "build"
            parsed_errors = [
                e for e in parsed_errors
                if error_fixer._find_matching_file(e.file_path, candidate_files)
            ]
            if not parsed_errors:
                # Attribute errors from file paths mentioned in the build output,
                # falling back to the files this edit touched
                import re as _re
                mentioned = {
                    m for m in _re.findall(r"src/[\w\-./]+\.(?:tsx|ts|jsx|js|css)", build_output)
                    if m in candidate_files
                }
                target_files = mentioned or set(new_codes.keys())
                parsed_errors = [
                    BuildError(file_path=f, line=None, column=None,
                               error_type="build", message=build_output[:1500])
                    for f in target_files
                ]

            fixed_files, _ = await asyncio.to_thread(
                error_fixer.fix_build_errors, candidate_files, parsed_errors, build_output,
                cost_tracker
            )
            candidate_files = fixed_files
            # Keep edited-file contents in sync with any repairs
            for f in new_codes:
                new_codes[f] = candidate_files.get(f, new_codes[f])

    return preview_result, candidate_files


async def _run_page_creation(
    project_id: str,
    request: ComponentEditRequest,
    user_id: str,
    project: Dict[str, Any],
    files: Dict[str, str],
    supabase,
    progress,
    cost_tracker=None,
) -> ComponentEditResponse:
    """
    Confirmed create-page flow (from the edit chat): generate the page with
    the generation model, wire routing + linkage, build-verify, save, update
    website_structure, and log one GENERATION quota unit. The rate check
    already ran with call_type='generation' in the pipeline entry.
    """
    from app.services.page_creation_service import page_creation_service, PageCreationError

    progress("analyzing", "Planning the new page")
    try:
        result = await page_creation_service.create_page(
            project=project,
            files=files,
            new_page=request.confirmed_page,
            selected_element=request.selected_element,
            instruction=request.instruction,
            cost_tracker=cost_tracker,
        )
    except PageCreationError as e:
        return ComponentEditResponse(success=False, message=str(e))

    new_codes: Dict[str, str] = result["new_codes"]
    route = result["route"]
    nav_label = result["nav_label"]

    # Element linkage: wire the selected element to the new page via a normal
    # LLM edit on its component file (build-verified together with the page)
    if result["linked_via"] == "element" and request.selected_element:
        progress("editing", "Linking the selected element to the new page")
        source_file = await component_editor_service.identify_component(request.selected_element, files)
        if source_file and source_file in files:
            link_instruction = (
                f"Make the selected element navigate to the new page at \"{route}\" using a "
                f"react-router <Link to=\"{route}\"> (or add an onClick navigate) while keeping "
                f"its appearance unchanged. Ensure the Link import from 'react-router-dom' exists."
            )
            link_files = {**files, **new_codes}
            success, _old, linked_code, error = await component_editor_service.modify_component_code(
                file_path=source_file,
                instruction=link_instruction,
                element_context=request.selected_element,
                project_id=project_id,
                files=link_files,
                business_context=project.get("business_analysis"),
                scope="section",
                cost_tracker=cost_tracker,
            )
            if success and linked_code:
                new_codes[source_file] = linked_code
            else:
                logger.warning(f"[PAGE CREATE] Element link edit failed (non-fatal): {error}")

    progress("building", "Building and verifying the new page")
    preview_result, candidate_files = await _build_verify_with_repairs(
        project_id, files, new_codes, cost_tracker=cost_tracker
    )
    if preview_result is None:
        logger.error("[PAGE CREATE] Build failed after repair attempts; nothing saved")
        return ComponentEditResponse(
            success=False,
            message="The new page didn't compile, so nothing was changed. Try rephrasing the request.",
        )

    # Green build — persist changed/new files
    files_to_save = {
        path: content for path, content in candidate_files.items()
        if files.get(path) != content
    }
    logger.info(f"[PAGE CREATE] Saving {len(files_to_save)} file(s)")
    for file_path, file_content in files_to_save.items():
        save_success, save_message = await component_editor_service.apply_component_edit(
            project_id=project_id, file_path=file_path, new_code=file_content
        )
        if not save_success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save {file_path}: {save_message}",
            )

    # Persist the structure (pages + navigation) and swap the preview
    new_preview_id = preview_result.get("preview_id")
    preview_url = preview_result.get("preview_url")
    old_preview_id = project.get("preview_id")
    try:
        supabase.table("projects").update({
            "website_structure": result["updated_structure"],
            "preview_id": new_preview_id,
            "last_edited_at": datetime.utcnow().isoformat(),
        }).eq("id", project_id).execute()
    except Exception as e:
        logger.warning(f"[PAGE CREATE] Failed to update project row: {e}")
    if old_preview_id and old_preview_id != new_preview_id:
        try:
            vite_preview_service.delete_preview(old_preview_id)
        except Exception as e:
            logger.warning(f"[PAGE CREATE] Failed to delete old preview {old_preview_id}: {e}")

    linked_note = {
        "nav": "and added it to the navigation menu",
        "element": "and linked it from your selected element",
        "none": "— reachable at its URL (no nav link could be added automatically)",
    }[result["linked_via"]]
    edit_description = f"Created the \"{nav_label}\" page at {route} {linked_note}."

    # Chat history (page creation is not revertible via edit history in v1,
    # so no project_edit_history rows)
    chat_message_id = str(uuid.uuid4())
    try:
        supabase.table("project_chat_messages").insert({
            "id": chat_message_id,
            "project_id": project_id,
            "user_id": user_id,
            "message_type": "edit",
            "user_prompt": request.instruction,
            "ai_response": edit_description,
            "metadata": {
                "kind": "create_page",
                "page_file": result["page_file"],
                "route": route,
                "files_saved": sorted(files_to_save.keys()),
            },
        }).execute()
    except Exception as e:
        logger.error(f"[PAGE CREATE] Failed to save chat history: {e}")

    # One generation quota unit (the rate check at pipeline entry used 'generation')
    await log_ai_call(
        user_id=user_id,
        call_type="generation",
        project_id=project_id,
        endpoint=f"/edit/project/{project_id}",
        supabase_client=supabase,
    )

    progress("done", "New page created")
    logger.info(f"[PAGE CREATE] ✓ Created {result['page_file']} at {route} (linked via {result['linked_via']})")
    return ComponentEditResponse(
        success=True,
        message=edit_description,
        edit_description=edit_description,
        updated_file=result["page_file"],
        updated_files=sorted(files_to_save.keys()),
        preview_url=preview_url,
        preview_id=new_preview_id,
        chat_message_id=chat_message_id,
    )


async def _run_edit_pipeline(
    project_id: str,
    request: ComponentEditRequest,
    user_id: str,
    progress=None,
) -> ComponentEditResponse:
    """
    Core edit pipeline shared by the standard and streaming edit endpoints.

    Identifies the target component, runs the AI edit (multimodal + structural
    escalation), build-verifies, saves, and records history. `progress(stage,
    detail)` — if provided — is called at stage boundaries so the streaming
    endpoint can surface live status; it's a no-op for the standard endpoint.

    Returns a ComponentEditResponse or raises HTTPException.
    """
    progress = progress or (lambda *a, **k: None)
    supabase = get_supabase_client()

    # Edit-path token accounting: one generation_cost_tracking row per edit
    # request (analysis + modify + build-fix calls). Persisted in the finally
    # block so early confirm/clarify returns that already burned an analysis
    # call are counted too; requests that never reached an LLM save nothing.
    from app.services.cost_calculator import CostTracker
    cost_tracker = CostTracker(generation_type="edit", endpoint=f"/edit/project/{project_id}")

    logger.info(f"[COMPONENT EDIT] Starting edit request for project {project_id} by user {user_id}")
    logger.info(f"[COMPONENT EDIT] Instruction: '{request.instruction}' (length: {len(request.instruction)})")
    if request.selected_element:
        logger.info(f"[COMPONENT EDIT] Selected element tag: {request.selected_element.get('tagName', 'unknown')}")
        logger.info(f"[COMPONENT EDIT] Selected element text content: '{request.selected_element.get('textContent', '')[:50]}...'")
    else:
        logger.info(f"[COMPONENT EDIT] No element selected — page-scope edit")

    try:
        # Check rate limits: normal edits use the edit quota; a confirmed page
        # creation is a full page generation and consumes the generation quota
        logger.info(f"[COMPONENT EDIT] Checking rate limits...")
        rate_call_type = "generation" if request.confirmed_page else "edit"
        is_allowed, rate_info = await check_user_rate_limit(user_id, supabase, call_type=rate_call_type)

        if not is_allowed:
            logger.warning(f"[COMPONENT EDIT] Rate limit exceeded for user {user_id}: {rate_info.get('limit_type')}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=rate_info.get('message', 'Rate limit exceeded'),
                headers={
                    "Retry-After": str(rate_info.get('retry_after_seconds', 60)),
                    "X-RateLimit-Type": rate_info.get('limit_type', 'unknown'),
                    "X-RateLimit-Tier": rate_info.get('tier', 'unknown')
                }
            )

        # Verify project ownership and fetch business context
        logger.info(f"[COMPONENT EDIT] Fetching project {project_id} from database")
        response = supabase.table("projects")\
            .select("id, user_id, project_type, generation_status, business_analysis, website_structure, preview_id")\
            .eq("id", project_id)\
            .execute()

        if not response.data:
            logger.error(f"[COMPONENT EDIT] Project {project_id} not found in database")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        project = response.data[0]
        logger.info(f"[COMPONENT EDIT] Found project: type={project.get('project_type')}, status={project.get('generation_status')}, owner={project.get('user_id')}")
        
        # Check ownership
        if project["user_id"] != user_id:
            logger.error(f"[COMPONENT EDIT] Access denied: user {user_id} does not own project {project_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        # Check if it's a React project
        if project.get("project_type") != "react":
            logger.error(f"[COMPONENT EDIT] Project {project_id} is not a React project (type: {project.get('project_type')})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This is not a React project"
            )
        
        # Check if project is completed
        if project.get("generation_status") != "completed":
            logger.error(f"[COMPONENT EDIT] Project {project_id} is not completed (status: {project.get('generation_status')})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project generation is not completed yet"
            )
        
        # Resolve the selection set (multi-select sends selected_elements; single select falls back)
        selected_elements = request.selected_elements or (
            [request.selected_element] if request.selected_element else []
        )
        scope = request.scope or "element"
        files = await project_file_manager.get_project_files(project_id)

        # Confirmed page creation: skip the edit targeting/analysis entirely —
        # the user already approved the page spec in the chat
        if request.confirmed_page:
            return await _run_page_creation(
                project_id, request, user_id, project, files, supabase, progress,
                cost_tracker=cost_tracker
            )

        if not selected_elements:
            # No selection: the whole page is the target (chat message without a
            # selection). Prefer the page currently shown in the preview iframe.
            scope = "page"
            page_file = _page_file_for_route(
                request.current_route, project.get("website_structure") or {}, files
            ) or _find_page_file(files)
            if page_file:
                logger.info(f"[COMPONENT EDIT] Page-scope target resolved to {page_file} (route: {request.current_route})")
            if not page_file:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not identify a page file to edit"
                )
            selected_elements = [{
                "tagName": "page",
                "textContent": "",
                "classList": [],
                "attributes": {},
                "component": {"componentFile": page_file},
            }]
        logger.info(f"[COMPONENT EDIT] Editing {len(selected_elements)} selected element(s), scope={scope}")

        # Group selected elements by their component file
        targets_by_file: Dict[str, List[Dict[str, Any]]] = {}
        for element in selected_elements:
            component_file = await component_editor_service.identify_component(element, files)
            if not component_file:
                logger.error(f"[COMPONENT EDIT] Could not identify component file for element: {element.get('tagName', 'unknown')}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Could not identify component file for one of the selected elements"
                )
            targets_by_file.setdefault(component_file, []).append(element)

        logger.info(f"[COMPONENT EDIT] Target files: {list(targets_by_file.keys())}")

        # Extract business context for better AI editing
        business_analysis = project.get("business_analysis", {})
        logger.info(f"[COMPONENT EDIT] Business analysis available: {bool(business_analysis)}")

        # Conversational context: feed the last few edits so follow-ups resolve
        # ("make it darker" after "make the heading blue" should target the same
        # element/color without re-selection). Kept as a SEPARATE prompt block
        # (not merged into the instruction text) — mixing it into the quoted
        # "USER INSTRUCTION" let history bleed into targeting and caused edits
        # to land on a previously-touched element instead of the new selection.
        effective_instruction = request.instruction
        conversation_context = None
        try:
            recent_messages = (
                supabase.table("project_chat_messages")
                .select("user_prompt, ai_response")
                .eq("project_id", project_id)
                .eq("message_type", "edit")
                .order("created_at", desc=True)
                .limit(6)
                .execute()
            )
            history_rows = list(reversed(recent_messages.data or []))
            if history_rows:
                transcript_lines = []
                budget = 1500  # rough character budget, not exact tokens
                for row in history_rows:
                    line = f'User: {row["user_prompt"][:200]}\nApplied: {row["ai_response"][:200]}'
                    if budget - len(line) < 0:
                        break
                    transcript_lines.append(line)
                    budget -= len(line)
                if transcript_lines:
                    conversation_context = "\n---\n".join(transcript_lines)
        except Exception as e:
            logger.warning(f"[COMPONENT EDIT] Failed to load conversational context: {e}")

        # Make uploaded attachment URLs available to the LLM: when the user says
        # "use the attached image", the model must embed these exact public URLs.
        # The images themselves are also sent as multimodal input (base64 data URLs).
        attachment_images: List[str] = []
        if request.attachments:
            media_ids = [a["media_id"] for a in request.attachments if a.get("media_id")]
            if media_ids:
                owned = supabase.table("project_media")\
                    .select("id")\
                    .in_("id", media_ids)\
                    .eq("user_id", user_id)\
                    .execute()
                owned_ids = {r["id"] for r in (owned.data or [])}
                if owned_ids != set(media_ids):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="One or more attachments do not belong to you"
                    )
            attachment_urls = [a["url"] for a in request.attachments if a.get("url")]
            attachment_images = await fetch_images_as_data_urls(attachment_urls)
            if attachment_urls:
                url_lines = "\n".join(f"  {i+1}. {u}" for i, u in enumerate(attachment_urls))
                effective_instruction = (
                    f"{effective_instruction}\n\n"
                    f"[The user attached {len(attachment_urls)} uploaded image(s), publicly hosted at:\n"
                    f"{url_lines}\n"
                    f"Follow the ATTACHED IMAGES guidance for whether to embed these URLs or "
                    f"treat the images as a style reference only.]"
                )
                logger.info(f"[COMPONENT EDIT] {len(attachment_urls)} attachment URL(s) added to instruction context")

        # URL references in the edit instruction ("make the hero look like
        # https://stripe.com"): fetch the referenced site's design and append it
        # verbatim — same mechanism as the attachment-URL block above — so it
        # feeds both analyze_edit_request and the code edit. A weak/failed fetch
        # asks for a screenshot via the confirm channel instead of guessing.
        if settings.url_ingestion_enabled:
            instruction_urls = [u.rstrip(").,;\"'") for u in URL_RE.findall(request.instruction)]
            if instruction_urls:
                ref_url = instruction_urls[0]
                extraction = await extract_site_design(ref_url)
                if extraction.ok and extraction.confidence >= WEAK_CONFIDENCE:
                    from app.services.intent_checker import _keyword_fidelity
                    design_block = to_prompt_block(extraction, _keyword_fidelity(request.instruction))
                    if design_block:
                        effective_instruction = f"{effective_instruction}\n\n{design_block}"
                        logger.info(f"[COMPONENT EDIT] Design context from {ref_url} added to instruction (confidence={extraction.confidence})")
                elif settings.edit_clarify_enabled and not request.skip_clarification \
                        and not request.attachments:
                    question = (
                        f"I couldn't read enough of {ref_url} to copy its design — could you "
                        "attach a screenshot of it, or describe the colors, fonts and layout "
                        "you want?"
                    )
                    logger.info(f"[COMPONENT EDIT] Weak URL extraction ({extraction.failure_reason or extraction.confidence}) — asking for clarification")
                    # Deliberately no log_ai_call: a clarification round is free
                    return ComponentEditResponse(
                        success=True,
                        needs_confirmation=True,
                        message=question,
                        confirmation={
                            "kind": "clarify",
                            "question": question,
                            "wants_attachment": True,
                        },
                    )

        # The user's answer from a previous clarify round rides with the instruction.
        if request.clarification_response:
            effective_instruction = (
                f"{effective_instruction}\nClarification from user: {request.clarification_response.strip()}"
            )

        # Analyze the request once up front: structural rewrites ("turn this into
        # a carousel") escalate element scope to section, drop containment, and
        # pull vetted patterns (+ their npm deps) from the component library.
        progress("analyzing", "Understanding your request")
        shared_component_files = [
            p for p in files
            if p.startswith("src/components/") and not p.startswith("src/components/ui/")
            and p.endswith((".tsx", ".jsx"))
        ]
        website_structure = project.get("website_structure") or {}
        existing_routes = [
            p.get("path") for p in website_structure.get("pages", []) if p.get("path")
        ] or ["/"]
        has_real_selection = bool(request.selected_element or request.selected_elements)
        edit_analysis = await component_editor_service.analyze_edit_request(
            effective_instruction, selected_elements[0], images=attachment_images or None,
            shared_components=shared_component_files or None,
            existing_routes=existing_routes,
            has_selection=has_real_selection,
            cost_tracker=cost_tracker
        )

        # Clarify-first: the analysis flagged a missing resource or contradiction
        # ("use our logo" with nothing attached). Ask instead of guessing — max
        # one round (skip_clarification on resubmit bypasses this gate).
        if (
            settings.edit_clarify_enabled
            and edit_analysis.get("clarification_question")
            and not request.skip_clarification
            and not (request.confirmed_target or request.confirmed_page)
        ):
            question = str(edit_analysis["clarification_question"]).strip()
            if question:
                logger.info(f"[COMPONENT EDIT] Clarification requested: {question}")
                # Deliberately no log_ai_call: a clarification round is free
                return ComponentEditResponse(
                    success=True,
                    needs_confirmation=True,
                    message=question,
                    confirmation={
                        "kind": "clarify",
                        "question": question,
                        "wants_attachment": bool(edit_analysis.get("clarification_wants_attachment")),
                    },
                )

        # New-page intent: ask the user to confirm the page spec before running
        # the (generation-quota) page creation. No edit/generation has run yet.
        if edit_analysis.get("edit_type") == "create_page" and edit_analysis.get("new_page"):
            new_page = edit_analysis["new_page"]
            if not has_real_selection:
                new_page["link_from_selection"] = False
            route_hint = new_page.get("route") or ""
            link_hint = (
                "linked from your selected element"
                if new_page.get("link_from_selection")
                else "added to the navigation menu"
            )
            logger.info(f"[COMPONENT EDIT] Create-page intent: {new_page.get('name')} at {route_hint} — asking for confirmation")
            # Deliberately no log_ai_call: an aborted confirm shouldn't burn quota
            return ComponentEditResponse(
                success=True,
                needs_confirmation=True,
                message=(
                    f"I'll create a new page \"{new_page.get('nav_label') or new_page.get('name')}\" "
                    f"at {route_hint}, {link_hint}. This counts as one website generation. Create it?"
                ),
                confirmation={
                    "kind": "create_page",
                    "new_page": new_page,
                },
            )

        is_structural = bool(edit_analysis.get("requires_structural_rewrite")) and \
            edit_analysis.get("confidence", 0) >= 0.6

        # Retargeting: the instruction implies a shared component beyond the
        # selection ("the header", "all buttons"). Editing it changes every
        # page that imports it, so ask the user to confirm before running the
        # edit. confirmed_target on resubmit applies the retarget directly.
        if request.confirmed_target:
            if request.confirmed_target not in files:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Confirmed target file not found: {request.confirmed_target}"
                )
            if list(targets_by_file.keys()) != [request.confirmed_target]:
                logger.info(f"[COMPONENT EDIT] Retargeting confirmed: {list(targets_by_file.keys())} -> {request.confirmed_target}")
                targets_by_file = {request.confirmed_target: selected_elements}
                if scope == "element":
                    scope = "section"  # containment against the original element no longer applies
        else:
            suggested_file = edit_analysis.get("target_component_file")
            if (
                suggested_file
                and suggested_file in files
                and suggested_file.startswith("src/components/")
                and suggested_file not in targets_by_file
                and edit_analysis.get("confidence", 0) >= 0.6
            ):
                affected_pages = _pages_importing(suggested_file, files)
                if len(affected_pages) > 1:
                    component_name = suggested_file.rsplit("/", 1)[-1].rsplit(".", 1)[0]
                    page_names = [p.rsplit("/", 1)[-1].rsplit(".", 1)[0] for p in affected_pages]
                    logger.info(
                        f"[COMPONENT EDIT] Retarget suggested: {suggested_file} "
                        f"(affects {len(affected_pages)} pages) — asking for confirmation"
                    )
                    # Deliberately no log_ai_call: an aborted confirm shouldn't burn quota
                    return ComponentEditResponse(
                        success=True,
                        needs_confirmation=True,
                        message=(
                            f"This edit targets the shared {component_name} component, "
                            f"which appears on {len(affected_pages)} pages "
                            f"({', '.join(page_names)}). Apply it site-wide?"
                        ),
                        confirmation={
                            "kind": "retarget",
                            "target_file": suggested_file,
                            "resolved_file": next(iter(targets_by_file), None),
                            "affected_pages": affected_pages,
                            "reason": f"The instruction refers to the {component_name} component, which is shared across pages.",
                        },
                    )
        matched_library = []
        library_note = None
        if is_structural:
            matched_library = component_library.match_components(
                edit_analysis.get("suggested_components"), request.instruction
            )
            library_note = component_library.build_library_note(matched_library)
            if scope == "element":
                scope = "section"
                logger.info(
                    f"[COMPONENT EDIT] Structural rewrite detected "
                    f"(components: {[c.name for c in matched_library]}) — escalating scope to section"
                )

        # LLM edit per target file, with scope-containment verification and one strict retry
        old_codes: Dict[str, str] = {}
        new_codes: Dict[str, str] = {}
        for component_file, targets in targets_by_file.items():
            primary_element = targets[0]
            additional = targets[1:]
            strict_note = None
            contained = True
            old_code, new_code = "", ""

            progress("editing", f"Rewriting {component_file.split('/')[-1]}")
            for attempt in range(2):
                logger.info(f"[COMPONENT EDIT] Calling AI to modify {component_file} (attempt {attempt + 1})")
                success, old_code, new_code, error = await component_editor_service.modify_component_code(
                    file_path=component_file,
                    instruction=effective_instruction,
                    element_context=primary_element,
                    project_id=project_id,
                    files=files,
                    business_context=business_analysis,
                    additional_contexts=additional,
                    scope=scope,
                    strict_note=strict_note,
                    images=attachment_images or None,
                    analysis=edit_analysis,
                    library_note=library_note,
                    conversation_context=conversation_context,
                    cost_tracker=cost_tracker
                )

                if not success:
                    logger.error(f"[COMPONENT EDIT] AI modification failed: {error}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Failed to modify component: {error}"
                    )

                # Element scope must only change the selected element(s)
                if scope != "element":
                    break
                contained, violation = component_editor_service.check_edit_containment(
                    old_code, new_code, targets
                )
                if contained:
                    break
                strict_note = (
                    f"You modified code outside the selected element(s) ({violation}). "
                    "Change ONLY the selected element(s); every other line of the file "
                    "must remain exactly as it is."
                )
                cost_tracker.increment_retries()

            if scope == "element" and not contained:
                logger.error(f"[COMPONENT EDIT] Containment violation persisted for {component_file}; nothing saved")
                return ComponentEditResponse(
                    success=False,
                    message=(
                        "The AI kept changing code outside your selection, so nothing was changed. "
                        "Try rephrasing the instruction or widening the scope to the section."
                    )
                )

            old_codes[component_file] = old_code
            new_codes[component_file] = new_code

        # Structural rewrites may need new npm deps (e.g. embla for carousels):
        # merge them into package.json BEFORE the preview build (which runs npm install)
        if matched_library and "package.json" in files:
            deps = component_library.collect_dependencies(matched_library)
            updated_package = component_library.ensure_package_dependencies(
                new_codes.get("package.json", files["package.json"]), deps
            )
            if updated_package:
                old_codes.setdefault("package.json", files["package.json"])
                new_codes["package.json"] = updated_package

        # Deterministic nav-link repair when shared components changed: keep
        # every page reachable (bad hash/plain anchors blank the HashRouter
        # preview). Runs before build-verify so the repaired code is verified.
        if any(p.startswith("src/components/") for p in new_codes):
            try:
                from app.services.validators.nav_link_validator import (
                    validate_and_fix_nav_links,
                    ensure_catch_all_route,
                )
                fixed_nav, nav_changes = validate_and_fix_nav_links(
                    {**files, **new_codes}, project.get("website_structure") or {}
                )
                for nav_path, nav_content in fixed_nav.items():
                    old_codes.setdefault(nav_path, files.get(nav_path, ""))
                    new_codes[nav_path] = nav_content
                if nav_changes:
                    logger.info(f"[COMPONENT EDIT] Nav link validator repaired {len(nav_changes)} link(s)")
                # Older projects were generated without a catch-all route —
                # patch App.tsx opportunistically so bad links can't blank the app
                app_tsx = new_codes.get("src/App.tsx", files.get("src/App.tsx"))
                if app_tsx:
                    patched_app = ensure_catch_all_route(app_tsx)
                    if patched_app:
                        old_codes.setdefault("src/App.tsx", files.get("src/App.tsx", ""))
                        new_codes["src/App.tsx"] = patched_app
                        logger.info("[COMPONENT EDIT] Added missing catch-all route to App.tsx")
            except Exception as e:
                logger.warning(f"[COMPONENT EDIT] Nav link validation failed (non-fatal): {e}")

        # Build-verify: the edit is only saved after the project compiles.
        # On failure, feed build errors back to the LLM for up to 2 repair attempts.
        progress("building", "Building and verifying the preview")
        preview_result, candidate_files = await _build_verify_with_repairs(
            project_id, files, new_codes, cost_tracker=cost_tracker
        )

        if preview_result is None:
            logger.error(f"[COMPONENT EDIT] Build failed after repair attempts; nothing saved")
            return ComponentEditResponse(
                success=False,
                message=(
                    "The AI's change didn't compile, so nothing was changed. "
                    "Try rephrasing the instruction."
                )
            )

        # Green build — persist every file that changed (edits + any build repairs)
        files_to_save = {
            path: content for path, content in candidate_files.items()
            if files.get(path) != content
        }
        logger.info(f"[COMPONENT EDIT] Saving {len(files_to_save)} changed file(s) to database")
        for file_path, file_content in files_to_save.items():
            save_success, save_message = await component_editor_service.apply_component_edit(
                project_id=project_id,
                file_path=file_path,
                new_code=file_content
            )
            if not save_success:
                logger.error(f"[COMPONENT EDIT] Failed to save {file_path}: {save_message}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to save component: {save_message}"
                )

        # Swap the project's preview to the freshly verified build and clean up the old one
        new_preview_id = preview_result.get("preview_id")
        preview_url = preview_result.get("preview_url")
        old_preview_id = project.get("preview_id")
        try:
            supabase.table("projects").update({"preview_id": new_preview_id}).eq("id", project_id).execute()
        except Exception as e:
            logger.warning(f"[COMPONENT EDIT] Failed to store new preview_id: {e}")
        try:
            supabase.table("projects").update(
                {"last_edited_at": datetime.utcnow().isoformat()}
            ).eq("id", project_id).execute()
        except Exception as e:
            logger.warning(f"[COMPONENT EDIT] Failed to stamp last_edited_at: {e}")
        if old_preview_id and old_preview_id != new_preview_id:
            try:
                vite_preview_service.delete_preview(old_preview_id)
            except Exception as e:
                logger.warning(f"[COMPONENT EDIT] Failed to delete old preview {old_preview_id}: {e}")

        # Primary file for descriptions/history (first target file)
        component_file = next(iter(targets_by_file.keys()))
        old_code = old_codes[component_file]
        new_code = new_codes[component_file]
        primary_element = request.selected_element or selected_elements[0]

        # Generate edit description
        edit_description = await component_editor_service.generate_edit_description(
            instruction=request.instruction,
            element_context=primary_element,
            file_path=component_file
        )
        logger.info(f"[COMPONENT EDIT] Generated description: {edit_description}")

        # Save to chat history
        logger.info(f"[COMPONENT EDIT] Saving to chat history")
        chat_message_id = str(uuid.uuid4())

        try:
            # Insert chat message
            chat_insert = supabase.table("project_chat_messages").insert({
                "id": chat_message_id,
                "project_id": project_id,
                "user_id": user_id,
                "message_type": "edit",
                "user_prompt": request.instruction,
                "ai_response": edit_description,
                "metadata": {
                    "file_path": component_file,
                    "scope": scope,
                    "edit_mode": edit_analysis.get("edit_mode"),
                    "patch_blocks": edit_analysis.get("patch_blocks"),
                    "selected_element": {
                        "tagName": primary_element.get('tagName', ''),
                        "textContent": (primary_element.get('textContent') or '')[:100],
                        "component": primary_element.get('component', {})
                    },
                    "attachments": request.attachments or []
                }
            }).execute()

            # Insert edit history — one row per changed file (including files the
            # build-repair step touched), all sharing this chat_message_id, so a
            # revert restores the complete pre-edit state.
            history_rows = [
                {
                    "project_id": project_id,
                    "chat_message_id": chat_message_id,
                    "file_path": file_path,
                    "old_code": files.get(file_path, ""),
                    "new_code": file_content,
                    "diff_summary": edit_description,
                    "selected_element": primary_element,
                    "edit_description": edit_description,
                    "ai_instruction": request.instruction
                }
                for file_path, file_content in files_to_save.items()
            ]
            if history_rows:
                supabase.table("project_edit_history").insert(history_rows).execute()

            logger.info(f"[COMPONENT EDIT] Chat and edit history saved successfully")

        except Exception as e:
            logger.error(f"[COMPONENT EDIT] Failed to save chat/edit history: {str(e)}")
            # Don't fail the request if history saving fails

        # Log the action
        logger.info(f"[COMPONENT EDIT] Logging action to database")
        action_logger = ActionLogger(supabase)
        await action_logger.log_action(
            user_id=user_id,
            action="component_edited",
            details={
                "project_id": project_id,
                "component_file": component_file,
                "instruction": request.instruction,
                "element_tag": primary_element.get('tagName', ''),
                "element_text": (primary_element.get('textContent') or '')[:100]
            }
        )

        # Log AI call for rate limiting (counts as 1 edit)
        await log_ai_call(
            user_id=user_id,
            call_type="edit",
            project_id=project_id,
            endpoint=f"/edit/project/{project_id}",
            supabase_client=supabase
        )

        logger.info(f"[COMPONENT EDIT] ✓ Component {component_file} edited successfully for project {project_id}")

        progress("done", "Edit applied")
        return ComponentEditResponse(
            success=True,
            message=f"Component {component_file} updated successfully",
            updated_file=component_file,
            updated_files=sorted(files_to_save.keys()),
            preview_url=preview_url,
            preview_id=new_preview_id,
            old_code=old_code,
            new_code=new_code,
            edit_description=edit_description,
            chat_message_id=chat_message_id
        )

    except HTTPException as e:
        cost_tracker.mark_failed(f"{e.status_code}: {e.detail}")
        logger.error(f"[COMPONENT EDIT] HTTPException: {e.status_code} - {e.detail}")
        raise
    except Exception as e:
        cost_tracker.mark_failed(str(e))
        logger.error(f"[COMPONENT EDIT] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to edit component"
        )
    finally:
        # Persist token/cost accounting for any request that reached an LLM.
        # save_to_database swallows its own errors, so this can't mask the
        # response or the original exception.
        if cost_tracker.model_calls:
            if cost_tracker.status == "in_progress":
                cost_tracker.mark_completed()
            await cost_tracker.save_to_database(project_id, user_id, supabase)



async def _handle_property_edit(
    project_id: str,
    request: PropertyEditRequest,
    user_id: str,
    supabase: Any
) -> PropertyEditResponse:
    """
    Core handler for property edit operations.
    
    This function contains all the logic for editing properties and is called
    through the queue system to ensure sequential processing per project.
    
    Args:
        project_id: ID of the project being edited
        request: Property edit request containing changes
        user_id: ID of the current user
        supabase: Supabase client instance
    
    Returns:
        PropertyEditResponse with the edit results
    
    Raises:
        HTTPException: On validation or processing errors
    """
    logger.info(f"[PROPERTY EDIT] Handler processing edit for project {project_id}")
    logger.info(f"[PROPERTY EDIT] Editing {request.component_file} with {len(request.properties)} property changes")
    
    try:
        # Verify project ownership and type
        project_response = supabase.table("projects").select("*").eq("id", project_id).single().execute()
        
        if not project_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        project = project_response.data
        
        if project.get("user_id") != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to edit this project"
            )
        
        if project.get("project_type") != "react":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Property editing is only supported for React projects"
            )
        
        # Load ALL project files (needed for prop-aware editing)
        logger.info(f"[PROPERTY EDIT] Loading all project files for {project_id}")
        project_files = await project_file_manager.get_project_files(project_id)

        if not project_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project files not found"
            )

        # Check if the component file exists
        if request.component_file not in project_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Component file '{request.component_file}' not found in project"
            )

        # Get the component file content
        original_code = project_files[request.component_file]

        logger.info(f"[PROPERTY EDIT] Applying {len(request.properties)} property changes to {request.component_file}")

        # Build component relationship map (needed for prop-based edits)
        component_tracker = ComponentRelationshipTracker()

        # Log the property edit started
        await ActionLogger(supabase).log_action(
            user_id=user_id,
            action="property_edit_started",
            details={
                "project_id": project_id,
                "component_file": request.component_file,
                "properties": [p.property for p in request.properties]
            }
        )
        component_tracker.analyze_project_structure(project_files)

        # Convert PropertyChange objects to dicts for direct_code_editor
        properties_dict = [
            {
                "property": p.property,
                "value": p.value,
                "oldValue": p.oldValue,
                "unit": p.unit
            }
            for p in request.properties
        ]

        # Apply property changes using direct code editor
        success, modified_code, error_message, prop_edit_metadata = direct_code_editor.edit_properties(
            code=original_code,
            element_selector=request.element_selector,
            properties=properties_dict,
            files=project_files,
            component_tracker=component_tracker
        )

        await ActionLogger(supabase).log_action(
            user_id=user_id,
            action="property_edit_completed",
            details={
                "project_id": project_id,
                "component_file": request.component_file,
                "success": success,
                "error_message": error_message,
                "prop_edit_metadata": prop_edit_metadata
            }
        )

        # Check if this is a prop edit that needs parent component update
        prop_edit_info_response = None  # Initialize here so it's accessible later
        
        # If we have component edits (success=True and modified_code), save them first
        # This handles cases where both component edits (like alt) and prop edits (like src) are made
        if success and modified_code and prop_edit_metadata:
            logger.info(f"[PROPERTY EDIT] Saving component edits before handling prop edits")
            await project_file_manager.save_project_file(
                project_id=project_id,
                file_path=request.component_file,
                file_content=modified_code,
                overwrite=False
            )
            # Update project_files dict with component edits for prop edit handling
            project_files[request.component_file] = modified_code
        
        # Handle array prop edits (array items passed as props)
        if prop_edit_metadata and prop_edit_metadata.get('type') == 'array_prop_edit':
            logger.info(f"[PROPERTY EDIT] Array prop edit detected - updating array '{prop_edit_metadata['prop_name']}[{prop_edit_metadata['array_index']}].{prop_edit_metadata['property_path']}' at source")
            
            # Update array item at source (parent component)
            array_prop_success, updated_files, array_prop_error = direct_code_editor.update_array_prop_at_source(
                files=project_files,
                component_file=request.component_file,
                prop_name=prop_edit_metadata['prop_name'],
                array_index=prop_edit_metadata['array_index'],
                property_path=prop_edit_metadata['property_path'],
                new_value=prop_edit_metadata['new_value'],
                object_name=prop_edit_metadata['object_name'],
                component_tracker=component_tracker
            )
            
            if array_prop_success and updated_files:
                logger.info(f"[PROPERTY EDIT] Successfully updated array prop at source")
                
                # Save all updated files
                files_updated = []
                prop_source_file = None
                for file_path, file_content in updated_files.items():
                    if file_content != project_files.get(file_path):
                        logger.info(f"[PROPERTY EDIT] Saving updated file: {file_path}")
                        await project_file_manager.save_project_file(
                            project_id=project_id,
                            file_path=file_path,
                            file_content=file_content,
                            overwrite=False
                        )
                        files_updated.append(file_path)
                        if file_path != request.component_file:
                            prop_source_file = file_path
                
                # Merge updated files into project_files (don't replace, as component file might not be in updated_files)
                project_files.update(updated_files)
                # Ensure modified_code is preserved if component file wasn't in updated_files
                if request.component_file not in updated_files and modified_code:
                    project_files[request.component_file] = modified_code
                # Get the latest modified_code (either from updated_files or preserved)
                modified_code = project_files.get(request.component_file, modified_code)
                
                logger.info(f"[PROPERTY EDIT] Updated {len(files_updated)} files: {files_updated}")
                
                # Store prop edit info for response
                prop_edit_info_response = {
                    'prop_name': prop_edit_metadata['prop_name'],
                    'source_file': prop_source_file or request.component_file,
                    'new_value': prop_edit_metadata['new_value']
                }
                
                # Mark as successful since we've updated the files
                success = True
            else:
                error_msg = f"Could not update array prop at source: {array_prop_error}"
                logger.error(f"[PROPERTY EDIT] {error_msg}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )
        
        # Handle regular prop edits
        elif prop_edit_metadata and prop_edit_metadata.get('type') == 'prop_edit':
            logger.info(f"[PROPERTY EDIT] Prop edit detected - updating prop '{prop_edit_metadata['prop_name']}' at source")

            # Update prop at source (parent component)
            prop_success, updated_files, prop_error = direct_code_editor.update_prop_at_source(
                files=project_files,
                component_file=request.component_file,
                prop_name=prop_edit_metadata['prop_name'],
                new_value=prop_edit_metadata['new_value'],
                component_tracker=component_tracker
            )

            if prop_success and updated_files:
                logger.info(f"[PROPERTY EDIT] Successfully updated prop at source")

                # Save all updated files
                files_updated = []
                prop_source_file = None
                for file_path, file_content in updated_files.items():
                    if file_content != project_files.get(file_path):
                        logger.info(f"[PROPERTY EDIT] Saving updated file: {file_path}")
                        await project_file_manager.save_project_file(
                            project_id=project_id,
                            file_path=file_path,
                            file_content=file_content,
                            overwrite=False
                        )
                        files_updated.append(file_path)
                        # The parent file (where prop is defined) is the one that's not the component file
                        if file_path != request.component_file:
                            prop_source_file = file_path

                # Merge updated files into project_files (don't replace, as component file might not be in updated_files)
                project_files.update(updated_files)
                # Ensure modified_code is preserved if component file wasn't in updated_files
                if request.component_file not in updated_files and modified_code:
                    project_files[request.component_file] = modified_code
                # Get the latest modified_code (either from updated_files or preserved)
                modified_code = project_files.get(request.component_file, modified_code)

                logger.info(f"[PROPERTY EDIT] Updated {len(files_updated)} files: {files_updated}")
                
                # Store prop edit info for response
                prop_edit_info_response = {
                    'prop_name': prop_edit_metadata['prop_name'],
                    'source_file': prop_source_file or request.component_file,
                    'new_value': prop_edit_metadata['new_value']
                }
            else:
                # Fallback: Couldn't update at source, hardcode the value
                logger.warning(f"[PROPERTY EDIT] Could not update prop at source: {prop_error}")
                logger.warning(f"[PROPERTY EDIT] Falling back to hardcoding the value in component")

                # Use modified_code if we have component edits, otherwise use original_code
                # This ensures we're working with the latest version of the component file
                code_to_use = modified_code if modified_code else original_code
                logger.info(f"[PROPERTY EDIT] Using {'modified_code' if modified_code else 'original_code'} for fallback")

                # Hardcode the value by directly replacing the JSX expression
                # Replace {propName} with the actual value
                prop_expr = f"{{{prop_edit_metadata['prop_name']}}}"
                new_value = prop_edit_metadata['new_value']

                # Use regex to find and replace the prop expression in the element
                # This is a simple find-replace that should work for most cases
                if prop_expr in code_to_use:
                    # Find the element and replace the prop expression
                    # We need to be careful to only replace within the specific element
                    element_selector = request.element_selector

                    # Use the direct editor to find the element content
                    from app.services.direct_code_editor import DirectCodeEditor
                    editor = DirectCodeEditor()
                    element_data = editor._find_element_content(code_to_use, element_selector)

                    if element_data:
                        _, tag_end, content_end, _, _, old_content = element_data

                        if prop_expr in old_content:
                            # Replace the prop expression with the new value
                            new_content = old_content.replace(prop_expr, new_value)
                            modified_code = code_to_use[:tag_end] + new_content + code_to_use[content_end:]

                            logger.info(f"[PROPERTY EDIT] Successfully hardcoded value in component")

                            # Save the hardcoded version
                            await project_file_manager.save_project_file(
                                project_id=project_id,
                                file_path=request.component_file,
                                file_content=modified_code,
                                overwrite=False
                            )

                            # Update project_files dict for preview
                            project_files[request.component_file] = modified_code
                        else:
                            # Couldn't find prop expression in element
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Could not update prop '{prop_edit_metadata['prop_name']}' at source and fallback failed: {prop_error}"
                            )
                    else:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Could not locate element for fallback edit: {prop_error}"
                        )
                else:
                    await ActionLogger(supabase).log_action(
                        user_id=user_id,
                        action="property_edit_fallback_failed",
                        details={"project_id": project_id, "component_file": request.component_file, "error_message": "Could not find prop expression in element", "prop_name": prop_edit_metadata['prop_name']}
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Could not update prop '{prop_edit_metadata['prop_name']}' at source and fallback failed: {prop_error}"
                    )

        elif not success:
            # Log the failed file
            await ActionLogger(supabase).log_action(
                user_id=user_id,
                action="property_edit_failed",
                details={"project_id": project_id, "component_file": request.component_file, "error_message": error_message}
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to apply property changes: {error_message}"
            )

        else:
            # Regular direct edit (not a prop)
            # Save the updated file
            logger.info(f"[PROPERTY EDIT] Saving updated file to project {project_id}")
            await project_file_manager.save_project_file(
                project_id=project_id,
                file_path=request.component_file,
                file_content=modified_code,
                overwrite=False
            )

            # Update project_files dict for preview
            project_files[request.component_file] = modified_code
        
        # Rebuild preview in background so it's ready for next load (tab switch, page reload)
        # Don't return preview_url to frontend to avoid iframe reload (keeps optimistic update visible)
        logger.info(f"[PROPERTY EDIT] Rebuilding preview in background")
        preview_url = None  # Don't return URL to frontend
        
        try:
            existing_preview = project.get("preview_id")
            
            if existing_preview:
                preview_status = vite_preview_service.get_preview_status(existing_preview)
                
                if preview_status and preview_status.get("exists"):
                    # Update existing preview in background
                    # Include all files that were updated (component + parent files for prop edits)
                    logger.info(f"[PROPERTY EDIT] Updating preview {existing_preview} in background")
                    changed_files = {}
                    
                    # Always include the component file
                    if request.component_file in project_files:
                        changed_files[request.component_file] = project_files[request.component_file]
                    
                    # Include parent files if they were updated (for prop edits)
                    if prop_edit_info_response and prop_edit_info_response.get('source_file'):
                        source_file = prop_edit_info_response['source_file']
                        if source_file != request.component_file and source_file in project_files:
                            changed_files[source_file] = project_files[source_file]
                            logger.info(f"[PROPERTY EDIT] Including parent file '{source_file}' in preview update")
                    
                    if changed_files:
                        update_result = vite_preview_service.update_preview_files(
                            preview_id=existing_preview,
                            updated_files=changed_files
                        )
                        
                        if update_result.get("success"):
                            build_time = update_result.get("build_time", 0)
                            logger.info(f"[PROPERTY EDIT] Background rebuild completed in {build_time}s")
                        else:
                            logger.warning(f"[PROPERTY EDIT] Background rebuild failed: {update_result.get('error')}")
                    else:
                        logger.warning(f"[PROPERTY EDIT] No files to update in preview")
                else:
                    logger.warning(f"[PROPERTY EDIT] Preview expired, will recreate on next view")
            else:
                logger.info(f"[PROPERTY EDIT] No preview yet, will create on first view")
                    
        except Exception as preview_error:
            logger.error(f"[PROPERTY EDIT] Background rebuild failed: {str(preview_error)}", exc_info=True)
        
        # Log the successful action
        await ActionLogger(supabase).log_action(
            user_id=user_id,
            action="property_edit_applied",
            details={
                "project_id": project_id,
                "component_file": request.component_file,
                "properties_changed": [p.property for p in request.properties],
                "element_selector": request.element_selector,
                "batch_mode": request.batch,
                "success": True
            }
        )
        
        logger.info(f"[PROPERTY EDIT] Property edit completed successfully")

        # Stamp last edit time for the unpublished-changes indicator
        try:
            supabase.table("projects").update(
                {"last_edited_at": datetime.utcnow().isoformat()}
            ).eq("id", project_id).execute()
        except Exception as e:
            logger.warning(f"[PROPERTY EDIT] Failed to stamp last_edited_at: {e}")

        # Prepare prop_edit_info if this was a prop edit
        # prop_edit_info_response is already set above if it was a prop edit

        return PropertyEditResponse(
            success=True,
            message=f"Successfully updated {len(request.properties)} properties",
            updated_file=request.component_file,
            changes_applied=request.properties,
            preview_url=preview_url,
            new_code=modified_code,
            old_code=original_code,
            prop_edit_info=prop_edit_info_response
        )
        
    except HTTPException as e:
        logger.error(f"[PROPERTY EDIT] HTTPException: {e.status_code} - {e.detail}")
        raise
    except Exception as e:
        logger.error(f"[PROPERTY EDIT] Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to edit properties"
        )
