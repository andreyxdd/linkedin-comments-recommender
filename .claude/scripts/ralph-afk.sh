#!/usr/bin/env bash
#
# ralph-afk.sh - Unattended PRD execution loop (profile-aware)
#
# Usage:
#   ./ralph-afk.sh <prd-issue-number> <max-iterations> [--review]
#   ./ralph-afk.sh --reset <prd-issue-number>
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
PROGRESS_FILE="${CLAUDE_DIR}/ralph-progress.json"
CONFIG_FILE="${CLAUDE_DIR}/ralph.json"
DEFAULT_PROFILE_FILE="${CLAUDE_DIR}/overrides/profile.env"
PROFILE_FILE="${RALPH_PROFILE_FILE:-${DEFAULT_PROFILE_FILE}}"

if [[ -f "${PROFILE_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${PROFILE_FILE}"
fi

RALPH_BASE_BRANCH="${RALPH_BASE_BRANCH:-main}"
RALPH_PRD_LABEL_PREFIX="${RALPH_PRD_LABEL_PREFIX:-prd}"
RALPH_AFK_LABEL="${RALPH_AFK_LABEL:-afk}"
RALPH_HITL_LABEL="${RALPH_HITL_LABEL:-hitl}"
RALPH_NEEDS_REVIEW_LABEL="${RALPH_NEEDS_REVIEW_LABEL:-needs-review}"
MAX_REVIEW_ATTEMPTS="${RALPH_MAX_REVIEW_ATTEMPTS:-3}"

render_template() {
  local text="$1"
  local issue="${2:-}"
  local pr="${3:-}"
  local repo="${4:-}"
  text="${text//\{\{issue\}\}/${issue}}"
  text="${text//\{\{pr\}\}/${pr}}"
  text="${text//\{\{repo\}\}/${repo}}"
  text="${text//\{\{base_branch\}\}/${RALPH_BASE_BRANCH}}"
  printf "%s" "${text}"
}

default_implement_cmd() {
  cat <<EOF
docker sandbox run claude -- -p "Implement GitHub issue #{{issue}} in this repository ({{repo}}).

## Instructions
1. Read issue #{{issue}} and implement all acceptance criteria.
2. Stay on current branch (${RALPH_BASE_BRANCH}); do not create a new branch.
3. Follow .claude/CLAUDE.md and .claude/security.md if present.
4. Commit with conventional commit format and include: Closes #{{issue}}." --allowedTools "Bash,Read,Edit,Write,Glob,Grep,Agent"
EOF
}

default_implement_pr_cmd() {
  cat <<EOF
docker sandbox run claude -- -p "Implement GitHub issue #{{issue}} in this repository ({{repo}}).

## Instructions
1. Read issue #{{issue}} and implement all acceptance criteria.
2. Create and use branch issue-{{issue}}.
3. Commit and push branch.
4. Open PR targeting ${RALPH_BASE_BRANCH} with body containing: Closes #{{issue}}.
5. Follow .claude/CLAUDE.md and .claude/security.md if present." --allowedTools "Bash,Read,Edit,Write,Glob,Grep,Agent"
EOF
}

default_review_cmd() {
  cat <<EOF
docker sandbox run claude -- -p "Review PR #{{pr}} in repository {{repo}} against issue #{{issue}}." --agent code-reviewer --allowedTools "Bash,Read,Glob,Grep"
EOF
}

default_fix_pr_cmd() {
  cat <<EOF
docker sandbox run claude -- -p "PR #{{pr}} in repository {{repo}} has review feedback for issue #{{issue}}. Read comments, apply changes, commit, and push." --allowedTools "Bash,Read,Edit,Write,Glob,Grep,Agent"
EOF
}

RALPH_IMPLEMENT_CMD="${RALPH_IMPLEMENT_CMD:-$(default_implement_cmd)}"
RALPH_IMPLEMENT_PR_CMD="${RALPH_IMPLEMENT_PR_CMD:-$(default_implement_pr_cmd)}"
RALPH_REVIEW_CMD="${RALPH_REVIEW_CMD:-$(default_review_cmd)}"
RALPH_FIX_PR_CMD="${RALPH_FIX_PR_CMD:-$(default_fix_pr_cmd)}"

if [[ "${1:-}" == "--reset" ]]; then
  if [[ -z "${2:-}" ]]; then
    echo "Usage: $0 --reset <prd-issue-number>"
    exit 1
  fi
  if [[ -f "${PROGRESS_FILE}" ]]; then
    existing_prd="$(jq -r '.prd_issue' "${PROGRESS_FILE}" 2>/dev/null || echo "")"
    if [[ "${existing_prd}" == "${2}" ]]; then
      rm "${PROGRESS_FILE}"
      echo "Progress cleared for PRD #${2}."
    else
      echo "Progress file is for PRD #${existing_prd}, not #${2}. No action taken."
    fi
  else
    echo "No progress file found."
  fi
  exit 0
fi

if [[ -z "${1:-}" || -z "${2:-}" ]]; then
  echo "Usage: $0 <prd-issue-number> <max-iterations> [--review]"
  echo "       $0 --reset <prd-issue-number>"
  exit 1
fi

PRD_ISSUE="$1"
ITERATIONS="$2"
REVIEW_ALL=false
[[ "${3:-}" == "--review" ]] && REVIEW_ALL=true
REPO="$(gh repo view --json nameWithOwner -q '.nameWithOwner')"

if [[ -f "${CONFIG_FILE}" ]]; then
  TEST_CMD="$(jq -r '.test_cmd // empty' "${CONFIG_FILE}")"
  BUILD_CMD="$(jq -r '.build_cmd // empty' "${CONFIG_FILE}")"
else
  echo "WARNING: ${CONFIG_FILE} not found. Test gate disabled for direct-to-${RALPH_BASE_BRANCH} flow."
  TEST_CMD=""
  BUILD_CMD=""
fi

acquire_lock() {
  if [[ -f "${PROGRESS_FILE}" ]]; then
    existing_pid="$(jq -r '.pid // empty' "${PROGRESS_FILE}" 2>/dev/null || echo "")"
    if [[ -n "${existing_pid}" ]] && kill -0 "${existing_pid}" 2>/dev/null; then
      echo "ERROR: Another ralph instance (PID ${existing_pid}) is running."
      echo "If stale, run: $0 --reset ${PRD_ISSUE}"
      exit 1
    fi
  fi
}

init_progress() {
  cat > "${PROGRESS_FILE}" <<EOF
{
  "prd_issue": ${PRD_ISSUE},
  "max_iterations": ${ITERATIONS},
  "iterations_completed": 0,
  "review_all": ${REVIEW_ALL},
  "current_issue": null,
  "current_state": "idle",
  "current_pr": null,
  "completed_issues": [],
  "pid": $$,
  "started_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "last_updated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
}

read_progress() {
  [[ -f "${PROGRESS_FILE}" ]] || return 1
  file_prd="$(jq -r '.prd_issue' "${PROGRESS_FILE}")"
  if [[ "${file_prd}" != "${PRD_ISSUE}" ]]; then
    echo "ERROR: Progress file is for PRD #${file_prd}, not #${PRD_ISSUE}."
    exit 1
  fi
  return 0
}

update_progress_json() {
  local expr="$1"
  local tmp="${PROGRESS_FILE}.tmp"
  jq "${expr} | .last_updated = \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\" | .pid = $$" "${PROGRESS_FILE}" > "${tmp}" && mv "${tmp}" "${PROGRESS_FILE}"
}

set_progress_num() {
  local field="$1"
  local value="$2"
  update_progress_json ".${field} = ${value}"
}

set_progress_str() {
  local field="$1"
  local value="$2"
  local tmp="${PROGRESS_FILE}.tmp"
  jq --arg v "${value}" ".${field} = \$v | .last_updated = \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\" | .pid = $$" "${PROGRESS_FILE}" > "${tmp}" && mv "${tmp}" "${PROGRESS_FILE}"
}

add_completed_issue() {
  local issue_num="$1"
  update_progress_json ".completed_issues += [${issue_num}] | .completed_issues |= unique"
}

get_progress_field() {
  jq -r ".${1}" "${PROGRESS_FILE}"
}

get_progress_num() {
  jq ".${1}" "${PROGRESS_FILE}"
}

run_cmd_template() {
  local template="$1"
  local issue="$2"
  local pr="${3:-}"
  local rendered
  rendered="$(render_template "${template}" "${issue}" "${pr}" "${REPO}")"
  eval "${rendered}"
}

find_next_issue() {
  local issues body blocked_line blockers all_closed bstate
  issues="$(gh issue list --label "${RALPH_PRD_LABEL_PREFIX}/${PRD_ISSUE}" --label "${RALPH_AFK_LABEL}" --state open --json number -q '.[].number' | sort -n)"
  [[ -n "${issues}" ]] || { echo ""; return; }

  for num in ${issues}; do
    body="$(gh issue view "${num}" --json body -q '.body')"
    blocked_line="$(printf "%s\n" "${body}" | awk 'BEGIN{IGNORECASE=1} /^Blocked by:/{print; exit}')"

    if [[ -z "${blocked_line}" ]] || [[ "${blocked_line,,}" == *"none"* ]]; then
      echo "${num}"
      return
    fi

    blockers="$(printf "%s" "${blocked_line}" | grep -oE '#[0-9]+' | grep -oE '[0-9]+' || true)"
    all_closed=true
    for b in ${blockers}; do
      bstate="$(gh issue view "${b}" --json state -q '.state')"
      if [[ "${bstate}" == "OPEN" ]]; then
        all_closed=false
        break
      fi
    done
    if [[ "${all_closed}" == true ]]; then
      echo "${num}"
      return
    fi
  done

  echo ""
}

check_all_closed() {
  open_count="$(gh issue list --label "${RALPH_PRD_LABEL_PREFIX}/${PRD_ISSUE}" --state open --json number -q 'length')"
  [[ "${open_count}" -eq 0 ]]
}

check_hitl_blocker() {
  hitl_issues="$(gh issue list --label "${RALPH_PRD_LABEL_PREFIX}/${PRD_ISSUE}" --label "${RALPH_HITL_LABEL}" --state open --json number,title -q '.[] | "#\(.number): \(.title)"')"
  if [[ -n "${hitl_issues}" ]]; then
    printf "%s\n" "${hitl_issues}"
    return 0
  fi
  return 1
}

issue_needs_review() {
  local issue_num="$1"
  labels="$(gh issue view "${issue_num}" --json labels -q '.labels[].name')"
  printf "%s\n" "${labels}" | grep -qx "${RALPH_NEEDS_REVIEW_LABEL}"
}

should_review() {
  local issue_num="$1"
  [[ "${REVIEW_ALL}" == true ]] && return 0
  issue_needs_review "${issue_num}"
}

run_test_gate() {
  if [[ -n "${BUILD_CMD}" ]]; then
    echo " -> Running build gate: ${BUILD_CMD}"
    eval "${BUILD_CMD}" || { echo " -> BUILD FAILED."; return 1; }
  fi
  if [[ -n "${TEST_CMD}" ]]; then
    echo " -> Running test gate: ${TEST_CMD}"
    eval "${TEST_CMD}" || { echo " -> TESTS FAILED."; return 1; }
  fi
  return 0
}

implement_issue_main() {
  run_cmd_template "${RALPH_IMPLEMENT_CMD}" "$1"
}

implement_issue_pr() {
  run_cmd_template "${RALPH_IMPLEMENT_PR_CMD}" "$1"
}

review_pr() {
  run_cmd_template "${RALPH_REVIEW_CMD}" "$2" "$1"
}

fix_pr() {
  run_cmd_template "${RALPH_FIX_PR_CMD}" "$2" "$1"
}

handle_main_flow() {
  local issue_num="$1"
  set_progress_str "current_state" "test_gate"

  if ! run_test_gate; then
    set_progress_str "current_state" "failed"
    echo " -> Test gate failed for #${issue_num}. Fix and rerun."
    exit 1
  fi

  git push origin "${RALPH_BASE_BRANCH}"
  gh issue close "${issue_num}" --comment "Implemented and committed to ${RALPH_BASE_BRANCH}."
  add_completed_issue "${issue_num}"
  completed="$(get_progress_num "iterations_completed")"
  set_progress_num "iterations_completed" "$((completed + 1))"
  set_progress_str "current_state" "idle"
  set_progress_num "current_issue" "null"
  set_progress_num "current_pr" "null"
}

handle_review_flow() {
  local issue_num="$1"
  local pr_num="$2"

  set_progress_str "current_state" "reviewing"
  for ((attempt=1; attempt<=MAX_REVIEW_ATTEMPTS; attempt++)); do
    echo " -> Review attempt ${attempt}/${MAX_REVIEW_ATTEMPTS}"
    review_pr "${pr_num}" "${issue_num}"
    review_state="$(gh pr view "${pr_num}" --json reviewDecision -q '.reviewDecision')"
    if [[ "${review_state}" == "APPROVED" ]]; then
      break
    fi
    if [[ "${attempt}" -eq "${MAX_REVIEW_ATTEMPTS}" ]]; then
      set_progress_str "current_state" "failed"
      echo " -> PR #${pr_num} failed review."
      exit 1
    fi
    fix_pr "${pr_num}" "${issue_num}"
  done

  gh pr merge "${pr_num}" --squash --delete-branch
  gh issue close "${issue_num}" --comment "Implemented in PR #${pr_num}."
  add_completed_issue "${issue_num}"
  completed="$(get_progress_num "iterations_completed")"
  set_progress_num "iterations_completed" "$((completed + 1))"
  set_progress_str "current_state" "idle"
  set_progress_num "current_issue" "null"
  set_progress_num "current_pr" "null"
}

handle_resume() {
  issue_num="$(get_progress_num "current_issue")"
  state="$(get_progress_field "current_state")"
  pr_num="$(get_progress_field "current_pr")"
  [[ "${issue_num}" == "null" ]] && return 0

  gh_state="$(gh issue view "${issue_num}" --json state -q '.state')"
  if [[ "${gh_state}" == "CLOSED" ]]; then
    add_completed_issue "${issue_num}"
    set_progress_str "current_state" "idle"
    set_progress_num "current_issue" "null"
    set_progress_num "current_pr" "null"
    return 0
  fi

  case "${state}" in
    implementing)
      if should_review "${issue_num}"; then
        existing_pr="$(gh pr list --head "issue-${issue_num}" --json number -q '.[0].number' 2>/dev/null || true)"
        if [[ -z "${existing_pr}" ]]; then
          implement_issue_pr "${issue_num}"
          existing_pr="$(gh pr list --head "issue-${issue_num}" --json number -q '.[0].number')"
        fi
        set_progress_num "current_pr" "${existing_pr}"
        handle_review_flow "${issue_num}" "${existing_pr}"
      else
        implement_issue_main "${issue_num}"
        handle_main_flow "${issue_num}"
      fi
      ;;
    pr_created|reviewing)
      if [[ -z "${pr_num}" || "${pr_num}" == "null" ]]; then
        pr_num="$(gh pr list --head "issue-${issue_num}" --json number -q '.[0].number' 2>/dev/null || true)"
        [[ -n "${pr_num}" ]] || { set_progress_str "current_state" "failed"; exit 1; }
      fi
      handle_review_flow "${issue_num}" "${pr_num}"
      ;;
    test_gate)
      handle_main_flow "${issue_num}"
      ;;
    failed)
      set_progress_str "current_state" "implementing"
      handle_resume
      ;;
    *)
      set_progress_str "current_state" "idle"
      ;;
  esac
}

acquire_lock
if read_progress; then
  current_state="$(get_progress_field "current_state")"
  if [[ "${current_state}" != "idle" && "${current_state}" != "null" ]]; then
    echo "Resuming PRD #${PRD_ISSUE} from state: ${current_state}"
    handle_resume
  fi
else
  init_progress
fi

iterations_completed="$(get_progress_num "iterations_completed")"
start_iteration="$((iterations_completed + 1))"

for ((i=start_iteration; i<=ITERATIONS; i++)); do
  echo ""
  echo "========================================"
  echo " Iteration ${i} / ${ITERATIONS} - PRD #${PRD_ISSUE}"
  echo "========================================"

  if hitl_list="$(check_hitl_blocker)"; then
    echo "HITL issues require manual action:"
    echo "${hitl_list}"
    exit 0
  fi

  next_issue="$(find_next_issue)"
  if [[ -z "${next_issue}" ]]; then
    if check_all_closed; then
      echo "All child issues for PRD #${PRD_ISSUE} are closed."
      rm -f "${PROGRESS_FILE}"
      exit 0
    fi
    echo "No unblocked AFK issues found. Check issue dependencies."
    exit 1
  fi

  issue_title="$(gh issue view "${next_issue}" --json title -q '.title')"
  echo " -> Implementing #${next_issue}: ${issue_title}"
  set_progress_num "current_issue" "${next_issue}"
  set_progress_str "current_state" "implementing"

  if should_review "${next_issue}"; then
    echo " -> Mode: branch + PR + review"
    implement_issue_pr "${next_issue}"
    pr_num="$(gh pr list --head "issue-${next_issue}" --json number -q '.[0].number')"
    [[ -n "${pr_num}" ]] || { set_progress_str "current_state" "failed"; exit 1; }
    set_progress_num "current_pr" "${pr_num}"
    set_progress_str "current_state" "pr_created"
    handle_review_flow "${next_issue}" "${pr_num}"
  else
    echo " -> Mode: direct to ${RALPH_BASE_BRANCH}"
    implement_issue_main "${next_issue}"
    handle_main_flow "${next_issue}"
  fi

  if check_all_closed; then
    echo "PRD #${PRD_ISSUE} complete after ${i} iterations."
    rm -f "${PROGRESS_FILE}"
    exit 0
  fi
done

echo "Reached iteration limit (${ITERATIONS}). Re-run to continue."
