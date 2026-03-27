---
name: qa
description: Generate a manual QA checklist for a completed PRD. Use when user wants to verify a PRD implementation, create QA steps, or test acceptance criteria after the ralph loop completes.
---

# QA Checklist Generator

Generate a step-by-step manual QA checklist for a completed PRD.

## Process

1. Ask the user for the PRD GitHub issue number.

2. Fetch the PRD: `gh issue view <number>`

3. Fetch all child issues: `gh issue list --label "prd/<number>" --state all --json number,title,body,state`

4. For each child issue, read its acceptance criteria from the `## Acceptance criteria` section.

5. Produce a numbered, step-by-step QA checklist that a human can follow manually. For each step:
   - Reference which child issue and acceptance criterion it verifies
   - Include exact commands to run, URLs to visit, or payloads to send
   - Specify the expected output or behavior to observe
   - Note whether an automated test already covers this criterion

6. Group steps by child issue / feature area.

7. Print the checklist to stdout. Do NOT create files, issues, or PRs.
