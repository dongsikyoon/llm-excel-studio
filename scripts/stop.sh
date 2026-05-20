#!/bin/bash
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PID_FILE="$ROOT/logs/streamlit.pid"

if [ ! -f "$PID_FILE" ]; then echo "실행 중인 프로세스 없음"; exit 0; fi
PID=$(cat "$PID_FILE")
if kill -0 "$PID" 2>/dev/null; then
    kill "$PID" && rm -f "$PID_FILE"
    echo "종료됨 (PID: $PID)"
else
    rm -f "$PID_FILE"; echo "이미 종료된 프로세스"
fi
