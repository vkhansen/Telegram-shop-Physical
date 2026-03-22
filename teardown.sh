#!/usr/bin/env bash
# teardown.sh - Stop all containers, KEEP database and volumes
# Usage: ./teardown.sh

set -uo pipefail

echo "Telegram Shop - Teardown (preserving data)"

echo "Force-stopping all containers..."
docker kill $(docker ps -q) 2>/dev/null || true
docker-compose down --remove-orphans --timeout 5 2>/dev/null || true

echo "All containers stopped. Database and volumes preserved."
