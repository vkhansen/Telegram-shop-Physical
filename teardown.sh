#!/usr/bin/env bash
# teardown.sh — Stop and remove all containers
# Usage:
#   ./teardown.sh          — stop containers (preserves data)
#   ./teardown.sh --clean  — stop containers AND remove volumes (wipes all data)

set -euo pipefail

CLEAN=false

for arg in "$@"; do
    case "$arg" in
        --clean) CLEAN=true ;;
        -h|--help)
            echo "Usage: $0 [--clean]"
            echo "  --clean  Remove volumes (wipes DB, Redis, Tailscale state)"
            exit 0
            ;;
        *) echo "Unknown option: $arg"; exit 1 ;;
    esac
done

echo "=== Telegram Shop — Teardown ==="

if $CLEAN; then
    echo "Stopping containers and removing volumes..."
    docker-compose down -v
    echo "All containers stopped. Volumes removed (DB, Redis, Tailscale state wiped)."
else
    echo "Stopping containers..."
    docker-compose down
    echo "All containers stopped. Volumes preserved."
fi

echo "=== Teardown complete ==="
