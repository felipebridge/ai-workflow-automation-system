#!/usr/bin/env python3
import os, sys, json, subprocess, datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(os.environ.get("GITHUB_WORKSPACE", Path(__file__).parents[3]))
REPORTS = ROOT / ".github" / "reports" / "deps"
SKIP = {".github", ".git", "node_modules", ".venv", "venv"}


def find_req_files():
    return [f for f in ROOT.rglob("requirements*.txt") if not any(s in f.parts for s in SKIP)]


def parse_req(path):
    pkgs = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        for sep in ("==", ">=", "~=", "<=", "!="):
            if sep in line:
                name, ver = line.split(sep, 1)
                pkgs.append((name.strip().lower(), ver.strip().split(",")[0], sep))
                break
        else:
            pkgs.append((line.lower(), None, None))
    return pkgs


def pip_audit():
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pip_audit", "--format", "json", "--no-deps"],
            capture_output=True, text=True, timeout=60, cwd=ROOT
        )
        data = json.loads(r.stdout) if r.stdout else {}
        return {
            item["name"].lower(): [v["id"] for v in item.get("vulns", [])]
            for item in data.get("dependencies", [])
            if item.get("vulns")
        }
    except Exception:
        return {}


def latest_version(pkg):
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pip", "index", "versions", pkg],
            capture_output=True, text=True, timeout=15
        )
        for line in r.stdout.splitlines():
            if "Available versions:" in line:
                versions = line.split(":", 1)[1].strip().split(", ")
                return versions[0].strip() if versions else None
    except Exception:
        pass
    return None


def is_patch(current, latest):
    try:
        c = tuple(int(x) for x in current.split(".")[:3])
        l = tuple(int(x) for x in latest.split(".")[:3])
        return l[:2] == c[:2] and l[2] > c[2]
    except Exception:
        return False


def is_minor(current, latest):
    try:
        c = tuple(int(x) for x in current.split(".")[:3])
        l = tuple(int(x) for x in latest.split(".")[:3])
        return l[0] == c[0] and l[1] > c[1]
    except Exception:
        return False


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)

    req_files = find_req_files()
    vulns = pip_audit()
    updates = []

    for rf in req_files:
        for name, pinned, op in parse_req(rf):
            if op == "==":
                latest = latest_version(name)
                if latest and latest != pinned:
                    if is_patch(pinned, latest):
                        updates.append((name, pinned, latest, "patch"))
                    elif is_minor(pinned, latest):
                        updates.append((name, pinned, latest, "minor"))
            elif op is None:
                updates.append((name, None, None, "unpinned"))

    today = datetime.date.today()
    lines = [
        "# Dependency Report", "",
        f"_Date: {today.isoformat()}_", "",
    ]

    if req_files:
        lines += ["**Scanned:**", ""]
        for f in req_files:
            lines.append(f"- `{f.relative_to(ROOT)}`")

    lines += ["", "## Security", ""]
    if vulns:
        lines += ["| Package | CVE |", "|---------|-----|"]
        for pkg, ids in vulns.items():
            lines.append(f"| `{pkg}` | {', '.join(ids)} |")
        lines.append(f"\n> ⚠️ {len(vulns)} package(s) with known issues.")
    else:
        lines.append("No known CVEs found.")

    patch = [(p, c, l) for p, c, l, k in updates if k == "patch"]
    minor = [(p, c, l) for p, c, l, k in updates if k == "minor"]
    unpinned = [(p,) for p, c, l, k in updates if k == "unpinned"]

    lines += ["", "## Updates", ""]
    if patch:
        lines += ["**Patch (safe):**", "", "| Package | Current | Latest |", "|---------|---------|--------|"]
        for p, c, l in patch:
            lines.append(f"| `{p}` | `{c}` | `{l}` |")
        lines.append("")
    if minor:
        lines += ["**Minor (review first):**", "", "| Package | Current | Latest |", "|---------|---------|--------|"]
        for p, c, l in minor:
            lines.append(f"| `{p}` | `{c}` | `{l}` |")
        lines.append("")
    if unpinned:
        lines += ["**Unpinned:**", "", "| Package |", "|---------|"]
        for (p,) in unpinned:
            lines.append(f"| `{p}` |")
        lines += ["", "> These aren't pinned — builds may not be reproducible."]
    if not patch and not minor and not unpinned:
        lines.append("All deps look current.")

    lines += ["", "---"]
    path = REPORTS / f"{today.strftime('%Y-%m')}-dep-report.md"
    path.write_text("\n".join(lines), encoding="utf-8")

    print(f"CVEs: {len(vulns)} | Patch updates: {len(patch)}")
    print(f"Report: {path.relative_to(ROOT)}")
    if vulns:
        print(f"::warning::Dependency audit: {len(vulns)} CVE(s) found.")
    else:
        print(f"::notice::Dependency audit clean. {len(patch)} patch update(s) available.")


if __name__ == "__main__":
    main()
