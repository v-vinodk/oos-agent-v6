#!/bin/bash
# ═══════════════════════════════════════════════════════════
#  noon OOS Agent — One-shot GitHub + Streamlit deploy script
# ═══════════════════════════════════════════════════════════
set -e

BOLD='\033[1m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'
YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║   noon OOS Agent — GitHub + Streamlit Deployment    ║${NC}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

# ── Step 1: Check git is installed ────────────────────────────────────────────
echo -e "${CYAN}▶ Step 1/6 — Checking prerequisites...${NC}"
if ! command -v git &>/dev/null; then
  echo -e "${RED}  ✗ git not found. Install from https://git-scm.com${NC}"; exit 1
fi
echo -e "${GREEN}  ✓ git found${NC}"

if ! command -v gh &>/dev/null; then
  echo -e "${YELLOW}  ⚠ GitHub CLI (gh) not found.${NC}"
  echo "    We'll create the repo manually. Install gh later from https://cli.github.com"
  GH_CLI=false
else
  GH_CLI=true
  echo -e "${GREEN}  ✓ GitHub CLI found${NC}"
fi

# ── Step 2: Collect info ───────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}▶ Step 2/6 — Repository setup${NC}"
read -p "  Your GitHub username: " GH_USER
REPO_NAME="oos-agent"
read -p "  Repo name [${REPO_NAME}]: " INPUT
REPO_NAME="${INPUT:-$REPO_NAME}"
REPO_URL="https://github.com/${GH_USER}/${REPO_NAME}.git"
echo "  Will push to: ${REPO_URL}"

# ── Step 3: Init git, make .gitignore watertight ──────────────────────────────
echo ""
echo -e "${CYAN}▶ Step 3/6 — Initialising git...${NC}"

cat > .gitignore << 'GITEOF'
.env
.streamlit/secrets.toml
__pycache__/
*.pyc
*.pyo
venv/
.venv/
*.egg-info/
.DS_Store
GITEOF

git init -q
git add .
git commit -q -m "noon OOS Analytics Agent v5 — initial deploy"
echo -e "${GREEN}  ✓ Git repo initialised and committed${NC}"

# ── Step 4: Create GitHub repo ────────────────────────────────────────────────
echo ""
echo -e "${CYAN}▶ Step 4/6 — Creating GitHub repository...${NC}"
if [ "$GH_CLI" = true ]; then
  gh repo create "${GH_USER}/${REPO_NAME}" --private --source=. --remote=origin --push
  echo -e "${GREEN}  ✓ Repo created and pushed via GitHub CLI${NC}"
else
  echo ""
  echo -e "${YELLOW}  ── Manual step required ──${NC}"
  echo "  1. Open https://github.com/new in your browser"
  echo "  2. Repository name: ${REPO_NAME}"
  echo "  3. Set to PRIVATE"
  echo "  4. Click 'Create repository' (do NOT add README or .gitignore)"
  echo ""
  read -p "  Press ENTER once you've created the empty repo on GitHub..."
  git remote remove origin 2>/dev/null || true
  git remote add origin "${REPO_URL}"
  git branch -M main
  git push -u origin main
  echo -e "${GREEN}  ✓ Code pushed to GitHub${NC}"
fi

# ── Step 5: Print secrets for Streamlit Cloud ─────────────────────────────────
echo ""
echo -e "${CYAN}▶ Step 5/6 — Your Streamlit Cloud secrets${NC}"
echo ""
echo -e "${YELLOW}  Copy everything between the lines below into:${NC}"
echo -e "${YELLOW}  Streamlit Cloud → your app → Advanced settings → Secrets${NC}"
echo ""
echo "  ┌─────────────────────────────────────────────────────┐"

# Read values from .env if it exists
ANTHROPIC_KEY=$(grep ANTHROPIC_API_KEY .env 2>/dev/null | cut -d= -f2 | tr -d '"' || echo "sk-ant-your-key-here")
BQ_PROJECT=$(grep BQ_PROJECT .env 2>/dev/null | cut -d= -f2 | tr -d '"' || echo "noonbigmktgsandbox")
BQ_DATASET=$(grep BQ_DATASET .env 2>/dev/null | cut -d= -f2 | tr -d '"' || echo "vinod")
BQ_TABLE=$(grep BQ_TABLE .env 2>/dev/null | cut -d= -f2 | tr -d '"' || echo "oos_sku_daily")

cat << SECRETS_EOF
  ANTHROPIC_API_KEY = "${ANTHROPIC_KEY}"
  BQ_PROJECT        = "${BQ_PROJECT}"
  BQ_DATASET        = "${BQ_DATASET}"
  BQ_TABLE          = "${BQ_TABLE}"

  [gcp_service_account]
  type            = "service_account"
  project_id      = "${BQ_PROJECT}"
  private_key_id  = "PASTE_FROM_YOUR_JSON_KEY_FILE"
  private_key     = "-----BEGIN RSA PRIVATE KEY-----\nPASTE_YOUR_PRIVATE_KEY_HERE\n-----END RSA PRIVATE KEY-----\n"
  client_email    = "oos-agent@${BQ_PROJECT}.iam.gserviceaccount.com"
  client_id       = "PASTE_FROM_YOUR_JSON_KEY_FILE"
  auth_uri        = "https://accounts.google.com/o/oauth2/auth"
  token_uri       = "https://oauth2.googleapis.com/token"
SECRETS_EOF

echo "  └─────────────────────────────────────────────────────┘"

# ── Step 6: Print deploy instructions ────────────────────────────────────────
echo ""
echo -e "${CYAN}▶ Step 6/6 — Deploy on Streamlit Community Cloud${NC}"
echo ""
echo "  1. Go to: https://share.streamlit.io"
echo "  2. Sign in with your GitHub account (${GH_USER})"
echo "  3. Click 'Create app'"
echo "  4. Fill in:"
echo "       Repository : ${GH_USER}/${REPO_NAME}"
echo "       Branch     : main"
echo "       Main file  : app.py"
echo "  5. Click 'Advanced settings' → paste the secrets above"
echo "  6. Click 'Deploy'"
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✓ Done! Your app will be live at:                  ║${NC}"
echo -e "${GREEN}║  https://${GH_USER}-${REPO_NAME}-app-xxxx.streamlit.app  ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  Share that URL with your team. They log in with:"
echo "    category_manager / noon2024"
echo "    analyst / analyst123"
echo "    admin / admin123"
echo ""
