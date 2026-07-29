# CLAUDE.md — Doormat Package Detector

## Project context
Doormat Package Detector — a physical AI hobby project.
- **Stack:** Python, YOLOv8 nano, OpenCV
- **Hardware:** Raspberry Pi 5 with a camera
- **Notifications:** Telegram and/or Pushover
- **User:** Beginner, zero prior coding experience, learning by doing.
  Explain what you're about to do in one plain sentence before doing it.

---

## API keys & secrets
- Never expose API keys, tokens, or secrets (Telegram bot token, Pushover key) in any committed file
- Always use a `.env` file for secrets, and verify `.env` is in `.gitignore` before any git operation
- Never print or log secrets to the console/terminal
- If any action could expose a secret, stop and warn with:
  `⚠️ SECURITY WARNING: [description] — do you want to proceed?`

---

## Git & GitHub
- "Local" means local files only — never `git add`, `git commit`, or `git push` unless explicitly told to "push to GitHub"
- Never auto-push or auto-deploy under any circumstances, even if a feature is complete
- When changes are ready, state the exact git commands to run and wait for confirmation

---

## Always do
- Write complete files, not partial snippets, unless a diff is explicitly requested
- State in one sentence what you're about to do before writing any code
- Handle errors explicitly — explain in plain English what an error means before fixing it
- Check if a Python package is already installed before installing a new one
- When installing a package, state which version it installed
- Keep a running `session-log.md` noting what was built and any key decisions

## Never do
- Leave debug print statements in once something works
- Leave dead or commented-out code
- Duplicate logic — if something will be reused (like a notification function), pull it into its own function
- Build for hypothetical future hardware/features beyond what was asked for today

## Flag but don't auto-fix
- If there's a simpler way to do something asked for, flag it with:
  `💡 SIMPLER APPROACH: [description] — want me to use this instead?`

---

## Automatic CLAUDE.md updates
After every major feature or significant change, automatically update this file (no need to ask first) with:
- **What changed** — plain-English description
- **Why** — the reason/decision behind it
- **Files changed** — list of files touched
- **New env vars** — if any were added to `.env`
- **New dependencies** — package name + version installed
- **Current build status checklist** — what's working, what's not, what's next

Add entries under the **Update Log** below, newest at the bottom. Keep `session-log.md` for day-to-day narration; keep this file's log focused on durable decisions and current state so a future session can get oriented fast.

## Session log
- Maintain `session-log.md` in the project root
- After each session (or whenever meaningful progress is made), append an entry automatically — no need to ask first
- Format: timestamped heading, then short bullets (not essay-style) covering:
  - What was built
  - What broke
  - How it was debugged/fixed
  - Current status
- Keep entries skimmable — this file gets pasted back to the user for quick review

## LinkedIn moments log
- Maintain `linkedin-moments.md` in the project root
- Trigger loosely, by intent, not by exact keyword — any message where the user is clearly asking to save something as a LinkedIn-worthy moment (e.g. "LinkedIn moment:", "add this to our LinkedIn md", "log this as a potential LinkedIn post", or similar phrasing in plain English) should trigger this
- On trigger: create `linkedin-moments.md` if it doesn't exist, then append the moment as a new bullet at the bottom with today's date
- Format: `- YYYY-MM-DD: one or two terse lines, not a paragraph`
- Never rewrite or edit past entries — only append
- After logging, confirm briefly — don't ask follow-up questions

---

## Build status checklist
- [ ] Project environment set up (Python, dependencies)
- [ ] `.env` and `.gitignore` configured
- [ ] Camera capture working
- [ ] YOLOv8 nano detection working
- [ ] Package/delivery event logic defined
- [ ] Telegram notification working
- [ ] Pushover notification working
- [ ] Running reliably on Raspberry Pi 5

---

## Update Log
### 2026-07-03 — Project initialized
- What: Created project CLAUDE.md with rules for secrets, git behavior, code quality, and communication style.
- Why: Establish ground rules before any code is written, since user is a beginner and wants consistent guardrails.
- Files changed: CLAUDE.md
- New env vars: none
- New dependencies: none
