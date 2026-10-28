#!/usr/bin/env bash
# Start the embedded seekdb API. Embeddings stay in the browser.
set -euo pipefail
cd "$(dirname "$0")/.."
exec npx tsx scripts/run-seekdb.ts
