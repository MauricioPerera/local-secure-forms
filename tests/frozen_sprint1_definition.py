"""Pruebas congeladas del alcance del Objetivo 1."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_definition_has_product_boundary_and_principles():
    text = (ROOT / "DEFINITION.md").read_text(encoding="utf-8")
    for marker in (
        "## Problema",
        "## Solución",
        "## Usuarios y actores",
        "## Alcance inicial",
        "## Fuera de alcance",
        "## Principios no negociables",
        "El secreto no aparece",
        "El agente no puede confirmar",
    ):
        assert marker in text


def test_contract_points_to_definition_and_test():
    text = (ROOT / "knowledge" / "contracts" / "sprint1-product-architecture.md").read_text(encoding="utf-8")
    assert "task: sprint1_product_architecture" in text
    assert "target: DEFINITION.md" in text
    assert "tests: tests/frozen_sprint1_definition.py" in text
    assert "PARAR y reportar si" in text


def test_knowledge_index_links_required_nodes():
    text = (ROOT / "knowledge" / "index.md").read_text(encoding="utf-8")
    for relative in (
        "../DEFINITION.md",
        "domain/actors.md",
        "domain/use-cases.md",
        "architecture/boundaries.md",
        "contracts/sprint1-product-architecture.md",
    ):
        assert relative in text
