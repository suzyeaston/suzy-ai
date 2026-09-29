#!/usr/bin/env bash
set -Eeuo pipefail

WORKSPACE="${SUZY_AI_WORKSPACE:-${HOME}/Projects/suzy-ai-workspace}"
APPS="${WORKSPACE}/apps"

mkdir -p "$APPS"

sync_repo() {
  local full="$1"
  local name="${full#*/}"
  local dest="${APPS}/${name}"

  if [[ -d "${dest}/.git" ]]; then
    echo "→ updating ${full}"
    git -C "$dest" fetch --prune
    git -C "$dest" checkout main >/dev/null 2>&1 || true

    if [[ -n "$(git -C "$dest" status --porcelain)" ]]; then
      echo "! ${name} has local changes; leaving it alone."
    else
      git -C "$dest" pull --ff-only || true
    fi
  else
    echo "→ cloning ${full}"
    gh repo clone "$full" "$dest"
  fi
}

sync_repo "suzyeaston/appliance-latent-space-live"
sync_repo "suzyeaston/pop-context"
sync_repo "suzyeaston/suzyeastonca"

echo
echo "Workspace:"
echo "  ${APPS}"
