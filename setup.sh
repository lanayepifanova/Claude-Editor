#!/usr/bin/env bash
# =============================================================================
#  Claude Video Editor — one-shot macOS installer
#  Installs everything Claude needs to cut, caption and finish a video.
#  There is no NLE here on purpose — Premiere and its MCP bridge were removed
#  on 2026-09-21. ffmpeg does the cutting and compositing.
#    - Homebrew (if missing)
#    - Node.js 22+  (via your existing nvm, or Homebrew as fallback)
#    - FFmpeg
#    - whisper.cpp + the small.en model  (local caption timings)
#    - HyperFrames skills                (HTML -> motion-graphics engine)
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
# 5. whisper.cpp + the small.en model (caption timings, entirely local)
# ---------------------------------------------------------------------------
step "whisper.cpp"
if ! command -v whisper-cli >/dev/null 2>&1; then
  brew install whisper-cpp || die "whisper-cpp install failed."
fi
ok "whisper-cli ready"

# small.en, NOT base.en — base mangles finance/hardware jargon ("trade GPU out",
# "Cash shuttle listed on Nimus"). preprocess.py defaults to this exact path.
WHISPER_MODEL="$HOME/.cache/whisper/ggml-small.en.bin"
if [ ! -f "$WHISPER_MODEL" ]; then
  warn "Downloading the small.en model (~488 MB)…"
  mkdir -p "$(dirname "$WHISPER_MODEL")"
  curl -fL --progress-bar -o "$WHISPER_MODEL" \
    "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin" \
    || { rm -f "$WHISPER_MODEL"; die "model download failed."; }
fi
ok "small.en model at $WHISPER_MODEL"

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
echo -e "\n${GREEN}Install complete — nothing else to configure.${NC}"
cat <<'NEXT'

There is no app to open and no bridge to start. To make a video:

  1. Drop footage into  footage/
  2. Fill in the "How I edit" section of  CLAUDE.md  with your style.
  3. Ask Claude:  "Cut the silence out of footage/<clip>.mp4 and caption it."

Claude follows NEW-VIDEO.md: analyse -> drop repeated takes -> caption ->
render -> composite -> export to output/. Every step is verified as text.

See SETUP.md in this folder for the full walkthrough and troubleshooting.
NEXT
