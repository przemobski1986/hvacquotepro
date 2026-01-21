import subprocess
from pathlib import Path

def test_smoke_isolated_ps1():
    backend_dir = Path(__file__).resolve().parents[1]
    ps1 = backend_dir / "run_smoke_isolated.ps1"
    assert ps1.exists(), f"Brak pliku: {ps1}"

    r = subprocess.run(
        ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(ps1)],
        cwd=str(backend_dir),
        check=False
    )
    assert r.returncode == 0
