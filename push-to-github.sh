#!/bin/bash
# ==============================================================================
# lvbathrooms — one-shot push to GitHub
# ==============================================================================
#
# Usage:
#   1. Unzip lvbathrooms-full-package.zip somewhere (e.g. ~/Projects/).
#   2. Copy this script into the unzipped lvbathrooms/ folder.
#   3. From Terminal: cd ~/Projects/lvbathrooms && bash push-to-github.sh
#
# What this does:
#   - Verifies prerequisites (git, gh CLI, authenticated)
#   - Initialises a git repo in the current folder
#   - Creates MPB-Group/lvbathrooms as a private repo on GitHub
#   - Commits and pushes everything on 'main' branch
#
# What this does NOT do:
#   - Anything irreversible without your confirmation
#   - Anything with Cloudflare (separate step — see DEPLOY.md)
#   - DNS changes
# ==============================================================================

set -e  # exit on any error

REPO_NAME="lvbathrooms"
REPO_ORG="MPB-Group"
REPO_VISIBILITY="private"  # change to "public" if you want

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " Bathrooms by LV — one-shot push to GitHub"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ---- Prerequisites ----------------------------------------------------------

# 1. git
if ! command -v git >/dev/null 2>&1; then
  echo "❌ git is not installed."
  echo "   Install with: xcode-select --install  (macOS)"
  exit 1
fi

# 2. gh (GitHub CLI)
if ! command -v gh >/dev/null 2>&1; then
  echo "❌ GitHub CLI (gh) is not installed."
  echo "   Install with: brew install gh"
  echo "   Then run: gh auth login  (and follow the browser prompts)"
  exit 1
fi

# 3. gh auth status
if ! gh auth status >/dev/null 2>&1; then
  echo "❌ GitHub CLI is installed but not logged in."
  echo "   Run: gh auth login  (and follow the browser prompts)"
  exit 1
fi

# 4. we're in the right folder
if [ ! -f "README.md" ] || [ ! -d "site" ]; then
  echo "❌ This doesn't look like the lvbathrooms folder."
  echo "   Expected to see README.md + site/ in the current directory."
  echo "   cd into the unzipped lvbathrooms folder and run this again."
  exit 1
fi

echo "✓ git: $(git --version | head -1)"
echo "✓ gh:  $(gh --version | head -1)"
echo "✓ authenticated as: $(gh api user --jq .login)"
echo "✓ running from $(pwd)"
echo ""

# ---- Confirmation prompt ----------------------------------------------------

echo "About to do the following:"
echo "  1. Initialise a git repo in $(pwd)"
echo "  2. Create $REPO_ORG/$REPO_NAME as a $REPO_VISIBILITY GitHub repo"
echo "  3. Add all files, commit them, and push to main"
echo ""
read -p "Proceed? (y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

# ---- Git init (only if not already a repo) ----------------------------------

if [ -d ".git" ]; then
  echo "→ git repo already initialised here, reusing"
else
  echo "→ git init"
  git init -b main
fi

# ---- .gitignore at the repo root (separate from site/.gitignore) ------------

if [ ! -f ".gitignore" ]; then
  cat > .gitignore <<'GITIGNORE'
# Node + build output (inside site/)
site/node_modules/
site/_site/
.DS_Store
*.log
.env
GITIGNORE
  echo "→ wrote repo-root .gitignore"
fi

# ---- Stage + commit ---------------------------------------------------------

echo "→ staging files..."
git add -A

# Configure a default author if not set (gh CLI's login is used)
if [ -z "$(git config user.email)" ]; then
  EMAIL=$(gh api user --jq .email 2>/dev/null || echo "")
  NAME=$(gh api user --jq .name 2>/dev/null || gh api user --jq .login)
  [ -n "$EMAIL" ] && git config user.email "$EMAIL"
  [ -n "$NAME" ]  && git config user.name  "$NAME"
fi

git commit -m "Initial commit: Bathrooms by LV rebuild from WordPress

- 11ty static site in site/
- 7 pages migrated (home, 3 services, contact, projects index, privacy)
- 18 project case studies in site/src/projects/
- 178 images in site/public/images/
- SEO metadata preserved from Yoast
- Cloudflare Pages config (wrangler.toml, _redirects, sitemap.xml)
- Migration docs in docs/ and reference content in content/
"

# ---- Create GitHub repo -----------------------------------------------------

# Does the repo already exist?
if gh repo view "$REPO_ORG/$REPO_NAME" >/dev/null 2>&1; then
  echo ""
  echo "⚠  $REPO_ORG/$REPO_NAME already exists on GitHub."
  echo "   Not recreating. Adding it as the 'origin' remote and pushing."
  if ! git remote get-url origin >/dev/null 2>&1; then
    git remote add origin "git@github.com:$REPO_ORG/$REPO_NAME.git"
  fi
else
  echo "→ creating $REPO_ORG/$REPO_NAME on GitHub ($REPO_VISIBILITY)"
  gh repo create "$REPO_ORG/$REPO_NAME" \
    --"$REPO_VISIBILITY" \
    --source=. \
    --remote=origin \
    --description "Bathrooms by LV — static site rebuilt from WordPress"
fi

# ---- Push -------------------------------------------------------------------

echo "→ pushing..."
git push -u origin main

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " ✓ Done!"
echo ""
echo " Repo:   https://github.com/$REPO_ORG/$REPO_NAME"
echo ""
echo " Next step: set up Cloudflare Pages — see DEPLOY.md in this folder"
echo " or tell Claude you're ready and he'll drive the browser with you."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
