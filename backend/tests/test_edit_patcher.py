"""Unit tests for the SEARCH/REPLACE edit patcher (pure functions, no LLM)."""

import pytest

from app.services.edit_patcher import (
    PatchApplyError,
    PatchFormatError,
    SearchReplaceBlock,
    apply_blocks,
    parse_blocks,
)

FILE = """import React from 'react';

export function Hero() {
  return (
    <section id="hero" data-component="Hero">
      <h1 data-element="hero-title">Welcome</h1>
      <button data-element="hero-cta">Get Started</button>
    </section>
  );
}
"""


def block(search: str, replace: str) -> str:
    return f"<<<<<<< SEARCH\n{search}\n=======\n{replace}\n>>>>>>> REPLACE"


class TestParseBlocks:
    def test_single_block(self):
        blocks = parse_blocks(block("old line", "new line"))
        assert blocks == [SearchReplaceBlock(search="old line", replace="new line")]

    def test_multiple_blocks_and_surrounding_prose(self):
        text = "Here are the changes:\n" + block("a", "b") + "\n\n" + block("c", "d")
        blocks = parse_blocks(text)
        assert [b.search for b in blocks] == ["a", "c"]
        assert [b.replace for b in blocks] == ["b", "d"]

    def test_wrapped_in_markdown_fence(self):
        blocks = parse_blocks("```tsx\n" + block("a", "b") + "\n```")
        assert blocks[0].search == "a"

    def test_crlf_response(self):
        blocks = parse_blocks(block("a", "b").replace("\n", "\r\n"))
        assert blocks == [SearchReplaceBlock(search="a", replace="b")]

    def test_empty_replace_side(self):
        blocks = parse_blocks("<<<<<<< SEARCH\ngone\n=======\n>>>>>>> REPLACE")
        assert blocks == [SearchReplaceBlock(search="gone", replace="")]

    def test_no_blocks_raises(self):
        with pytest.raises(PatchFormatError):
            parse_blocks("Sure! I changed the button color for you.")

    def test_empty_response_raises(self):
        with pytest.raises(PatchFormatError):
            parse_blocks("   ")

    def test_dangling_block_raises(self):
        with pytest.raises(PatchFormatError):
            parse_blocks("<<<<<<< SEARCH\nfoo\n=======\nbar")

    def test_misplaced_marker_raises(self):
        with pytest.raises(PatchFormatError):
            parse_blocks("<<<<<<< SEARCH\nfoo\n<<<<<<< SEARCH\n=======\n>>>>>>> REPLACE")

    def test_tolerates_marker_length_variation(self):
        blocks = parse_blocks("<<<<<< SEARCH\na\n======\nb\n>>>>>> REPLACE")
        assert blocks == [SearchReplaceBlock(search="a", replace="b")]


class TestApplyBlocks:
    def test_exact_replacement(self):
        blocks = [SearchReplaceBlock(
            search='      <h1 data-element="hero-title">Welcome</h1>',
            replace='      <h1 data-element="hero-title">Hello there</h1>',
        )]
        result = apply_blocks(FILE, blocks)
        assert "Hello there" in result
        assert "Welcome" not in result
        assert result.count("data-element") == 2

    def test_sequential_blocks_see_earlier_replacements(self):
        blocks = [
            SearchReplaceBlock(search="Welcome", replace="Hello"),
            SearchReplaceBlock(search="Hello", replace="Howdy"),
        ]
        assert "Howdy" in apply_blocks(FILE, blocks)

    def test_insertion_via_anchor(self):
        blocks = [SearchReplaceBlock(
            search='      <button data-element="hero-cta">Get Started</button>',
            replace='      <button data-element="hero-cta">Get Started</button>\n'
                    '      <p data-element="hero-note">No credit card required</p>',
        )]
        result = apply_blocks(FILE, blocks)
        assert "No credit card required" in result
        assert "Get Started" in result

    def test_deletion_via_empty_replace(self):
        blocks = [SearchReplaceBlock(
            search='      <button data-element="hero-cta">Get Started</button>\n',
            replace="",
        )]
        result = apply_blocks(FILE, blocks)
        assert "Get Started" not in result
        assert "hero-title" in result

    def test_whitespace_tolerant_fallback(self):
        # Model copied the line without the trailing spaces present in the file
        file_with_trailing = FILE.replace(
            '      <h1 data-element="hero-title">Welcome</h1>',
            '      <h1 data-element="hero-title">Welcome</h1>   ',
        )
        blocks = [SearchReplaceBlock(
            search='      <h1 data-element="hero-title">Welcome</h1>',
            replace='      <h1 data-element="hero-title">Hi</h1>',
        )]
        result = apply_blocks(file_with_trailing, blocks)
        assert "Hi" in result and "Welcome" not in result

    def test_no_match_raises(self):
        with pytest.raises(PatchApplyError):
            apply_blocks(FILE, [SearchReplaceBlock(search="not in the file", replace="x")])

    def test_ambiguous_match_raises(self):
        ambiguous = "line\nline\n"
        with pytest.raises(PatchApplyError):
            apply_blocks(ambiguous, [SearchReplaceBlock(search="line", replace="x")])

    def test_empty_search_raises(self):
        with pytest.raises(PatchApplyError):
            apply_blocks(FILE, [SearchReplaceBlock(search="  ", replace="x")])

    def test_unchanged_lines_preserved_exactly(self):
        blocks = [SearchReplaceBlock(search="Get Started", replace="Sign Up")]
        result = apply_blocks(FILE, blocks)
        assert result.replace("Sign Up", "Get Started") == FILE
