# CLAUDE.md

This file describes project-specific conventions and pitfalls that agents must follow.

## References

- Refer to `.claude/security.md` for security rules.
- Use conventional commit messages format: https://www.conventionalcommits.org/en/v1.0.0/
- Default implementation approach: use the `/tdd` skill for test-driven development.

## Project Technical Docs

List the local source-of-truth docs for architecture and operations.

Example:

- `docs/architecture.md`
- `docs/deployment.md`
- `docs/ci-cd.md`
- `docs/database.md`

## Rule

If technical decisions change, update the relevant docs in the same PR/commit so code and docs do not drift.
