#!/usr/bin/env python3
"""Deterministic first-pass reconnaissance of a source repository.

Usage:
  python3 repo_recon.py <local-path | https://github.com/owner/repo> [--out DIR] [--json]

If given a URL, clones it (full history, blobs fetched lazily) into DIR (default ./recon-<repo>).
Prints a markdown report and writes recon.json beside the clone.

This is a starting map, not an analysis: it finds manifests, dependencies, infrastructure,
entry points, tests and the shape of the git history. Reading the code is still the real work.
"""
import json
import os
import re
import subprocess
import sys
import tomllib
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

SKIP_DIRS = {".git", "node_modules", "vendor", "dist", "build", "out", "target", ".next", ".nuxt",
             "__pycache__", ".venv", "venv", "env", ".tox", ".mypy_cache", ".pytest_cache", "coverage",
             "third_party", "thirdparty", "external", ".gradle", ".idea", ".vscode", "Pods", "bower_components",
             ".turbo", ".cache", ".svelte-kit", "site-packages", ".terraform"}

EXT_LANG = {
    ".py": "Python", ".ipynb": "Jupyter", ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".jsx": "JavaScript (JSX)", ".ts": "TypeScript", ".tsx": "TypeScript (TSX)", ".go": "Go", ".rs": "Rust",
    ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin", ".scala": "Scala", ".rb": "Ruby", ".php": "PHP",
    ".cs": "C#", ".fs": "F#", ".c": "C", ".h": "C/C++ header", ".cc": "C++", ".cpp": "C++", ".cxx": "C++",
    ".hpp": "C++", ".m": "Objective-C", ".mm": "Objective-C++", ".swift": "Swift", ".dart": "Dart",
    ".ex": "Elixir", ".exs": "Elixir", ".erl": "Erlang", ".hs": "Haskell", ".ml": "OCaml", ".clj": "Clojure",
    ".lua": "Lua", ".r": "R", ".jl": "Julia", ".zig": "Zig", ".nim": "Nim", ".sol": "Solidity",
    ".vue": "Vue", ".svelte": "Svelte", ".astro": "Astro", ".html": "HTML", ".css": "CSS", ".scss": "SCSS",
    ".sass": "Sass", ".less": "Less", ".sql": "SQL", ".prisma": "Prisma schema", ".graphql": "GraphQL",
    ".gql": "GraphQL", ".proto": "Protocol Buffers", ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
    ".ps1": "PowerShell", ".tf": "Terraform", ".hcl": "HCL", ".yaml": "YAML", ".yml": "YAML",
    ".toml": "TOML", ".json": "JSON", ".md": "Markdown", ".mdx": "MDX", ".tex": "LaTeX",
    ".cu": "CUDA", ".wgsl": "WGSL", ".glsl": "GLSL", ".asm": "Assembly", ".s": "Assembly",
}
DATA_LANGS = {"YAML", "TOML", "JSON", "Markdown", "MDX", "HTML", "CSS", "SCSS", "Sass", "Less", "LaTeX"}

from known_packages import KNOWN  # noqa: E402  (shared with artifact_recon.py)


def run(cmd, cwd=None, timeout=120):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return r.stdout if r.returncode == 0 else ""
    except (OSError, subprocess.TimeoutExpired):
        return ""


def walk(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".") or d in {".github", ".circleci"}]
        for f in filenames:
            yield Path(dirpath) / f


def known(name):
    name = re.sub(r"/v\d+$", "", name)  # Go major-version suffixes
    if name in KNOWN:
        return KNOWN[name]
    for k, v in KNOWN.items():
        if name.startswith(k + "/") or (k.startswith("@") and name.startswith(k)):
            return v
    return None


def read(p, limit=400_000):
    try:
        return p.read_text(errors="replace")[:limit]
    except OSError:
        return ""


# ------------------------------------------------------------------ clone
args = sys.argv[1:]
if not args:
    print(__doc__)
    sys.exit(2)
target = args[0]
out_dir = None
if "--out" in args:
    out_dir = args[args.index("--out") + 1]
want_json = "--json" in args

if re.match(r"https?://|git@", target):
    name = re.sub(r"\.git$", "", target.rstrip("/").split("/")[-1])
    dest = Path(out_dir or f"recon-{name}").resolve()
    if not dest.exists():
        r = subprocess.run(["git", "clone", "--quiet", "--filter=blob:none", target, str(dest)],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"Clone failed: {r.stderr.strip()}")
            sys.exit(1)
    root = dest
else:
    root = Path(target).resolve()
if not root.is_dir():
    print(f"Not a directory: {root}")
    sys.exit(1)

R = {"root": str(root)}

# ------------------------------------------------------------------ files & languages
lang_files, lang_lines = Counter(), Counter()
files = []
for p in walk(root):
    rel = p.relative_to(root)
    files.append(rel)
    lang = EXT_LANG.get(p.suffix.lower())
    if p.name == "Dockerfile" or p.name.startswith("Dockerfile."):
        lang = "Dockerfile"
    if lang:
        lang_files[lang] += 1
        try:
            if p.stat().st_size < 2_000_000:
                lang_lines[lang] += sum(1 for _ in p.open("rb"))
        except OSError:
            pass
R["file_count"] = len(files)
R["languages"] = [{"language": l, "files": lang_files[l], "lines": lang_lines[l]}
                  for l, _ in lang_lines.most_common()]

# ------------------------------------------------------------------ tree (2 levels)
tree = defaultdict(int)
for f in files:
    parts = f.parts
    if len(parts) == 1:
        tree["."] += 1
    else:
        tree[parts[0] + ("/" + parts[1] if len(parts) > 2 else "")] += 1
R["tree"] = dict(sorted(tree.items()))

# ------------------------------------------------------------------ manifests & dependencies
manifests = []


def add_manifest(path, kind, deps=None, dev=None, extra=None):
    deps, dev = deps or {}, dev or {}
    detected = {}
    for n in list(deps) + list(dev):
        k = known(n)
        if k:
            detected[k[0]] = k[1]
    manifests.append({"path": str(path), "kind": kind, "dependencies": deps, "dev_dependencies": dev,
                      "detected": detected, **(extra or {})})


for f in files:
    p = root / f
    n = f.name
    try:
        if n == "package.json":
            d = json.loads(read(p))
            add_manifest(f, "npm", d.get("dependencies"), d.get("devDependencies"),
                         {"name": d.get("name"), "scripts": d.get("scripts", {}), "main": d.get("main"),
                          "bin": d.get("bin"), "workspaces": d.get("workspaces"), "engines": d.get("engines")})
        elif n == "pyproject.toml":
            d = tomllib.loads(read(p))
            proj = d.get("project", {})
            deps = {re.split(r"[<>=!~;\[ ]", x)[0].lower(): x for x in proj.get("dependencies", [])}
            poetry = d.get("tool", {}).get("poetry", {})
            deps.update({k.lower(): str(v) for k, v in poetry.get("dependencies", {}).items() if k != "python"})
            dev = {}
            for grp in proj.get("optional-dependencies", {}).values():
                dev.update({re.split(r"[<>=!~;\[ ]", x)[0].lower(): x for x in grp})
            add_manifest(f, "python (pyproject)", deps, dev,
                         {"name": proj.get("name") or poetry.get("name"), "scripts": proj.get("scripts", {}),
                          "build_backend": d.get("build-system", {}).get("build-backend")})
        elif re.match(r"requirements.*\.txt$", n):
            deps = {}
            for line in read(p).splitlines():
                line = line.split("#")[0].strip()
                if line and not line.startswith("-"):
                    deps[re.split(r"[<>=!~;\[ ]", line)[0].lower()] = line
            add_manifest(f, "python (requirements)", deps)
        elif n == "go.mod":
            txt = read(p)
            deps = dict(re.findall(r"^\s*([\w./-]+\.[\w./-]+)\s+(v[\w.+-]+)", txt, re.M))
            mod = re.search(r"^module\s+(\S+)", txt, re.M)
            gov = re.search(r"^go\s+(\S+)", txt, re.M)
            add_manifest(f, "go", deps, extra={"name": mod and mod.group(1), "go": gov and gov.group(1)})
        elif n == "Cargo.toml":
            d = tomllib.loads(read(p))
            norm = lambda m: {k: (v if isinstance(v, str) else v.get("version", "*")) for k, v in m.items()}
            add_manifest(f, "rust", norm(d.get("dependencies", {})), norm(d.get("dev-dependencies", {})),
                         {"name": d.get("package", {}).get("name"),
                          "workspace_members": d.get("workspace", {}).get("members")})
        elif n == "pom.xml":
            txt = read(p)
            deps = {a: "" for a in re.findall(r"<artifactId>([^<]+)</artifactId>", txt)[1:]}
            add_manifest(f, "maven", deps)
        elif n in ("build.gradle", "build.gradle.kts"):
            txt = read(p)
            deps = {m[1]: m[2] for m in re.findall(r"""['"]([\w.-]+):([\w.-]+):?([\w.+-]*)['"]""", txt)}
            add_manifest(f, "gradle", deps)
        elif n == "Gemfile":
            deps = {g: "" for g in re.findall(r"""^\s*gem\s+['"]([\w-]+)['"]""", read(p), re.M)}
            add_manifest(f, "ruby", deps)
        elif n == "composer.json":
            d = json.loads(read(p))
            add_manifest(f, "php", d.get("require"), d.get("require-dev"))
        elif n.endswith(".csproj"):
            deps = dict(re.findall(r'PackageReference Include="([^"]+)"(?: Version="([^"]*)")?', read(p)))
            add_manifest(f, ".NET", deps)
        elif n == "pubspec.yaml":
            txt = read(p)
            block = re.search(r"^dependencies:\n((?:[ \t]+.*\n?)*)", txt, re.M)
            deps = dict(re.findall(r"^\s{2}([\w_]+):\s*(.*)$", block.group(1), re.M)) if block else {}
            add_manifest(f, "dart/flutter", deps)
        elif n == "mix.exs":
            deps = {d: "" for d in re.findall(r"\{:(\w+),", read(p))}
            add_manifest(f, "elixir", deps)
        elif n == "CMakeLists.txt" and len(f.parts) <= 2:
            txt = read(p)
            add_manifest(f, "cmake", {m: "" for m in re.findall(r"find_package\((\w+)", txt)},
                         extra={"project": (re.search(r"project\((\w+)", txt) or [None, None])[1]})
    except (ValueError, tomllib.TOMLDecodeError, AttributeError, TypeError) as e:
        manifests.append({"path": str(f), "kind": "unparsed", "error": str(e)[:120]})
R["manifests"] = manifests
stack = defaultdict(set)
for m in manifests:
    for label, cat in m.get("detected", {}).items():
        stack[cat].add(label)
R["detected_stack"] = {k: sorted(v) for k, v in sorted(stack.items())}

# ------------------------------------------------------------------ infrastructure, CI, deploy
infra = defaultdict(list)
for f in files:
    p, n, s = root / f, f.name, str(f)
    if n == "Dockerfile" or n.startswith("Dockerfile.") or n.endswith(".Dockerfile"):
        bases = re.findall(r"^\s*FROM\s+(\S+)", read(p), re.M | re.I)
        infra["Docker"].append(f"{s} (FROM {', '.join(bases[:4])})")
    elif re.match(r"(docker-)?compose(\.[\w-]+)?\.ya?ml$", n):
        txt = read(p)
        svc = re.search(r"^services:\n((?:[ \t]+.*\n?|\n)*)", txt, re.M)
        names = re.findall(r"^  ([\w.-]+):\s*$", svc.group(1), re.M) if svc else []
        images = re.findall(r"^\s+image:\s*['\"]?([^\s'\"]+)", txt, re.M)
        infra["Compose"].append(f"{s}: services {names}; images {images[:8]}")
    elif s.startswith(".github/workflows/") and n.endswith((".yml", ".yaml")):
        txt = read(p)
        wf = re.search(r"^name:\s*(.+)$", txt, re.M)
        inline = re.search(r"^on:\s*\[?([\w, -]+)\]?\s*$", txt, re.M)
        on = [x.strip() for x in inline.group(1).split(",")] if inline else []
        on += re.findall(r"^\s{2}(push|pull_request|pull_request_target|schedule|workflow_dispatch|workflow_run|workflow_call|release|merge_group)\b", txt, re.M)
        infra["GitHub Actions"].append(f"{s}: {wf.group(1).strip() if wf else n} (on {sorted(set(on))})")
    elif n in (".gitlab-ci.yml", "Jenkinsfile", "azure-pipelines.yml", "bitbucket-pipelines.yml") or s.startswith(".circleci/"):
        infra["CI (other)"].append(s)
    elif n.endswith(".tf"):
        txt = read(p)
        provs = set(re.findall(r'provider\s+"(\w+)"', txt)) | {r.split("_")[0] for r in re.findall(r'resource\s+"(\w+)"', txt)}
        infra["Terraform"].append(f"{s}: {sorted(provs)}")
    elif n == "Chart.yaml":
        infra["Helm"].append(s)
    elif n.endswith((".yaml", ".yml")) and re.search(r"^kind:\s*(Deployment|Service|Ingress|StatefulSet|CronJob|ConfigMap)", read(p, 20000), re.M):
        infra["Kubernetes manifests"].append(s)
    elif n in ("Procfile", "vercel.json", "netlify.toml", "fly.toml", "render.yaml", "railway.json",
               "app.yaml", "serverless.yml", "serverless.yaml", "wrangler.toml", "amplify.yml", "nixpacks.toml"):
        infra["Deploy target"].append(s)
    elif n in ("Makefile", "justfile", "Taskfile.yml", "turbo.json", "nx.json", "pnpm-workspace.yaml", "lerna.json"):
        infra["Build orchestration"].append(s)
    elif re.match(r"\.env(\.[\w-]+)?\.(example|sample|template)$|^\.env\.example$|^example\.env$", n):
        keys = re.findall(r"^\s*([A-Z][A-Z0-9_]+)\s*=", read(p), re.M)
        infra["Env vars (names only)"].append(f"{s}: {keys[:40]}")
R["infrastructure"] = dict(infra)

# ------------------------------------------------------------------ entry points, data, tests, docs
entry, data, tests, docs = [], [], Counter(), []
for f in files:
    p, n, s = root / f, f.name, str(f)
    low = s.lower()
    if p.suffix in (".js", ".mjs", ".ts") and p.stat().st_size < 100_000 and not re.search(r"\.(test|spec|config|d)\.", n):
        txt = read(p, 100000)
        if re.search(r"\bexpress\(\)|\.listen\(\s*\w|NestFactory\.create|new Hono\(|Fastify\(|createServer\(|new ApolloServer\(", txt):
            entry.append(s + "  (starts a server)")
    if p.suffix == ".py" and p.stat().st_size < 400_000 and re.search(r"=\s*(FastAPI|Flask|Starlette|Sanic|Quart)\(", read(p, 60000)):
        entry.append(s + "  (creates the web app)")
    if p.suffix in (".py", ".go", ".rs", ".java", ".kt", ".c", ".cpp", ".cs") and p.stat().st_size < 400_000:
        txt = read(p, 60000)
        if (p.suffix == ".py" and ('if __name__ == "__main__"' in txt or "if __name__ == '__main__'" in txt)) \
                or n in ("manage.py", "wsgi.py", "asgi.py") \
                or (p.suffix == ".go" and re.search(r"^package main\b", txt, re.M) and "func main()" in txt) \
                or (p.suffix == ".rs" and "fn main()" in txt) \
                or (p.suffix in (".java", ".kt") and re.search(r"static void main\(|fun main\(", txt)) \
                or (p.suffix in (".c", ".cpp") and re.search(r"\bint\s+main\s*\(", txt)) \
                or (p.suffix == ".cs" and "static void Main(" in txt):
            entry.append(s)
    if n in ("index.html",) and len(f.parts) <= 3:
        entry.append(s)
    if n == "schema.prisma" or "migration" in low or "/alembic/" in low or n in ("crud.py", "repository.py") or n.endswith(".sql") or re.search(r"(^|/)models?(/|\.py$)", low) \
            or n in ("schema.graphql", "schema.rb", "models.py", "entities") or n.endswith(".proto"):
        data.append(s)
    if re.search(r"(^|/)(tests?|__tests__|spec|e2e|cypress)(/|$)", low) or re.search(r"(_test\.go|\.test\.[jt]sx?|\.spec\.[jt]sx?|^test_.*\.py|_test\.py|Test\.java|_spec\.rb)$", n):
        tests[f.parts[0] if len(f.parts) > 1 else "."] += 1
    if (re.match(r"(readme|architecture|design|contributing|changelog|security|adr|deployment|development)", n.lower())
            and (p.suffix.lower() in (".md", ".rst", ".txt", ".adoc", "") )) or (low.startswith(("docs/", "doc/", "adr/")) and p.suffix in (".md", ".mdx", ".rst")):
        docs.append(s)
for m in manifests:
    if m.get("kind") == "npm":
        sc = m.get("scripts") or {}
        for k in ("start", "dev", "serve", "build"):
            if k in sc:
                entry.append(f"{m['path']} scripts.{k}: {sc[k]}")
        if m.get("main"):
            entry.append(f"{m['path']} main: {m['main']}")
        if m.get("bin"):
            entry.append(f"{m['path']} bin: {m['bin']}")
R["entry_points"] = entry[:60]
R["data_layer_hints"] = data[:60]
R["tests_by_top_dir"] = dict(tests)
R["docs"] = docs[:40]

lic = next((root / f for f in files if len(f.parts) == 1 and f.name.upper().startswith(("LICENSE", "LICENCE", "COPYING"))), None)
if lic:
    head = read(lic, 3000)
    guess = next((name for pat, name in [(r"MIT License|Permission is hereby granted, free of charge", "MIT"),
                                          (r"Apache License", "Apache-2.0"), (r"GNU AFFERO", "AGPL"),
                                          (r"GNU LESSER", "LGPL"), (r"GNU GENERAL PUBLIC LICENSE", "GPL"),
                                          (r"Mozilla Public License", "MPL-2.0"), (r"BSD", "BSD"),
                                          (r"Business Source License", "BUSL (source-available)"),
                                          (r"Elastic License", "Elastic (source-available)"),
                                          (r"unlicense", "Unlicense")] if re.search(pat, head, re.I)), "unknown — read it")
    R["license"] = {"file": lic.name, "guess": guess}
else:
    R["license"] = {"file": None, "guess": "NO LICENCE FILE — all rights reserved by default"}

# ------------------------------------------------------------------ git archaeology
if (root / ".git").exists():
    g = lambda *a: run(["git", "-C", str(root), *a])
    log = g("log", "--reverse", "--format=%h|%ad|%an|%s", "--date=short").splitlines()
    git = {"commits": len(log)}
    if log:
        git["first_commit"] = log[0].split("|")[1]
        git["last_commit"] = log[-1].split("|")[1]
        git["authors"] = len({l.split("|")[2] for l in log})
        git["first_commits"] = log[:15]
        months = Counter(l.split("|")[1][:7] for l in log)
        git["commits_per_month"] = dict(sorted(months.items()))
    tags = g("for-each-ref", "--sort=creatordate", "--format=%(refname:short)|%(creatordate:short)", "refs/tags").splitlines()
    git["tags"] = tags[:10] + (["…"] if len(tags) > 20 else []) + tags[-10:] if len(tags) > 20 else tags
    # When did each top-level area first appear? (build order the author actually followed)
    added = g("log", "--reverse", "--diff-filter=A", "--name-only", "--format=@@%ad", "--date=short")
    first_seen, date = {}, None
    for line in added.splitlines():
        if line.startswith("@@"):
            date = line[2:]
        elif line.strip():
            parts = line.split("/")
            area = parts[0] if len(parts) == 1 else "/".join(parts[:2]) if parts[0] in ("src", "packages", "apps", "lib", "cmd", "internal", "crates", "services") and len(parts) > 2 else parts[0]
            first_seen.setdefault(area, date)
    git["areas_first_seen"] = [(a, d, (root / a).exists()) for a, d in sorted(first_seen.items(), key=lambda kv: kv[1])[:60]]
    noise = re.compile(r"(\.lock$|lock\.json$|lock\.yaml$|\.sum$|(^|/)(CHANGELOG|HISTORY|release-notes|RELEASE)[^/]*$|\.md$|\.mdx$|\.snap$|\.svg$|\.png$|^\.github/)", re.I)
    churn = Counter(l for l in g("log", "--format=", "--name-only", "-n", "3000").splitlines()
                    if l.strip() and not noise.search(l))
    git["most_changed_files"] = churn.most_common(20)
    R["git"] = git

# ------------------------------------------------------------------ GitHub releases (shipped artifacts -> REA territory)
m = re.match(r"https?://github\.com/([^/]+)/([^/.]+)", target)
if m:
    rel = run(["gh", "api", f"repos/{m.group(1)}/{m.group(2)}/releases?per_page=5",
               "--jq", '.[] | "\\(.tag_name)|\\(.published_at[:10])|\\([.assets[].name] | join(", "))"'], timeout=30)
    R["releases"] = rel.splitlines() if rel else "unavailable (no gh auth / no releases)"

# ------------------------------------------------------------------ output
(root.parent / f"recon-{root.name}.json").write_text(json.dumps(R, indent=1, default=str))
if want_json:
    print(json.dumps(R, indent=1, default=str))
    sys.exit(0)

o = [f"# Recon: {re.sub(r'^recon-', '', root.name)}\n", f"{R['file_count']} files scanned (vendor/build dirs skipped).\n"]
o.append("## Languages (by lines)")
code = [l for l in R["languages"] if l["language"] not in DATA_LANGS]
other = [l for l in R["languages"] if l["language"] in DATA_LANGS]
o += [f"- {l['language']}: {l['lines']:,} lines in {l['files']} files" for l in code[:12]]
if other:
    o.append("- (config/docs: " + ", ".join(f"{l['language']} {l['lines']:,}" for l in other[:6]) + ")")
o.append("\n## Detected stack (from manifests)")
o += [f"- **{cat}**: {', '.join(v)}" for cat, v in R["detected_stack"].items()] or ["- nothing recognised — read the manifests"]
o.append("\n## Manifests")
for mf in manifests:
    if mf["kind"] == "unparsed":
        o.append(f"- `{mf['path']}`: could not parse ({mf['error']})")
        continue
    nd, ndev = len(mf["dependencies"] or {}), len(mf["dev_dependencies"] or {})
    line = f"- `{mf['path']}` ({mf['kind']}{', ' + str(mf.get('name')) if mf.get('name') else ''}): {nd} deps, {ndev} dev"
    if mf.get("scripts"):
        line += f"; scripts: {', '.join(list(mf['scripts'])[:10])}"
    o.append(line)
o.append("\n## Infrastructure, CI, deploy")
o += [f"- **{k}**: " + "; ".join(v[:6]) + (f" (+{len(v)-6} more)" if len(v) > 6 else "") for k, v in R["infrastructure"].items()] or ["- none found"]
o.append("\n## Entry points")
o += [f"- {e}" for e in R["entry_points"][:25]] or ["- none detected"]
o.append("\n## Data layer hints")
o += [f"- {d}" for d in R["data_layer_hints"][:20]] or ["- none detected"]
o.append("\n## Tests (files by top-level dir)")
o.append("- " + (", ".join(f"{k}: {v}" for k, v in R["tests_by_top_dir"].items()) or "no tests detected"))
o.append(f"\n## Licence\n- {R['license']['file']}: {R['license']['guess']}")
o.append("\n## Docs worth reading first")
o += [f"- {d}" for d in R["docs"][:15]] or ["- none"]
o.append("\n## Top of the tree (files per dir)")
o += [f"- {k}: {v}" for k, v in list(R["tree"].items())[:40]]
if "git" in R:
    G = R["git"]
    o.append(f"\n## Git archaeology\n- {G['commits']} commits by {G.get('authors', '?')} authors, {G.get('first_commit')} → {G.get('last_commit')}")
    o.append("- **How it started (first commits):**")
    o += [f"  - {c}" for c in G.get("first_commits", [])]
    o.append("- **When each area first appeared (the author's build order):**")
    o += [f"  - {d}  {a}" + ("" if alive else "  (since removed: a rewrite or refactor happened)") for a, d, alive in G.get("areas_first_seen", [])[:30]]
    o.append("- **Most-changed files (where the complexity lives):**")
    o += [f"  - {n}× {f}" for f, n in G.get("most_changed_files", [])[:12]]
    if G.get("tags"):
        o.append("- Tags: " + ", ".join(G["tags"]))
if "releases" in R:
    o.append("\n## Releases (shipped artifacts → REA candidates)")
    o += [f"- {r}" for r in R["releases"]] if isinstance(R["releases"], list) else [f"- {R['releases']}"]
print("\n".join(o))
