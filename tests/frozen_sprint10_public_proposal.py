from pathlib import Path


ROOT = Path(__file__).parents[1]


def read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8").lower()


def test_public_implementation_guide_covers_security_and_platforms():
    text = read("IMPLEMENTATION-GUIDE.md")
    assert "recibe secretos ni puede confirmar" in text
    assert "puede confirmar" in text
    assert "windows" in text and "macos" in text and "linux" in text
    assert "headless" in text


def test_contributor_and_feedback_paths_avoid_real_secrets():
    assert "no se aceptan cambios" in read("CONTRIBUTING.md")
    feedback = read("FEEDBACK.md")
    assert "ejemplo sintético" in feedback
    assert "security.md" in feedback


def test_sprint10_contract_is_frozen():
    text = read("knowledge/contracts/sprint10-public-proposal.md")
    assert "status: frozen" in text
    assert "canal de feedback" in text
    assert "parar" in text and "reportar" in text
    assert "no se realizan envíos" in text
