# Setup — Claude Video Editor

Everything Claude needs to cut video inside Premiere Pro, in one folder.
Two engines: **Premiere Pro MCP** (drives Premiere) and **HyperFrames**
(HTML → motion graphics).

## 0. Prerequisites

| Piece | Status | Notes |
|---|---|---|
| Adobe Premiere Pro 2020+ | **you install** | Needs an Adobe account. Tested on Premiere 26. |
| GitHub CLI (`gh`) | already ✓ | Signed in. |
| Node.js 22+ | installer handles | Via your existing nvm, or Homebrew. |
| FFmpeg | installer handles | Via Homebrew. |
| Homebrew | installer handles | Installed if missing. |
| `adobe-premiere-pro-mcp` + CEP panel | installer handles | The Premiere bridge. |
| HyperFrames skills | installer handles | The motion-graphics engine. |

## 1. Run the installer

From this folder, in Terminal:

```bash
bash setup.sh
```

It's safe to re-run — it skips anything already there. If you install Premiere
*after* running it, just run `bash setup.sh` again so the CEP panel installs.

## 2. One-time steps inside Premiere Pro

1. Open Premiere Pro.
2. **Preferences → Plugins →** enable **"UXP Plugins > Enable developer mode"**.
3. Quit and reopen Premiere.
4. **Window → Extensions → MCP Bridge (CEP)**.
5. Set **Temp Directory** to `/tmp/premiere-mcp-bridge`.
6. **Save Configuration → Start Bridge → Test Connection**.

If Test Connection fails, click **Run Diagnostics** in the panel and check
`/tmp/premiere-mcp-bridge/premiere-mcp-diagnostics-latest.json`.

## 3. Connect Claude

The installer configures Claude Desktop's MCP config automatically. After it runs:

- **Restart the Claude desktop app** so it loads the new `premiere-pro` MCP server.
- Ask Claude: **"Run `verify_premiere_connection`. Make no changes."**
- A reply with your Premiere build + open project = you're live.

For a full end-to-end check with Premiere open on a scratch project:

```bash
premiere-pro-mcp --doctor
```

## 4. Make your first edit

1. Drop raw footage into `footage/`.
2. Open `project/` and create/save a Premiere project there.
3. Fill in the **"How I edit"** section of `CLAUDE.md` with your style.
4. Tell Claude: *"Import everything from footage/, propose an edit plan, then
   build a rough cut on a new sequence."*
5. For graphics: *"Using HyperFrames, make a [title card / lower-third / …],
   render it to graphics/, and place it on the timeline."*

## Troubleshooting

- **Client sees the MCP but tool calls fail** → Premiere isn't open, no project is
  open, the CEP panel isn't started, or its Temp Directory isn't
  `/tmp/premiere-mcp-bridge`. Right-click the panel → **Reload** after updates.
- **`setup:doctor` fails** → CEP extension not installed, Premiere debug mode off,
  or Claude Desktop config points to the wrong path. Re-run `bash setup.sh`.
- **HyperFrames render fails** → confirm `ffmpeg -version` works and Node is 22+.

## Sources / upstream

- Premiere MCP: `hetpatel-11/Adobe_Premiere_Pro_MCP` (283 tools; CEP bridge)
- HyperFrames: `heygen-com/hyperframes` (HTML → MP4 motion graphics)
