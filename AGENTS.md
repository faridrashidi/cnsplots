# AGENTS.md

## Repository expectations

- Never work directly on `main`; always create a feature branch first.
- Create a new branch named feature/<short-name> from main.
- Run tests and lint before opening a pull request.
- Keep commits small and messages clear using gitmoji style.
- Open the first PR as a draft unless I say otherwise.
- Ask before adding dependencies, changing CI, or touching deployment files.

## Pull request expectations

- Use `gh pr create`.
- Base branch: `main`.
- PR body should include:
  - what changed
  - how it was tested
  - any risks or follow-ups

## Commit message and PR title format expectations

- Generate exactly one commit subject line in the format '<emoji> <subject>'.
- Use a Unicode Gitmoji, not shortcode, and do not add a scope, colon, body, or trailing period.
- Base the message only on the staged diff. Do not invent intent from unstaged files, branch names, or unrelated context.
- Prefer the smallest accurate claim and describe only the dominant change when multiple edits are present.
- Write the subject in imperative mood, capitalize the first word unless style or syntax requires otherwise, and keep it under 72 characters.
- Use only these Gitmoji choices: ✨ feature, 🐛 bug, ♻️ refactor, 📝 docs or text, ✅ tests, 🔧 config or tooling, ⬆️ upgrade dependencies, ⬇️ downgrade dependencies, ➕ add dependency, ➖ remove dependency, 🔥 remove code or files, 🚚 move or rename, 💄 UI or style, 🚨 lint or warnings, ⚡️ performance, 👷 CI or build, 🔒️ security.
- Tie-break rules: choose 🐛 or ✨ over ♻️ when the main intent is a fix or feature, use dependency emojis for dependency-only diffs, and use 🔧 for config-only changes.
