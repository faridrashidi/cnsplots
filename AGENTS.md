# AGENTS.md

## Working branch rules

- Never work directly on `main`.
- If starting new work, create and switch to a new branch from `main` named `feature/<short-name>`.
- If already on the intended feature branch, continue there unless explicitly told to create a new branch.
- Do not rename or delete branches unless explicitly asked.
- Do not use `gh` to create branches; use `git`.

## Implementation rules

- Follow the smallest-change approach that fully solves the task.
- Do not make unrelated refactors or opportunistic cleanup unless explicitly asked.
- Ask before:
  - adding or removing dependencies
  - changing CI, build, release, or deployment files
  - modifying infrastructure, secrets, or environment configuration
  - running destructive commands

## Validation rules

- Before opening a pull request, run:
  - `make test`
  - `make lint`
- If either command fails:
  - fix the issue when it is clearly in scope
  - otherwise stop and report the failure clearly
- Do not claim tests passed unless they were actually run successfully.

## Commit rules

- Keep commits small and messages clear.
- Prefer a single commit for a small, self-contained change.
- For larger work, use multiple logical commits rather than one large commit.
- Do not amend, squash, or rewrite existing commits unless explicitly asked.

## Commit subject format

- Each commit subject line must use the format `<emoji> <subject>`.
- Use a Unicode Gitmoji, not a shortcode.
- Do not add a scope, colon, body, or trailing period.
- Base the subject only on the staged diff.
- Do not infer intent from unstaged files, branch names, task titles, or unrelated context.
- Prefer the smallest accurate claim.
- When multiple edits exist, describe only the dominant change.
- Write in imperative mood.
- Capitalize the first word unless syntax or style requires otherwise.
- Keep the subject under 72 characters.

## Allowed Gitmoji choices

- ✨ feature
- 🐛 bug fix
- ♻️ refactor
- 📝 docs or text
- ✅ tests
- 🔧 config or tooling
- ⬆️ upgrade dependencies
- ⬇️ downgrade dependencies
- ➕ add dependency
- ➖ remove dependency
- 🔥 remove code or files
- 🚚 move or rename
- 💄 UI or style
- 🚨 lint or warnings
- ⚡️ performance
- 👷 CI or build
- 🔒️ security

## Gitmoji tie-break rules

- Choose 🐛 or ✨ over ♻️ when the main intent is a fix or feature.
- Use dependency emojis only for dependency-only diffs.
- Use 🔧 for config-only or tooling-only diffs.
- Use ✅ only when the change is primarily test-related.
- Use 📝 only when the change is primarily documentation or text-related.

## Pull request rules

- Use `gh pr create`.
- Base branch must be `main`.
- Open the first pull request as a draft unless explicitly told otherwise.
- Push the branch before creating the pull request.
- PR title must use the format `<emoji> <subject>`.
- Use a Unicode Gitmoji, not a shortcode.
- Do not add a scope, colon, body, or trailing period.
- Base the PR title on the overall diff against `main`, not only the staged diff.
- Prefer the smallest accurate claim and describe only the dominant change in the pull request.
- Write in imperative mood.
- Capitalize the first word unless syntax or style requires otherwise.
- Keep the title under 72 characters.
- Use the same allowed Gitmoji choices and tie-break rules as commit subjects.
- PR body must include:
  - what changed
  - how it was tested
  - any risks or follow-ups
