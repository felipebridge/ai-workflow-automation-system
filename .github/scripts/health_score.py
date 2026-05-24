#!/usr/bin/env python3
import os, sys, json, subprocess, datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(os.environ.get("GITHUB_WORKSPACE", Path(__file__).parents[3]))
REPORTS = ROOT / ".github" / "reports" / "health"
SKIP = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv"}


def file_counts():
    counts = {}
    for f in ROOT.rglob("*"):
        if f.is_file() and not any(s in f.parts for s in SKIP):
            ext = f.suffix.lower() or "(none)"
            counts[ext] = counts.get(ext, 0) + 1
    return counts


def key_files():
    req = list(ROOT.rglob("requirements*.txt")) + list(ROOT.rglob("pyproject.toml"))
    pkg = (ROOT / "frontend" / "package.json").exists() or (ROOT / "package.json").exists()
    docker = (ROOT / "docker-compose.yml").exists() or (ROOT / "Dockerfile").exists()
    return {
        "README.md": (ROOT / "README.md").exists(),
        ".gitignore": (ROOT / ".gitignore").exists(),
        "requirements / pyproject": bool(req),
        "tests": bool(list(ROOT.rglob("test_*.py")) + list(ROOT.rglob("*_test.py"))),
        ".env.example": bool(list(ROOT.rglob(".env.example"))),
        "docker": docker,
        "frontend deps": pkg,
    }


def test_count():
    return len(list(ROOT.rglob("test_*.py"))) + len(list(ROOT.rglob("*_test.py")))


def source_count():
    return len([
        f for f in ROOT.rglob("*.py")
        if not any(s in f.parts for s in SKIP) and "test" not in f.name.lower()
    ])


def git_metrics():
    def g(*args):
        try:
            return subprocess.check_output(["git", "-C", str(ROOT)] + list(args), text=True).strip()
        except Exception:
            return ""
    last = g("log", "-1", "--format=%ci")[:10] or "n/a"
    total = g("rev-list", "--count", "HEAD") or "0"
    cutoff = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
    recent = g("log", f"--after={cutoff}", "--oneline")
    return {
        "last_commit": last,
        "total_commits": int(total) if total.isdigit() else 0,
        "commits_last_30d": len(recent.splitlines()) if recent else 0,
    }


def readme_score():
    r = ROOT / "README.md"
    if not r.exists():
        return 0
    t = r.read_text(encoding="utf-8", errors="ignore")
    s = 0
    if len(t) > 500: s += 15
    if "```" in t: s += 20
    if any(h in t for h in ["## ", "# "]): s += 10
    if any(w in t.lower() for w in ["install", "setup", "getting started"]): s += 20
    if any(w in t.lower() for w in ["usage", "example", "quickstart"]): s += 15
    if any(w in t.lower() for w in ["require", "depend"]): s += 10
    if len(t.splitlines()) >= 40: s += 10
    return min(s, 100)


def badge(n):
    return "🟢" if n >= 80 else "🟡" if n >= 60 else "🟠" if n >= 40 else "🔴"


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)

    kf = key_files()
    fc = file_counts()
    tc = test_count()
    sc = source_count()
    gm = git_metrics()
    rs = readme_score()

    doc_pts = round(rs * 0.25)
    struct_pts = round((sum(kf.values()) / len(kf)) * 25)
    test_pts = round(min(tc / max(sc * 0.25, 1), 1.0) * 25) if sc else 0
    activity_pts = round(min(gm["commits_last_30d"] / 6, 1.0) * 25)
    score = doc_pts + struct_pts + test_pts + activity_pts

    today = datetime.date.today()
    top_ext = sorted(fc.items(), key=lambda x: x[1], reverse=True)[:6]

    lines = [
        "# Repository Health Report", "",
        f"**Score: {score}/100** {badge(score)}", "",
        f"_Report date: {today.isoformat()}_", "",
        "## Score Breakdown", "",
        "| Dimension | Score | Max |",
        "|-----------|------:|----:|",
        f"| Documentation | {doc_pts} | 25 |",
        f"| Project structure | {struct_pts} | 25 |",
        f"| Testing | {test_pts} | 25 |",
        f"| Activity | {activity_pts} | 25 |",
        "", "## Project Structure", "",
        "| Check | Status |", "|-------|--------|",
    ]
    for k, v in kf.items():
        lines.append(f"| `{k}` | {'✅' if v else '❌'} |")

    lines += [
        "", "## Code Metrics", "",
        f"- Python source files: **{sc}**",
        f"- Test files: **{tc}**",
        f"- README quality: **{rs}/100**",
        "", "### File types", "",
    ]
    for ext, n in top_ext:
        lines.append(f"- `{ext}` — {n} files")

    lines += [
        "", "## Git Activity", "",
        "| Metric | Value |", "|--------|-------|",
        f"| Last commit | `{gm['last_commit']}` |",
        f"| Total commits | {gm['total_commits']} |",
        f"| Commits (30d) | {gm['commits_last_30d']} |",
        "", "---", "_Health check done._",
    ]

    path = REPORTS / f"{today.strftime('%Y-%m')}-health.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Health score: {score}/100 {badge(score)}")
    print(f"Report: {path.relative_to(ROOT)}")
    print(f"::notice::Health score {score}/100 {badge(score)}")


if __name__ == "__main__":
    main()
