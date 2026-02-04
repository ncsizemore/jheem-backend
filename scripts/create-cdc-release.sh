#!/bin/bash
# =============================================================================
# Create CDC Testing Release from Server Simulations
# =============================================================================
# Run this on shield1-jhu server where simulations are stored
# Requires: gh cli authenticated
#
# Usage: ./create-cdc-release.sh [--dry-run]
# =============================================================================

set -e

RELEASE_TAG="cdc-testing-v1.0.0"
RELEASE_TITLE="CDC Testing Simulations v1.0.0"
REPO="ncsizemore/jheem-simulations"
SIM_DIR="/mnt/jheem_nas_share/simulations/cdct/final.ehe.state-1000"

# CDC Testing 18 states (matching Shiny app)
STATES=("AL" "AZ" "CA" "FL" "GA" "IL" "KY" "LA" "MD" "MO" "MS" "NY" "OH" "SC" "TN" "TX" "WA" "WI")

# Scenarios - using raw file patterns
# noint = baseline, cdct.end = cessation, cdct.bintr = brief, cdct.pintr = prolonged
SCENARIO_PATTERNS=("noint" "cdct.end" "cdct.bintr" "cdct.pintr")

DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
  DRY_RUN=true
  echo "🔸 DRY RUN MODE"
fi

echo ""
echo "=========================================="
echo "Creating CDC Testing Release: $RELEASE_TAG"
echo "=========================================="
echo ""

# Verify files exist
echo "📋 Verifying source files..."
MISSING=0
FOUND=0
MISSING_STATES=""

for state in "${STATES[@]}"; do
  STATE_MISSING=0
  STATE_SCENARIOS=""
  for scenario in "${SCENARIO_PATTERNS[@]}"; do
    FILE="$SIM_DIR/$state/cdct_final.ehe.state-1000_${state}_${scenario}.Rdata"
    if [[ ! -f "$FILE" ]]; then
      ((MISSING++))
      ((STATE_MISSING++))
      STATE_SCENARIOS="$STATE_SCENARIOS $scenario"
    else
      ((FOUND++))
    fi
  done
  if [[ $STATE_MISSING -gt 0 ]]; then
    echo "  ❌ $state: missing$STATE_SCENARIOS"
    MISSING_STATES="$MISSING_STATES $state"
  fi
done

echo ""
echo "  ✅ Found: $FOUND files"
if [[ $MISSING -gt 0 ]]; then
  echo "  ❌ Missing: $MISSING files"
  echo "  States with missing files:$MISSING_STATES"
  echo ""

  # Show which states have complete data
  echo "📊 States with COMPLETE data (all 4 scenarios):"
  for state in "${STATES[@]}"; do
    COMPLETE=true
    for scenario in "${SCENARIO_PATTERNS[@]}"; do
      FILE="$SIM_DIR/$state/cdct_final.ehe.state-1000_${state}_${scenario}.Rdata"
      if [[ ! -f "$FILE" ]]; then
        COMPLETE=false
        break
      fi
    done
    if [[ "$COMPLETE" == true ]]; then
      echo "  ✅ $state"
    fi
  done

  echo ""
  read -p "Continue with available files only? [y/N] " -n 1 -r
  echo
  if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    exit 1
  fi
fi

# Calculate size
echo ""
echo "📊 Calculating total size..."
TOTAL_SIZE=$(du -ch ${SIM_DIR}/{AL,AZ,CA,FL,GA,IL,KY,LA,MD,MO,MS,NY,OH,SC,TN,TX,WA,WI}/*{noint,cdct.end,cdct.bintr,cdct.pintr}.Rdata 2>/dev/null | tail -1 | cut -f1)
echo "  Total: $TOTAL_SIZE"

if [[ "$DRY_RUN" == true ]]; then
  echo ""
  echo "🔸 DRY RUN - Would upload these files:"
  for state in "${STATES[@]}"; do
    for scenario in "${SCENARIO_PATTERNS[@]}"; do
      FILE="$SIM_DIR/$state/cdct_final.ehe.state-1000_${state}_${scenario}.Rdata"
      if [[ -f "$FILE" ]]; then
        SIZE=$(ls -lh "$FILE" | awk '{print $5}')
        echo "  cdct_final.ehe.state-1000_${state}_${scenario}.Rdata ($SIZE)"
      fi
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
## CDC Testing Simulations

Raw 1000-simulation data for CDC-funded HIV testing impact analysis.

### Contents
- **18 states**: AL, AZ, CA, FL, GA, IL, KY, LA, MD, MO, MS, NY, OH, SC, TN, TX, WA, WI
- **4 scenarios**: baseline (noint), cessation (cdct.end), brief interruption (cdct.bintr), prolonged interruption (cdct.pintr)
- **72 files total**

### File Naming Convention
```
cdct_final.ehe.state-1000_{STATE}_{scenario}.Rdata
```

### Scenarios
| File Pattern | Description |
|--------------|-------------|
| `noint` | No intervention (baseline) |
| `cdct.end` | Complete cessation of CDC testing |
| `cdct.bintr` | Brief interruption of CDC testing |
| `cdct.pintr` | Prolonged interruption of CDC testing |

### Usage
Used by the generate-cdc-testing workflow to extract plot data for the JHEEM Portal.
EOF
)"

echo "✅ Release created"

# Upload files
echo ""
echo "☁️  Uploading files (this will take a while - ~86GB)..."

for state in "${STATES[@]}"; do
  echo "  📤 Uploading $state..."
  for scenario in "${SCENARIO_PATTERNS[@]}"; do
    FILE="$SIM_DIR/$state/cdct_final.ehe.state-1000_${state}_${scenario}.Rdata"
    if [[ -f "$FILE" ]]; then
      gh release upload "$RELEASE_TAG" "$FILE" --repo "$REPO"
    fi
  done
done

echo ""
echo "✅ Upload complete!"

# Verify
UPLOADED=$(gh release view "$RELEASE_TAG" --repo "$REPO" --json assets --jq '.assets | length')
echo "📊 Assets uploaded: $UPLOADED (expected: $FOUND)"

echo ""
echo "=========================================="
echo "🎉 CDC Testing Release Complete"
echo "=========================================="
echo "https://github.com/$REPO/releases/tag/$RELEASE_TAG"
