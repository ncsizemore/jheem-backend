#!/usr/bin/env bash
# =============================================================================
# report-progress.sh — Pipe docker stdout through this to report progress
# to Upstash Redis. The portal status API reads the key to show live updates.
#
# Usage:
#   docker run ... 2>&1 | ./scripts/report-progress.sh sim <key>
#   docker run ... 2>&1 | ./scripts/report-progress.sh extract <key> <expected_files>
#   ./scripts/report-progress.sh phase <key> <phase> <message>
#
# Modes:
#   sim       Parse R container phases + simulation progress lines from stdin.
#   extract   Parse "SUCCESS: Generated ..." lines from stdin, count vs expected.
#   phase     Write a single phase update (no stdin). For transitions between
#             docker runs where stdout parsing isn't needed.
#
# Environment:
#   UPSTASH_REDIS_REST_URL    Upstash REST endpoint
#   UPSTASH_REDIS_REST_TOKEN  Upstash auth token
#
# Stdin is always echoed to stdout so the job log is preserved.
# Redis write failures are logged once but never kill the pipeline.
# Writes are rate-limited to at most once per WRITE_INTERVAL seconds.
# =============================================================================

set -uo pipefail

MODE="${1:?Usage: report-progress.sh <sim|extract|phase> <key> [args...]}"
PROGRESS_KEY="${2:?Missing progress key}"
shift 2

REDIS_URL="${UPSTASH_REDIS_REST_URL:-}"
REDIS_TOKEN="${UPSTASH_REDIS_REST_TOKEN:-}"
WRITE_INTERVAL=5   # seconds between Redis writes
TTL=1800            # 30 minutes

# --- State ---
last_write_time=0
ok_logged=0
fail_logged=0

# --- Helpers ---

write_redis() {
  local value="$1"

  if [ -z "$REDIS_URL" ] || [ -z "$REDIS_TOKEN" ]; then
    if [ "$fail_logged" = "0" ]; then
      echo "  [progress] Upstash credentials not configured, skipping" >&2
      fail_logged=1
    fi
    return
  fi

  local body
  body=$(jq -n -c --arg key "$PROGRESS_KEY" --arg val "$value" \
    '["SET", $key, $val, "EX", "'"$TTL"'"]')

  local resp http_code
  resp=$(curl -s -w "\n%{http_code}" \
    "$REDIS_URL" \
    -H "Authorization: Bearer $REDIS_TOKEN" \
    -d "$body" 2>&1) || true
  http_code=$(echo "$resp" | tail -1)

  if [ "$http_code" != "200" ]; then
    if [ "$fail_logged" = "0" ]; then
      echo "  [progress] Redis write failed (HTTP $http_code): $(echo "$resp" | head -1)" >&2
      fail_logged=1
    fi
  elif [ "$ok_logged" = "0" ]; then
    echo "  [progress] Redis write OK (key: $PROGRESS_KEY)"
    ok_logged=1
  fi
}

# Write at most once per WRITE_INTERVAL seconds
throttled_write() {
  local value="$1"
  local now
  now=$(date +%s)
  if (( now - last_write_time >= WRITE_INTERVAL )); then
    write_redis "$value"
    last_write_time=$now
  fi
}

# Always write (for phase transitions, final updates)
immediate_write() {
  write_redis "$1"
  last_write_time=$(date +%s)
}

# --- Mode: phase (no stdin) ---

if [ "$MODE" = "phase" ]; then
  phase="${1:?Missing phase name}"
  message="${2:-}"
  immediate_write "{\"phase\":\"$phase\",\"message\":\"$message\"}"
  exit 0
fi

# --- Mode: sim ---

if [ "$MODE" = "sim" ]; then
  current_phase="loading"

  while IFS= read -r line; do
    echo "$line"

    # Phase transitions from custom_simulation.R
    if [[ "$line" =~ "--- Phase 1:" ]]; then
      current_phase="loading"
      immediate_write '{"phase":"loading","message":"Loading workspace..."}'

    elif [[ "$line" =~ "--- Phase 2:" ]]; then
      immediate_write '{"phase":"loading","message":"Loading base simulation data..."}'

    elif [[ "$line" =~ "--- Phase 3:" ]]; then
      current_phase="simulating"
      immediate_write '{"phase":"simulating","message":"Starting simulation...","percent":0}'

    elif [[ "$line" =~ [Pp]rogress:\ ([0-9]+)\ of\ ([0-9]+) ]]; then
      current="${BASH_REMATCH[1]}"
      total="${BASH_REMATCH[2]}"
      if (( total > 0 )); then
        pct=$((current * 100 / total))
        throttled_write "{\"phase\":\"simulating\",\"message\":\"Running simulation...\",\"percent\":$pct,\"simsComplete\":$current,\"simsTotal\":$total}"
      fi

    elif [[ "$line" =~ "--- Phase 4:" ]]; then
      current_phase="saving"
      immediate_write '{"phase":"saving","message":"Saving simulation results..."}'

    elif [[ "$line" =~ "SIMULATION COMPLETE" ]]; then
      immediate_write '{"phase":"saving","message":"Simulation complete, preparing extraction..."}'
    fi
  done

  # Final write for the last sim progress (may have been throttled)
  exit "${PIPESTATUS[0]:-0}"
fi

# --- Mode: extract ---

if [ "$MODE" = "extract" ]; then
  expected="${1:-0}"
  count=0

  while IFS= read -r line; do
    echo "$line"

    if [[ "$line" =~ "SUCCESS: Generated" ]]; then
      count=$((count + 1))
      if (( expected > 0 )); then
        pct=$((count * 100 / expected))
      else
        pct=0
      fi
      throttled_write "{\"phase\":\"extracting\",\"message\":\"Generating data files...\",\"percent\":$pct,\"filesComplete\":$count,\"filesTotal\":$expected}"
    fi
  done

  # Final count (in case last write was throttled)
  if (( count > 0 )); then
    if (( expected > 0 )); then
      pct=$((count * 100 / expected))
    else
      pct=100
    fi
    immediate_write "{\"phase\":\"extracting\",\"message\":\"Extraction complete\",\"percent\":$pct,\"filesComplete\":$count,\"filesTotal\":$expected}"
  fi

  exit "${PIPESTATUS[0]:-0}"
fi

echo "Unknown mode: $MODE" >&2
exit 1
