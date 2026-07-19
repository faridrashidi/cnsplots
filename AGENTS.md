# AGENTS.md

Use this file as the repo-specific operating manual for branch, validation, commit, and pull request behavior. When two rules appear to overlap, follow the more specific rule.

## Working branch rules

- Never work directly on `main`.
- If starting new work, create and switch to a new branch from `main` named `<type>/<short-name>` such as `feature/<short-name>`, `bugfix/<short-name>`, `docs/<short-name>`, `refactor/<short-name>`, or `chore/<short-name>`.
- If you discover local changes while on `main`, create the new branch first and continue the work there.
- If already on the intended work branch, continue there unless explicitly told to create a new branch.
- Do not rename or delete branches unless explicitly asked.
- Do not use `gh` to create branches; use `git`.

## Implementation rules

- Follow the smallest-change approach that fully solves the task.
- Keep the diff scoped to the task at hand. If you notice a separate issue, mention it instead of bundling it into the same change.
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
- Run validation after the proposed changes are in place so the results match the branch you plan to submit.
- If either command fails:
  - fix the issue when it is clearly in scope
  - otherwise stop and report the failure clearly, including which command failed
- Do not claim tests passed unless they were actually run successfully.

## Commit rules

- Keep commits small and messages clear.
- Prefer a single commit for a small, self-contained change.
- For larger work, use multiple logical commits rather than one large commit.
- Do not amend, squash, or rewrite existing commits unless explicitly asked.
- Each commit message must start with `<emoji> <subject>`.
- Use a Unicode Gitmoji, not a shortcode.
- In the subject line, do not add a scope, colon, or trailing period.
- Base the subject only on the staged diff.
- Do not infer intent from unstaged files, branch names, task titles, or unrelated context.
- Prefer the smallest accurate claim.
- When multiple edits exist, describe only the dominant change.
- Write in imperative mood.
- Capitalize the first word unless syntax or style requires otherwise.
- For subject use at most five words, excluding the emoji.
- Add a body only when it meaningfully explains why, highlights follow-up work, or calls out a breaking change.
- If you add a body, leave one blank line after the subject and keep the body concise.

## Gitmoji rules

Use one Gitmoji to communicate the primary intent of a commit or pull request title. Choose the emoji for the dominant change, not every kind of edit in the diff.

### Repo format

This repository uses:

```
<emoji> <subject>

[optional body]
```

- The subject line is required.
- The body is optional.
- This repository intentionally uses a space after the emoji instead of the scoped `emoji(scope):` style you may see in other Gitmoji examples.
- The full Gitmoji catalog is available at: https://gitmoji.dev/api/gitmojis.

### Selecting the correct emoji

1. **Identify the primary purpose** of the staged diff for a commit, or of the full diff against `main` for a pull request title
2. **Choose the most specific emoji** that matches that dominant change
3. **Use only one emoji** for clarity
4. **Prioritize by impact** when several fit: Breaking changes (💥) > Features (✨) > Fixes (🐛) > Refactoring (♻️)
5. **Prefer purpose-specific emojis** over broad fallbacks when the diff is clearly dominated by one type of work

### Examples

```
📝 Clarify pull request label rules
```

```
🐛 Prevent crash when input data is empty
```

```
♻️ Simplify plot configuration parsing
```

```
💥 Remove legacy export format

Clients must switch to the new export path before upgrading.
```

### Best practices

1. **Be atomic**: one emoji, one purpose, one commit
2. **Write clear subjects**: keep them imperative and specific
3. **Use the body for context**: explain why, risk, or follow-up work when needed
4. **Reference issues when helpful**: include issue numbers when they add useful context
5. **Use 💥 for breaking changes**: make the impact explicit in the body when applicable

## Pull request rules

- Use `gh pr create`.
- When creating a PR, add exactly one release label with `gh pr create --label <label>`.
- Choose the release label from the overall diff against `main`, not from the most recent commit alone.
- Use the release label that matches the dominant change:
  - `bug` for bug fixes
  - `enhancement` for user-facing features or improvements
  - `documentation` for documentation or text-only changes
  - `maintenance` for internal chores, tooling, config, or refactors
  - `ignore-for-release` only when the PR should be excluded from release notes
- Base branch must be `main`.
- Open the first pull request as a draft unless explicitly told otherwise.
- Push the branch before creating the pull request.
- PR title must use the format `<emoji> <descriptive subject>`.
- Use a Unicode Gitmoji, not a shortcode.
- In the title line, do not add a scope, colon, or trailing period.
- Base the PR title on the overall diff against `main`, not only the staged diff.
- Prefer the smallest accurate claim and make the PR title more specific than the commit subject by naming the dominant change and affected area or behavior in a single phrase.
- Write in imperative mood.
- Capitalize the first word unless syntax or style requires otherwise.
- For title use at most five words, excluding the emoji.
- Use the same Gitmoji selection and tie-break rules as commit subjects.
- Use the same `<emoji> <subject>` format as commit subjects.
- PR body must include:
  - what changed
  - how it was tested
  - any risks or follow-ups
