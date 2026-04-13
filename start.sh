#!/usr/bin/env bash
# start.sh — Linux / macOS 用起動スクリプト
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# .env が存在すれば読み込む
if [ -f ".env" ]; then
    set -a
    source .env
    set +a
fi

# 仮想環境のアクティベート
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

python main.py
