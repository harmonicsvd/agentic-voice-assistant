# ---- set once ----
#!/usr/bin/env bash
set -euo pipefail

BASE="http://127.0.0.1:9000"   # Backend Agent URL
KEY="hQq8ZcTnq7GT4_3cFZezGYk8sFSlGMM4iBrZDif5Jps"
SUB="104659023322141767006"
DATE="2026-08-30"

post_event () {
  local id="$1" time="$2" title="$3" duration="$4" mode="$5" city="$6" location="$7"

  payload=$(jq -n \
    --arg date "$DATE" \
    --arg time "$time" \
    --arg title "$title" \
    --arg duration "$duration" \
    --arg mode "$mode" \
    --arg sub "$SUB" \
    --arg city "$city" \
    --arg location "$location" \
    '
    {
      parameters: {
        date: $date,
        time: $time,
        title: $title,
        duration: $duration,
        meeting_mode: $mode,
        user_sub: $sub
      },
      user_sub: $sub
    }
    | if $city != "" then .parameters.city = $city else . end
    | if $location != "" then .parameters.location = $location else . end
    ')

  curl -sS -X POST "$BASE/internal/skills/google_calendar" \
    -H "Content-Type: application/json" \
    -H "X-Internal-API-Key: $KEY" \
    -d "$payload"
  echo
}


# 1) Project Kickoff Meeting - based on meeting notes
post_event "tc1" "09:00" "Project Kickoff Meeting" "60 min" "in_person" "" "Conference Room A"

# 2) Technical Architecture Review - John's action item
post_event "tc2" "11:00" "Technical Architecture Finalization" "45 min" "online" "" ""

# 3) Marketing Materials Preparation - Sarah's action item
post_event "tc3" "14:00" "Marketing Materials Review" "30 min" "online" "" ""

# 4) Development Environment Setup - Mike's action item
post_event "tc4" "15:30" "Development Environment Setup" "60 min" "online" "" ""

# 5) Stakeholder Coordination - Lisa's action item
post_event "tc5" "17:00" "Stakeholder Coordination Meeting" "45 min" "online" "" ""

# 6) MVP Planning - Q1 2025 timeline discussion
post_event "tc6" "10:00" "MVP Launch Planning" "90 min" "in_person" "" "Conference Room A"
