#!/bin/bash
# =============================================================================
# Create AJPH Release from Server Simulations
# =============================================================================
# Run this on shield1-jhu server where simulations are stored
# Requires: gh cli authenticated
#
# Usage: ./create-ajph-release.sh [--dry-run]
# =============================================================================

set -e

RELEASE_TAG="ryan-white-ajph-v1.0.0"
RELEASE_TITLE="Ryan White AJPH State-Level Simulations v1.0.0"
REPO="ncsizemore/jheem-simulations"
SIM_DIR="/mnt/jheem_nas_share/simulations/rw/final.ehe.state-1000"

# AJPH 11 states
STATES=("AL" "CA" "FL" "GA" "IL" "LA" "MO" "MS" "NY" "TX" "WI")

# Scenarios with file patterns
declare -A SCENARIOS=(
  ["noint"]="baseline"
  ["rw.end"]="cessation"
  ["rw.b.intr"]="brief_interruption"
  ["rw.p.intr"]="prolonged_interruption"
)

DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
  DRY_RUN=true
  echo "🔸 DRY RUN MODE"
fi

echo ""
echo "=========================================="
echo "Creating AJPH Release: $RELEASE_TAG"
echo "=========================================="
echo ""

# Verify files exist
echo "📋 Verifying source files..."
MISSING=0
for state in "${STATES[@]}"; do
  for scenario in "${!SCENARIOS[@]}"; do
    FILE="$SIM_DIR/$state/rw_final.ehe.state-1000_${state}_${scenario}.Rdata"
    if [[ ! -f "$FILE" ]]; then
      echo "  ❌ Missing: $FILE"
      ((MISSING++))
    fi
  done
done

if [[ $MISSING -gt 0 ]]; then
  echo "❌ $MISSING files missing. Aborting."
  exit 1
fi
echo "  ✅ All 44 files found"

# Calculate size
echo ""
echo "📊 Calculating total size..."
TOTAL_SIZE=$(du -ch ${SIM_DIR}/{AL,CA,FL,GA,IL,LA,MO,MS,NY,TX,WI}/*{noint,rw.end,rw.b.intr,rw.p.intr}.Rdata 2>/dev/null | tail -1 | cut -f1)
echo "  Total: $TOTAL_SIZE"

if [[ "$DRY_RUN" == true ]]; then
  echo ""
  echo "🔸 DRY RUN - Would upload these files:"
  for state in "${STATES[@]}"; do
    for scenario in "${!SCENARIOS[@]}"; do
      echo "  rw_final.ehe.state-1000_${state}_${scenario}.Rdata"
    done
  done
  exit 0
fi

# Check if release exists
echo ""
echo "🔍 Checking for existing release..."
if gh release view "$RELEASE_TAG" --repo "$REPO" &>/dev/null; then
  echo "❌ Release $RELEASE_TAG already exists!"
  echo "   Delete first: gh release delete $RELEASE_TAG --repo $REPO --yes"
  exit 1
fi

# Create release
echo ""
echo "🚀 Creating release..."
gh release create "$RELEASE_TAG" \
  --repo "$REPO" \
  --title "$RELEASE_TITLE" \
  --notes "$(cat <<'EOF'
## Ryan White AJPH State-Level Simulations

Finalized 1000-simulation data for 11 states, matching the AJPH 2025 publication.

### Contents
- **11 states**: AL, CA, FL, GA, IL, LA, MO, MS, NY, TX, WI
- **4 scenarios**: baseline (noint), cessation (rw.end), brief_interruption (rw.b.intr), prolonged_interruption (rw.p.intr)
- **44 files total**

### File Naming Convention
```
rw_final.ehe.state-1000_{STATE}_{scenario}.Rdata
```

### Scenarios
| File Pattern | Description |
|--------------|-------------|
| `noint` | No intervention (baseline) |
| `rw.end` | Permanent cessation of Ryan White |
| `rw.b.intr` | Brief interruption (18 months) |
| `rw.p.intr` | Prolonged interruption (42 months) |

### Note
This replaces the deprecated `ryan-white-state-v1.0.0` release which contained trimmed/incorrect simsets.
EOF
)"

echo "✅ Release created"

# Upload files
echo ""
echo "☁️  Uploading 44 files (this will take a while)..."

for state in "${STATES[@]}"; do
  echo "  📤 Uploading $state..."
  for scenario in "${!SCENARIOS[@]}"; do
    FILE="$SIM_DIR/$state/rw_final.ehe.state-1000_${state}_${scenario}.Rdata"
    gh release upload "$RELEASE_TAG" "$FILE" --repo "$REPO"
  done
done

echo ""
echo "✅ Upload complete!"

# Verify
UPLOADED=$(gh release view "$RELEASE_TAG" --repo "$REPO" --json assets --jq '.assets | length')
echo "📊 Assets uploaded: $UPLOADED (expected: 44)"

echo ""
echo "=========================================="
echo "🎉 AJPH Release Complete"
echo "=========================================="
echo "https://github.com/$REPO/releases/tag/$RELEASE_TAG"
