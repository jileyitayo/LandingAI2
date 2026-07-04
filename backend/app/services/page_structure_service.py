"""
Deterministic page section parsing and reordering.

Generated pages render their sections as the direct children of a container
(usually <main>). This service extracts EVERY direct child as an opaque block
(component invocations, inline <section>s, JSX expressions) and reorders them by
index — nothing is dropped, no LLM involved. Header/Footer (outside the
container) are never touched.
"""

import logging
import re
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

_IDENT_RE = re.compile(r"[A-Za-z][A-Za-z0-9]*")
_HEADING_RE = re.compile(r"<h[1-3][^>]*>\s*([^<{][^<]*?)\s*</h[1-3]>", re.DOTALL)
_COMMENT_TEXT_RE = re.compile(r"\{/\*\s*(.*?)\s*\*/\}", re.DOTALL)
_COMMENT_ONLY_RE = re.compile(r"^\{\s*/\*.*?\*/\s*\}$", re.DOTALL)
_INNER_COMPONENT_RE = re.compile(r"<([A-Z][A-Za-z0-9]*)\b")


class SectionBlock:
    def __init__(self, block_id: int, name: str, source: str, is_component: bool):
        self.id = block_id
        self.name = name
        self.source = source
        self.is_component = is_component


def _find_container_region(code: str) -> Optional[Tuple[int, int]]:
    """Return (inner_start, inner_end) of the reorderable container's children.

    Prefers <main>; the container's direct children are the page sections.
    Returns None when no safe container is found.
    """
    open_match = re.search(r"<main\b[^>]*>", code)
    if open_match:
        # match the corresponding </main> (main is never nested in these pages)
        close = code.find("</main>", open_match.end())
        if close != -1:
            return open_match.end(), close
    return None


def _skip_string(text: str, i: int) -> int:
    """i points at a quote char; return index just past the closing quote."""
    quote = text[i]
    i += 1
    n = len(text)
    while i < n:
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == quote:
            return i + 1
        i += 1
    return i


def _skip_braces(text: str, i: int) -> int:
    """i points at '{'; return index just past the matching '}' (quote-aware)."""
    depth = 0
    n = len(text)
    while i < n:
        ch = text[i]
        if ch in "\"'`":
            i = _skip_string(text, i)
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return i


def _skip_element(text: str, i: int) -> Optional[int]:
    """i points at '<' of an element; return index just past its end (or None)."""
    n = len(text)
    tag_stack: List[str] = []
    while i < n:
        ch = text[i]
        if ch in "\"'`":
            i = _skip_string(text, i)
            continue
        if ch == "{":
            i = _skip_braces(text, i)
            continue
        if ch == "<":
            if text[i:i + 4] == "<!--":
                end = text.find("-->", i)
                i = end + 3 if end != -1 else n
                continue
            is_close = text[i + 1:i + 2] == "/"
            name_match = _IDENT_RE.match(text, i + (2 if is_close else 1))
            # Find this tag's closing '>'
            j = i + 1
            while j < n and text[j] not in ">":
                if text[j] in "\"'`":
                    j = _skip_string(text, j) - 1
                elif text[j] == "{":
                    j = _skip_braces(text, j) - 1
                j += 1
            if j >= n:
                return None
            self_closing = text[j - 1] == "/"
            tag_name = name_match.group(0) if name_match else ""
            if is_close:
                if tag_stack and tag_stack[-1] == tag_name:
                    tag_stack.pop()
                if not tag_stack:
                    return j + 1
            elif not self_closing:
                tag_stack.append(tag_name)
            else:
                if not tag_stack:
                    return j + 1
            i = j + 1
            continue
        i += 1
    return None


def _humanize(name: str) -> str:
    """Split PascalCase into spaced words: 'HeroSection' -> 'Hero Section'."""
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)


def _derive_name(element_source: str, preceding: str, index: int) -> Tuple[str, bool]:
    """Return (display_name, is_component) for a block. element_source is the
    element/expression text (without leading trivia); preceding is the trivia."""
    m = _IDENT_RE.match(element_source, 1) if element_source.startswith("<") else None
    tag = m.group(0) if m else ""
    if tag and tag[0].isupper():
        return _humanize(tag), True
    # A wrapper element around a single component → name after that component
    inner = _INNER_COMPONENT_RE.search(element_source)
    if inner:
        return _humanize(inner.group(1)), True
    # Inline element/expression — try a leading comment, then a heading
    comment = _COMMENT_TEXT_RE.search(preceding)
    if comment:
        return comment.group(1)[:40], False
    heading = _HEADING_RE.search(element_source)
    if heading:
        return heading.group(1)[:40], False
    if element_source.startswith("{"):
        return f"Dynamic block {index + 1}", False
    return f"Section {index + 1}", False


def parse_sections(code: str) -> Optional[List[SectionBlock]]:
    """
    Parse every direct child block of the page's container.
    Returns None when the page has no safe container to reorder.
    """
    region = _find_container_region(code)
    if not region:
        return None
    inner_start, inner_end = region
    inner = code[inner_start:inner_end]

    blocks: List[SectionBlock] = []
    i = 0
    n = len(inner)
    prev_end = 0  # end of the previous block's source (start of this block's leading trivia)
    block_index = 0

    while i < n:
        ch = inner[i]
        if ch.isspace():
            i += 1
            continue
        if ch == "{":
            end = _skip_braces(inner, i)
            # A standalone JSX comment isn't a reorderable block — leave it in
            # place as leading trivia for the following block.
            if _COMMENT_ONLY_RE.match(inner[i:end].strip()):
                i = end
                continue
            preceding = inner[prev_end:i]
            source = inner[prev_end:end]
            name, is_comp = _derive_name(inner[i:end], preceding, block_index)
            blocks.append(SectionBlock(block_index, name, source, is_comp))
            block_index += 1
            prev_end = end
            i = end
            continue
        if ch == "<":
            end = _skip_element(inner, i)
            if end is None:
                break
            preceding = inner[prev_end:i]
            source = inner[prev_end:end]
            name, is_comp = _derive_name(inner[i:end], preceding, block_index)
            blocks.append(SectionBlock(block_index, name, source, is_comp))
            block_index += 1
            prev_end = end
            i = end
            continue
        i += 1

    return blocks


def reorder_sections(code: str, new_order: List[int]) -> Tuple[Optional[str], Optional[str]]:
    """
    Reorder the container's blocks. new_order is a permutation of block ids.
    Returns (new_code, error); new_code is None on any validation failure so a
    corrupted file is never saved.
    """
    blocks = parse_sections(code)
    if blocks is None:
        return None, "This page has no reorderable section container."
    if len(blocks) < 2:
        return None, "This page doesn't have multiple blocks to reorder."

    ids = [b.id for b in blocks]
    if sorted(new_order) != sorted(ids):
        return None, "The requested order isn't a valid permutation of this page's blocks."

    region = _find_container_region(code)
    inner_start, inner_end = region
    inner = code[inner_start:inner_end]

    by_id = {b.id: b for b in blocks}
    # The tail is whatever trivia follows the last block (indentation before </main>)
    last_block_end = inner.rfind(blocks[-1].source) + len(blocks[-1].source)
    tail = inner[last_block_end:]

    new_inner = "".join(by_id[bid].source for bid in new_order) + tail
    new_code = code[:inner_start] + new_inner + code[inner_end:]

    # Safety: reordering only permutes existing blocks, so total length is preserved
    if len(new_code) != len(code):
        return None, "Reordering changed the page size; aborted to avoid corruption."

    return new_code, None
