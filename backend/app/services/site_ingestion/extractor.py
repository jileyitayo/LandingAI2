"""Fetch a website with httpx (no headless browser) and extract design signals.

Handles both server-rendered HTML and SPA shells: when the HTML body has
little text, the largest JS bundles are mined for human-readable strings,
and linked CSS is always mined for colors/fonts. Every outbound request
(including sub-fetches and redirect hops) passes the SSRF guard first.
"""

import asyncio
import colorsys
import logging
import re
import time
from html.parser import HTMLParser
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import httpx

from app.config import settings
from app.services.site_ingestion.models import ColorInfo, DesignExtraction
from app.services.site_ingestion.ssrf import validate_url

logger = logging.getLogger(__name__)

WEAK_CONFIDENCE = 0.35

MAX_HTML_BYTES = settings.site_ingest_max_html_bytes
MAX_CSS_BYTES = 1 * 1024 * 1024
MAX_JS_BYTES = 2 * 1024 * 1024
MAX_REDIRECTS = 3
MAX_STYLESHEETS = 3
MAX_JS_BUNDLES = 2
OVERALL_TIMEOUT_S = settings.site_ingest_timeout_s
SPA_BODY_TEXT_THRESHOLD = 300

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

SECTION_TOKENS = (
    "hero", "feature", "pricing", "testimonial", "faq", "about", "service",
    "contact", "team", "gallery", "portfolio", "blog", "cta", "footer",
    "newsletter", "stats", "how-it-works", "benefits",
)

GENERIC_FONTS = {
    "sans-serif", "serif", "monospace", "system-ui", "ui-sans-serif",
    "ui-serif", "ui-monospace", "cursive", "fantasy", "inherit", "initial",
    "unset", "-apple-system", "blinkmacsystemfont", "segoe ui", "arial",
    "helvetica", "helvetica neue", "times new roman", "emoji",
    "apple color emoji", "segoe ui emoji", "segoe ui symbol", "noto color emoji",
    # monospace fallback stacks (code blocks, not brand typography)
    "sfmono-regular", "sf mono", "menlo", "monaco", "consolas",
    "liberation mono", "courier new", "courier", "roboto mono",
}

# 15-minute in-process TTL cache: a clarified resubmit re-runs the pre-flight,
# this avoids paying the fetch twice.
_CACHE_TTL_S = 15 * 60
_cache: Dict[str, Tuple[float, DesignExtraction]] = {}


class _IndexParser(HTMLParser):
    """One-pass parser over index.html collecting design-relevant signals."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stylesheets: List[str] = []
        self.google_fonts: List[str] = []
        self.icons: List[Tuple[str, str]] = []  # (rel, href)
        self.scripts: List[str] = []
        self.inline_css: List[str] = []
        self.inline_styles: List[str] = []
        self.title = ""
        self.meta_description = ""
        self.og_image = ""
        self.theme_color = ""
        self.nav_labels: List[str] = []
        self.headings: List[str] = []
        self.copy: List[str] = []
        self.logo_imgs_header: List[str] = []
        self.logo_imgs: List[str] = []
        self.section_hints: List[str] = []
        self._stack: List[str] = []
        self._in_style = False
        self._in_nav = 0
        self._in_header = 0
        self._in_a = 0
        self._text_target: Optional[List[str]] = None
        self._text_buf: List[str] = []
        self.body_text_len = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        self._stack.append(tag)
        if tag == "style":
            self._in_style = True
        elif tag == "nav":
            self._in_nav += 1
        elif tag == "header":
            self._in_header += 1
        elif tag == "a":
            self._in_a += 1
        elif tag == "link":
            rel = (a.get("rel") or "").lower()
            href = a.get("href") or ""
            if "stylesheet" in rel and href:
                if "fonts.googleapis.com" in href:
                    self.google_fonts.append(href)
                else:
                    self.stylesheets.append(href)
            elif "icon" in rel and href:
                self.icons.append((rel, href))
        elif tag == "script":
            src = a.get("src")
            if src:
                self.scripts.append(src)
        elif tag == "meta":
            name = (a.get("name") or a.get("property") or "").lower()
            content = a.get("content") or ""
            if name == "description":
                self.meta_description = content
            elif name == "og:image":
                self.og_image = content
            elif name == "theme-color":
                self.theme_color = content
        elif tag == "img":
            src = a.get("src") or ""
            blob = f"{src} {a.get('alt', '')} {a.get('class', '')} {a.get('id', '')}".lower()
            if src and "logo" in blob:
                (self.logo_imgs_header if (self._in_header or self._in_nav) else self.logo_imgs).append(src)
        elif tag in ("title",):
            self._text_target, self._text_buf = "title", []
        elif tag in ("h1", "h2", "h3"):
            self._text_target, self._text_buf = "heading", []
        elif tag in ("p", "li"):
            self._text_target, self._text_buf = "copy", []
        if tag in ("section", "header", "footer", "main", "nav", "div"):
            ident = f"{a.get('id', '')} {a.get('class', '')}".lower()
            for token in SECTION_TOKENS:
                if token in ident and token not in self.section_hints:
                    self.section_hints.append(token)
        style_attr = a.get("style")
        if style_attr:
            self.inline_styles.append(style_attr)

    def handle_endtag(self, tag):
        if self._stack and self._stack[-1] == tag:
            self._stack.pop()
        if tag == "style":
            self._in_style = False
        elif tag == "nav":
            self._in_nav = max(0, self._in_nav - 1)
        elif tag == "header":
            self._in_header = max(0, self._in_header - 1)
        elif tag == "a":
            self._in_a = max(0, self._in_a - 1)
        if self._text_target and tag in ("title", "h1", "h2", "h3", "p", "li"):
            text = re.sub(r"\s+", " ", "".join(self._text_buf)).strip()
            if text:
                if self._text_target == "title" and not self.title:
                    self.title = text
                elif self._text_target == "heading" and len(text) >= 3:
                    self.headings.append(text)
                elif self._text_target == "copy" and len(text) >= 20:
                    self.copy.append(text)
            self._text_target = None

    def handle_data(self, data):
        if self._in_style:
            self.inline_css.append(data)
            return
        text = data.strip()
        if not text:
            return
        self.body_text_len += len(text)
        if self._text_target:
            self._text_buf.append(data)
        if self._in_a and (self._in_nav or self._in_header):
            label = re.sub(r"\s+", " ", text)
            if 2 <= len(label) <= 30 and label not in self.nav_labels:
                self.nav_labels.append(label)


# --- Color helpers ---------------------------------------------------------

_HEX_RE = re.compile(r"#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")
_RGB_RE = re.compile(r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})")
_HSL_RE = re.compile(r"hsla?\(\s*(\d{1,3}(?:\.\d+)?)\s*,\s*(\d{1,3}(?:\.\d+)?)%\s*,\s*(\d{1,3}(?:\.\d+)?)%")


def _norm_hex(h: str) -> str:
    h = h.lower()
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return f"#{h}"


def _collect_colors(text: str, source: str, counts: Dict[str, Dict]) -> None:
    for m in _HEX_RE.finditer(text):
        value = _norm_hex(m.group(1))
        entry = counts.setdefault(value, {"count": 0, "source": source})
        entry["count"] += 1
    for m in _RGB_RE.finditer(text):
        r, g, b = (min(255, int(v)) for v in m.groups())
        value = f"#{r:02x}{g:02x}{b:02x}"
        entry = counts.setdefault(value, {"count": 0, "source": source})
        entry["count"] += 1
    for m in _HSL_RE.finditer(text):
        h, s, l = (float(v) for v in m.groups())
        r, g, b = colorsys.hls_to_rgb((h % 360) / 360.0, l / 100.0, s / 100.0)
        value = f"#{round(r * 255):02x}{round(g * 255):02x}{round(b * 255):02x}"
        entry = counts.setdefault(value, {"count": 0, "source": source})
        entry["count"] += 1


_FONT_FAMILY_RE = re.compile(r"font-family\s*:\s*([^;}{]+)", re.IGNORECASE)
_CSS_VAR_RE = re.compile(
    r"(--[a-z0-9-]*(?:primary|accent|brand|background|secondary|foreground)[a-z0-9-]*)\s*:\s*([^;}{]+)",
    re.IGNORECASE,
)


def _collect_fonts(text: str, fonts: List[str]) -> None:
    for m in _FONT_FAMILY_RE.finditer(text):
        for family in m.group(1).split(","):
            family = family.strip().strip("'\"").strip()
            if not family or family.lower() in GENERIC_FONTS or family.startswith("var("):
                continue
            if family not in fonts and len(family) <= 40:
                fonts.append(family)


# --- JS string mining (SPA copy fallback) ----------------------------------

_JS_STRING_RE = re.compile(r"""["']([A-Za-z][A-Za-z0-9 ,.'!?&:%$’-]{2,79})["']""")


_FRAMEWORK_NOISE_PREFIXES = (
    "React", "Warning", "Error", "Invalid ", "Expected ", "Unknown ",
    "Cannot ", "Failed ", "Minified ", "Unsupported ", "Missing ",
)


def _looks_human(s: str) -> bool:
    if " " not in s:
        return False
    if s == s.lower():  # event lists / keyword soup ("change click focusin …")
        return False
    if re.search(r"[a-z][A-Z]", s):  # camelCase identifier
        return False
    if any(t in s for t in ("://", "\\", ".js", ".css", ".svg", ".png", "==", "javascript:")):
        return False
    if s.startswith(_FRAMEWORK_NOISE_PREFIXES):  # React/dev warnings in bundles
        return False
    letters = sum(c.isalpha() or c == " " for c in s)
    return letters / len(s) > 0.85


def _mine_js_strings(js: str, limit: int = 150) -> List[str]:
    seen, out = set(), []
    for m in _JS_STRING_RE.finditer(js):
        s = m.group(1).strip()
        if s.lower() in seen or not _looks_human(s):
            continue
        seen.add(s.lower())
        out.append(s)
        if len(out) >= limit:
            break
    return out


# --- Fetching ---------------------------------------------------------------

async def _fetch(
    client: httpx.AsyncClient, url: str, max_bytes: int, expect_html: bool = False
) -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
    """GET with SSRF validation, manual redirects and a streaming byte cap.

    Returns (body, failure_reason, final_url).
    """
    current = url
    for _ in range(MAX_REDIRECTS + 1):
        ok, reason, normalized = await validate_url(current)
        if not ok:
            logger.warning(f"[SITE INGEST] SSRF blocked {current}: {reason}")
            return None, "ssrf_blocked", None
        current = normalized
        try:
            async with client.stream(
                "GET", current, headers={"User-Agent": USER_AGENT}, follow_redirects=False
            ) as resp:
                if resp.status_code in (301, 302, 303, 307, 308):
                    location = resp.headers.get("location")
                    if not location:
                        return None, "http_error", None
                    current = urljoin(current, location)
                    continue
                if resp.status_code != 200:
                    return None, "http_error", None
                if expect_html:
                    ctype = resp.headers.get("content-type", "")
                    if ctype and "html" not in ctype:
                        return None, "non_html", None
                chunks, total = [], 0
                async for chunk in resp.aiter_bytes():
                    total += len(chunk)
                    if total > max_bytes:
                        if expect_html:
                            return None, "too_large", None
                        break  # sub-resources: truncate, keep what we have
                    chunks.append(chunk)
                return b"".join(chunks), None, current
        except httpx.TimeoutException:
            return None, "timeout", None
        except httpx.HTTPError as e:
            logger.warning(f"[SITE INGEST] fetch error for {current}: {e}")
            return None, "fetch_error", None
    return None, "http_error", None  # redirect loop


def _confidence(ex: DesignExtraction) -> float:
    score = 0.0
    if len(ex.colors) >= 3:
        score += 0.25
    if len(ex.fonts) >= 1:
        score += 0.15
    if len(ex.nav_labels) >= 2:
        score += 0.2
    if sum(len(c) for c in ex.copy_snippets) >= 300:
        score += 0.3
    if ex.logo_candidates:
        score += 0.1
    return round(score, 2)


async def extract_site_design(url: str) -> DesignExtraction:
    """Fetch `url` and extract design signals. Never raises."""
    cached = _cache.get(url)
    if cached and time.monotonic() - cached[0] < _CACHE_TTL_S:
        return cached[1]

    started = time.monotonic()
    try:
        result = await asyncio.wait_for(_extract(url), timeout=OVERALL_TIMEOUT_S)
    except asyncio.TimeoutError:
        result = DesignExtraction(url=url, ok=False, failure_reason="timeout")
    except Exception as e:
        logger.warning(f"[SITE INGEST] unexpected failure for {url}: {e}")
        result = DesignExtraction(url=url, ok=False, failure_reason="fetch_error")

    logger.info(
        f"[SITE INGEST] url={url} ok={result.ok} reason={result.failure_reason} "
        f"confidence={result.confidence} colors={len(result.colors)} fonts={len(result.fonts)} "
        f"copy={len(result.copy_snippets)} duration={time.monotonic() - started:.1f}s"
    )
    _cache[url] = (time.monotonic(), result)
    if len(_cache) > 100:
        _cache.pop(next(iter(_cache)))
    return result


async def _extract(url: str) -> DesignExtraction:
    timeout = httpx.Timeout(8.0, connect=4.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        body, failure, final_url = await _fetch(client, url, MAX_HTML_BYTES, expect_html=True)
        if body is None:
            return DesignExtraction(url=url, ok=False, failure_reason=failure)

        html = body.decode("utf-8", errors="replace")
        parser = _IndexParser()
        try:
            parser.feed(html)
        except Exception as e:
            logger.warning(f"[SITE INGEST] HTML parse error for {url}: {e}")

        ex = DesignExtraction(url=url, final_url=final_url, ok=True)
        ex.title = parser.title or None
        ex.meta_description = parser.meta_description or None
        ex.nav_labels = parser.nav_labels[:10]
        ex.headings = parser.headings[:12]
        ex.copy_snippets = parser.copy[:20]
        ex.section_hints = parser.section_hints[:12]
        ex.google_fonts_urls = [urljoin(final_url, u) for u in parser.google_fonts[:3]]

        color_counts: Dict[str, Dict] = {}
        fonts: List[str] = []
        if parser.theme_color:
            _collect_colors(parser.theme_color, "meta_theme", color_counts)
        for css in parser.inline_css:
            _collect_colors(css, "css", color_counts)
            _collect_fonts(css, fonts)
        for style in parser.inline_styles[:200]:
            _collect_colors(style, "inline_style", color_counts)
            _collect_fonts(style, fonts)

        # Google Fonts URLs carry the family names directly.
        for gf_url in ex.google_fonts_urls:
            for fam in re.findall(r"family=([^&:]+)", gf_url):
                fam = fam.replace("+", " ").strip()
                if fam and fam not in fonts:
                    fonts.append(fam)

        # CSS pass: linked stylesheets (SSRF re-validated inside _fetch).
        css_vars: Dict[str, str] = {}
        for href in parser.stylesheets[:MAX_STYLESHEETS]:
            css_body, _, _ = await _fetch(client, urljoin(final_url, href), MAX_CSS_BYTES)
            if not css_body:
                continue
            css_text = css_body.decode("utf-8", errors="replace")
            _collect_colors(css_text, "css", color_counts)
            _collect_fonts(css_text, fonts)
            for m in _CSS_VAR_RE.finditer(css_text):
                if len(css_vars) < 12:
                    css_vars.setdefault(m.group(1), m.group(2).strip()[:60])

        # JS pass: only for SPA shells with no readable body text.
        if parser.body_text_len < SPA_BODY_TEXT_THRESHOLD and parser.scripts:
            bundles = sorted(parser.scripts, key=lambda s: ("chunk" not in s, s))[:MAX_JS_BUNDLES]
            for src in bundles:
                js_body, _, _ = await _fetch(client, urljoin(final_url, src), MAX_JS_BYTES)
                if not js_body:
                    continue
                js_text = js_body.decode("utf-8", errors="replace")
                mined = _mine_js_strings(js_text)
                ex.copy_snippets.extend(s for s in mined if len(s) >= 20)
                _collect_colors(js_text, "js", color_counts)
                _collect_fonts(js_text, fonts)
            ex.copy_snippets = ex.copy_snippets[:30]

        # Logo candidates, best-first.
        logos: List[str] = []
        for src in parser.logo_imgs_header + parser.logo_imgs:
            logos.append(urljoin(final_url, src))
        apple = [h for r, h in parser.icons if "apple-touch" in r]
        favicons = [h for r, h in parser.icons if "apple-touch" not in r]
        for href in apple + favicons:
            logos.append(urljoin(final_url, href))
        if parser.og_image:
            logos.append(urljoin(final_url, parser.og_image))
        seen = set()
        ex.logo_candidates = [u for u in logos if not (u in seen or seen.add(u))][:5]

        ranked = sorted(color_counts.items(), key=lambda kv: -kv[1]["count"])
        ex.colors = [
            ColorInfo(value=v, count=meta["count"], source=meta["source"])
            for v, meta in ranked[:12]
        ]
        ex.css_variables = css_vars
        ex.fonts = fonts[:6]

        excerpt_parts = []
        if ex.title:
            excerpt_parts.append(f"TITLE: {ex.title}")
        if ex.meta_description:
            excerpt_parts.append(f"DESCRIPTION: {ex.meta_description}")
        if ex.headings:
            excerpt_parts.append("HEADINGS: " + " | ".join(ex.headings))
        if ex.copy_snippets:
            excerpt_parts.append("COPY: " + " | ".join(ex.copy_snippets))
        ex.raw_excerpts = "\n".join(excerpt_parts)[:6000]

        ex.confidence = _confidence(ex)
        return ex
