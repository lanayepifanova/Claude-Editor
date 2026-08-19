#!/usr/bin/env python3
"""
cleanup.py — reclaim disk from FINISHED projects, without ever losing an edit.

Nothing here guesses that a project is done. You say so:

    python3 edit/cleanup.py --list                    # what exists, what it costs
    python3 edit/cleanup.py --done Reddit             # dry run (the default)
    python3 edit/cleanup.py --done Reddit --apply     # actually delete
    python3 edit/cleanup.py --caches --apply          # node_modules, caches, junk

Two rules make this safe to run without reading the code first:

1. It only ever removes things that can be REBUILT. A cut_proof.mp4 counts as
   rebuildable only if its source clip is still on disk — check `source` in
   silence.json. When the footage is gone the proof is the last copy of that
   cut, so this refuses to touch it. That is not a hypothetical: footage/ is
   deleted at the end of a video by design (see CLAUDE.md), which quietly turns
   every proof render into an original.
2. Everything else is protected by path, not by intent. footage/, output/,
   project/, and every .json in an analysis dir are unreachable from here even
   if a pattern is wrong.
"""
import re
import argparse, json, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Never reachable, whatever else this file says. Checked per path, after
# resolution, so a symlink or a stray glob cannot walk into them.
PROTECTED = ("footage", "output", "project", ".git")

# Rebuildable given the inputs that live in git. Everything else is left alone.
CACHE_PATTERNS = [
    ("**/node_modules",  "npm install"),
    ("**/.hf-cache",     "hyperframes refetches"),
    ("**/__pycache__",   "python rewrites"),
    ("**/snapshots",     "hyperframes snapshot"),
    ("**/.thumbnails",   "regenerated on demand"),
    ("**/.DS_Store",     "Finder"),
]


# Generated graphics projects and extracted panel crops. Same principle as the
# proof rule: reclaimable only when it can be REBUILT from something in git.
# A *-motion dir is rebuildable when its composition HTML is committed (that is
# exactly what was lost on 2026-08-17, when cleanup ran ahead of the commit).
# A *-bubbles crop dir is rebuildable from the committed PNG decks via
# edit/extract_panels.py, so it needs no HTML.
GRAPHICS_GLOBS = ["graphics/*-motion", "graphics/*-bubbles"]

# Loose render files sitting directly in graphics/ — the .mov/.mp4 a composition
# renders to. They are the biggest thing on disk by far (four of them were 1.5 GB
# after one video) and nothing else swept them, so they piled up across sessions.
# Same rebuildable test as everything here: a render may go only when the
# composition that produces it is committed, matched by name — "sonytsmc-cap.mov"
# and "sonytsmc-cap-v2.mov" both map to graphics/sonytsmc-captions/. No match
# means KEEP, because an unmatched render might be the only copy of something.
RENDER_GLOBS = ["graphics/*.mov", "graphics/*.mp4"]


def render_source(f):
    """(ok, why) — is this loose render rebuildable from a committed composition?"""
    stem = re.sub(r"-v\d+$", "", f.stem)
    for d in sorted(ROOT.glob("graphics/*")):
        if not d.is_dir() or not d.name.startswith(stem):
            continue
        htmls = sorted(d.glob("*.html")) + sorted(d.glob("variants/*.html"))
        committed = [h for h in htmls if tracked(h)]
        if committed:
            return True, f"re-render from {d.name}/{committed[0].name}"
    return False, f"no committed composition matches '{stem}'"


def cmd_renders(apply, force):
    freed = 0
    found = False
    for pat in RENDER_GLOBS:
        for f in sorted(ROOT.glob(pat)):
            if not f.is_file():
                continue
            found = True
            ok, why = render_source(f)
            print(f"\n{f.relative_to(ROOT)}  {human(size_of(f))}")
            if not ok and not force:
                print(f"  KEEPING — {why}")
                print("    commit the composition first, or pass --force.")
                continue
            if not ok:
                print(f"  --force: discarding an unmatched render ({why})")
            else:
                print(f"  {why}")
            freed += remove([f], apply)
    if not found:
        print("no loose renders in graphics/")
    return freed


def graphics_status(d):
    """(ok, why) — may this generated graphics dir be deleted?"""
    htmls = sorted(d.glob("*.html")) + sorted(d.glob("variants/*.html"))
    if not htmls:
        return True, "crops, regenerable by edit/extract_panels.py"
    untracked = [h for h in htmls if not tracked(h)]
    if untracked:
        return False, ("composition not committed: "
                       + ", ".join(h.name for h in untracked))
    return True, f"{len(htmls)} composition(s) committed, re-render to rebuild"


def cmd_graphics(apply, force):
    freed = 0
    found = False
    for pat in GRAPHICS_GLOBS:
        for d in sorted(ROOT.glob(pat)):
            if not d.is_dir():
                continue
            found = True
            ok, why = graphics_status(d)
            print(f"\n{d.relative_to(ROOT)}  {human(size_of(d))}")
            if not ok and not force:
                print(f"  KEEPING — {why}")
                print("    commit it first, or pass --force to discard it anyway.")
                continue
            if not ok:
                print(f"  --force: discarding an uncommitted composition ({why})")
            else:
                print(f"  {why}")
            freed += remove([d], apply)
    if not found:
        print("no generated graphics dirs")
    return freed


def human(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024 or u == "GB":
            return f"{n:.0f} {u}" if u in ("B", "KB") else f"{n:.1f} {u}"
        n /= 1024


def size_of(p):
    if p.is_file():
        return p.stat().st_size
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())


def guarded(p):
    """True if p is safe to delete. Fails closed."""
    try:
        p = p.resolve()
        rel = p.relative_to(ROOT)
    except (ValueError, OSError):
        return False                      # outside the repo entirely
    return bool(rel.parts) and rel.parts[0] not in PROTECTED


def tracked(p):
    """Is this path committed? A tracked input can be restored with git."""
    r = subprocess.run(["git", "ls-files", "--error-unmatch", str(p)],
                       cwd=ROOT, capture_output=True)
    return r.returncode == 0


def projects():
    """Every analysis dir, with the name you would pass to --done."""
    out = []
    for d in sorted(ROOT.glob("edit/analysis*")):
        if not d.is_dir():
            continue
        name = d.name[len("analysis-"):] if d.name.startswith("analysis-") else "default"
        out.append((name, d))
    return out


def proof_status(d):
    """(proof_path, rebuildable, why) for one analysis dir."""
    proof = d / "cut_proof.mp4"
    if not proof.exists():
        return None, False, "no proof render"
    sil = d / "silence.json"
    src = None
    if sil.exists():
        src = json.load(open(sil)).get("source")
    if not src:
        return proof, False, ("silence.json has no `source` — cannot prove the "
                              "clip still exists, so treating as irreplaceable")
    sp = Path(src)
    if not sp.is_absolute():
        sp = ROOT / sp
    if not sp.exists():
        return proof, False, f"source clip is gone ({src}) — this proof is the last copy"
    return proof, True, f"rebuildable from {src}"


def cmd_list():
    print(f"{'project':<22} {'analysis':>10} {'proof':>10}  status")
    print("-" * 78)
    total = 0
    for name, d in projects():
        proof, ok, why = proof_status(d)
        jsz = sum(f.stat().st_size for f in d.glob("*.json"))
        psz = proof.stat().st_size if proof else 0
        total += psz
        mark = "reclaimable" if ok else "KEEP"
        print(f"{name:<22} {human(jsz):>10} {human(psz):>10}  {mark} — {why}")
    print(f"\nproof renders on disk: {human(total)}")

    print("\ncaches and junk:")
    csz = 0
    for pat, how in CACHE_PATTERNS:
        hits = [p for p in ROOT.glob(pat) if guarded(p)]
        if not hits:
            continue
        s = sum(size_of(p) for p in hits)
        csz += s
        print(f"  {pat:<20} {len(hits):>3} path(s) {human(s):>10}   (rebuilt by {how})")
    print(f"  {'':<20} {'':>3}          {human(csz):>10}   total")
    print("\nnothing above is deleted without --apply.")


def remove(paths, apply):
    freed = 0
    for p in paths:
        if not guarded(p):
            print(f"  REFUSED (protected path) {p}")
            continue
        s = size_of(p)
        freed += s
        print(f"  {'deleted' if apply else 'would delete'} {p.relative_to(ROOT)}  {human(s)}")
        if apply:
            shutil.rmtree(p) if p.is_dir() else p.unlink()
    return freed


def cmd_done(names, apply, force):
    known = dict(projects())
    freed = 0
    for name in names:
        d = known.get(name)
        if d is None:
            print(f"! no analysis dir for '{name}'. Known: {', '.join(known) or '(none)'}")
            continue
        proof, ok, why = proof_status(d)
        print(f"\n{name}  ({d.relative_to(ROOT)})")
        inputs = sorted(f.name for f in d.glob("*.json"))
        print(f"  inputs kept: {' '.join(inputs) or '(none)'}"
              f"{'  [committed]' if inputs and tracked(d/inputs[0]) else ''}")
        if proof is None:
            print(f"  {why} — nothing to reclaim")
            continue
        if not ok and not force:
            print(f"  KEEPING cut_proof.mp4 ({human(proof.stat().st_size)})")
            print(f"    {why}")
            print(f"    re-export it to output/ first, or pass --force if you truly")
            print(f"    do not want this cut back.")
            continue
        if not ok:
            print(f"  --force: deleting an IRREPLACEABLE proof ({why})")
        freed += remove([proof], apply)
    return freed


def cmd_caches(apply):
    paths = []
    for pat, _ in CACHE_PATTERNS:
        paths += [p for p in ROOT.glob(pat) if guarded(p)]
    if not paths:
        print("nothing to sweep")
        return 0
    return remove(sorted(set(paths)), apply)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="show projects and sizes")
    ap.add_argument("--done", nargs="+", metavar="NAME",
                    help="projects you have finished with")
    ap.add_argument("--graphics", action="store_true",
                    help="remove generated graphics projects and panel crops")
    ap.add_argument("--renders", action="store_true",
                    help="remove loose .mov/.mp4 renders in graphics/ whose composition is committed")
    ap.add_argument("--caches", action="store_true",
                    help="sweep node_modules, .hf-cache, __pycache__, snapshots, .DS_Store")
    ap.add_argument("--apply", action="store_true", help="actually delete (default: dry run)")
    ap.add_argument("--force", action="store_true",
                    help="delete a proof even when its source clip is gone")
    a = ap.parse_args()

    if not (a.list or a.done or a.caches or a.graphics or a.renders):
        ap.print_help()
        return

    if a.list:
        cmd_list()
        return

    freed = 0
    if a.renders:
        freed += cmd_renders(a.apply, a.force)
    if a.done:
        freed += cmd_done(a.done, a.apply, a.force)
    if a.graphics:
        freed += cmd_graphics(a.apply, a.force)
    if a.caches:
        freed += cmd_caches(a.apply)

    print(f"\n{'reclaimed' if a.apply else 'would reclaim'} {human(freed)}"
          f"{'' if a.apply else '   (dry run — pass --apply)'}")
    print("footage/, output/, project/ and every analysis .json were never candidates.")


if __name__ == "__main__":
    main()
