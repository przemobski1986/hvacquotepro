import subprocess
import sys

tests = [
    ["python", "smoke_timekeeping.py"],
    ["python", "smoke_timekeeping_stop.py"],
]

for cmd in tests:
    print("RUN:", " ".join(cmd))
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        print(p.stdout)
        print(p.stderr, file=sys.stderr)
        raise SystemExit(p.returncode)
    print(p.stdout.strip())

print("ALL_OK")
