#!/usr/bin/env sh
# Download the current official Sequence OpenAPI spec to docs/openapi.yaml (gitignored).
set -e
cd "$(dirname "$0")/.."
curl -fsSL -o docs/openapi.yaml https://api.getsequence.io/platform/v1/openapi
echo "Saved docs/openapi.yaml ($(wc -c < docs/openapi.yaml) bytes)"
