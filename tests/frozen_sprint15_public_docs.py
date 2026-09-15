"""La documentación pública debe describir la extensión sin debilitar LSFA."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_landing_links_the_dynamic_presentation_documentation():
    landing = (ROOT / "site" / "index.html").read_text(encoding="utf-8")
    assert 'id="presentation"' in landing
    assert 'href="presentation.html"' in landing
    assert "Presentación 0.3" in landing


def test_technical_page_states_the_trust_boundary():
    page = (ROOT / "site" / "presentation.html").read_text(encoding="utf-8")
    for statement in (
        "La presentación nunca autoriza",
        "El agente puede sugerir",
        "La política local controla",
        "El cliente renderiza siempre",
        "LSFA sigue sin ser MCP",
    ):
        assert statement in page


def test_public_page_assets_are_local_and_present():
    for name in ("index.html", "presentation.html", "styles.css",
                 "presentation.css", "app.js"):
        assert (ROOT / "site" / name).is_file()
