# AGENTS.md

## Working branch rules

- Never work directly on `main`.
- If starting new work, create and switch to a new branch from `main` named `<type>/<short-name>` such as `feature/<short-name>`, `bugfix/<short-name>`, `docs/<short-name>`, `refactor/<short-name>`, or `chore/<short-name>`.
- If already on the intended work branch, continue there unless explicitly told to create a new branch.
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

## Gitmoji rules

A gitmoji commit message is composed using the following pieces:

- **intention**: The intention you want to express with the commit, using an emoji from the gitmoji list. In unicode format.
- **message**: A brief explanation of the change.

### Format

```
<intention> <message>

[optional body]
```

### Reference

Fetch all available gitmojis from: https://gitmoji.dev/api/gitmojis.

### Selecting the correct emoji

1. **Identify the primary purpose** of the commit
2. **Choose the most specific emoji** that matches the change
3. **Use only one emoji** per commit for clarity
4. **Prioritize by impact**: Breaking changes (💥) > Features (✨) > Fixes (🐛) > Refactoring (♻️)

### Examples

```
✨ Add user authentication system

Implement JWT-based authentication with login and registration endpoints.
Closes #123
```

```
🐛 Resolve null pointer exception in user service

Added null check before accessing user properties to prevent crashes.
```

```
📝 Update installation instructions

Added step-by-step guide for setting up the development environment.
```

```
⚡️ Optimize user query with indexing

Reduced query time from 500ms to 50ms by adding composite index.
```

```
💥 Update API response format to REST specification

All API endpoints now return data in a standardized envelope format.
Clients must update their response parsing logic.
```

### Best Practices

1. **Be atomic**: One emoji, one purpose, one commit
2. **Write clear subjects**: Keep under 60 characters, imperative mood
3. **Use the body**: Explain "why" not "what" for complex changes
4. **Reference issues**: Include issue numbers when applicable
5. **Indicate breaking changes**: Use 💥.

## Pull request rules

- Use `gh pr create`.
- When creating a PR, add exactly one release label with `gh pr create --label <label>`.
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
- Do not add a scope, colon, body, or trailing period.
- Base the PR title on the overall diff against `main`, not only the staged diff.
- Prefer the smallest accurate claim and make the PR title more specific than the commit subject by naming the dominant change and affected area or behavior in a single phrase.
- Write in imperative mood.
- Capitalize the first word unless syntax or style requires otherwise.
- Keep the title under 72 characters.
- Use the same allowed Gitmoji choices and tie-break rules as commit subjects.
- PR body must include:
  - what changed
  - how it was tested
  - any risks or follow-ups
