"""Release tool: one script for the local preview and for CI (.github/workflows/release.yml).

    python tools/release/release.py preview pcb/module-board/v0.1     # check + render notes, no tag needed
    python tools/release/release.py check   <tag> [--github-output]  # gates only
    python tools/release/release.py build   <tag>                    # firmware: run PlatformIO, collect binaries
    python tools/release/release.py package <tag> [--out dist]       # assets + SHA256SUMS + notes.md
    (--local on build/package skips the tag/main gates, for testing before a tag exists)

Tags are <type>/<component>/v<version> (see .github/RELEASING.md):
    pcb/<board>/vX.Y   hw/<part>/vX.Y   fw/<target>/vX.Y.Z   app/<application>/vX.Y.Z   (+ optional -rc.N)

Each component has <folder>/<component>/release.toml (what to ship) and RELEASE-NOTES.md (this
release's version, status and prose). Standard library only (Python 3.11+).
"""
import argparse, hashlib, json, os, re, shutil, subprocess, sys, tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
FOLDERS = {"pcb": "pcb", "hw": "hardware", "fw": "firmware", "app": "applications"}
BUILT_IN_CI = {"fw", "app"}            # firmware is always built from the tagged source; pcb/hw never
TAG_RE = re.compile(r"^(pcb|hw|fw|app)/([a-z0-9][a-z0-9-]*)/v(\d+)\.(\d+)(?:\.(\d+))?(?:-rc\.(\d+))?$")
RESULT = {"pass": "✅ pass", "fail": "❌ fail", "pending": "⏳ not yet tested", "n/a": "➖ n/a"}
REPO = os.environ.get("GITHUB_REPOSITORY", "DrewFerg11/split-flap")


class Fail(Exception):
    pass


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout.strip()


# ---------------------------------------------------------------- tag + component
def parse_tag(tag):
    m = TAG_RE.match(tag)
    if not m:
        raise Fail(f"tag {tag!r} is not <pcb|hw|fw|app>/<component>/vX.Y[.Z][-rc.N]")
    kind, comp, major, minor, patch, rc = m.groups()
    if kind in ("pcb", "hw") and patch is not None:
        raise Fail(f"{kind} versions are vMAJOR.MINOR (matching the silkscreen/part label), got {tag}")
    if kind in ("fw", "app") and patch is None:
        raise Fail(f"{kind} versions are full semver vMAJOR.MINOR.PATCH, got {tag}")
    version = tag.rsplit("/v", 1)[1]
    return {
        "tag": tag, "type": kind, "component": comp, "version": version,
        "dir": f"{FOLDERS[kind]}/{comp}",
        "prerelease": int(major) == 0 or rc is not None,
    }


def load(t):
    d = os.path.join(ROOT, t["dir"])
    mpath = os.path.join(d, "release.toml")
    if not os.path.exists(mpath):
        raise Fail(f"no manifest: {t['dir']}/release.toml")
    with open(mpath, "rb") as f:
        man = tomllib.load(f)
    if man.get("component") != t["component"]:
        raise Fail(f"release.toml component {man.get('component')!r} != tag component {t['component']!r}")
    npath = os.path.join(d, man.get("notes", "RELEASE-NOTES.md"))
    if not os.path.exists(npath):
        raise Fail(f"no release notes: {os.path.relpath(npath, ROOT)}")
    text = open(npath, encoding="utf-8").read().replace("\r\n", "\n")
    m = re.match(r"\+\+\+\n(.*?)\n\+\+\+\n(.*)", text, re.S)
    if not m:
        raise Fail(f"{os.path.relpath(npath, ROOT)}: needs a +++ TOML front matter +++ block")
    front, body = tomllib.loads(m.group(1)), m.group(2)
    if front.get("version") != t["version"]:
        raise Fail(f"RELEASE-NOTES.md version {front.get('version')!r} != tag version {t['version']!r}")
    sections, cur = {}, None
    for line in body.split("\n"):
        h = re.match(r"## (.+)", line)
        if h:
            cur = h.group(1).strip()
            sections[cur] = []
        elif cur:
            sections[cur].append(line)
    sections = {k: "\n".join(v).strip() for k, v in sections.items()}
    if not sections.get("Summary"):
        raise Fail("RELEASE-NOTES.md needs a non-empty '## Summary' section")
    return d, man, front, sections


# ---------------------------------------------------------------- gates
def is_lfs_pointer(path):
    with open(path, "rb") as f:
        return f.read(64).startswith(b"version https://git-lfs")


def check_report(kind, path):
    txt = open(os.path.join(ROOT, path), encoding="utf-8", errors="replace").read()
    if kind == "kicad-erc":
        m = re.search(r"ERC messages:\s*\d+\s+Errors\s+(\d+)", txt)
        if not m:
            raise Fail(f"{path}: can't read the ERC error count")
        if int(m.group(1)):
            raise Fail(f"{path}: {m.group(1)} ERC errors")
    elif kind == "kicad-drc":
        errs = len(re.findall(r";\s*error\b", txt))
        if errs:
            raise Fail(f"{path}: {errs} DRC errors")
        for what in ("unconnected pads", "Footprint errors"):
            m = re.search(rf"Found (\d+) {what}", txt)
            if not m or int(m.group(1)):
                raise Fail(f"{path}: expected 'Found 0 {what}'")
    else:
        raise Fail(f"unknown check kind {kind!r}")


def files_of(man):
    return [a["path"] for a in man.get("assets", [])] + [i["path"] for i in man.get("images", [])]


def gates(t, d, man, front, local):
    problems = []
    for rel in files_of(man) + [c["path"] for c in man.get("checks", [])]:
        p = os.path.join(d, rel)
        if not os.path.isfile(p):
            problems.append(f"missing: {t['dir']}/{rel}")
        elif os.path.getsize(p) == 0:
            problems.append(f"empty: {t['dir']}/{rel}")
        elif is_lfs_pointer(p):
            problems.append(f"LFS pointer, not the file (checkout without lfs?): {t['dir']}/{rel}")
    for c in man.get("checks", []):
        p = os.path.join(d, c["path"])
        if os.path.isfile(p):
            try:
                check_report(c["kind"], os.path.relpath(p, ROOT).replace(os.sep, "/"))
            except Fail as e:
                problems.append(str(e))
    names = [asset_name(man, t, a) for a in man.get("assets", [])]
    if len(set(names)) != len(names):
        problems.append("two assets map to the same release file name")
    if t["type"] == "app":
        for comp_tag in front.get("tested_with", {}).values():
            if not local and not git("rev-parse", "-q", "--verify", f"refs/tags/{comp_tag}"):
                problems.append(f"tested_with tag does not exist: {comp_tag}")
        if not front.get("tested_with"):
            problems.append("app release needs a [tested_with] table in RELEASE-NOTES.md")
    if t["type"] in BUILT_IN_CI and "build" not in man:
        problems.append(f"{t['type']} releases are built by CI: release.toml needs a [build] table")
    if t["type"] not in BUILT_IN_CI and "build" in man:
        problems.append(f"{t['type']} releases are never built in CI: remove [build] from release.toml")
    if not local:
        if git("rev-parse", "HEAD") != git("rev-list", "-n1", t["tag"]):
            problems.append("checked-out commit is not the tagged commit")
        if subprocess.run(["git", "merge-base", "--is-ancestor", t["tag"], "origin/main"], cwd=ROOT,
                          capture_output=True).returncode:
            problems.append("tagged commit is not on main: merge first, then tag")
    if problems:
        raise Fail("release gates failed:\n  - " + "\n  - ".join(problems))


# ---------------------------------------------------------------- assets
def asset_name(man, t, a):
    return f"{man['asset_prefix']}-v{t['version']}-{a['name']}"


def build(t, d, man):
    b = man["build"]
    if b.get("system") != "platformio":
        raise Fail(f"unsupported build system {b.get('system')!r}")
    proj = os.path.join(d, b.get("project", "."))
    out = os.path.join(ROOT, "dist", "build")
    os.makedirs(out, exist_ok=True)
    for env in b["envs"]:
        r = subprocess.run(["pio", "run", "-d", proj, "-e", env])
        if r.returncode:
            raise Fail(f"pio run -e {env} failed")
        for art in b.get("artifacts", ["firmware.bin", "firmware.elf"]):
            src = os.path.join(proj, ".pio", "build", env, art)
            if not os.path.isfile(src):
                raise Fail(f"build produced no {art} for env {env}")
            stem, ext = os.path.splitext(art)
            shutil.copy2(src, os.path.join(out, f"{man['asset_prefix']}-v{t['version']}-{env}{'' if stem == 'firmware' else '-' + stem}{ext}"))
    print("built:", ", ".join(sorted(os.listdir(out))))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def collect(t, d, man, out):
    """Copy committed assets (+ CI-built binaries) into out/assets under their release names."""
    adir = os.path.join(out, "assets")
    shutil.rmtree(adir, ignore_errors=True)
    os.makedirs(adir)
    rows = []
    for a in man.get("assets", []):
        dst = os.path.join(adir, asset_name(man, t, a))
        shutil.copy2(os.path.join(d, a["path"]), dst)
        rows.append((os.path.basename(dst), a.get("description", "")))
    built = os.path.join(ROOT, "dist", "build")
    if t["type"] in BUILT_IN_CI and os.path.isdir(built):
        for f in sorted(os.listdir(built)):
            shutil.copy2(os.path.join(built, f), os.path.join(adir, f))
            rows.append((f, "firmware, built by CI from this tag" if f.endswith(".bin") else "debug symbols"))
    sums = [(sha256(os.path.join(adir, n)), n) for n, _ in rows]
    with open(os.path.join(adir, "SHA256SUMS"), "w", newline="\n") as f:
        f.writelines(f"{h}  {n}\n" for h, n in sums)
    return [(n, desc, os.path.getsize(os.path.join(adir, n)), h) for (n, desc), (h, _) in zip(rows, sums)]


# ---------------------------------------------------------------- notes
def size(n):
    return f"{n / 1e6:.1f} MB" if n >= 1e6 else f"{n / 1e3:.0f} kB" if n >= 1e3 else f"{n} B"


def raw(sha, d, rel):
    return f"https://raw.githubusercontent.com/{REPO}/{sha}/{os.path.relpath(os.path.join(d, rel), ROOT).replace(os.sep, '/')}"


def blob(sha, d, rel):
    return f"https://github.com/{REPO}/blob/{sha}/{os.path.relpath(os.path.join(d, rel), ROOT).replace(os.sep, '/')}"


def table(header, rows):
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def previous_tag(t):
    prefix = f"{t['type']}/{t['component']}/v"
    key = lambda s: [int(x) for x in re.findall(r"\d+", s[len(prefix):])]
    tags = [x for x in git("tag", "--list", prefix + "*").split("\n") if x and x != t["tag"] and TAG_RE.match(x)]
    older = [x for x in tags if key(x) < key(t["tag"])]
    return max(older, key=key) if older else None


def render(t, d, man, front, sections, files, sha, local):
    kind = t["type"]
    status = [f"**{front.get('status', 'Release')}**"] + [str(x) for x in front.get("status_details", [])]
    pre = ("> [!NOTE]\n> Pre-release: " + front.get("prerelease_note", "not yet validated for general use.")) if t["prerelease"] else ""
    imgs = man.get("images", [])
    cells = [f'<a href="{raw(sha, d, i["path"])}"><img src="{raw(sha, d, i["path"])}" width="{man.get("image_width", 300)}" alt="{i.get("caption", "")}"></a>' for i in imgs]
    caps = [i.get("caption", "") for i in imgs]
    grid = []
    for k in range(0, len(cells), 3):
        grid.append("<tr>" + "".join(f"<td align=\"center\">{c}<br><sub>{cap}</sub></td>" for c, cap in zip(cells[k:k + 3], caps[k:k + 3])) + "</tr>")
    images = f"<table>{''.join(grid)}</table>" if grid else ""
    specs = table(["", ""], [(k, v) for k, v in man.get("specs", {}).items()]) if man.get("specs") else ""
    bring = front.get("bringup", {})
    bringup = table(["Test", "Result"], [(k, RESULT.get(v, v)) for k, v in bring.items()]) if bring else ""
    order = man.get("order", {})
    order_md = ""
    if order:
        order_md = table(["Setting", "Value"], [(k, v) for k, v in order.get("settings", {}).items()])
        if order.get("steps"):
            order_md += "\n\n" + "\n".join(f"{n}. {s}" for n, s in enumerate(order["steps"], 1))
    links = man.get("links", {})
    link_md = " · ".join(f"[{k}]({v if v.startswith('http') else blob(sha, d, v)})" for k, v in links.items())
    link_md += (" · " if link_md else "") + f"[source at this release](https://github.com/{REPO}/tree/{sha}/{t['dir']})"
    tested = front.get("tested_with", {})
    tested_md = table(["Component", "Release"], [(k, f"[`{v}`](https://github.com/{REPO}/releases/tag/{v})") for k, v in tested.items()]) if tested else ""
    prev = None if local else previous_tag(t)
    if man.get("auto_changes", kind in BUILT_IN_CI) and prev:
        log = git("log", "--no-merges", "--format=- %s (%h)", f"{prev}..{t['tag']}", "--", t["dir"])
        changes = f"Since [`{prev}`](https://github.com/{REPO}/releases/tag/{prev}):\n\n" + (log or "- no changes in this folder")
    else:
        changes = ""
    files_md = table(["File", "What", "Size", "SHA-256"], [(f"`{n}`", desc, size(s), f"`{h[:12]}`") for n, desc, s, h in files])
    files_md += "\n\nFull checksums in `SHA256SUMS`."
    extra = "\n\n".join(f"## {k}\n\n{v}" for k, v in sections.items() if k != "Summary" and v)
    built = "Firmware built by CI from this tag" if kind in BUILT_IN_CI else "Files built locally and committed; this release only attaches them"
    footer = f"{built} · commit [`{sha[:7]}`](https://github.com/{REPO}/commit/{sha}) · generated by `tools/release/release.py`"
    values = {
        "title": f"{man['name']} v{t['version']}", "status": " · ".join(status), "prerelease": pre,
        "summary": sections["Summary"], "images": images, "specs": specs, "bringup": bringup,
        "notes": extra, "order": order_md, "files": files_md, "links": link_md, "tested_with": tested_md,
        "changes": changes, "footer": footer,
    }
    tpl = open(os.path.join(TEMPLATES, f"{kind}.md"), encoding="utf-8").read()
    md = re.sub(r"\{\{(\w+)\}\}", lambda m: values[m.group(1)], tpl)
    # drop headings whose section rendered empty, then squeeze blank runs
    md = re.sub(r"^## [^\n]+\n+(?=## |<sub>|\Z)", "", md, flags=re.M)
    return re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"


# ---------------------------------------------------------------- commands
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["preview", "check", "build", "package"])
    ap.add_argument("tag")
    ap.add_argument("--out", default=os.path.join(ROOT, "dist"))
    ap.add_argument("--github-output", action="store_true")
    ap.add_argument("--local", action="store_true", help="skip the tag/main gates (testing before tagging)")
    a = ap.parse_args()
    try:
        t = parse_tag(a.tag)
        d, man, front, sections = load(t)
        local = a.cmd == "preview" or a.local
        gates(t, d, man, front, local)
        if a.cmd == "check":
            info = {**t, "build": t["type"] in BUILT_IN_CI, "title": f"{man['name']} v{t['version']}"}
            print(json.dumps(info, indent=2))
            if a.github_output:
                with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                    for k, v in info.items():
                        f.write(f"{k}={json.dumps(v) if isinstance(v, bool) else v}\n")
        elif a.cmd == "build":
            build(t, d, man)
        else:
            files = collect(t, d, man, a.out)
            sha = git("rev-parse", "HEAD")
            md = render(t, d, man, front, sections, files, sha, local)
            with open(os.path.join(a.out, "notes.md"), "w", encoding="utf-8", newline="\n") as f:
                f.write(md)
            with open(os.path.join(a.out, "title.txt"), "w", encoding="utf-8") as f:
                f.write(f"{man['name']} v{t['version']}")
            print(f"{'PREVIEW' if local else 'packaged'}: {a.out}/notes.md + {len(files)} assets"
                  f" ({'pre-release' if t['prerelease'] else 'release'}, not marked Latest)")
            if local:
                print("note: preview links/images use the current HEAD commit; the real release uses the tagged commit")
    except Fail as e:
        sys.exit(f"release: {e}")


if __name__ == "__main__":
    main()
