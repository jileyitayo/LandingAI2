"""
SEARCH/REPLACE patch parsing and application for LLM edit responses.

Patch-mode edits ask the model for aider-style blocks instead of the whole
rewritten file, cutting output tokens by an order of magnitude on small edits:

    <<<<<<< SEARCH
    (contiguous lines copied exactly from the file)
    =======
    (replacement lines)
    >>>>>>> REPLACE

Parsing and application are deliberately strict: a block that doesn't apply
cleanly raises so the caller can fall back to a full-file rewrite. The
materialized result is still run through the existing containment check and
build-verify, so a bad patch can never reach the database.
"""

import re
from dataclasses import dataclass
from typing import List

SEARCH_RE = re.compile(r"^<{5,9}\s*SEARCH\s*$")
DIVIDER_RE = re.compile(r"^={5,9}\s*$")
REPLACE_RE = re.compile(r"^>{5,9}\s*REPLACE\s*$")

# Prompt spec injected into patch-mode edit prompts. Kept here so the edit
# service and the error fixer describe the exact format this module parses.
PATCH_FORMAT_SPEC = """Return your changes ONLY as one or more SEARCH/REPLACE blocks, nothing else (no prose, no markdown fences):

<<<<<<< SEARCH
(contiguous lines copied EXACTLY from the current file, including indentation)
=======
(the replacement lines)
>>>>>>> REPLACE

RULES:
- The SEARCH text must be an EXACT, UNIQUE, contiguous excerpt of the current file. Include 2-3 surrounding unchanged lines so it matches only once.
- Keep each block minimal — only the lines that change plus their anchor lines.
- To INSERT code: SEARCH for the anchor line(s), REPLACE with the anchor line(s) plus the new code.
- To DELETE code: leave the replacement side empty.
- Multiple blocks are allowed; list them in file order.

EXAMPLE (changing a button label and nothing else):
<<<<<<< SEARCH
        <button className="bg-blue-600 text-white" data-element="primary-cta">
          Get Started
        </button>
=======
        <button className="bg-blue-600 text-white" data-element="primary-cta">
          Start Free Trial
        </button>
>>>>>>> REPLACE"""


class PatchFormatError(ValueError):
    """The response could not be parsed as SEARCH/REPLACE blocks."""


class PatchApplyError(ValueError):
    """A parsed block could not be applied to the original text."""


@dataclass
class SearchReplaceBlock:
    search: str
    replace: str


def _strip_wrapping_fence(text: str) -> str:
    """Tolerate a response wrapped in a single markdown code fence."""
    stripped = text.strip()
    if stripped.startswith("```") and stripped.endswith("```"):
        lines = stripped.splitlines()
        if len(lines) >= 2:
            return "\n".join(lines[1:-1])
    return stripped


def parse_blocks(response: str) -> List[SearchReplaceBlock]:
    """
    Parse SEARCH/REPLACE blocks out of an LLM response.

    Raises:
        PatchFormatError: no well-formed block, or a dangling marker.
    """
    if not response or not response.strip():
        raise PatchFormatError("Empty response")

    text = _strip_wrapping_fence(response.replace("\r\n", "\n"))

    blocks: List[SearchReplaceBlock] = []
    state = "outside"  # outside | search | replace
    search_lines: List[str] = []
    replace_lines: List[str] = []

    for line in text.split("\n"):
        if state == "outside":
            if SEARCH_RE.match(line):
                state = "search"
                search_lines, replace_lines = [], []
            # Anything else outside a block (stray prose) is ignored.
        elif state == "search":
            if DIVIDER_RE.match(line):
                state = "replace"
            elif SEARCH_RE.match(line) or REPLACE_RE.match(line):
                raise PatchFormatError("Misplaced marker inside SEARCH section")
            else:
                search_lines.append(line)
        elif state == "replace":
            if REPLACE_RE.match(line):
                blocks.append(SearchReplaceBlock(
                    search="\n".join(search_lines),
                    replace="\n".join(replace_lines),
                ))
                state = "outside"
            elif SEARCH_RE.match(line) or DIVIDER_RE.match(line):
                raise PatchFormatError("Misplaced marker inside REPLACE section")
            else:
                replace_lines.append(line)

    if state != "outside":
        raise PatchFormatError("Dangling SEARCH/REPLACE block (missing closing marker)")
    if not blocks:
        raise PatchFormatError("No SEARCH/REPLACE blocks found in response")
    return blocks


def apply_blocks(original: str, blocks: List[SearchReplaceBlock]) -> str:
    """
    Apply blocks sequentially to `original` and return the patched text.

    Matching is exact-substring first; if that fails, one whitespace-tolerant
    fallback compares lines with trailing whitespace stripped (the original
    file's lines are kept, so indentation is preserved). A search text that
    matches zero or multiple locations raises PatchApplyError — ambiguity
    must fall back to a full-file rewrite rather than guess.
    """
    text = original
    for i, block in enumerate(blocks, 1):
        if not block.search.strip():
            raise PatchApplyError(f"Block {i}: empty SEARCH text")
        text = _apply_one(text, block, i)
    return text


def _apply_one(text: str, block: SearchReplaceBlock, index: int) -> str:
    count = text.count(block.search)
    if count == 1:
        return text.replace(block.search, block.replace, 1)
    if count > 1:
        raise PatchApplyError(f"Block {index}: SEARCH text is ambiguous ({count} matches)")

    # Whitespace-tolerant fallback: line-wise match ignoring trailing whitespace.
    text_lines = text.split("\n")
    search_lines = [l.rstrip() for l in block.search.split("\n")]
    n = len(search_lines)
    matches = [
        start for start in range(len(text_lines) - n + 1)
        if [l.rstrip() for l in text_lines[start:start + n]] == search_lines
    ]
    if len(matches) != 1:
        raise PatchApplyError(
            f"Block {index}: SEARCH text not found"
            if not matches
            else f"Block {index}: SEARCH text is ambiguous ({len(matches)} matches)"
        )
    start = matches[0]
    replace_lines = block.replace.split("\n") if block.replace else []
    return "\n".join(text_lines[:start] + replace_lines + text_lines[start + n:])
