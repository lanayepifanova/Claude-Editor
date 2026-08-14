#!/usr/bin/env bash
# =============================================================================
#  Claude Video Editor — one-shot macOS installer
#  Installs everything Claude needs to edit video inside Premiere Pro:
#    - Homebrew (if missing)
#    - Node.js 22+  (via your existing nvm, or Homebrew as fallback)
#    - FFmpeg
#    - adobe-premiere-pro-mcp  (the Premiere bridge) + its CEP panel
#    - HyperFrames skills       (HTML -> motion-graphics engine)
#
#  Safe to re-run. It skips anything already installed.
#  Run from inside this folder:   bash setup.sh
# =============================================================================
set -uo pipefail

BLUE='\033[1;34m'; GREEN='\033[1;32m'; YELLOW='\033[1;33m'; RED='\033[1;31m'; NC='\033[0m'
step() { echo -e "\n${BLUE}==>${NC} $*"; }
ok()   { echo -e "${GREEN}  ✓${NC} $*"; }
warn() { echo -e "${YELLOW}  !${NC} $*"; }
die()  { echo -e "${RED}  ✗${NC} $*"; exit 1; }

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

echo -e "${BLUE}Claude Video Editor — setup${NC}"
echo    "Project folder: $PROJECT_DIR"

# ---------------------------------------------------------------------------
# 0. Sanity: macOS only
# ---------------------------------------------------------------------------
[ "$(uname)" = "Darwin" ] || die "This installer is macOS-only."

# ---------------------------------------------------------------------------
# 1. Homebrew
# ---------------------------------------------------------------------------
step "Homebrew"
if ! command -v brew >/dev/null 2>&1; then
  warn "Homebrew not found — installing (you may be prompted for your password)…"
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" \
    || die "Homebrew install failed."
fi
# Load brew into this shell (Apple Silicon path first, then Intel)
if [ -x /opt/homebrew/bin/brew ]; then eval "$(/opt/homebrew/bin/brew shellenv)"
elif [ -x /usr/local/bin/brew ]; then eval "$(/usr/local/bin/brew shellenv)"; fi
command -v brew >/dev/null 2>&1 && ok "Homebrew ready ($(brew --version | head -1))"

# ---------------------------------------------------------------------------
# 2. Node.js 22+  (prefer your existing nvm; fall back to Homebrew)
# ---------------------------------------------------------------------------
step "Node.js 22+"
node_major() { node -v 2>/dev/null | sed -E 's/v([0-9]+).*/\1/'; }

if [ -s "$HOME/.nvm/nvm.sh" ]; then
  export NVM_DIR="$HOME/.nvm"
  # shellcheck disable=SC1091
  . "$HOME/.nvm/nvm.sh"
  if ! command -v node >/dev/null 2>&1 || [ "$(node_major)" -lt 22 ]; then
    warn "Installing Node 22 via nvm…"
    nvm install 22 && nvm alias default 22 && nvm use 22
  fi
fi
if ! command -v node >/dev/null 2>&1 || [ "$(node_major)" -lt 22 ]; then
  warn "Installing Node 22 via Homebrew…"
  brew install node@22 && brew link --overwrite --force node@22
fi
command -v node >/dev/null 2>&1 && [ "$(node_major)" -ge 22 ] \
  && ok "Node $(node -v) / npm $(npm -v)" \
  || die "Node 22+ still not available. Install it manually, then re-run."

# ---------------------------------------------------------------------------
# 3. FFmpeg
# ---------------------------------------------------------------------------
step "FFmpeg"
if ! command -v ffmpeg >/dev/null 2>&1; then
  brew install ffmpeg || die "FFmpeg install failed."
fi
ok "FFmpeg $(ffmpeg -version | head -1 | awk '{print $3}')"

# ---------------------------------------------------------------------------
# 4. GitHub CLI (you said this is already set up — verify only)
# ---------------------------------------------------------------------------
step "GitHub CLI"
if command -v gh >/dev/null 2>&1; then
  if gh auth status >/dev/null 2>&1; then ok "gh installed and signed in"
  else warn "gh installed but not signed in — run:  gh auth login"; fi
else
  warn "gh not found — installing…"; brew install gh && warn "Now run:  gh auth login"
fi

# ---------------------------------------------------------------------------
# 5. Premiere Pro MCP bridge (global) + CEP panel
# ---------------------------------------------------------------------------
step "Adobe Premiere Pro MCP bridge"
npm install -g adobe-premiere-pro-mcp || die "npm global install of adobe-premiere-pro-mcp failed."
ok "adobe-premiere-pro-mcp installed"
warn "Installing the CEP panel into Premiere + configuring Claude Desktop…"
premiere-pro-mcp --install-cep || warn "--install-cep reported an issue (fine if Premiere isn't installed yet; re-run after installing Premiere)."
echo "  Running doctor (non-fatal)…"
premiere-pro-mcp --doctor || warn "doctor found issues — expected until Premiere is installed and the CEP bridge is started."

# ---------------------------------------------------------------------------
# 6. HyperFrames skills (motion-graphics engine)
# ---------------------------------------------------------------------------
step "HyperFrames skills"
# Installs the core skill set for agents (router + domain skills + media-use).
npx -y hyperframes skills update || warn "hyperframes skills update reported an issue — you can re-run it later."
ok "HyperFrames skills attempted"

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo -e "\n${GREEN}Software install complete.${NC}"
cat <<'NEXT'

NEXT — the few things that must happen inside Premiere (one time):
  1. Open Adobe Premiere Pro.
  2. Preferences > Plugins  ->  enable "UXP Plugins > Enable developer mode".
  3. Quit and reopen Premiere Pro.
  4. Window > Extensions > MCP Bridge (CEP).
  5. Set  Temp Directory  to:  /tmp/premiere-mcp-bridge
  6. Click  Save Configuration  ->  Start Bridge  ->  Test Connection.

THEN, in Claude:
  - Restart the Claude desktop app so it picks up the new MCP server.
  - Ask Claude:  "Run verify_premiere_connection. Make no changes."
  - If that returns your Premiere build + open project, you're live.

See SETUP.md in this folder for the full walkthrough and troubleshooting.
NEXT
