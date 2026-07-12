"""Tests for the site_ingestion package: SSRF guard + design extractor."""

import httpx
import pytest

from app.services.site_ingestion import extractor as extractor_mod
from app.services.site_ingestion.extractor import extract_site_design
from app.services.site_ingestion.models import to_prompt_block
from app.services.site_ingestion.ssrf import validate_url


# ---------------------------------------------------------------------------
# SSRF guard
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
@pytest.mark.parametrize("url", [
    "http://localhost:8000/admin",
    "http://127.0.0.1/",
    "https://127.0.0.1:443/x",
    "http://169.254.169.254/latest/meta-data/",
    "http://10.0.0.5/",
    "http://192.168.1.1/",
    "http://172.16.0.1/",
    "http://[::1]/",
    "http://0.0.0.0/",
    "http://foo.internal/",
    "http://printer.local/",
    "file:///etc/passwd",
    "ftp://example.com/",
    "http://user:pass@example.com/",
    "http://example.com:22/",
])
async def test_validate_url_blocks(url):
    ok, reason, _ = await validate_url(url)
    assert ok is False
    assert reason is not None


@pytest.mark.asyncio
async def test_validate_url_allows_public_https():
    ok, reason, normalized = await validate_url("https://example.com/page")
    assert ok is True, f"expected allowed, got {reason}"
    assert normalized == "https://example.com/page"


# ---------------------------------------------------------------------------
# Extractor fixtures
# ---------------------------------------------------------------------------

STATIC_HTML = """<!doctype html>
<html><head>
<title>Acme Bakery — Fresh Bread Daily</title>
<meta name="description" content="Artisan sourdough baked every morning in Brooklyn.">
<meta name="theme-color" content="#c0392b">
<link rel="stylesheet" href="/assets/site.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Playfair+Display&family=Inter">
<link rel="icon" href="/favicon.svg">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<style>h1 { color: #2c3e50; font-family: 'Playfair Display', serif; }</style>
</head><body>
<header><nav>
<img src="/img/acme-logo.png" alt="Acme Bakery logo" class="logo">
<a href="/">Home</a><a href="/menu">Menu</a><a href="/about">About</a><a href="/contact">Contact</a>
</nav></header>
<section id="hero"><h1>Fresh bread, every single morning</h1>
<p>We bake small-batch sourdough with locally milled flour and a 48-hour ferment for maximum flavor.</p></section>
<section class="features-grid"><h2>Why Acme</h2>
<p>Family owned since 1998, our bakery has served the neighborhood with honest ingredients and no shortcuts whatsoever.</p></section>
<section class="pricing-table"><h2>Subscriptions</h2>
<p>Get a weekly bread box delivered to your door starting at twelve dollars per week, cancel anytime.</p></section>
<footer><p>Visit us at 12 Bread Street, Brooklyn — open seven days a week from dawn until we sell out.</p></footer>
</body></html>"""

STATIC_CSS = """:root { --primary-color: #c0392b; --accent-color: #f39c12; --background: #fdf6ec; }
body { font-family: Inter, sans-serif; color: rgb(44, 62, 80); background: #fdf6ec; }
h1, h2 { font-family: 'Playfair Display', serif; color: #c0392b; }
.btn { background: #c0392b; color: #fdf6ec; } .btn:hover { background: #f39c12; }
a { color: #c0392b; } .muted { color: hsl(210, 15%, 40%); }"""

SPA_HTML = """<!doctype html>
<html><head><title>Joof</title>
<link rel="stylesheet" href="/assets/index-abc123.css">
<link rel="icon" href="/favicon.ico">
<script type="module" src="/assets/index-abc123.js"></script>
</head><body><div id="root"></div></body></html>"""

SPA_CSS = """.hero{background:#0f172a;color:#f8fafc}.btn{background:#6366f1}
h1{font-family:'Space Grotesk',sans-serif}body{font-family:Manrope,sans-serif;color:#0f172a}"""

SPA_JS = """const x={title:"Build your dream website in minutes",cta:"Get started for free",
nav:["Home","Features","Pricing"],desc:"Joof helps small businesses launch beautiful landing pages with no code."};
export default x;"""

EMPTY_SPA_HTML = """<!doctype html><html><head><title>x</title></head>
<body><div id="root"></div></body></html>"""


def _transport(routes):
    def handler(request: httpx.Request) -> httpx.Response:
        key = request.url.path
        if key in routes:
            body, ctype = routes[key]
            return httpx.Response(200, content=body, headers={"content-type": ctype})
        return httpx.Response(404)
    return httpx.MockTransport(handler)


@pytest.fixture
def allow_test_hosts(monkeypatch):
    """Let *.test hosts through the SSRF guard (no DNS); real logic otherwise."""
    real = validate_url

    async def fake_validate(url):
        host = httpx.URL(url).host
        if host.endswith(".test"):
            return True, None, url
        return await real(url)

    monkeypatch.setattr(extractor_mod, "validate_url", fake_validate)
    monkeypatch.setattr(extractor_mod, "_cache", {})


def _patch_client_with_handler(monkeypatch, handler):
    real_client = httpx.AsyncClient

    def client_factory(**kwargs):
        kwargs["transport"] = httpx.MockTransport(handler)
        return real_client(**kwargs)

    monkeypatch.setattr(extractor_mod.httpx, "AsyncClient", client_factory)


def _patch_client(monkeypatch, routes):
    real_client = httpx.AsyncClient

    def client_factory(**kwargs):
        kwargs["transport"] = _transport(routes)
        return real_client(**kwargs)

    monkeypatch.setattr(extractor_mod.httpx, "AsyncClient", client_factory)


# ---------------------------------------------------------------------------
# Extractor behavior
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_static_html_extraction(monkeypatch, allow_test_hosts):
    _patch_client(monkeypatch, {
        "/": (STATIC_HTML, "text/html"),
        "/assets/site.css": (STATIC_CSS, "text/css"),
    })
    ex = await extract_site_design("https://bakery.test/")

    assert ex.ok is True
    assert ex.title.startswith("Acme Bakery")
    hexes = [c.value for c in ex.colors]
    assert "#c0392b" in hexes and "#f39c12" in hexes
    assert "#2c3e50" in hexes  # rgb(44,62,80) normalized
    assert "Playfair Display" in ex.fonts and "Inter" in ex.fonts
    assert any("acme-logo.png" in u for u in ex.logo_candidates)
    assert ex.logo_candidates[0].endswith("/img/acme-logo.png")  # header logo ranks first
    assert {"Home", "Menu", "About", "Contact"} <= set(ex.nav_labels)
    assert "hero" in ex.section_hints and "pricing" in ex.section_hints
    assert any("--primary-color" in k for k in ex.css_variables)
    assert ex.confidence >= 0.9  # all five signals present


@pytest.mark.asyncio
async def test_spa_shell_mines_js_strings(monkeypatch, allow_test_hosts):
    _patch_client(monkeypatch, {
        "/": (SPA_HTML, "text/html"),
        "/assets/index-abc123.css": (SPA_CSS, "text/css"),
        "/assets/index-abc123.js": (SPA_JS, "application/javascript"),
    })
    ex = await extract_site_design("https://joof.test/")

    assert ex.ok is True
    hexes = [c.value for c in ex.colors]
    assert "#6366f1" in hexes and "#0f172a" in hexes
    assert "Space Grotesk" in ex.fonts and "Manrope" in ex.fonts
    assert any("dream website" in s for s in ex.copy_snippets)
    assert any("landing pages" in s for s in ex.copy_snippets)


@pytest.mark.asyncio
async def test_bare_spa_is_weak(monkeypatch, allow_test_hosts):
    _patch_client(monkeypatch, {"/": (EMPTY_SPA_HTML, "text/html")})
    ex = await extract_site_design("https://empty.test/")
    assert ex.ok is True
    assert ex.confidence < extractor_mod.WEAK_CONFIDENCE


@pytest.mark.asyncio
async def test_http_error_marks_failure(monkeypatch, allow_test_hosts):
    _patch_client(monkeypatch, {})  # everything 404s
    ex = await extract_site_design("https://dead.test/")
    assert ex.ok is False
    assert ex.failure_reason == "http_error"


@pytest.mark.asyncio
async def test_ssrf_blocked_url_never_fetched(monkeypatch, allow_test_hosts):
    fetched = []

    def handler(request):
        fetched.append(str(request.url))
        return httpx.Response(200, content="x")

    _patch_client_with_handler(monkeypatch, handler)
    ex = await extract_site_design("http://169.254.169.254/latest/meta-data/")
    assert ex.ok is False
    assert ex.failure_reason == "ssrf_blocked"
    assert fetched == []


@pytest.mark.asyncio
async def test_redirect_to_private_blocked(monkeypatch, allow_test_hosts):
    def handler(request):
        if request.url.host == "redirector.test":
            return httpx.Response(302, headers={"location": "http://127.0.0.1/secret"})
        return httpx.Response(200, content="should not reach")

    _patch_client_with_handler(monkeypatch, handler)
    ex = await extract_site_design("https://redirector.test/")
    assert ex.ok is False
    assert ex.failure_reason == "ssrf_blocked"


# ---------------------------------------------------------------------------
# Prompt block rendering
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_prompt_block_replica_vs_inspired(monkeypatch, allow_test_hosts):
    _patch_client(monkeypatch, {
        "/": (STATIC_HTML, "text/html"),
        "/assets/site.css": (STATIC_CSS, "text/css"),
    })
    ex = await extract_site_design("https://bakery.test/")

    replica = to_prompt_block(ex, "replica")
    assert "GROUND TRUTH" in replica
    assert "#c0392b" in replica
    assert "acme-logo.png" in replica
    assert "untrusted" in replica

    inspired = to_prompt_block(ex, "inspired")
    assert "STYLE GUIDANCE" in inspired
    assert "do NOT embed its logo" in inspired
    assert "acme-logo.png" not in inspired


def test_prompt_block_none_for_failed_extraction():
    from app.services.site_ingestion.models import DesignExtraction
    ex = DesignExtraction(url="https://x.test/", ok=False, failure_reason="timeout")
    assert to_prompt_block(ex, "replica") is None
