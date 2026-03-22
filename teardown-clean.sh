#!/usr/bin/env bash
# teardown-clean.sh - Stop all containers AND wipe all data (DB, Redis, Tailscale)
# Usage: ./teardown-clean.sh
# WARNING: This deletes the database, Redis data, and Tailscale state!

set -uo pipefail

echo "Telegram Shop - Full Teardown (WIPING ALL DATA)"

echo "Force-stopping all containers..."
docker kill $(docker ps -q) 2>/dev/null || true
docker-compose down -v --remove-orphans --timeout 5 2>/dev/null || true

echo "All containers stopped. All volumes and data wiped."
