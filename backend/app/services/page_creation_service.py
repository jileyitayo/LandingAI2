"""
Page Creation Service

Creates a NEW page for an existing generated site from the edit chat:
generates the page file with the same per-page generator used at initial
generation (theme is inherited automatically — pages consume the CSS vars,
tailwind tokens, and shared Header/Footer/ui components already in the
project), wires it into App.tsx routing deterministically, and links it
either from the navigation menu or from a user-selected element.

The caller (edit pipeline) is responsible for build-verifying and saving
the returned files, updating projects.website_structure, and quota logging.
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional

from app.services.business_analyzer import BusinessAnalysis
from app.services.react_models import PageComponent, PageStructure, WebsiteStructure

logger = logging.getLogger(__name__)


class PageCreationError(Exception):
    """User-presentable failure while creating a page."""


def _sanitize_name(raw: str) -> str:
    """PascalCase page name with no spaces/symbols (matches generator naming)."""
    words = re.findall(r"[A-Za-z0-9]+", raw or "")
    name = "".join(w[:1].upper() + w[1:] for w in words)
    return name or "NewPage"


def _sanitize_route(raw: str, name: str) -> str:
    route = (raw or "").strip()
    if not route.startswith("/"):
        route = "/" + route
    route = re.sub(r"[^a-z0-9\-/]", "", route.lower().replace(" ", "-"))
    if route in ("", "/"):
        route = "/" + name.lower()
    return route


def _insert_route_into_app(app_tsx: str, page_name: str, page_filename: str, route: str) -> str:
    """Deterministically add the import + <Route> for the new page."""
    import_line = f"import {page_name} from './pages/{page_filename}'"
    if import_line not in app_tsx:
        imports = list(re.finditer(r"^import .*$", app_tsx, re.MULTILINE))
        if not imports:
            raise PageCreationError("Could not find imports in App.tsx")
        last = imports[-1]
        app_tsx = app_tsx[:last.end()] + "\n" + import_line + app_tsx[last.end():]

    route_line = f'          <Route path="{route}" element={{<{page_name} />}} />\n'
    catch_all = re.search(r'^\s*<Route\s+path="\*".*$', app_tsx, re.MULTILINE)
    if catch_all:
        insert_at = catch_all.start()
    else:
        closing = app_tsx.find("</Routes>")
        if closing == -1:
            raise PageCreationError("Could not find </Routes> in App.tsx")
        insert_at = closing
    return app_tsx[:insert_at] + route_line + app_tsx[insert_at:]


# JSX-arrow-tolerant <Link ...>...</Link> matcher (same trick as nav_link_validator)
_LINK_RE_TEMPLATE = r'<Link\b((?:=>|[^>])*?to="{path}"(?:=>|[^>])*)>(.*?)</Link>'


def _insert_nav_link_into_header(header: str, nav_items: List[Dict[str, str]], nav_label: str, route: str) -> Optional[str]:
    """
    Clone the last existing nav Link (per nav block — desktop + mobile) with
    the new label/route. Returns updated content, or None if no pattern match
    (caller falls back to an LLM edit).
    """
    if f'to="{route}"' in header:
        return header  # already linked (idempotent)

    # Try existing nav items from last to first until one matches in the file
    for item in reversed(nav_items):
        path = item.get("path")
        if not path:
            continue
        pattern = re.compile(_LINK_RE_TEMPLATE.format(path=re.escape(path)), re.DOTALL)
        matches = list(pattern.finditer(header))
        if not matches:
            continue

        result = []
        last_end = 0
        for m in matches:
            attrs = m.group(1)
            clone_attrs = attrs.replace(f'to="{path}"', f'to="{route}"')
            # Keep data-element attributes unique-ish for the selector
            clone_attrs = re.sub(
                r'data-element="([^"]*)"',
                f'data-element="nav-{re.sub(r"[^a-z0-9]+", "-", nav_label.lower()).strip("-")}"',
                clone_attrs,
            )
            clone = f"<Link{clone_attrs}>{nav_label}</Link>"
            result.append(header[last_end:m.end()])
            # Preserve the original indentation of the cloned line
            line_start = header.rfind("\n", 0, m.start()) + 1
            indent = header[line_start:m.start()]
            indent = indent if indent.strip() == "" else "          "
            result.append(f"\n{indent}{clone}")
            last_end = m.end()
        result.append(header[last_end:])
        return "".join(result)

    return None


class PageCreationService:
    def __init__(self):
        # Lazy import: react_website_generator is heavy and pulls the LLM client
        self._generator = None

    @property
    def generator(self):
        if self._generator is None:
            from app.services.react_website_generator import ReactWebsiteGenerator
            self._generator = ReactWebsiteGenerator()
        return self._generator

    async def create_page(
        self,
        project: Dict[str, Any],
        files: Dict[str, str],
        new_page: Dict[str, Any],
        selected_element: Optional[Dict[str, Any]] = None,
        instruction: str = "",
    ) -> Dict[str, Any]:
        """
        Generate the new page + route wiring + nav/element linkage.

        Returns {"new_codes": {path: content}, "updated_structure": dict,
                 "page_file": str, "route": str, "linked_via": "nav"|"element"|"none"}
        Raises PageCreationError with a user-presentable message.
        """
        try:
            structure = WebsiteStructure.model_validate(project.get("website_structure") or {})
            analysis = BusinessAnalysis.model_validate(project.get("business_analysis") or {})
        except Exception as e:
            raise PageCreationError(
                "This project is missing the stored website structure needed to create pages."
            ) from e

        name = _sanitize_name(new_page.get("name") or new_page.get("nav_label") or "")
        route = _sanitize_route(new_page.get("route") or "", name)
        nav_label = (new_page.get("nav_label") or name).strip()
        description = (new_page.get("description") or instruction).strip()
        link_from_selection = bool(new_page.get("link_from_selection")) and bool(selected_element)

        # Collision checks
        existing_routes = {p.path for p in structure.pages}
        if route in existing_routes:
            raise PageCreationError(f"A page already exists at {route}.")
        page_filename = name.lower().replace(" ", "-")
        page_file = f"src/pages/{page_filename}.tsx"
        if page_file in files:
            raise PageCreationError(f"A page file already exists at {page_file}.")
        if "src/App.tsx" not in files:
            raise PageCreationError("Could not find src/App.tsx in this project.")

        page = PageStructure(
            name=name,
            path=route,
            title=f"{nav_label} | {structure.name}",
            description=description[:300] or f"{nav_label} page",
            has_header=True,
            has_footer=True,
            components=[
                PageComponent(name=f"{name}Hero", type="hero", props=[]),
                PageComponent(name=f"{name}Content", type="content", props=[]),
            ],
        )

        # Generate against a working copy that includes the new page in the
        # structure so nav context in the prompt mentions it
        structure_for_gen = structure.model_copy(deep=True)
        structure_for_gen.pages.append(page)
        if not link_from_selection:
            from app.services.react_models import NavItem
            structure_for_gen.navigation.append(NavItem(label=nav_label, path=route))

        logger.info(f"[PAGE CREATE] Generating page '{name}' at {route} ({'element link' if link_from_selection else 'nav link'})")
        files_copy = dict(files)
        page_content = await asyncio.to_thread(
            self.generator._generate_page_component,
            page, structure_for_gen, analysis, files_copy
        )

        new_codes: Dict[str, str] = {
            p: c for p, c in files_copy.items() if p not in files  # new components
        }
        new_codes[page_file] = page_content

        # Deterministic App.tsx route insertion (before the catch-all)
        new_codes["src/App.tsx"] = _insert_route_into_app(
            files["src/App.tsx"], name, page_filename, route
        )

        linked_via = "none"
        if link_from_selection:
            linked_via = "element"  # caller wires the selected element via an LLM edit
        else:
            header_file = next(
                (p for p in ("src/components/Header.tsx", "src/components/Header.jsx") if p in files),
                None,
            )
            if header_file:
                nav_items = [n.model_dump() for n in structure.navigation]
                updated_header = _insert_nav_link_into_header(
                    files[header_file], nav_items, nav_label, route
                )
                if updated_header:
                    new_codes[header_file] = updated_header
                    linked_via = "nav"
                else:
                    logger.warning("[PAGE CREATE] Header nav pattern not found — page reachable by URL; caller may LLM-fix")

        # Updated structure for the projects row
        updated_structure = structure.model_copy(deep=True)
        updated_structure.pages.append(page)
        updated_structure.page_count = len(updated_structure.pages)
        if linked_via == "nav":
            from app.services.react_models import NavItem
            updated_structure.navigation.append(NavItem(label=nav_label, path=route))

        return {
            "new_codes": new_codes,
            "updated_structure": updated_structure.model_dump(),
            "page_file": page_file,
            "route": route,
            "page_name": name,
            "nav_label": nav_label,
            "linked_via": linked_via,
        }


page_creation_service = PageCreationService()
