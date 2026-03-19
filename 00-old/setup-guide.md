# MacroSnaps - GitHub + Claude Code Setup Guide

## What's in the repo package

I've organized all your files into a clean repo structure:

```
macrosnaps-repo/
  .gitignore          <- excludes .env, __pycache__, .DS_Store, backups, etc.
  .env.example         <- template for API keys
  CLAUDE.md            <- project context file (Claude Code reads this automatically)
  README.md            <- project overview
  glossary/            <- 6 JSON files (source of truth)
    macro.json
    credit.json
    equity.json
    fx.json
    trade.json
    institutions.json
  backend/             <- Flask API + data pipeline (all your Python files)
    api.py
    init_database.py
    models/
    services/          <- 9 fetcher/loader pairs + Claude service
    utils/
    migrations/
  frontend/            <- the HTML prototype
    macrosnaps-globe.html
  docs/                <- handover documentation
    handover-session7.md
```

Backup files (`.backup`) and `__pycache__` are excluded.

---

## Step 1: Create the GitHub repo

1. Go to https://github.com/new
2. Repository name: `macrosnaps` (or whatever you prefer)
3. Set to **Private**
4. Do NOT initialize with README (we already have one)
5. Click "Create repository"
6. Copy the repo URL (e.g. `https://github.com/yourusername/macrosnaps.git`)

---

## Step 2: Push the repo from your Mac

Download the `macrosnaps-repo.tar.gz` file I've prepared, then in Terminal:

```bash
# Extract the repo
cd ~/Desktop    # or wherever you downloaded it
tar -xzf macrosnaps-repo.tar.gz
cd macrosnaps-repo

# Initialize git and push
git init
git add .
git commit -m "Initial commit: glossary JSONs, backend, frontend prototype, docs"
git branch -M main
git remote add origin https://github.com/YOURUSERNAME/macrosnaps.git
git push -u origin main
```

Replace `YOURUSERNAME` with your actual GitHub username.

If you haven't used git on this Mac before, you may need to authenticate. GitHub will prompt you to either sign in via browser or create a personal access token (Settings > Developer settings > Personal access tokens > Fine-grained tokens).

---

## Step 3: Install Claude Code

The npm method in your handover notes is now deprecated. Anthropic recommends the **native installer** - no Node.js required.

### On macOS (recommended method):

```bash
# Option A: Native installer (recommended)
curl -fsSL https://code.claude.com/install | sh

# Option B: Homebrew
brew install claude-code
```

Verify it installed:

```bash
claude --version
```

### Authentication

Claude Code can authenticate via:
- **Claude Pro or Max plan** (recommended if you already subscribe to Claude) - just log in with your Claude.ai account
- **Anthropic Console** - go to console.anthropic.com, set up billing, then authenticate via OAuth

When you first run `claude`, it will walk you through the auth flow.

---

## Step 4: Connect Claude Code to the repo

```bash
cd ~/Desktop/macrosnaps-repo    # or wherever the repo lives
claude
```

Claude Code will automatically read the `CLAUDE.md` file at the project root. This file contains the full glossary schema, project structure, voice/style rules, and enrichment instructions - so Claude Code will immediately understand the project context.

---

## Step 5: Test it

Once inside Claude Code, try the test from your handover notes:

```
> Add carry trade to the glossary
```

Claude Code should:
1. Read `CLAUDE.md` to understand the schema
2. Determine that "carry trade" belongs in `fx.json` (or `trade.json`)
3. Create a properly structured entry with bluf at 3 levels
4. Commit the change to git

You can also try:

```
> Enrich the "hawkish" entry in macro.json with full sections at all 3 levels
```

```
> Show me all thin entries in credit.json that need enrichment
```

---

## Step 6: Verify and push

After Claude Code makes changes:

```bash
git status          # see what changed
git diff            # review the changes
git push            # push to GitHub
```

Or you can ask Claude Code to handle git directly:

```
> Commit and push the changes you just made
```

---

## Troubleshooting

- **`claude: command not found`** - Run `claude doctor` or check that the install path is in your shell PATH
- **Permission errors with npm** - Don't use `sudo npm install`. Use the native installer instead
- **Git auth issues** - Create a personal access token at GitHub Settings > Developer settings > Personal access tokens

For the latest Claude Code docs: https://code.claude.com/docs/en/setup
