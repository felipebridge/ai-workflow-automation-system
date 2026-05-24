#!/usr/bin/env python3
import os, sys, json, subprocess, datetime
from pathlib import Path
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(os.environ.get("GITHUB_WORKSPACE", Path(__file__).parents[3]))
REPORTS = ROOT / ".github" / "reports" / "health"
STATE = ROOT / ".github" / "reports" / ".metrics-state.json"
SKIP = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv"}


def git(*args):
    try:
        return subprocess.check_output(
            ["git", "-C", str(ROOT)] + list(args),
            text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return ""


def activity_by_week(weeks=12):
    cutoff = datetime.date.today() - datetime.timedelta(weeks=weeks)
    raw = git("log", f"--after={cutoff.isoformat()}", "--format=%ai")
    wmap = defaultdict(int)
    for line in raw.splitlines():
        try:
            d = datetime.datetime.fromisoformat(line.strip()[:10])
            wmap[d.strftime("%Y-W%W")] += 1
        except Exception:
            pass
    return [{"week": k, "commits": v} for k, v in sorted(wmap.items())]


def top_contributors(n=5):
    raw = git("shortlog", "-sn", "HEAD")
    result = []
    for line in raw.splitlines()[:n]:
        parts = line.strip().split("\t", 1)
        if len(parts) == 2:
            result.append({"commits": int(parts[0].strip()), "author": parts[1].strip()})
    return result


def churn_stats():
    cutoff = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    raw = git("log", f"--after={cutoff}", "--shortstat", "--no-merges")
    added = removed = 0
    for line in raw.splitlines():
        if "insertion" in line or "deletion" in line:
            for p in line.strip().split(","):
                p = p.strip()
                if "insertion" in p:
                    added += int(p.split()[0])
                elif "deletion" in p:
                    removed += int(p.split()[0])
    return {"added": added, "removed": removed, "net": added - removed}


def total_loc():
    n = 0
    for f in ROOT.rglob("*.py"):
        if any(s in f.parts for s in SKIP):
            continue
        try:
            n += len(f.read_text(encoding="utf-8", errors="ignore").splitlines())
        except Exception:
            pass
    return n


def load_state():
    if STATE.exists():
        try:
            return json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_state(s):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=2), encoding="utf-8")


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    today = datetime.date.today()
    month = today.strftime("%Y-%m")
    path = REPORTS / f"{month}-metrics.md"

    state = load_state()
    if state.get("last_metrics_month") == month and path.exists():
        print(f"Metrics already up to date for {month}.")
        return

    activity = activity_by_week(12)
    contributors = top_contributors(5)
    churn = churn_stats()
    loc = total_loc()
    total_str = git("rev-list", "--count", "HEAD") or "?"

    lines = [
        "# Project Metrics Snapshot", "",
        f"_Captured: {today.isoformat()}_", "",
        "## Overview", "",
        "| Metric | Value |", "|--------|-------|",
        f"| Total commits | {total_str} |",
        f"| Total Python LOC | {loc:,} |",
        f"| Lines added (30d) | +{churn['added']:,} |",
        f"| Lines removed (30d) | -{churn['removed']:,} |",
        f"| Net churn (30d) | {'+' if churn['net'] >= 0 else ''}{churn['net']:,} |",
        "", "## Commit Activity (last 12 weeks)", "",
        "| Week | Commits |", "|------|---------|",
    ]
    for entry in activity[-12:]:
        bar = "x" * min(entry["commits"], 20)
        lines.append(f"| {entry['week']} | {entry['commits']} |")

    if contributors:
        lines += ["", "## Top Contributors", "", "| Author | Commits |", "|--------|---------|"]
        for c in contributors:
            lines.append(f"| {c['author']} | {c['commits']} |")

    lines += ["", "---"]
    path.write_text("\n".join(lines), encoding="utf-8")

    state["last_metrics_month"] = month
    save_state(state)

    print(f"Metrics: {loc:,} LOC, {churn['added']} lines added last 30d")
    print(f"Report: {path.relative_to(ROOT)}")
    print(f"::notice::Metrics snapshot for {month}")


if __name__ == "__main__":
    main()
