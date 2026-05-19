#!/bin/bash
# LLM Excel Studio 실행 스크립트

PORT=${1:-8501}
LOG="streamlit.log"
PID_FILE="streamlit.pid"

if [ -f "$PID_FILE" ] && kill -0 "$(cat $PID_FILE)" 2>/dev/null; then
    echo "이미 실행 중입니다. (PID: $(cat $PID_FILE))"
    echo "중지하려면: ./stop.sh"
    exit 1
fi

nohup streamlit run app.py \
    --server.port "$PORT" \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.runOnSave true \
    > "$LOG" 2>&1 &

echo $! > "$PID_FILE"
echo "LLM Excel Studio 시작됨"
echo "  로컬:  http://localhost:$PORT"
echo "  로그:  tail -f $LOG"
echo "  중지:  ./stop.sh"
