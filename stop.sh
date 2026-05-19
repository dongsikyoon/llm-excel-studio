#!/bin/bash
PID_FILE="streamlit.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "실행 중인 프로세스가 없습니다."
    exit 0
fi

PID=$(cat "$PID_FILE")
if kill -0 "$PID" 2>/dev/null; then
    kill "$PID"
    rm -f "$PID_FILE"
    echo "LLM Excel Studio 종료됨 (PID: $PID)"
else
    echo "프로세스가 이미 종료되어 있습니다."
    rm -f "$PID_FILE"
fi
