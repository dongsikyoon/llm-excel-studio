#!/bin/bash
# 프로젝트 루트에서 실행: ./scripts/run.sh
PORT=${1:-8501}
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$ROOT/logs/streamlit.log"
PID_FILE="$ROOT/logs/streamlit.pid"

mkdir -p "$ROOT/logs"

if [ -f "$PID_FILE" ] && kill -0 "$(cat $PID_FILE)" 2>/dev/null; then
    echo "이미 실행 중 (PID: $(cat $PID_FILE)) — 중지: ./scripts/stop.sh"
    exit 1
fi

cd "$ROOT"
nohup streamlit run app.py \
    --server.port "$PORT" \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.runOnSave true \
    > "$LOG" 2>&1 &

echo $! > "$PID_FILE"
echo "시작됨 → http://localhost:$PORT  (로그: tail -f $LOG)"
