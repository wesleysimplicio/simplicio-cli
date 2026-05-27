#!/usr/bin/env bash
# simplicio-userpromptsubmit — fires on every Claude Code UserPromptSubmit event.
#
# Reads the user prompt from CLAUDE_USER_PROMPT and pipes it to `simplicio
# detect`. If the heuristic decides it is a code-edit task, a PROMPT_HINT is
# printed to stderr nudging the agent to invoke the simplicio-cli skill. Always
# exits 0 — never blocks.
#
# Installed by `simplicio init`. Safe to delete to disable.
set -u

prompt="${CLAUDE_USER_PROMPT:-}"
if [ -z "$prompt" ]; then
  exit 0
fi

if ! command -v simplicio >/dev/null 2>&1; then
  exit 0
fi

printf '%s' "$prompt" | simplicio detect 2>&1 1>/dev/null || true
exit 0
