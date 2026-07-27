#!/usr/bin/env bash
# Durable Matrix anomaly watcher — PID file + restart-safe loop.
# Usage:
#   ./scripts/anomaly_monitor.sh start
#   ./scripts/anomaly_monitor.sh stop
#   ./scripts/anomaly_monitor.sh status
#   ./scripts/anomaly_monitor.sh run     # foreground (default if no args)
set -u
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
LOG="$ROOT/.matrix_daemon.log"
ALERT_LOG="$ROOT/.matrix_anomaly_alerts.log"
PID_FILE="$ROOT/.matrix_anomaly_monitor.pid"
MONITOR_LOG="$ROOT/.matrix_anomaly_monitor.log"
PORT="${MATRIX_DASHBOARD_PORT:-8765}"
URL="http://127.0.0.1:${PORT}"
INTERVAL="${MATRIX_ANOMALY_INTERVAL:-30}"

alert() {
  local code="$1"
  local msg="$2"
  local ts
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  if tail -n 20 "$ALERT_LOG" 2>/dev/null | grep -q "$code — $msg"; then
    return 0
  fi
  echo "[$ts] $code — $msg" >> "$ALERT_LOG"
  python3 -c 'import json,sys; print("AGENT_MATRIX_ANOMALY "+json.dumps({"code":sys.argv[1],"msg":sys.argv[2],"at":sys.argv[3]}))' "$code" "$msg" "$ts"
}

run_loop() {
  touch "$ALERT_LOG"
  local last_error_pos=0
  [[ -f "$LOG" ]] && last_error_pos=$(wc -c < "$LOG" | tr -d ' ')
  echo "Matrix anomaly monitor started interval=${INTERVAL}s url=$URL pid=$$"
  while true; do
    code=$(curl -s -o /tmp/matrix_status.json -w "%{http_code}" --max-time 3 "$URL/api/status" 2>/dev/null || echo "000")
    if [[ "$code" != "200" ]]; then
      alert "link_down" "Console /api/status HTTP $code"
    else
      python3 - <<'PY' >/tmp/matrix_stale.txt 2>/dev/null || true
import json, time
from pathlib import Path
d = json.loads(Path("/tmp/matrix_status.json").read_text())
updated = float(d.get("updated_at") or 0)
age = time.time() - updated if updated else 0
status = str(d.get("status") or "")
if updated and age > 180 and status not in {"", "standby", "idle", "cycle_end"}:
    print(f"age={int(age)}s status={status}")
PY
      if [[ -s /tmp/matrix_stale.txt ]]; then
        alert "stale_console" "No console update: $(cat /tmp/matrix_stale.txt)"
      fi
    fi

    if ! lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
      alert "port_dead" "Nothing listening on :$PORT"
    fi

    if [[ -f "$LOG" ]]; then
      size=$(wc -c < "$LOG" | tr -d ' ')
      if (( size > last_error_pos )); then
        chunk=$(tail -c $((size - last_error_pos)) "$LOG" 2>/dev/null || true)
        last_error_pos=$size
        if echo "$chunk" | grep -Eiq 'CYCLE ERROR|Traceback|Address already in use|OllamaUnavailable|ABORT'; then
          snippet=$(echo "$chunk" | grep -Ei 'CYCLE ERROR|Traceback|Address already|OllamaUnavailable|ABORT' | tail -2 | tr '\n' ' ' | cut -c1-200)
          alert "daemon_error" "$snippet"
        fi
      fi
    fi

    echo "AGENT_MATRIX_HEARTBEAT ok http=$code $(date -u +%H:%M:%SZ)"
    sleep "$INTERVAL"
  done
}

cmd_start() {
  if [[ -f "$PID_FILE" ]]; then
    old=$(cat "$PID_FILE" 2>/dev/null || true)
    if [[ -n "$old" ]] && kill -0 "$old" 2>/dev/null; then
      echo "Already running pid=$old"
      exit 0
    fi
    rm -f "$PID_FILE"
  fi
  nohup bash "$0" run >>"$MONITOR_LOG" 2>&1 &
  echo $! >"$PID_FILE"
  echo "Started anomaly monitor pid=$(cat "$PID_FILE") log=$MONITOR_LOG"
}

cmd_stop() {
  if [[ ! -f "$PID_FILE" ]]; then
    echo "No monitor PID file."
    return 0
  fi
  pid=$(cat "$PID_FILE")
  kill "$pid" 2>/dev/null || true
  rm -f "$PID_FILE"
  echo "Stopped pid=$pid"
}

cmd_status() {
  if [[ -f "$PID_FILE" ]] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
    echo "running pid=$(cat "$PID_FILE")"
    tail -n 3 "$MONITOR_LOG" 2>/dev/null || true
  else
    echo "stopped"
    exit 1
  fi
}

case "${1:-run}" in
  start) cmd_start ;;
  stop) cmd_stop ;;
  status) cmd_status ;;
  run) run_loop ;;
  *)
    echo "Usage: $0 {start|stop|status|run}"
    exit 2
    ;;
esac
