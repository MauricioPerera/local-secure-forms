from pathlib import Path


def test_combined_start_script_keeps_companion_foreground_and_runner_scoped():
    script = (Path(__file__).resolve().parents[1] / "scripts" / "start-cloudpress-agent.ps1").read_text(encoding="utf-8")
    assert "run_cloudpress_agent.py" in script
    assert "-WindowStyle Hidden" in script
    assert "& $companion" in script
    assert "Stop-Process -Id $runnerProcess.Id" in script
    assert "--origin" in script
