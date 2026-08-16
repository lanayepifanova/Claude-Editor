#!/usr/bin/env python3
"""
session-cost.py — how expensive is the CURRENT session, and should it be reset?

Context is re-sent on every turn, so a long session charges its whole history
again each time you speak. This reads Claude Code's own transcript log and says
plainly whether to keep going or start fresh.

    python3 edit/session-cost.py            # full report
    python3 edit/session-cost.py --hook     # one line, only past HARD_CTX

The --hook form is wired to UserPromptSubmit in .claude/settings.json, so the
verdict arrives on its own instead of waiting for someone to remember it.
"""
import json, sys
from pathlib import Path

# a fresh session bootstraps from CLAUDE.md + WORKING-NOTES.md + edit/README.md
BOOTSTRAP = 6_000
WARN_CTX  = 120_000        # avg context per turn where a reset starts paying off
HARD_CTX  = 250_000


def newest_log():
    """This project's newest transcript, or None.

    Exact slug match only, walking up from cwd so it still works from a
    subdirectory. Deliberately NO cross-project fallback: silently measuring
    some other project's session would give a confident wrong verdict on the
    one decision here that actually costs money.
    """
    root = Path.home() / ".claude" / "projects"
    here = Path.cwd().resolve()
    for d in (here, *here.parents):
        proj = root / str(d).replace("/", "-")
        if proj.is_dir():
            logs = sorted(proj.glob("*.jsonl"),
                          key=lambda p: p.stat().st_mtime, reverse=True)
            if logs:
                return logs[0]
    return None


def main():
    hook = "--hook" in sys.argv
    log = newest_log()
    if not log:
        # in hook mode never block the prompt and never add noise
        sys.exit(0 if hook else "no session transcript found")
    turns = out = reads = writes = 0
    for line in open(log, errors="ignore"):
        line = line.strip()
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        u = (d.get("message") or {}).get("usage")
        if not u:
            continue
        turns += 1
        out += u.get("output_tokens", 0) or 0
        reads += u.get("cache_read_input_tokens", 0) or 0
        writes += u.get("cache_creation_input_tokens", 0) or 0
    if not turns:
        sys.exit(0 if hook else "transcript has no usage data yet")

    avg = reads / turns

    if hook:
        # Injected into context automatically. Stay terse — a verbose warning
        # about context cost that itself costs context is self-defeating.
        if avg >= HARD_CTX:
            print(f"[session-cost] context {avg:,.0f}/turn — {avg/BOOTSTRAP:.0f}x a fresh "
                  f"bootstrap. Finish the current step, then start a new session. "
                  f"Resume state: edit/manifest.json, edit/analysis-*/, NEW-VIDEO.md.")
        sys.exit(0)

    print(f"session : {log.name[:8]}…")
    print(f"turns   : {turns:,}")
    print(f"output  : {out:,} tokens   (the actual work)")
    print(f"context : {avg:,.0f} per turn   (re-read every time you speak)")
    print(f"total   : {reads + writes + out:,} token events\n")

    if avg >= HARD_CTX:
        print(f"  VERDICT: start a fresh session now.")
        print(f"  Every further turn costs ~{avg:,.0f} tokens before you get a word out;")
        print(f"  a fresh one bootstraps for ~{BOOTSTRAP:,} — roughly {avg/BOOTSTRAP:.0f}x cheaper.")
        sys.exit(2)
    if avg >= WARN_CTX:
        print(f"  VERDICT: finish the current task, then reset.")
        print(f"  Starting new work here costs ~{avg/BOOTSTRAP:.0f}x what a fresh session would.")
        sys.exit(1)
    print("  VERDICT: fine to continue.")


if __name__ == "__main__":
    main()
