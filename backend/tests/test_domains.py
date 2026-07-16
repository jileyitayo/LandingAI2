"""Tests for the custom domains endpoints and helpers.

Everything external (Supabase, Vercel) is mocked — these tests never talk to
real services.
"""

import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings
from app.utils.auth import get_current_user
from app.routers import domains as domains_module
from app.routers.domains import normalize_domain
from app.services.deployments import vercel_deployer as deployer_module
from app.services.deployments.vercel_deployer import VercelDeployer

TEST_USER_ID = "user-1"
TEST_PROJECT_ID = "proj-1"


# ============================================================================
# Fakes
# ============================================================================

class FakeResult:
    def __init__(self, data=None):
        self.data = data


class FakeQuery:
    def __init__(self, store, table_name):
        self.store = store
        self.table_name = table_name
        self.op = None
        self.payload = None
        self.filters = []

    def select(self, *args, **kwargs):
        self.op = "select"
        return self

    def update(self, payload):
        self.op = "update"
        self.payload = payload
        return self

    def insert(self, payload):
        self.op = "insert"
        self.payload = payload
        return self

    def eq(self, col, val):
        self.filters.append(("eq", col, val))
        return self

    def neq(self, col, val):
        self.filters.append(("neq", col, val))
        return self

    def single(self):
        return self

    def is_(self, col, val):
        return self

    def execute(self):
        if self.op == "update":
            self.store.updates.append(dict(self.payload))
            if self.store.update_error:
                raise Exception(self.store.update_error)
            return FakeResult([{}])
        if self.op == "select":
            filter_cols = [f[1] for f in self.filters]
            if "custom_domain" in filter_cols:
                return FakeResult(list(self.store.domain_conflicts))
            project = self.store.project
            return FakeResult([dict(project)] if project else [])
        return FakeResult([])


class FakeSupabase:
    def __init__(self, project=None):
        self.project = project
        self.domain_conflicts = []
        self.updates = []
        self.update_error = None

    def table(self, name):
        return FakeQuery(self, name)


class FakeDeployer:
    """Stands in for VercelDeployer inside the router."""

    def __init__(self):
        self.attach_calls = []
        self.detach_calls = []
        self.status_result = {
            "attached": True,
            "status": "pending_dns",
            "verified": False,
            "misconfigured": True,
            "dns_instructions": [{"type": "A", "name": "@", "value": "76.76.21.21"}],
            "apex_name": "example.com",
        }
        self.attach_error = None

    async def attach_custom_domain(self, vercel_project, domain):
        if self.attach_error:
            raise self.attach_error
        self.attach_calls.append((vercel_project, domain))
        return {"name": domain, "apexName": "example.com"}

    async def detach_custom_domain(self, vercel_project, domain):
        self.detach_calls.append((vercel_project, domain))

    async def get_domain_status(self, vercel_project, domain):
        return dict(self.status_result)

    async def get_deployment_project_id(self, deployment_id):
        return "prj_backfilled"


# ============================================================================
# Fixtures
# ============================================================================

def make_project(**overrides):
    project = {
        "id": TEST_PROJECT_ID,
        "user_id": TEST_USER_ID,
        "deployment_id": "dpl_1",
        "vercel_project_id": "prj_1",
        "custom_domain": None,
        "custom_domain_status": None,
        "custom_domain_error": None,
        "custom_domain_updated_at": None,
    }
    project.update(overrides)
    return project


@pytest.fixture
def client(monkeypatch):
    fake_user = {
        "id": TEST_USER_ID,
        "sub": TEST_USER_ID,
        "user_id": TEST_USER_ID,
        "email": "test@example.com",
    }

    async def fake_verify_token(token):
        return fake_user

    # AuthenticationMiddleware verifies the bearer token before routes run
    monkeypatch.setattr("app.middleware.auth_middleware.verify_token", fake_verify_token)
    app.dependency_overrides[get_current_user] = lambda: fake_user

    test_client = TestClient(app)
    test_client.headers.update({"Authorization": "Bearer test-token"})
    yield test_client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def fake_env(monkeypatch):
    """Fake supabase + deployer wired into the domains router; pro tier."""
    supabase = FakeSupabase(project=make_project())
    deployer = FakeDeployer()
    monkeypatch.setattr(domains_module, "get_supabase_client", lambda: supabase)
    monkeypatch.setattr(domains_module, "VercelDeployer", lambda: deployer)
    monkeypatch.setattr(domains_module, "get_user_tier_name", lambda user_id: "pro")
    return supabase, deployer


# ============================================================================
# normalize_domain
# ============================================================================

class TestNormalizeDomain:
    def test_lowercases_and_strips_scheme_path(self):
        assert normalize_domain(" HTTPS://Example.COM/path?q=1 ") == "example.com"

    def test_strips_trailing_dot_and_port(self):
        assert normalize_domain("example.com.:443") == "example.com"

    def test_subdomain_ok(self):
        assert normalize_domain("blog.example.co.uk") == "blog.example.co.uk"

    @pytest.mark.parametrize("bad", ["", "foo", "foo..bar", "-x.com", "x-.com", "localhost", "a b.com"])
    def test_rejects_invalid(self, bad):
        with pytest.raises(ValueError):
            normalize_domain(bad)

    @pytest.mark.parametrize("blocked", ["mysite.vercel.app", "vercel.com", "foo.sitesmith.app"])
    def test_rejects_blocked_suffixes(self, blocked):
        with pytest.raises(ValueError):
            normalize_domain(blocked)

    def test_idna_encodes_unicode(self):
        assert normalize_domain("münchen.de") == "xn--mnchen-3ya.de"


# ============================================================================
# POST /projects/{id}/domain
# ============================================================================

class TestSetDomain:
    def test_free_tier_forbidden(self, client, fake_env, monkeypatch):
        monkeypatch.setattr(domains_module, "get_user_tier_name", lambda user_id: "free")
        response = client.post(
            f"/api/v1/projects/{TEST_PROJECT_ID}/domain", json={"domain": "example.com"}
        )
        assert response.status_code == 403
        assert "Pro" in response.json()["detail"]

    def test_invalid_domain_422(self, client, fake_env):
        response = client.post(
            f"/api/v1/projects/{TEST_PROJECT_ID}/domain", json={"domain": "not a domain"}
        )
        assert response.status_code == 422

    def test_blocked_suffix_422(self, client, fake_env):
        response = client.post(
            f"/api/v1/projects/{TEST_PROJECT_ID}/domain", json={"domain": "foo.vercel.app"}
        )
        assert response.status_code == 422

    def test_unpublished_409(self, client, fake_env):
        supabase, _ = fake_env
        supabase.project = make_project(deployment_id=None, vercel_project_id=None)
        response = client.post(
            f"/api/v1/projects/{TEST_PROJECT_ID}/domain", json={"domain": "example.com"}
        )
        assert response.status_code == 409
        assert "Publish" in response.json()["detail"]

    def test_domain_on_another_project_409(self, client, fake_env):
        supabase, _ = fake_env
        supabase.domain_conflicts = [{"id": "other-project"}]
        response = client.post(
            f"/api/v1/projects/{TEST_PROJECT_ID}/domain", json={"domain": "example.com"}
        )
        assert response.status_code == 409

    def test_unknown_project_404(self, client, fake_env):
        supabase, _ = fake_env
        supabase.project = None
        response = client.post(
            f"/api/v1/projects/{TEST_PROJECT_ID}/domain", json={"domain": "example.com"}
        )
        assert response.status_code == 404

    def test_not_owner_403(self, client, fake_env):
        supabase, _ = fake_env
        supabase.project = make_project(user_id="someone-else")
        response = client.post(
            f"/api/v1/projects/{TEST_PROJECT_ID}/domain", json={"domain": "example.com"}
        )
        assert response.status_code == 403

    def test_happy_path_attaches_and_persists(self, client, fake_env):
        supabase, deployer = fake_env
        response = client.post(
            f"/api/v1/projects/{TEST_PROJECT_ID}/domain", json={"domain": "Example.com"}
        )
        assert response.status_code == 200
        body = response.json()
        assert body["domain"] == "example.com"
        assert body["status"] == "pending_dns"
        assert body["dns_instructions"] == [{"type": "A", "name": "@", "value": "76.76.21.21"}]
        assert deployer.attach_calls == [("prj_1", "example.com")]
        persisted = [u for u in supabase.updates if u.get("custom_domain") == "example.com"]
        assert persisted and persisted[0]["custom_domain_status"] == "pending_dns"

    def test_backfills_vercel_project_id(self, client, fake_env):
        supabase, deployer = fake_env
        supabase.project = make_project(vercel_project_id=None)
        response = client.post(
            f"/api/v1/projects/{TEST_PROJECT_ID}/domain", json={"domain": "example.com"}
        )
        assert response.status_code == 200
        assert deployer.attach_calls == [("prj_backfilled", "example.com")]
        assert any(u.get("vercel_project_id") == "prj_backfilled" for u in supabase.updates)

    def test_replace_detaches_old_domain(self, client, fake_env):
        supabase, deployer = fake_env
        supabase.project = make_project(custom_domain="old.com", custom_domain_status="verified")
        response = client.post(
            f"/api/v1/projects/{TEST_PROJECT_ID}/domain", json={"domain": "new.com"}
        )
        assert response.status_code == 200
        assert deployer.detach_calls == [("prj_1", "old.com")]
        assert deployer.attach_calls == [("prj_1", "new.com")]

    def test_vercel_domain_in_use_maps_409(self, client, fake_env):
        _, deployer = fake_env
        deployer.attach_error = deployer_module.VercelDomainError(
            "in use", code="domain_already_in_use", status_code=409
        )
        response = client.post(
            f"/api/v1/projects/{TEST_PROJECT_ID}/domain", json={"domain": "example.com"}
        )
        assert response.status_code == 409

    def test_unique_violation_race_maps_409(self, client, fake_env):
        supabase, _ = fake_env
        supabase.update_error = 'duplicate key value violates unique constraint "idx_projects_custom_domain_unique" (23505)'
        response = client.post(
            f"/api/v1/projects/{TEST_PROJECT_ID}/domain", json={"domain": "example.com"}
        )
        assert response.status_code == 409


# ============================================================================
# GET /projects/{id}/domain
# ============================================================================

class TestGetDomainStatus:
    def test_no_domain_returns_empty(self, client, fake_env):
        response = client.get(f"/api/v1/projects/{TEST_PROJECT_ID}/domain")
        assert response.status_code == 200
        assert response.json()["domain"] is None

    def test_free_tier_can_still_read(self, client, fake_env, monkeypatch):
        monkeypatch.setattr(domains_module, "get_user_tier_name", lambda user_id: "free")
        response = client.get(f"/api/v1/projects/{TEST_PROJECT_ID}/domain")
        assert response.status_code == 200

    def test_live_check_updates_cached_status(self, client, fake_env):
        supabase, deployer = fake_env
        supabase.project = make_project(
            custom_domain="example.com", custom_domain_status="pending_dns"
        )
        deployer.status_result.update(
            {"status": "verified", "verified": True, "misconfigured": False, "dns_instructions": []}
        )
        response = client.get(f"/api/v1/projects/{TEST_PROJECT_ID}/domain")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "verified"
        assert body["verified"] is True
        assert any(u.get("custom_domain_status") == "verified" for u in supabase.updates)

    def test_unpublished_returns_cached_without_vercel_call(self, client, fake_env):
        supabase, deployer = fake_env
        supabase.project = make_project(
            deployment_id=None,
            vercel_project_id=None,
            custom_domain="example.com",
            custom_domain_status="pending_dns",
        )
        response = client.get(f"/api/v1/projects/{TEST_PROJECT_ID}/domain")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "pending_dns"
        assert "publish" in (body["error"] or "").lower()
        assert deployer.attach_calls == []

    def test_detached_on_vercel_triggers_reattach(self, client, fake_env):
        supabase, deployer = fake_env
        supabase.project = make_project(
            custom_domain="example.com", custom_domain_status="verified"
        )
        deployer.status_result["attached"] = False
        response = client.get(f"/api/v1/projects/{TEST_PROJECT_ID}/domain")
        assert response.status_code == 200
        assert deployer.attach_calls == [("prj_1", "example.com")]

    def test_vercel_error_falls_back_to_cached(self, client, fake_env, monkeypatch):
        supabase, deployer = fake_env
        supabase.project = make_project(
            custom_domain="example.com", custom_domain_status="verified"
        )

        async def boom(*args, **kwargs):
            raise deployer_module.VercelDeploymentError("vercel down")

        monkeypatch.setattr(deployer, "get_domain_status", boom)
        response = client.get(f"/api/v1/projects/{TEST_PROJECT_ID}/domain")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "verified"
        assert "vercel down" in body["error"]


# ============================================================================
# DELETE /projects/{id}/domain
# ============================================================================

class TestRemoveDomain:
    def test_no_domain_noop(self, client, fake_env):
        response = client.delete(f"/api/v1/projects/{TEST_PROJECT_ID}/domain")
        assert response.status_code == 200
        assert "No custom domain" in response.json()["message"]

    def test_removes_and_clears_columns(self, client, fake_env):
        supabase, deployer = fake_env
        supabase.project = make_project(
            custom_domain="example.com", custom_domain_status="verified"
        )
        response = client.delete(f"/api/v1/projects/{TEST_PROJECT_ID}/domain")
        assert response.status_code == 200
        assert deployer.detach_calls == [("prj_1", "example.com")]
        cleared = supabase.updates[-1]
        assert cleared["custom_domain"] is None
        assert cleared["custom_domain_status"] is None

    def test_clears_db_even_if_vercel_fails(self, client, fake_env, monkeypatch):
        supabase, deployer = fake_env
        supabase.project = make_project(custom_domain="example.com")

        async def boom(*args, **kwargs):
            raise deployer_module.VercelDeploymentError("vercel down")

        monkeypatch.setattr(deployer, "detach_custom_domain", boom)
        response = client.delete(f"/api/v1/projects/{TEST_PROJECT_ID}/domain")
        assert response.status_code == 200
        assert supabase.updates[-1]["custom_domain"] is None

    def test_unpublished_clears_without_vercel(self, client, fake_env):
        supabase, deployer = fake_env
        supabase.project = make_project(
            deployment_id=None, vercel_project_id=None, custom_domain="example.com"
        )
        response = client.delete(f"/api/v1/projects/{TEST_PROJECT_ID}/domain")
        assert response.status_code == 200
        assert deployer.detach_calls == []
        assert supabase.updates[-1]["custom_domain"] is None


# ============================================================================
# VercelDeployer domain composites (www <-> apex pairing)
# ============================================================================

@pytest.fixture
def real_deployer(monkeypatch):
    monkeypatch.setattr(settings, "vercel_api_token", "test-token")
    return VercelDeployer()


class TestAttachCustomDomain:
    @pytest.mark.asyncio
    async def test_apex_adds_www_counterpart_with_redirect(self, real_deployer, monkeypatch):
        monkeypatch.setattr(real_deployer, "get_project_domain", AsyncMock(return_value=None))
        add = AsyncMock(return_value={"name": "example.com", "apexName": "example.com"})
        monkeypatch.setattr(real_deployer, "add_project_domain", add)

        await real_deployer.attach_custom_domain("prj_1", "example.com")

        assert add.await_args_list[0].args == ("prj_1", "example.com")
        assert add.await_args_list[1].args == ("prj_1", "www.example.com")
        assert add.await_args_list[1].kwargs == {"redirect": "example.com"}

    @pytest.mark.asyncio
    async def test_www_adds_apex_counterpart_with_redirect(self, real_deployer, monkeypatch):
        monkeypatch.setattr(real_deployer, "get_project_domain", AsyncMock(return_value=None))
        add = AsyncMock(return_value={"name": "www.example.com", "apexName": "example.com"})
        monkeypatch.setattr(real_deployer, "add_project_domain", add)

        await real_deployer.attach_custom_domain("prj_1", "www.example.com")

        assert add.await_args_list[1].args == ("prj_1", "example.com")
        assert add.await_args_list[1].kwargs == {"redirect": "www.example.com"}

    @pytest.mark.asyncio
    async def test_deep_subdomain_attaches_alone(self, real_deployer, monkeypatch):
        monkeypatch.setattr(real_deployer, "get_project_domain", AsyncMock(return_value=None))
        add = AsyncMock(return_value={"name": "blog.example.com", "apexName": "example.com"})
        monkeypatch.setattr(real_deployer, "add_project_domain", add)

        await real_deployer.attach_custom_domain("prj_1", "blog.example.com")

        assert add.await_count == 1

    @pytest.mark.asyncio
    async def test_idempotent_when_already_attached(self, real_deployer, monkeypatch):
        existing = {"name": "blog.example.com", "apexName": "example.com"}
        monkeypatch.setattr(real_deployer, "get_project_domain", AsyncMock(return_value=existing))
        add = AsyncMock()
        monkeypatch.setattr(real_deployer, "add_project_domain", add)

        result = await real_deployer.attach_custom_domain("prj_1", "blog.example.com")

        assert result == existing
        assert add.await_count == 0

    @pytest.mark.asyncio
    async def test_counterpart_failure_not_fatal(self, real_deployer, monkeypatch):
        monkeypatch.setattr(real_deployer, "get_project_domain", AsyncMock(return_value=None))

        async def add(vercel_project, domain, redirect=None):
            if domain == "www.example.com":
                raise deployer_module.VercelDomainError("www taken", code="domain_already_in_use")
            return {"name": domain, "apexName": "example.com"}

        monkeypatch.setattr(real_deployer, "add_project_domain", add)

        result = await real_deployer.attach_custom_domain("prj_1", "example.com")
        assert result["name"] == "example.com"


class TestDeployWebsiteReattach:
    @pytest.mark.asyncio
    async def test_reattaches_stored_domain_and_persists_project_id(self, real_deployer, monkeypatch):
        supabase = FakeSupabase(
            project=make_project(custom_domain="example.com", project_type="static", html_content="<html></html>")
        )
        monkeypatch.setattr(deployer_module, "get_supabase_client", lambda: supabase)
        monkeypatch.setattr(
            real_deployer, "_generate_static_files",
            AsyncMock(return_value={"index.html": "<html></html>"})
        )
        monkeypatch.setattr(
            real_deployer, "deploy_from_files",
            AsyncMock(return_value={
                "deployment_id": "dpl_new",
                "deployment_url": "https://site.vercel.app",
                "project_id": "prj_new",
                "status": "ready",
            })
        )
        attach = AsyncMock()
        monkeypatch.setattr(real_deployer, "attach_custom_domain", attach)

        await real_deployer.deploy_website(TEST_PROJECT_ID)

        deploy_update = next(u for u in supabase.updates if "deployment_id" in u)
        assert deploy_update["vercel_project_id"] == "prj_new"
        attach.assert_awaited_once_with("prj_new", "example.com")

    @pytest.mark.asyncio
    async def test_reattach_failure_does_not_fail_deploy(self, real_deployer, monkeypatch):
        supabase = FakeSupabase(
            project=make_project(custom_domain="example.com", project_type="static", html_content="<html></html>")
        )
        monkeypatch.setattr(deployer_module, "get_supabase_client", lambda: supabase)
        monkeypatch.setattr(
            real_deployer, "_generate_static_files",
            AsyncMock(return_value={"index.html": "<html></html>"})
        )
        monkeypatch.setattr(
            real_deployer, "deploy_from_files",
            AsyncMock(return_value={
                "deployment_id": "dpl_new",
                "deployment_url": "https://site.vercel.app",
                "project_id": "prj_new",
                "status": "ready",
            })
        )
        monkeypatch.setattr(
            real_deployer, "attach_custom_domain",
            AsyncMock(side_effect=deployer_module.VercelDomainError("boom"))
        )

        result = await real_deployer.deploy_website(TEST_PROJECT_ID)
        assert result["deployment_id"] == "dpl_new"
