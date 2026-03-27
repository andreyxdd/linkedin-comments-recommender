---
name: prd-to-issues
description: Break a PRD into independently-grabbable GitHub issues using tracer-bullet vertical slices. Use when user wants to convert a PRD to issues, create implementation tickets, or break down a PRD into work items.
---

# PRD to Issues

Break a PRD into independently-grabbable GitHub issues using vertical slices (tracer bullets).

## Process

### 1. Locate the PRD

Ask the user for the PRD GitHub issue number (or URL).

If the PRD is not already in your context window, fetch it with `gh issue view <number>` (with comments).

### 2. Explore the codebase (optional)

If you have not already explored the codebase, do so to understand the current state of the code.

### 3. Draft vertical slices

Break the PRD into **tracer bullet** issues. Each issue is a thin vertical slice that cuts through ALL integration layers end-to-end, NOT a horizontal slice of one layer.

Slices may be 'HITL' or 'AFK'. HITL slices require human interaction, such as an architectural decision or a design review. AFK slices can be implemented and merged without human interaction. Prefer AFK over HITL where possible.

AFK slices may additionally be flagged for code review with the `needs-review` label. This tells the ralph loop to route the issue through the branch/PR/review flow instead of committing directly to main. Auto-assign `needs-review` to any AFK slice that touches security-sensitive areas. See the heuristics below.

<vertical-slice-rules>
- Each slice delivers a narrow but COMPLETE path through every layer (schema, API, UI, tests)
- A completed slice is demoable or verifiable on its own
- Prefer many thin slices over few thick ones
</vertical-slice-rules>

<needs-review-heuristics>
Auto-assign the `needs-review` label to any AFK slice that involves ANY of the following:

- **Authentication or sessions**: login, logout, session management, token handling, OAuth, SSO
- **Authorization**: role checks, permission gates, ownership validation, access control
- **Database migrations or schema changes**: new tables, column changes, index modifications
- **Cryptographic operations**: hashing, encryption, signing, key management
- **Secret or credential handling**: API keys, environment variables, token storage
- **User-uploaded content or file handling**: uploads, downloads, signed URLs, storage paths
- **PII or sensitive data**: email, phone, address, payment info, personal identifiers
- **Security headers or middleware**: CORS, CSP, CSRF, rate limiting, X-Frame-Options
- **Infrastructure or deployment config**: Docker, CI/CD, deploy scripts, environment config
- **Third-party API integrations**: external service calls that handle auth or sensitive data
- **High blast radius**: changes that touch 3+ modules/packages or affect shared interfaces, utilities, or types used across the codebase — where a subtle bug would cascade

These heuristics are derived from `.claude/security.md` and general risk assessment. When in doubt, flag for review — false positives are cheap, false negatives are not.

Do NOT assign `needs-review` to HITL slices (they are human-driven by definition).
</needs-review-heuristics>

### 4. Quiz the user

Present the proposed breakdown as a numbered list. For each slice, show:

- **Title**: short descriptive name
- **Type**: HITL / AFK
- **Code review**: Yes / No (for AFK slices only; show rationale if Yes)
- **Blocked by**: which other slices (if any) must complete first
- **User stories covered**: which user stories from the PRD this addresses

Apply the `<needs-review-heuristics>` above to auto-assign code review flags. Show your rationale for each flagged slice (e.g., "touches auth middleware", "adds DB migration").

Ask the user:

- Does the granularity feel right? (too coarse / too fine)
- Are the dependency relationships correct?
- Should any slices be merged or split further?
- Are the correct slices marked as HITL and AFK?
- Do the code review flags look right? (any to add or remove?)

Iterate until the user approves the breakdown.

### 5. Create the GitHub issues

For each approved slice, create a GitHub issue using `gh issue create` with the following labels:

- `--label "prd/<PRD-issue-number>"` — links the child to its parent PRD
- `--label "afk"` for AFK slices, or `--label "hitl"` for HITL slices
- `--label "needs-review"` for AFK slices flagged for code review

Example: `gh issue create --title "<title>" --body "<body>" --label "prd/13" --label "afk" --label "needs-review"`

Create issues in dependency order (blockers first) so you can reference real issue numbers in the "Blocked by" field.

<issue-template>
## Parent PRD

#<prd-issue-number>

## What to build

A concise description of this vertical slice. Describe the end-to-end behavior, not layer-by-layer implementation. Reference specific sections of the parent PRD rather than duplicating content.

## Acceptance criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Blocked by

IMPORTANT: Use this exact single-line format. Do NOT omit the "Blocked by:" prefix.

Blocked by: #X, #Y

Or if no blockers:

Blocked by: none

## User stories addressed

Reference by number from the parent PRD:

- User story 3
- User story 7

</issue-template>

Do NOT close or modify the parent PRD issue.
