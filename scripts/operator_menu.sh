#!/usr/bin/env bash
# AAIS operator menu — no-browser helpers (Linux/macOS)
# Usage: ./scripts/operator_menu.sh

BASE="http://127.0.0.1:8000"
LEGACY="$BASE/legacy_api"

show_menu() {
  echo ""
  echo "=== AAIS Operator Menu ==="
  echo "1) Health check"
  echo "2) List AI providers"
  echo "3) Create chat session"
  echo "4) Send message (needs session id)"
  echo "5) Capability bridge status"
  echo "6) Memory board snapshot"
  echo "7) ARIS boundary status"
  echo "0) Exit"
  echo ""
}

health_check() {
  curl -fsS "$BASE/health" | python -m json.tool 2>/dev/null || curl -fsS "$BASE/health"
}

list_providers() {
  curl -fsS "$LEGACY/api/jarvis/providers" | python -m json.tool 2>/dev/null || curl -fsS "$LEGACY/api/jarvis/providers"
}

create_session() {
  curl -fsS -X POST "$LEGACY/api/chat/sessions" \
    -H "Content-Type: application/json" \
    -d '{"system_prompt":"You are Jarvis."}' | python -m json.tool 2>/dev/null || true
}

send_message() {
  read -r -p "Session ID: " sid
  read -r -p "Message: " msg
  curl -fsS -X POST "$LEGACY/api/chat/sessions/${sid}/message" \
    -H "Content-Type: application/json" \
    -d "{\"message\":\"${msg}\",\"response_mode\":\"operator\"}" | python -m json.tool 2>/dev/null || true
}

bridge_status() {
  curl -fsS "$LEGACY/api/jarvis/capability-bridge/status" | python -m json.tool 2>/dev/null || curl -fsS "$LEGACY/api/jarvis/capability-bridge/status"
}

memory_board() {
  curl -fsS "$LEGACY/api/jarvis/memory/board" | python -m json.tool 2>/dev/null || curl -fsS "$LEGACY/api/jarvis/memory/board"
}

aris_status() {
  curl -fsS "$LEGACY/api/jarvis/aris-boundary/status" | python -m json.tool 2>/dev/null || curl -fsS "$LEGACY/api/jarvis/aris-boundary/status"
}

while true; do
  show_menu
  read -r -p "Choice: " choice
  case "$choice" in
    1) health_check ;;
    2) list_providers ;;
    3) create_session ;;
    4) send_message ;;
    5) bridge_status ;;
    6) memory_board ;;
    7) aris_status ;;
    0) break ;;
    *) echo "Unknown option" ;;
  esac
done
