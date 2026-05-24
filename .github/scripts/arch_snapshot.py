#!/usr/bin/env python3
import os, sys, ast, datetime
from pathlib import Path
from collections import defaultdict

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(os.environ.get("GITHUB_WORKSPACE", Path(__file__).parents[3]))
REPORTS = ROOT / ".github" / "reports" / "arch"
SKIP = {".git", ".github", "node_modules", "__pycache__", ".venv", "venv",
        ".mypy_cache", ".pytest_cache", "dist", "build", ".next"}


def build_tree(root, prefix="", max_depth=4, depth=0):
    if depth >= max_depth:
        return []
    lines = []
    children = sorted(
        [p for p in root.iterdir() if p.name not in SKIP],
        key=lambda p: (p.is_file(), p.name.lower())
    )
    for i, child in enumerate(children):
        last = i == len(children) - 1
        conn = "└── " if last else "├── "
        ext = "    " if last else "│   "
        if child.is_dir():
            lines.append(f"{prefix}{conn}{child.name}/")
            lines.extend(build_tree(child, prefix + ext, max_depth, depth + 1))
        else:
            lines.append(f"{prefix}{conn}{child.name}")
    return lines


def loc_by_module():
    result = defaultdict(int)
    for f in ROOT.rglob("*.py"):
        if any(s in f.parts for s in SKIP):
            continue
        try:
            n = len(f.read_text(encoding="utf-8", errors="ignore").splitlines())
        except Exception:
            n = 0
        parts = f.relative_to(ROOT).parts
        top = parts[0] if len(parts) > 1 else "root"
        result[top] += n
    return dict(result)


def get_imports(py_file):
    try:
        tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return []
    imps = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imps.append(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imps.append(node.module.split(".")[0])
    return list(set(imps))


def import_map():
    result = defaultdict(set)
    for f in ROOT.rglob("*.py"):
        if any(s in f.parts for s in SKIP):
            continue
        parts = f.relative_to(ROOT).parts
        mod = parts[0] if len(parts) > 1 else "root"
        for imp in get_imports(f):
            if imp not in ("__future__", mod):
                result[mod].add(imp)
    return {k: sorted(v) for k, v in result.items()}


def file_summary():
    counts = {}
    for f in ROOT.rglob("*"):
        if f.is_file() and not any(s in f.parts for s in SKIP):
            ext = f.suffix.lower() or "(none)"
            counts[ext] = counts.get(ext, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    tree = build_tree(ROOT)
    loc = loc_by_module()
    imps = import_map()
    fs = file_summary()
    today = datetime.date.today()
    total_loc = sum(loc.values())
    total_files = sum(fs.values())

    lines = [
        "# Architecture Snapshot", "",
        f"_Generated: {today.isoformat()}_", "",
        f"**{total_files} files** | **{total_loc:,} Python LOC**", "",
        "## Directory Tree", "", "```", f"{ROOT.name}/",
    ]
    lines.extend(tree)
    lines += ["```", "", "## Module Size (Python LOC)", "", "| Module | LOC |", "|--------|-----|"]
    for mod, n in sorted(loc.items(), key=lambda x: x[1], reverse=True):
        lines.append(f"| `{mod}` | {n:,} |")
    lines += ["", "## Imports", "", "| Module | Uses |", "|--------|------|"]
    for mod, deps in sorted(imps.items()):
        if deps:
            s = ", ".join(f"`{d}`" for d in deps[:8])
            if len(deps) > 8:
                s += f", ... (+{len(deps)-8})"
            lines.append(f"| `{mod}` | {s} |")
    lines += ["", "## File types", "", "| Extension | Files |", "|-----------|------:|"]
    for ext, n in list(fs.items())[:10]:
        lines.append(f"| `{ext}` | {n} |")
    lines += ["", "---"]
    path = REPORTS / f"{today.strftime('%Y-%m')}-snapshot.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Snapshot: {total_loc:,} LOC across {len(loc)} modules")
    print(f"Report: {path.relative_to(ROOT)}")
    print(f"::notice::Architecture snapshot ({total_loc:,} LOC)")


if __name__ == "__main__":
    main()
