# Setup — Claude Video Editor

Everything Claude needs to cut, caption and finish a video, in one folder.

One engine: **HyperFrames** (HTML → motion graphics and caption overlays),
plus ffmpeg and whisper.cpp. There is deliberately **no NLE** — no Premiere, no
Final Cut, no Resolve. The cut is computed, the graphics are rendered, and
ffmpeg composites and encodes the result. Nothing has to be open, and nothing
has to be clicked. (Premiere Pro and its MCP bridge were removed on 2026-09-21.)

## 0. Prerequisites

| Piece | Status | Notes |
|---|---|---|
| Node.js 22+ | installer handles | Via your existing nvm, or Homebrew. |
| FFmpeg | installer handles | Via Homebrew. Does the cutting, compositing and encoding. |
| whisper.cpp | installer handles | `whisper-cli` + the `small.en` model, for caption timings. Runs locally; nothing is uploaded. |
| Homebrew | installer handles | Installed if missing. |
| GitHub CLI (`gh`) | already ✓ | Signed in. |
| HyperFrames skills | installer handles | The motion-graphics engine. |

No Adobe account, no paid software, no GPU.

## 1. Run the installer

From this folder, in Terminal:

```bash
bash setup.sh
```

It's safe to re-run — it skips anything already there.

## 2. Make your first edit

1. Drop raw footage into `footage/`.
2. Fill in the **"How I edit"** section of `CLAUDE.md` with your style.
3. Tell Claude: *"Cut the silence out of `footage/<clip>.mp4` and caption it."*
   It follows `NEW-VIDEO.md` — analyse, drop repeated takes, caption, render,
   composite, export to `output/`.
4. For graphics: *"Using HyperFrames, make a [title card / lower-third / …] and
   composite it over the cut."*

Everything is verified as **text** — `check_render.py` reads the overlay's alpha
channel, `burn.py --verify` measures the luma difference between the uncaptioned
master and the final. No screenshots, no playback, no eyeballing.

## Troubleshooting

- **HyperFrames render fails** → confirm `ffmpeg -version` works and Node is 22+.
  The render runtime (bundled Chrome + fonts) lives in `~/.cache/hyperframes`;
  `npx -y hyperframes skills update` restores it.
- **No transcript / captions are empty** → `whisper-cli` isn't on PATH, or
  `~/.cache/whisper/ggml-small.en.bin` is missing. Re-run `bash setup.sh`.
- **Captions drift against the picture** → the transcript was made from the wrong
  audio. It must come from the **cut** audio, never the original. Re-run
  `preprocess.py`.

## Sources / upstream

Nothing on this machine reads from a GitHub checkout. `setup.sh` installs from
the **npm registry** and Homebrew, and what lands on disk is a complete copy —
so these are provenance links and a restore path, not a live dependency.

**HyperFrames** — HTML → MP4 motion graphics

- Upstream: <https://github.com/heygen-com/hyperframes>
- npm: `hyperframes` — <https://www.npmjs.com/package/hyperframes>
- Installed: **v0.8.58**, run via `npx` (not a global binary), cached under
  `~/.npm/_npx/`
- Skills (the part Claude actually reads): `~/.claude/skills/hyperframes*` and
  `~/.agents/skills/` — real files, ~5.5 MB
- Render runtime (bundled Chrome + fonts): `~/.cache/hyperframes`, ~197 MB
- Restore: `npx -y hyperframes skills update` (or re-run `setup.sh`)

**whisper.cpp** — local speech-to-text for caption timings

- Installed: `brew install whisper-cpp` → `whisper-cli`
- Model: `~/.cache/whisper/ggml-small.en.bin` (~488 MB) from
  <https://huggingface.co/ggerganov/whisper.cpp>
- **small.en, not base.en** — base mangles finance/hardware jargon.

*Note:* HyperFrames' upstream does not declare a license. Fine for using it as an
installed tool; worth checking before redistributing anything from it.

### Removed 2026-09-21 — Adobe Premiere Pro MCP

The studio used to drive Premiere over `adobe-premiere-pro-mcp` + a CEP bridge
panel. Lana asked for the pipeline to have no reliance on it, so the npm package,
the CEP panel, the `/tmp/premiere-mcp-bridge` temp dir and the `premiere-pro`
entry in `~/.claude.json` were all removed. Should it ever be wanted back:

```bash
npm install -g adobe-premiere-pro-mcp
premiere-pro-mcp --install-cep
claude mcp add premiere-pro -s user -e PREMIERE_TEMP_DIR=/tmp/premiere-mcp-bridge \
    -- node /opt/homebrew/lib/node_modules/adobe-premiere-pro-mcp/dist/index.js
```
