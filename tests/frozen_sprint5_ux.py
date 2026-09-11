"""Pruebas congeladas de las guías UX y de estilos LSFA."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_ux_guide_freezes_safe_flow_and_modes():
    text = (ROOT / "UX-GUIDE.md").read_text(encoding="utf-8")
    for marker in ("GUI", "Terminal", "Manual/headless", "preflight", "Sí, confirmar", "Rechazar", "Cancelar", "español", "inglés", "portugués"):
        assert marker in text
    assert "sin secretos" in text


def test_style_guide_freezes_unambiguous_actions():
    text = (ROOT / "STYLE-GUIDE.md").read_text(encoding="utf-8")
    for marker in ("Sí, confirmar", "Rechazar", "Cancelar", "Eliminar\npermanentemente", "riesgo"):
        assert marker in text
    assert "mayúsculas como única protección" in text


def test_contract_freezes_accessibility_and_security_boundary():
    text = (ROOT / "knowledge" / "contracts" / "sprint5-ux-style.md").read_text(encoding="utf-8")
    assert "task: sprint5_ux_style" in text
    assert "tests: tests/frozen_sprint5_ux.py" in text
    assert "PARAR y reportar si" in text
    assert "aceptar, rechazar y cancelar" in text
