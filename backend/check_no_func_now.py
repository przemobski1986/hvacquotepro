from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
APP = ROOT / "app"

PATTERNS = [
    "func.now()",
    "server_default=func.now()",
    "onupdate=func.now()",
]

hits = []

for p in APP.rglob("*.py"):
    try:
        text = p.read_text(encoding="utf-8")
    except Exception:
        continue
    for pat in PATTERNS:
        if pat in text:
            for i, line in enumerate(text.splitlines(), start=1):
                if pat in line:
                    hits.append(f"{p.relative_to(ROOT)}:{i}: {line.strip()}")

if hits:
    print("FAIL: found forbidden time defaults:")
    for h in hits:
        print("  " + h)
    sys.exit(1)

print("OK")
