#!/usr/bin/env python3
"""Read-only first-pass reconnaissance of a SHIPPED app (no source needed).

Usage:
  python3 artifact_recon.py <file-or-directory> [--json]

Accepts: an APK/AAB/IPA/JAR/ZIP/MSIX, an Electron app.asar, a tar/tgz release archive,
an ELF/PE/Mach-O binary, a .wasm file, or an installed app directory (e.g. Foo.app,
"C:/Program Files/Foo", an extracted AppImage).

It NEVER runs the target, decompiles code, bypasses protections or contacts the network.
It only reads bytes and file names to answer: what platform and framework is this,
what libraries does it bundle, what backend services does it talk to, and where are
the licence notices. Deeper questions (pseudocode, classes, runtime behaviour) are
REA's job — see references/rea.md.
"""
import io
import json
import re
import struct
import sys
import tarfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from known_packages import KNOWN  # shared with repo_recon.py
except ImportError:
    KNOWN = {}

MAX_SCAN = 256 * 1024 * 1024        # bytes of any single binary scanned for strings
findings = defaultdict(list)        # category -> [(label, evidence)]
extra_ev = Counter()                # (category, label) -> further pieces of evidence not shown
lib_hits = Counter()                # bytecode library -> class refs across all DEX files
lib_where = defaultdict(set)
top_pkgs = Counter()
dart_pkgs = Counter()
dep_notices = 0
deps = {}                           # name -> version (from real metadata only)
dep_eco = {}                        # name -> ecosystem


def add_dep(name, version, eco, overwrite=True):
    if overwrite or name not in deps:
        deps[name] = version
        dep_eco[name] = eco
domains = Counter()
notices = []


def add(cat, label, evidence):
    if any(l == label for l, _ in findings[cat]):
        extra_ev[(cat, label)] += 1
        return
    findings[cat].append((label, evidence))


# ---------------------------------------------------------------- fingerprints by file path
PATH_RULES = [
    (r"(^|/)resources/app\.asar$|(^|/)app\.asar$", "Electron", "Framework", "app.asar present"),
    (r"Electron Framework\.framework", "Electron", "Framework", "Electron Framework.framework"),
    (r"(^|/)libflutter\.so$|Flutter\.framework|(^|/)flutter_assets/", "Flutter", "Framework", "Flutter engine/assets"),
    (r"(^|/)libapp\.so$", "Flutter (AOT Dart snapshot)", "Framework", "libapp.so"),
    (r"index\.android\.bundle$|main\.jsbundle$|libreactnativejni\.so$|libreactnative\.so$", "React Native", "Framework", "RN bundle/JNI lib"),
    (r"libhermes\.so$|hermes\.framework", "Hermes JS engine", "Runtime", "Hermes binary"),
    (r"libunity\.so$|UnityFramework\.framework|(^|/)globalgamemanagers$|UnityPlayer\.dll", "Unity", "Game engine", "Unity runtime"),
    (r"libil2cpp\.so$|global-metadata\.dat$|GameAssembly\.dll", "Unity IL2CPP", "Game engine", "IL2CPP artifacts"),
    (r"libgodot|\.pck$", "Godot", "Game engine", "Godot runtime/pack"),
    (r"libUE4\.so$|libUnreal\.so$", "Unreal Engine", "Game engine", "Unreal runtime"),
    (r"libmonodroid\.so$|libmonosgen|(^|/)assemblies/.*\.dll$|libxamarin", "Xamarin / .NET MAUI", "Framework", "Mono/.NET assemblies"),
    (r"(^|/)(assets|public)/www/|cordova\.js$|cordova_plugins\.js$", "Cordova / Ionic", "Framework", "www bundle"),
    (r"capacitor\.config\.json$|capacitor\.plugins\.json$", "Capacitor", "Framework", "capacitor config"),
    (r"libQt[56]?Core|Qt[56]?Core\.dll|QtCore\.framework", "Qt", "Framework", "Qt core library"),
    (r"(^|/)classes\d*\.dex$", "Android (DEX bytecode)", "Platform", "classes.dex"),
    (r"(^|/)kotlin/|\.kotlin_module$|kotlin-tooling-metadata\.json$", "Kotlin", "Language", "Kotlin metadata"),
    (r"(^|/)Payload/[^/]+\.app/", "iOS app", "Platform", "Payload/*.app"),
    (r"AppxManifest\.xml$", "Windows MSIX/AppX", "Platform", "AppxManifest.xml"),
    (r"META-INF/MANIFEST\.MF$", "Java archive", "Platform", "MANIFEST.MF"),
    (r"(^|/)lib/[^/]+/lib[\w+-]+\.so$", "Native libraries (JNI)", "Native code", "lib/<abi>/*.so"),
    (r"libsqlcipher|libsqlite", "SQLite", "Storage", "bundled SQLite"),
    (r"libtensorflowlite|libtflite|\.tflite$", "TensorFlow Lite", "ML", "TFLite runtime/model"),
    (r"libonnxruntime|\.onnx$", "ONNX Runtime", "ML", "ONNX runtime/model"),
    (r"\.gguf$|\.safetensors$", "Bundled ML model", "ML", "model weights"),
    (r"(^|/)firebase|google-services|GoogleService-Info\.plist", "Firebase", "Backend service", "Firebase config"),
    (r"libsentry|io/sentry|Sentry\.framework", "Sentry", "Observability", "Sentry SDK"),
    (r"\.wasm$", "WebAssembly module", "Runtime", ".wasm file"),
    (r"(^|/)node_modules/", "Node.js packages bundled", "Runtime", "node_modules/"),
    (r"(^|/)_internal/|base_library\.zip$|\.pyz$", "PyInstaller (Python)", "Framework", "PyInstaller layout"),
]
NOTICE_RE = re.compile(r"(^|/)(LICEN[CS]E|NOTICE|COPYING|THIRD[_-]?PARTY|OSS|open_source|third_party_licen[cs]es|LICENSES\.chromium|ThirdPartyNotices|acknowledg)", re.I)

# DEX/JVM package prefixes -> library
JVM_LIBS = {
    "com/squareup/okhttp3": "OkHttp", "okhttp3": "OkHttp", "retrofit2": "Retrofit", "com/squareup/moshi": "Moshi",
    "com/google/gson": "Gson", "kotlinx/coroutines": "Kotlin Coroutines", "kotlinx/serialization": "kotlinx.serialization",
    "io/reactivex": "RxJava", "androidx/compose": "Jetpack Compose", "androidx/room": "Room (SQLite ORM)",
    "androidx/work": "WorkManager", "androidx/navigation": "Jetpack Navigation", "androidx/media3": "Media3 / ExoPlayer",
    "com/google/android/exoplayer2": "ExoPlayer", "dagger/hilt": "Hilt (DI)", "dagger": "Dagger (DI)", "org/koin": "Koin (DI)",
    "com/bumptech/glide": "Glide (images)", "coil": "Coil (images)", "com/squareup/picasso": "Picasso (images)",
    "io/ktor": "Ktor", "org/jsoup": "jsoup (HTML parsing)", "com/google/firebase": "Firebase",
    "com/google/android/gms": "Google Play services", "io/sentry": "Sentry", "com/facebook/react": "React Native",
    "io/flutter": "Flutter embedding", "org/mozilla/javascript": "Rhino JS engine", "org/schabi/newpipe/extractor": "NewPipe Extractor",
    "io/realm": "Realm DB", "net/zetetic": "SQLCipher", "org/greenrobot": "greenDAO/EventBus", "com/airbnb/lottie": "Lottie",
    "com/jakewharton/timber": "Timber (logging)", "org/acra": "ACRA (crash reports)", "com/google/zxing": "ZXing (barcodes)",
    "org/bouncycastle": "Bouncy Castle (crypto)", "com/stripe": "Stripe", "io/grpc": "gRPC", "com/google/protobuf": "Protocol Buffers",
    "org/jetbrains/compose": "Compose Multiplatform", "app/cash/sqldelight": "SQLDelight",
}
NATIVE_HINTS = [
    (rb"Go build ID: |\x00go1\.\d+|runtime\.gopanic", "Go", "Language"),
    (rb"/rustc/[0-9a-f]{40}|cargo/registry/src/", "Rust", "Language"),
    (rb"_MEIPASS|PyInstaller|PYZ-00\.pyz", "PyInstaller (Python)", "Framework"),
    (rb"__TAURI__|tauri::|tauri-runtime", "Tauri", "Framework"),
    (rb"Electron/\d+\.\d+|electron\.asar", "Electron", "Framework"),
    (rb"BSJB.{12}v\d\.\d", ".NET (CLR metadata)", "Runtime"),
    (rb"Qt_[56]\.\d+|QApplication", "Qt", "Framework"),
    (rb"GLIBC_2\.\d+", "glibc (dynamically linked, Linux)", "Platform"),
    (rb"sqlite3_open|SQLite format 3", "SQLite", "Storage"),
    (rb"libcurl|curl_easy_perform", "libcurl", "Networking"),
    (rb"OpenSSL \d|BoringSSL|rustls", "TLS library", "Networking"),
    (rb"google\.golang\.org/grpc|grpc-java|libgrpc|grpc\.health\.v1", "gRPC", "Networking"),
    (rb"google\.protobuf\.[A-Z]|libprotobuf|google\.golang\.org/protobuf", "Protocol Buffers", "Serialization"),
    (rb"v8::|V8 version", "V8 engine", "Runtime"),
    (rb"bun:main|Bun v\d", "Bun (compiled JS)", "Runtime"),
    (rb"pkg/prelude/bootstrap\.js|PKG_EXECPATH", "pkg (compiled Node.js)", "Runtime"),
    (rb"NODE_SEA_BLOB|node:sea", "Node single-executable app", "Runtime"),
]
DOMAIN_RE = re.compile(rb"https?://([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+)(?::\d+)?(?=[/\"'\s\x00)<>,;?#]|$)", re.I)
BORING_DOMAINS = re.compile(r"(^|\.)(w3\.org|schemas\.android\.com|apache\.org|xml\.org|xmlpull\.org|ns\.adobe\.com|"
                            r"purl\.org|openxmlformats\.org|microsoft\.com/winfx|example\.(com|org)|localhost|"
                            r"json-schema\.org|www\.inkscape\.org|creativecommons\.org|gnu\.org|opensource\.org|"
                            r"mozilla\.org/MPL|unicode\.org|ietf\.org|tools\.ietf\.org)$", re.I)


def scan_path(name, size=None):
    for pat, label, cat, ev in PATH_RULES:
        if re.search(pat, name, re.I):
            add(cat, label, f"{ev}: {name}")
            break
    global dep_notices
    if NOTICE_RE.search(name):
        if "node_modules/" in name or "/vendor/" in name:
            dep_notices += 1
        elif len(notices) < 60:
            notices.append(name)


def scan_bytes(data, origin):
    data = data[:MAX_SCAN]
    for pat, label, cat in NATIVE_HINTS:
        if re.search(pat, data):
            add(cat, label, f"byte pattern in {origin}")
    # Dart packages compiled into a Flutter AOT snapshot (libapp.so / App.framework/App)
    if re.search(r"libapp\.so$|App\.framework/App$|\.so$", origin) and b"package:flutter/" in data:
        for m in re.finditer(rb"package:([a-z0-9_]+)/", data):
            dart_pkgs[m.group(1).decode()] += 1
    # Go module build info: "dep\t<path>\t<version>"
    for m in re.finditer(rb"(?:^|\n)dep\t([^\t\n]+)\t(v[^\t\n]+)", data):
        add_dep(m.group(1).decode(errors="replace"), m.group(2).decode(errors="replace"), "Go modules")
    mod = re.search(rb"path\t([^\n]+)\nmod\t([^\t\n]+)\t([^\t\n]+)", data)
    if mod:
        add("Identity", f"Go module {mod.group(2).decode(errors='replace')} {mod.group(3).decode(errors='replace')}",
            f"embedded build info in {origin}")
    gov = re.search(rb"\x00(go1\.\d+(?:\.\d+)?)\x00", data) or re.search(rb"(go1\.\d+\.\d+)", data)
    if gov and any(l == "Go" for l, _ in findings.get("Language", [])):
        add("Toolchain", f"Go {gov.group(1).decode()}", f"version string in {origin}")
    # Rust crates from embedded registry paths
    for m in re.finditer(rb"cargo/registry/src/[^/]+/([A-Za-z0-9_\-]+?)-(\d+\.\d+\.\d+(?:-[\w.]+)?)/", data):
        add_dep(m.group(1).decode(), m.group(2).decode(), "Rust crates", overwrite=False)
    for m in DOMAIN_RE.finditer(data):
        d = m.group(1).decode(errors="ignore").lower()
        tld = d.rsplit(".", 1)[-1]
        if not BORING_DOMAINS.search(d) and tld.isalpha() and 2 <= len(tld) <= 8 and not d.replace(".", "").isdigit():
            domains[d] += 1


def scan_dex(data, origin):
    prefixes = Counter()
    for m in re.finditer(rb"L((?:[a-z][a-z0-9_]*/){1,4})[A-Za-z0-9_$]+;", data[:MAX_SCAN]):
        prefixes[m.group(1).decode().rstrip("/")] += 1
    claimed = set()
    for pre, lib in sorted(JVM_LIBS.items(), key=lambda kv: -len(kv[0])):
        matched = [p for p in prefixes if (p == pre or p.startswith(pre + "/")) and p not in claimed]
        hits = sum(prefixes[p] for p in matched)
        if hits:
            claimed.update(matched)
            lib_hits[lib] += hits
            lib_where[lib].add(pre + "/")
    for p, c in prefixes.items():
        parts = p.split("/")
        if parts[0] in ("java", "javax", "android", "kotlin", "dalvik", "sun", "jdk"):
            continue
        if len(parts[0]) <= 2 and len(parts) == 1:
            top_pkgs["(obfuscated short names)"] += c
            continue
        top_pkgs["/".join(parts[:3])] += c
    scan_bytes(data, origin)


def parse_asar(blob, origin):
    """Electron ASAR: pickle header (uint32 4, uint32 header_size, uint32 size, uint32 json_len) + JSON."""
    try:
        header_size = struct.unpack_from("<I", blob, 4)[0]
        json_len = struct.unpack_from("<I", blob, 12)[0]
        header = json.loads(blob[16:16 + json_len])
    except (struct.error, ValueError):
        return False
    base = 8 + header_size
    add("Framework", "Electron", f"valid ASAR archive: {origin}")
    files = []

    def walk(node, path):
        for name, child in node.get("files", {}).items():
            p = f"{path}/{name}" if path else name
            if "files" in child:
                walk(child, p)
            else:
                files.append((p, child))
    walk(header, "")
    add("Size", f"{len(files)} files inside ASAR", origin)

    def read_file(entry):
        if entry.get("unpacked"):
            return None
        off, size = int(entry.get("offset", 0)), int(entry.get("size", 0))
        return blob[base + off: base + off + size]

    for p, entry in files:
        scan_path(p)
        if p == "package.json":
            raw = read_file(entry)
            try:
                pj = json.loads(raw) if raw else {}
            except ValueError:
                pj = {}
            add("Identity", f"{pj.get('productName') or pj.get('name')} {pj.get('version', '')}".strip(), "ASAR package.json")
            if pj.get("main"):
                add("Entry points", f"main process: {pj['main']}", "ASAR package.json")
            for k, v in {**pj.get("dependencies", {}), **pj.get("optionalDependencies", {})}.items():
                add_dep(k, v, "npm", overwrite=False)
        m = re.match(r"node_modules/((?:@[^/]+/)?[^/]+)/package\.json$", p)
        if m:
            raw = read_file(entry)
            try:
                add_dep(m.group(1), json.loads(raw).get("version", "?"), "npm")
            except (ValueError, TypeError):
                pass
        elif p.endswith((".js", ".mjs", ".cjs", ".html")) and not p.startswith("node_modules/") and entry.get("size", 0) < 8_000_000:
            raw = read_file(entry)
            if raw:
                scan_bytes(raw, f"asar:{p}")
    return True


def scan_zip(zf, origin):
    names = zf.namelist()
    add("Size", f"{len(names)} entries", origin)
    for n in names:
        scan_path(n)
    for n in names:
        info = zf.getinfo(n)
        low = n.lower()
        if re.search(r"(^|/)classes\d*\.dex$", n):
            scan_dex(zf.read(n), n)
        elif low.endswith(".asar"):
            parse_asar(zf.read(n), n)
        elif re.search(r"META-INF/maven/.+/pom\.properties$", n):
            props = dict(re.findall(r"^(\w+)=(.*)$", zf.read(n).decode(errors="replace"), re.M))
            if props.get("artifactId"):
                add_dep(f"{props.get('groupId', '?')}:{props['artifactId']}", props.get("version", "?"), "Maven")
        elif n == "META-INF/MANIFEST.MF":
            mf = zf.read(n).decode(errors="replace")
            mc = re.search(r"^Main-Class:\s*(\S+)", mf, re.M)
            if mc:
                add("Entry points", f"Main-Class {mc.group(1)}", n)
        elif re.search(r"\.(so|dylib|dll|exe)$|/[^/.]+$", n) and info.file_size < MAX_SCAN and info.file_size > 50_000 \
                and not n.endswith("/") and ("lib/" in n or n.endswith((".dll", ".exe", ".dylib")) or ".app/" in n):
            scan_bytes(zf.read(n), n)
        elif low.endswith((".js", ".json", ".html", ".bundle", ".jsbundle", ".xml", ".properties")) and info.file_size < 20_000_000:
            scan_bytes(zf.read(n), n)
        elif n.endswith("META-INF/version-control-info.textproto") or n.endswith("app-metadata.properties"):
            add("Build metadata", zf.read(n).decode(errors="replace").strip().replace("\n", "; ")[:200], n)
        elif re.search(r"META-INF/[^/]+\.version$", n):
            v = zf.read(n).decode(errors="replace").strip()
            lib = n.split("/")[-1][:-len(".version")]
            if re.match(r"^[\w.\-]+$", v):
                add_dep(lib, v, "Android/Maven (META-INF)", overwrite=False)


def scan_dir(root):
    files = [p for p in root.rglob("*") if p.is_file()]
    add("Size", f"{len(files)} files", str(root))
    for p in files:
        rel = str(p.relative_to(root))
        scan_path(rel)
        if p.suffix == ".asar":
            parse_asar(p.read_bytes(), rel)
        elif p.suffix in (".apk", ".jar", ".zip", ".ipa", ".aab") and zipfile.is_zipfile(p):
            with zipfile.ZipFile(p) as zf:
                scan_zip(zf, rel)
        elif p.stat().st_size > 50_000 and (p.suffix in (".so", ".dll", ".exe", ".dylib", "") or p.stat().st_mode & 0o111):
            with p.open("rb") as fh:
                head = fh.read(4)
                if head[:4] in (b"\x7fELF", b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xca\xfe\xba\xbe") or head[:2] == b"MZ":
                    fh.seek(0)
                    scan_bytes(fh.read(MAX_SCAN), rel)


def kind_of(data, name):
    if data[:4] == b"PK\x03\x04":
        return "zip"
    if data[:4] == b"\x7fELF":
        return "ELF (AppImage)" if data[8:11] == b"AI\x02" else "ELF"
    if data[:2] == b"MZ":
        return "PE (Windows)"
    if data[:4] in (b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe"):
        return "Mach-O"
    if data[:4] == b"\xca\xfe\xba\xbe" and not name.endswith(".class"):
        return "Mach-O universal"
    if data[:4] == b"\x00asm":
        return "WebAssembly"
    if data[:2] == b"\x1f\x8b" or data[257:262] == b"ustar" or data[:3] == b"BZh" or data[:6] == b"\xfd7zXZ\x00":
        return "tar"
    if data[:4] == b"\x04\x00\x00\x00" and name.endswith(".asar"):
        return "asar"
    return "unknown"


# ---------------------------------------------------------------- main
if len(sys.argv) < 2:
    print(__doc__)
    sys.exit(2)
target = Path(sys.argv[1]).expanduser().resolve()
if not target.exists():
    print(f"Not found: {target}")
    sys.exit(1)

if target.is_dir():
    kind = "directory (installed or extracted app)"
    scan_dir(target)
else:
    with target.open("rb") as fh:
        head = fh.read(512)
    kind = kind_of(head, target.name)
    if kind == "zip":
        with zipfile.ZipFile(target) as zf:
            names = zf.namelist()
            kind = ("Android APK" if "AndroidManifest.xml" in names and any(n.endswith(".dex") for n in names)
                    else "Android App Bundle" if any(n.startswith("base/manifest/") for n in names)
                    else "iOS IPA" if any(n.startswith("Payload/") for n in names)
                    else "Java JAR" if "META-INF/MANIFEST.MF" in names and any(n.endswith(".class") for n in names)
                    else "Windows MSIX/AppX" if "AppxManifest.xml" in names else "ZIP archive")
            scan_zip(zf, target.name)
    elif kind == "asar":
        parse_asar(target.read_bytes(), target.name)
    elif kind == "tar":
        with tarfile.open(target) as tf:
            members = [m for m in tf.getmembers() if m.isfile()]
            add("Size", f"{len(members)} files in archive", target.name)
            for m in members:
                scan_path(m.name)
                if m.size > 50_000 or m.name.endswith(".asar"):
                    data = tf.extractfile(m).read(MAX_SCAN)
                    k = kind_of(data[:512], m.name)
                    if k == "asar":
                        parse_asar(data, m.name)
                    elif k == "zip":
                        scan_zip(zipfile.ZipFile(io.BytesIO(data)), m.name)
                    elif k != "unknown":
                        add("Binaries", f"{m.name} ({k})", target.name)
                        scan_bytes(data, m.name)
    else:
        with target.open("rb") as fh:
            scan_bytes(fh.read(MAX_SCAN), target.name)

for lib, hits in lib_hits.items():
    if hits >= 3:
        findings["Libraries (from bytecode package names)"].append(
            (lib, f"{hits} class refs under {', '.join(sorted(lib_where[lib]))}"))
findings["Libraries (from bytecode package names)"].sort(key=lambda le: -lib_hits[le[0]])
if not findings["Libraries (from bytecode package names)"]:
    del findings["Libraries (from bytecode package names)"]
if top_pkgs:
    obf = top_pkgs.pop("(obfuscated short names)", 0)
    if obf > 0.2 * (sum(top_pkgs.values()) + obf):
        add("Build metadata", "Code is minified/obfuscated (R8/ProGuard-style short names)",
            f"{obf} class refs in 1-2 letter packages")
    findings["_top_packages"] = top_pkgs.most_common(25)
if dart_pkgs:
    add("Language", "Dart", f"{len(dart_pkgs)} Dart packages named in the AOT snapshot")
    for name, c in dart_pkgs.most_common():
        if name not in ("flutter", "dart"):
            add_dep(name, f"{c} refs", "Dart packages (ref counts)", overwrite=False)

# dependency labels via repo_recon's table, when available
labelled = defaultdict(set)
for d in deps:
    key = re.sub(r"/v\d+$", "", d)
    hit = KNOWN.get(key) or next((v for k, v in KNOWN.items() if key.startswith(k + "/")), None)
    if hit:
        labelled[hit[1]].add(hit[0])

report = {"target": str(target), "kind": kind,
          "findings": {k: v for k, v in findings.items() if not k.startswith("_")},
          "top_packages": findings.get("_top_packages", []),
          "dependencies": deps, "dependency_ecosystems": dep_eco, "recognised_dependencies": {k: sorted(v) for k, v in labelled.items()},
          "domains": domains.most_common(40), "notice_files": notices, "dependency_notice_files": dep_notices}
out_json = target.parent / f"artifact-recon-{target.stem}.json"
try:
    out_json.write_text(json.dumps(report, indent=1, default=list))
except OSError:
    pass
if "--json" in sys.argv:
    print(json.dumps(report, indent=1, default=list))
    sys.exit(0)

o = [f"# Artifact recon: {target.name}", f"Kind: **{kind}**  (static read only; nothing was executed)\n"]
order = ["Platform", "Framework", "Language", "Runtime", "Game engine", "Toolchain", "Identity", "Entry points",
         "Native code", "Storage", "Networking", "Serialization", "ML", "Backend service", "Observability",
         "Libraries (from bytecode package names)", "Binaries", "Build metadata", "Size"]
for cat in order + [c for c in findings if c not in order and not c.startswith("_")]:
    if findings.get(cat):
        o.append(f"## {cat}")
        for label, ev in findings[cat][:25]:
            more = extra_ev.get((cat, label), 0)
            o.append(f"- **{label}** — {ev}" + (f"  (+{more} more)" if more else ""))
        o.append("")
if labelled:
    o.append("## Recognised dependencies (from embedded metadata)")
    o += [f"- **{cat}**: {', '.join(sorted(v))}" for cat, v in sorted(labelled.items())]
    o.append("")
if deps:
    o.append(f"## Dependencies from embedded metadata ({len(deps)})")
    by_eco = defaultdict(list)
    for k, v in deps.items():
        by_eco[dep_eco.get(k, "other")].append((k, v))
    for eco, items in sorted(by_eco.items()):
        if eco.startswith("Dart"):
            items.sort(key=lambda kv: -int(str(kv[1]).split()[0]))
            shown = ", ".join(k for k, _ in items[:60])
        else:
            items.sort()
            shown = ", ".join(f"{k}@{v}" for k, v in items[:60])
        o.append(f"- **{eco}** ({len(items)}): {shown}" + (" …" if len(items) > 60 else ""))
    o.append("")
if findings.get("_top_packages"):
    o.append("## Most-referenced code packages (app code + libraries)")
    o += [f"- {p}  ({c})" for p, c in findings["_top_packages"][:15]]
    o.append("")
if domains:
    o.append("## Domains referenced (candidate backends/services — verify, they may be docs or dead code)")
    o += [f"- {d} ({c})" for d, c in domains.most_common(25)]
    o.append("")
o.append("## Licence / third-party notice files (read these: they list bundled open-source components)")
o += [f"- {n}" for n in notices[:25]] or ["- none found at app level"]
if dep_notices:
    o.append(f"- plus {dep_notices} licence files inside bundled dependencies (node_modules/vendor)")
o.append("\nNext: deeper evidence (classes, pseudocode, IPC, runtime traffic) with REA — see references/rea.md.")
print("\n".join(o))
