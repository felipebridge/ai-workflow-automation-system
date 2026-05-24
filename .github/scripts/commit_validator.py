#!/usr/bin/env python3
import os, sys, json, subprocess, re
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(os.environ.get("GITHUB_WORKSPACE", Path(__file__).parents[3]))
PROTECTED_FILE = ROOT / ".github" / "policies" / "protected-paths.json"
THRESHOLDS_FILE = ROOT / ".github" / "policies" / "change-thresholds.json"

DEFAULT_THRESHOLDS = {"max_lines_changed": 200, "max_files_changed": 10, "min_confidence_score": 75}
DEFAULT_PROTECTED = {"exact": [], "prefixes": [], "patterns": []}


def load_json(path, default):
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return default


def staged_files():
    try:
        raw = subprocess.check_output(
            ["git", "-C", str(ROOT), "diff", "--cached", "--name-status"], text=True
        ).strip()
        return [line.split("\t")[-1] for line in raw.splitlines() if line.strip()]
    except Exception:
        return []


def staged_lines():
    try:
        raw = subprocess.check_output(
            ["git", "-C", str(ROOT), "diff", "--cached", "--stat"], text=True
        )
        for line in reversed(raw.splitlines()):
            nums = re.findall(r"\d+", line)
            if len(nums) >= 2:
                return sum(int(n) for n in nums[1:3])
    except Exception:
        pass
    return 0


def is_protected(filepath, policy):
    for exact in policy.get("exact", []):
        if filepath == exact:
            return True, f"exact: {exact}"
    for prefix in policy.get("prefixes", []):
        if filepath.startswith(prefix):
            return True, f"prefix: {prefix}"
    for pattern in policy.get("patterns", []):
        if re.search(pattern, filepath):
            return True, f"pattern: {pattern}"
    return False, ""


def confidence(files, lines, thresholds, blocked):
    score = 100
    if blocked:
        score -= 100
    max_lines = thresholds.get("max_lines_changed", 200)
    if lines > max_lines:
        score -= min(int((lines - max_lines) / max_lines * 50), 50)
    if len(files) > thresholds.get("max_files_changed", 10):
        score -= 20
    safe_only = all(
        any(safe in f for safe in [".github/reports/", "README", "docs/", ".md"])
        for f in files
    )
    if safe_only and files:
        score += 10
    return max(0, min(score, 100))


def main():
    policy = load_json(PROTECTED_FILE, DEFAULT_PROTECTED)
    thresholds = load_json(THRESHOLDS_FILE, DEFAULT_THRESHOLDS)
    min_score = thresholds.get("min_confidence_score", 75)

    files = staged_files()
    if not files:
        print("Nothing staged.")
        sys.exit(0)

    lines = staged_lines()
    blocked = []
    for f in files:
        ok, reason = is_protected(f, policy)
        if ok:
            blocked.append((f, reason))

    score = confidence(files, lines, thresholds, blocked)

    print(f"Files: {len(files)} | Lines: {lines} | Confidence: {score}/100")

    if blocked:
        print("BLOCKED — protected files in staged changes:")
        for f, r in blocked:
            print(f"  {f} -> {r}")
        sys.exit(1)

    if score < min_score:
        print(f"BLOCKED — confidence {score} below threshold {min_score}")
        sys.exit(1)

    print(f"OK — confidence {score}/100")
    sys.exit(0)


if __name__ == "__main__":
    main()
