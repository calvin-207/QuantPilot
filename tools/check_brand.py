"""Block importing an unrebranded upstream UI into QuantPilot.

This is a known-pattern check, not a complete legal/visual audit.
Provider identification and mandatory copyright notices remain valid.
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = tuple(re.compile(p, re.I) for p in (
    r"ftai-mark\.svg",
    r"etf\.jtxaionline\.com",
    r"ftai\.chat/ftshare",
    r"即刻体验\s*FtShare",
    r"FtShare\s*[·|]\s*ETF",
    r"ftshare-theme",
))
UI_DIRS = (ROOT / "src", ROOT / "frontend")
issues = []
for folder in UI_DIRS:
    if not folder.exists():
        continue
    for p in folder.rglob("*"):
        if not p.is_file() or p.suffix not in {".html", ".css", ".js", ".jsx", ".tsx", ".vue", ".svg"}:
            continue
        if p.name == "echarts.min.js":
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        for pattern in PATTERNS:
            if pattern.search(text):
                issues.append(f"{p.relative_to(ROOT)}: {pattern.pattern}")
if not (ROOT / "src/index.html").exists() and not (ROOT / "frontend").exists():
    print("NOT READY: upstream user interface not imported")
    sys.exit(2)
if issues:
    print("FAILED:\n" + "\n".join(issues))
    sys.exit(1)
print("PASS: known upstream promotional UI patterns absent")
