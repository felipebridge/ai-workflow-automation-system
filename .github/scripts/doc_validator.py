#!/usr/bin/env python3
import os, sys, re, ast, datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(os.environ.get("GITHUB_WORKSPACE", Path(__file__).parents[3]))
REPORTS = ROOT / ".github" / "reports" / "docs"
SKIP = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv"}


def check_readme():
    readme = ROOT / "README.md"
    if not readme.exists():
        return {"found": False, "score": 0, "issues": ["README.md missing"], "sections": [], "lines": 0}
    text = readme.read_text(encoding="utf-8", errors="ignore")
    score = 0
    issues = []
    criteria = [
        (len(text) >= 500, 10, "has enough content"),
        ("```" in text, 15, "has code examples"),
        (any(w in text.lower() for w in ["install", "setup", "getting started"]), 20, "setup instructions"),
        (any(w in text.lower() for w in ["usage", "example", "quickstart"]), 15, "usage examples"),
        (any(w in text.lower() for w in ["require", "depend"]), 10, "mentions dependencies"),
        (len(re.findall(r"^#{1,3}\s", text, re.MULTILINE)) >= 3, 10, "multiple sections"),
        (any(w in text.lower() for w in ["license", "mit", "apache"]), 5, "license mentioned"),
        (len(text.splitlines()) >= 40, 15, "at least 40 lines"),
    ]
    for ok, pts, label in criteria:
        if ok:
            score += pts
        else:
            issues.append(f"missing: {label}")
    sections = re.findall(r"^#{1,3}\s+(.+)$", text, re.MULTILINE)
    return {"found": True, "score": min(score, 100), "issues": issues,
            "sections": [s.strip() for s in sections], "lines": len(text.splitlines())}


def docstring_coverage():
    total_fn = documented_fn = total_cls = documented_cls = 0
    undocumented = []
    for f in ROOT.rglob("*.py"):
        if any(s in f.parts for s in SKIP):
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        rel = str(f.relative_to(ROOT))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                total_fn += 1
                if ast.get_docstring(node):
                    documented_fn += 1
                elif not node.name.startswith("_"):
                    undocumented.append(f"{rel}::{node.name}")
            elif isinstance(node, ast.ClassDef):
                total_cls += 1
                if ast.get_docstring(node):
                    documented_cls += 1
    fn_pct = round(documented_fn / total_fn * 100) if total_fn else 0
    return {"total_fn": total_fn, "documented_fn": documented_fn, "fn_pct": fn_pct,
            "total_cls": total_cls, "documented_cls": documented_cls,
            "undocumented_sample": undocumented[:10]}


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    readme = check_readme()
    docs = docstring_coverage()
    changelog = any((ROOT / n).exists() for n in ["CHANGELOG.md", "CHANGELOG", "CHANGES.md"])
    today = datetime.date.today()

    lines = ["# Doc Quality Report", "", f"_Date: {today.isoformat()}_", ""]
    if readme["found"]:
        s = readme["score"]
        b = "good" if s >= 75 else "needs work"
        lines += [f"## README — {s}/100 ({b})", "", f"- Lines: {readme['lines']}", ""]
        if readme["sections"]:
            lines += ["**Sections:**", ""]
            for sec in readme["sections"]:
                lines.append(f"- {sec}")
        if readme["issues"]:
            lines += ["", "**Gaps:**", ""]
            for issue in readme["issues"]:
                lines.append(f"- {issue}")
    else:
        lines.append("README.md not found.")

    lines += ["", "## Docstring Coverage", ""]
    if docs["total_fn"] > 0:
        lines += [
            "| | |", "|--|--|",
            f"| Functions | {docs['documented_fn']}/{docs['total_fn']} ({docs['fn_pct']}%) |",
            f"| Classes | {docs['documented_cls']}/{docs['total_cls']} |",
        ]
        if docs["undocumented_sample"]:
            lines += ["", "**Undocumented public functions (sample):**", ""]
            for fn in docs["undocumented_sample"]:
                lines.append(f"- `{fn}`")

    lines += ["", "## Changelog", ""]
    lines.append("Found." if changelog else "No CHANGELOG file.")
    lines += ["", "---"]

    path = REPORTS / f"{today.strftime('%Y-%m')}-doc-quality.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"README: {readme.get('score', 0)}/100 | Docstrings: {docs['fn_pct']}%")
    print(f"Report: {path.relative_to(ROOT)}")
    print(f"::notice::Docs -- README {readme.get('score',0)}/100, docstrings {docs['fn_pct']}%")


if __name__ == "__main__":
    main()
