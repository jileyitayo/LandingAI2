"""
Nav Link Validator

Deterministically repairs navigation links in generated component files so
every page of a generated site is actually reachable.

Why this exists: previews rewrite BrowserRouter -> HashRouter, and the
LLM-generated Header sometimes emits plain anchors (<a href="#features">Shop</a>
or <a href="/">) instead of react-router <Link to="/shop"> elements. In the
HashRouter preview a bad hash anchor navigates to a non-existent route and,
without a catch-all route, blanks the entire app; plain "/x" anchors trigger
full page loads that 404 against the preview's static file server.

The fix is pure string rewriting (no LLM) driven by the label->path map we
already know from website_structure.navigation + pages. It is idempotent:
running it twice is a no-op.
"""

import logging
import re
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

# Anchor tags that must never be rewritten
_SKIP_HREF_PREFIXES = ("http://", "https://", "mailto:", "tel:", "//")

# <a ...>...</a> — non-greedy to the first closing tag. Nested <a> is invalid
# HTML, so the first </a> after the opening tag is always the right one.
# Attrs tolerate `=>` so JSX arrow handlers (onClick={() => ...}) don't
# truncate the opening-tag match.
_ANCHOR_RE = re.compile(r"<a\b((?:=>|[^>])*)>(.*?)</a>", re.DOTALL)
_HREF_RE = re.compile(r"""\bhref\s*=\s*(?:"([^"]*)"|'([^']*)')""")
_TAG_STRIP_RE = re.compile(r"<[^>]+>")
_RRD_IMPORT_RE = re.compile(r"import\s*\{([^}]*)\}\s*from\s*['\"]react-router-dom['\"]")


def build_route_map(website_structure: dict) -> Dict[str, str]:
    """
    Build a lowercase label -> route path map from the stored structure.

    Sources: navigation items (label -> path) and pages (name -> path).
    Navigation wins on conflicts since it's what the Header renders.
    """
    route_map: Dict[str, str] = {}
    for page in website_structure.get("pages", []) or []:
        name = (page.get("name") or "").strip().lower()
        path = page.get("path")
        if name and path:
            route_map[name] = path
    for item in website_structure.get("navigation", []) or []:
        label = (item.get("label") or "").strip().lower()
        path = item.get("path")
        if label and path:
            route_map[label] = path
    return route_map


def _known_paths(website_structure: dict) -> set:
    paths = set()
    for page in website_structure.get("pages", []) or []:
        if page.get("path"):
            paths.add(page["path"])
    for item in website_structure.get("navigation", []) or []:
        if item.get("path"):
            paths.add(item["path"])
    return paths


def _ensure_link_import(content: str) -> str:
    """Make sure `Link` is imported from react-router-dom."""
    match = _RRD_IMPORT_RE.search(content)
    if match:
        names = [n.strip() for n in match.group(1).split(",") if n.strip()]
        if "Link" in names:
            return content
        names.append("Link")
        return content[:match.start()] + f"import {{ {', '.join(names)} }} from 'react-router-dom'" + content[match.end():]
    # No react-router-dom import yet: insert after the first import line
    first_import = re.search(r"^import .*$", content, re.MULTILINE)
    line = "import { Link } from 'react-router-dom';"
    if first_import:
        return content[:first_import.end()] + "\n" + line + content[first_import.end():]
    return line + "\n" + content


def _lookup_label(label: str, route_map: Dict[str, str]):
    """
    Resolve a visible label to a route: exact match first, then progressively
    shorter word prefixes so variants like "Shop Selection" or "Contact Us"
    still resolve to the "Shop" / "Contact" nav entries.
    """
    key = label.strip().lower()
    if key in route_map:
        return route_map[key]
    words = key.split()
    for i in range(len(words) - 1, 0, -1):
        prefix = " ".join(words[:i])
        if prefix in route_map:
            return route_map[prefix]
    return None


def _resolve_target(href: str, label: str, route_map: Dict[str, str], known_paths: set):
    """
    Decide whether an anchor should become a router Link.

    Returns the route path, or None to leave the anchor alone.
    """
    if not href or href.startswith(_SKIP_HREF_PREFIXES):
        return None

    if href.startswith("#") and len(href) > 1:
        # Hash anchor: only rewrite when the visible label is a known nav
        # entry — otherwise it's a legitimate same-page scroll anchor.
        # (Bare "#" placeholders are left alone.)
        return _lookup_label(label, route_map)

    if href.startswith("/"):
        # Plain path anchor: full page load inside the preview. Rewrite when
        # it's a known route; also try the label as a fallback.
        if href in known_paths:
            return href
        return _lookup_label(label, route_map)

    return None


_ROUTE_FOR_PATH_RE = r'<Route\s+path="{path}"\s+element=\{{<(\w+)\s*/?>\}}'


def ensure_catch_all_route(app_tsx: str) -> str | None:
    """
    Insert a `<Route path="*">` fallback (rendering the home page) into an
    existing App.tsx that lacks one, so unknown routes never blank the app.

    Returns the patched content, or None when no change is needed/possible.
    """
    if 'path="*"' in app_tsx:
        return None
    home_match = re.search(_ROUTE_FOR_PATH_RE.format(path="/"), app_tsx)
    if not home_match:
        # fall back to the first route's element
        home_match = re.search(r'<Route\s+path="[^"]*"\s+element=\{<(\w+)\s*/?>\}', app_tsx)
    if not home_match:
        return None
    home_component = home_match.group(1)
    closing = app_tsx.find("</Routes>")
    if closing == -1:
        return None
    line = f'          <Route path="*" element={{<{home_component} />}} />\n'
    return app_tsx[:closing] + line + app_tsx[closing:]


def validate_and_fix_nav_links(
    files: Dict[str, str],
    website_structure: dict,
) -> Tuple[Dict[str, str], List[str]]:
    """
    Rewrite broken nav anchors to react-router <Link> elements.

    Args:
        files: path -> content of the whole project
        website_structure: the projects.website_structure JSONB dict

    Returns:
        (changed_files, change_log) — changed_files contains only the files
        that were modified.
    """
    route_map = build_route_map(website_structure or {})
    known_paths = _known_paths(website_structure or {})
    if not route_map:
        return {}, []

    changed_files: Dict[str, str] = {}
    change_log: List[str] = []

    for path, content in files.items():
        if not path.startswith("src/components/") or path.startswith("src/components/ui/"):
            continue
        if not path.endswith((".tsx", ".jsx")):
            continue

        file_changes: List[str] = []

        def rewrite(match: re.Match) -> str:
            attrs, inner = match.group(1), match.group(2)
            if "target=" in attrs:
                return match.group(0)
            href_match = _HREF_RE.search(attrs)
            if not href_match:
                return match.group(0)
            href = href_match.group(1) if href_match.group(1) is not None else href_match.group(2)
            label = _TAG_STRIP_RE.sub("", inner).strip()
            target = _resolve_target(href, label, route_map, known_paths)
            if target is None:
                return match.group(0)
            new_attrs = attrs[:href_match.start()] + f'to="{target}"' + attrs[href_match.end():]
            file_changes.append(f"{path}: <a href=\"{href}\">{label[:40]} -> <Link to=\"{target}\">")
            return f"<Link{new_attrs}>{inner}</Link>"

        new_content = _ANCHOR_RE.sub(rewrite, content)
        if file_changes:
            new_content = _ensure_link_import(new_content)
            changed_files[path] = new_content
            change_log.extend(file_changes)

    if change_log:
        logger.info(f"[NAV VALIDATOR] Fixed {len(change_log)} nav link(s) in {len(changed_files)} file(s)")
        for entry in change_log:
            logger.info(f"[NAV VALIDATOR]   {entry}")

    return changed_files, change_log
