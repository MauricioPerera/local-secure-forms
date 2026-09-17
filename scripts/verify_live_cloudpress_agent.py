"""Live end-to-end verification for CloudPress' *reversible* agent tools.

Uses the local LSFA companion and its already-stored, scoped agent capability.
It deliberately never reads or prints the bearer token and records only IDs of
test artefacts so the separate, human-confirmed sensitive-action flow can purge
them afterwards.
"""

from __future__ import annotations

import base64
import json
import keyring
import time
import urllib.request
from pathlib import Path


ORIGIN = "https://auth-free-test-20260915.pages.dev"
LOOPBACK = "http://127.0.0.1:9463/v1/cloudpress/agent-api"
ARTIFACTS = Path(__file__).with_name("live-cloudpress-agent-artifacts.json")
PREFIX = f"__agent_e2e_{int(time.time())}"


def request(path: str, method: str = "GET", body: dict | None = None) -> dict:
    stored = json.loads(keyring.get_password("lsfa.cloudpress.agent-capability", ORIGIN) or "{}")
    channel = stored.get("channel_token")
    if not isinstance(channel, str) or not channel:
        raise RuntimeError("No hay canal LSFA vinculado para esta prueba.")
    payload = {
        "protocol": "lsfa",
        "version": "0.2",
        "origin": ORIGIN,
        "request": {"path": path, "method": method, "body": body},
    }
    remote = urllib.request.Request(
        LOOPBACK,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={"Origin": ORIGIN, "Content-Type": "application/json", "X-LSFA-Channel-Token": channel},
    )
    with urllib.request.urlopen(remote, timeout=25) as response:
        result = json.load(response)
    if not isinstance(result.get("status"), int) or not 200 <= result["status"] < 300:
        raise RuntimeError(f"El companion devolvió {result.get('status')}.")
    body_result = result.get("body")
    if not isinstance(body_result, dict):
        raise RuntimeError("CloudPress no devolvió JSON de objeto.")
    remote_status = body_result.get("status", 200)
    if isinstance(remote_status, int) and remote_status >= 400:
        raise RuntimeError(f"CloudPress rechazó {method} {path}: {body_result.get('error', remote_status)}")
    return body_result


def created_id(result: dict, label: str) -> int:
    value = result.get("id")
    if not isinstance(value, int) or value <= 0:
        raise RuntimeError(f"{label} no devolvió un id válido: {result}")
    return value


def main() -> None:
    checks: list[str] = []
    artefacts: dict[str, object] = {"prefix": PREFIX, "origin": ORIGIN}

    # cloudpress_read_admin_state: every read resource supported by the tool.
    for path in (
        "/api/admin/entries",
        "/api/admin/users",
        "/api/admin/taxonomies",
        "/api/admin/menus",
        "/api/admin/plugins",
        "/api/admin/media",
        "/api/admin/plugin-schema",
        "/api/admin/blocks",
    ):
        request(path)
    checks.append("cloudpress_read_admin_state:state-resources")

    # create/update/trash/restore content, then return the disposable draft to trash.
    content = request("/api/admin/entries", "POST", {
        "kind": "post", "title": f"{PREFIX}_content", "slug": f"{PREFIX}-content",
        "excerpt": "Artefacto de prueba del agente.", "body": "Prueba E2E.", "status": "draft",
    })
    content_id = created_id(content, "create_draft")
    artefacts["content_id"] = content_id
    request(f"/api/admin/entries/{content_id}", "PATCH", {"title": f"{PREFIX}_content_updated"})
    request(f"/api/admin/entries/{content_id}", "DELETE")
    request(f"/api/admin/trash/{content_id}", "POST", {})
    request(f"/api/admin/entries/{content_id}", "DELETE")
    checks.extend(("cloudpress_create_draft", "cloudpress_update_content", "cloudpress_trash_content", "cloudpress_restore_content"))

    # metadata and blocks reads against the test content.
    request("/api/admin/plugin-meta", "PUT", {"scope": "content", "id": content_id, "key": "seo-basico.meta-title", "value": f"{PREFIX} SEO"})
    request(f"/api/admin/plugin-meta?scope=content&id={content_id}")
    request(f"/api/admin/blocks?contentId={content_id}")
    checks.extend(("cloudpress_manage_meta", "cloudpress_read_admin_state:metadata", "cloudpress_read_admin_state:blocks"))

    # Keep the administrator in its current active state; this executes the mutation without disruption.
    users = request("/api/admin/users").get("users", [])
    admin = next((user for user in users if user.get("role") == "admin" and user.get("active") == 1), None)
    if not isinstance(admin, dict) or not isinstance(admin.get("id"), int):
        raise RuntimeError("No se encontró un administrador activo para la prueba no disruptiva.")
    request(f"/api/admin/users/{admin['id']}/active", "POST", {"active": True})
    checks.append("cloudpress_set_user_active:no_state_change")

    # Navigation tool: one taxonomy and one menu, each created and updated.
    category = request("/api/admin/taxonomies", "POST", {"type": "category", "name": f"{PREFIX}_navigation"})
    category_id = created_id(category, "manage_navigation taxonomy")
    artefacts["navigation_term_id"] = category_id
    request(f"/api/admin/taxonomies?id={category_id}", "PUT", {"type": "category", "name": f"{PREFIX}_navigation_updated"})
    menu = request("/api/admin/menus", "POST", {"label": f"{PREFIX}_menu", "url": "/", "position": 9999})
    menu_id = created_id(menu, "manage_navigation menu")
    artefacts["menu_id"] = menu_id
    request(f"/api/admin/menus?id={menu_id}", "PUT", {"label": f"{PREFIX}_menu_updated", "url": "/", "position": 9999})
    checks.append("cloudpress_manage_navigation")

    # Terms tool: core and plugin taxonomies, list/create/update.
    request("/api/admin/taxonomies")
    core_term = request("/api/admin/taxonomies", "POST", {"type": "tag", "name": f"{PREFIX}_core_term", "slug": f"{PREFIX}-core-term"})
    core_term_id = created_id(core_term, "manage_terms core")
    artefacts["core_term_id"] = core_term_id
    request(f"/api/admin/taxonomies?id={core_term_id}", "PUT", {"type": "tag", "name": f"{PREFIX}_core_term_updated", "slug": f"{PREFIX}-core-term-updated"})
    plugin_base = "/api/admin/plugins/cloudpress-commerce/taxonomies/product-category"
    request(plugin_base)
    plugin_term = request(plugin_base, "POST", {"name": f"{PREFIX}_plugin_term", "slug": f"{PREFIX}-plugin-term", "parentId": None})
    plugin_term_id = created_id(plugin_term, "manage_terms plugin")
    artefacts["plugin_term_id"] = plugin_term_id
    request(f"{plugin_base}/{plugin_term_id}", "PUT", {"name": f"{PREFIX}_plugin_term_updated", "slug": f"{PREFIX}-plugin-term-updated", "parentId": None})
    checks.append("cloudpress_manage_terms:core-and-plugin")

    # Plugin install is idempotent when the signed release is already active. Then toggle and restore it.
    installed = request("/api/admin/plugins", "POST", {"id": "seo-basico"})
    if installed.get("id") != "seo-basico":
        raise RuntimeError("install_plugin no devolvió el plugin solicitado.")
    request("/api/admin/plugins/seo-basico", "PATCH", {"status": "disabled"})
    request("/api/admin/plugins/seo-basico", "PATCH", {"status": "enabled"})
    checks.extend(("cloudpress_install_plugin:idempotent", "cloudpress_set_plugin_state:restored"))

    # 1x1 PNG and metadata update through the agent-only media route.
    png = "data:image/png;base64," + base64.b64encode(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4z8DwHwAFgAI/ScL8WQAAAABJRU5ErkJggg==")).decode("ascii")
    media = request("/api/admin/media-agent", "POST", {"filename": f"{PREFIX}.png", "dataUrl": png, "metadata": {"altText": "Píxel de prueba E2E"}})
    media_key = media.get("key")
    if not isinstance(media_key, str) or not media_key.startswith("media/"):
        raise RuntimeError("upload_media no devolvió una clave de medio válida.")
    artefacts["media_key"] = media_key
    request(f"/api/admin/media/{media_key[6:]}", "PATCH", {"caption": "Metadato actualizado durante prueba E2E"})
    checks.extend(("cloudpress_upload_media", "cloudpress_update_media_meta"))

    ARTIFACTS.write_text(json.dumps(artefacts, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "checks": checks, "artefacts": artefacts}, ensure_ascii=False))


if __name__ == "__main__":
    main()
