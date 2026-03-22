#!/usr/bin/env bash
# rebuild.sh - Teardown and rebuild all Docker containers
# Usage:
#   ./rebuild.sh            - rebuild everything, preserves DB/Redis data
#   ./rebuild.sh --clean    - full teardown, removes volumes and all data
#   ./rebuild.sh --bot-only - rebuild only the bot container

set -uo pipefail

CLEAN=false
BOT_ONLY=false

for arg in "$@"; do
    case "$arg" in
        --clean)    CLEAN=true ;;
        --bot-only) BOT_ONLY=true ;;
        -h|--help)
            echo "Usage: $0 [--clean] [--bot-only]"
            echo "  --clean     Remove volumes (wipes DB, Redis, Tailscale state)"
            echo "  --bot-only  Rebuild only the bot container"
            exit 0
            ;;
        *) echo "Unknown option: $arg"; exit 1 ;;
    esac
done

echo "Telegram Shop - Rebuild"

if $BOT_ONLY; then
    echo "[1/3] Stopping bot container..."
    docker kill telegram_shop_bot 2>/dev/null || true
    docker-compose rm -f bot 2>/dev/null || true

    echo "[2/3] Rebuilding bot image..."
    docker-compose build --no-cache bot

    echo "[3/3] Starting bot container..."
    docker-compose up -d bot

    echo "Bot rebuilt successfully"
    docker-compose ps
    exit 0
fi

echo "[1/4] Force-stopping all containers..."
docker kill $(docker ps -q) 2>/dev/null || true
docker-compose down --remove-orphans --timeout 5 2>/dev/null || true

if $CLEAN; then
    echo "[2/4] Removing volumes and all data..."
    docker-compose down -v --timeout 5 2>/dev/null || true
    echo "WARNING: All data has been wiped!"
else
    echo "[2/4] Keeping volumes, DB data preserved"
fi

echo "[3/4] Rebuilding images..."
docker-compose build --no-cache

echo "[4/4] Starting all containers..."
docker-compose up -d

echo ""
echo "Rebuild complete"
docker-compose ps
