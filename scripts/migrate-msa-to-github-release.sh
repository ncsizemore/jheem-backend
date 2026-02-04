#!/bin/bash
# =============================================================================
# Migrate MSA Simulations to GitHub Release
# =============================================================================
# This script:
# 1. Flattens and renames simulation files to match AJPH naming convention
# 2. Creates a GitHub release in jheem-simulations
# 3. Uploads all files to the release
#
# Usage:
#   ./migrate-msa-to-github-release.sh [--dry-run]
#
# Prerequisites:
#   - gh cli authenticated
#   - Source files in ~/Downloads/base/ and ~/Downloads/prerun/
# =============================================================================

set -e

# Configuration
RELEASE_TAG="ryan-white-msa-v1.0.0"
RELEASE_TITLE="Ryan White MSA Simulations v1.0.0"
REPO="ncsizemore/jheem-simulations"
BASE_DIR="$HOME/Downloads/base"
PRERUN_DIR="$HOME/Downloads/prerun"
STAGING_DIR="$HOME/Downloads/msa-release-staging"

# Parse arguments
DRY_RUN=false
if [[ "$1" == "--dry-run" ]]; then
  DRY_RUN=true
  echo "🔸 DRY RUN MODE - No release will be created"
fi

echo ""
echo "=========================================="
echo "MSA Simulation Migration to GitHub Release"
echo "=========================================="
echo ""
echo "Release: $RELEASE_TAG"
echo "Repository: $REPO"
echo "Source (base): $BASE_DIR"
echo "Source (prerun): $PRERUN_DIR"
echo "Staging: $STAGING_DIR"
echo ""

# Verify source directories exist
if [[ ! -d "$BASE_DIR" ]]; then
  echo "❌ Base directory not found: $BASE_DIR"
  exit 1
fi

if [[ ! -d "$PRERUN_DIR" ]]; then
  echo "❌ Prerun directory not found: $PRERUN_DIR"
  exit 1
fi

# Count source files
BASE_COUNT=$(find "$BASE_DIR" -name "C.*_base.Rdata" | wc -l | tr -d ' ')
PRERUN_CITY_COUNT=$(find "$PRERUN_DIR" -mindepth 1 -maxdepth 1 -type d -name "C.*" | wc -l | tr -d ' ')

echo "📊 Source file counts:"
echo "   Base files: $BASE_COUNT"
echo "   Prerun cities: $PRERUN_CITY_COUNT"
echo ""

# Create staging directory
echo "📁 Creating staging directory..."
rm -rf "$STAGING_DIR"
mkdir -p "$STAGING_DIR"

# Copy base files (already correctly named)
echo "📦 Copying base files..."
cp "$BASE_DIR"/C.*_base.Rdata "$STAGING_DIR/"
BASE_COPIED=$(ls "$STAGING_DIR"/*_base.Rdata 2>/dev/null | wc -l | tr -d ' ')
echo "   Copied $BASE_COPIED base files"

# Flatten and rename prerun files
echo "📦 Flattening prerun files..."
SCENARIOS=("cessation" "brief_interruption" "prolonged_interruption")
PRERUN_COPIED=0

for city_dir in "$PRERUN_DIR"/C.*; do
  if [[ ! -d "$city_dir" ]]; then
    continue
  fi

  city_code=$(basename "$city_dir")

  for scenario in "${SCENARIOS[@]}"; do
    src_file="$city_dir/${scenario}.Rdata"
    dst_file="$STAGING_DIR/${city_code}_${scenario}.Rdata"

    if [[ -f "$src_file" ]]; then
      cp "$src_file" "$dst_file"
      ((PRERUN_COPIED++))
    else
      echo "   ⚠️  Missing: $city_code/$scenario.Rdata"
    fi
  done
done

echo "   Copied $PRERUN_COPIED prerun files"

# Verify total count
TOTAL_FILES=$(ls "$STAGING_DIR"/*.Rdata 2>/dev/null | wc -l | tr -d ' ')
EXPECTED_FILES=$((BASE_COUNT * 4))  # 1 base + 3 scenarios per city

echo ""
echo "📊 Staging summary:"
echo "   Total files: $TOTAL_FILES"
echo "   Expected: $EXPECTED_FILES (${BASE_COUNT} cities × 4 scenarios)"

if [[ "$TOTAL_FILES" -ne "$EXPECTED_FILES" ]]; then
  echo "   ⚠️  File count mismatch!"
fi

# Show sample of staged files
echo ""
echo "📋 Sample staged files:"
ls "$STAGING_DIR" | head -8
echo "   ..."
ls "$STAGING_DIR" | tail -4

# Calculate total size
TOTAL_SIZE=$(du -sh "$STAGING_DIR" | cut -f1)
echo ""
echo "📦 Total size: $TOTAL_SIZE"

# Stop here if dry run
if [[ "$DRY_RUN" == true ]]; then
  echo ""
  echo "🔸 DRY RUN COMPLETE"
  echo "   Staged files are in: $STAGING_DIR"
  echo "   Run without --dry-run to create the release"
  exit 0
fi

# Confirm before proceeding
echo ""
read -p "Proceed with creating release and uploading $TOTAL_FILES files? [y/N] " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 1
fi

# Check if release already exists
echo ""
echo "🔍 Checking for existing release..."
if gh release view "$RELEASE_TAG" --repo "$REPO" &>/dev/null; then
  echo "❌ Release $RELEASE_TAG already exists!"
  echo "   Delete it first with: gh release delete $RELEASE_TAG --repo $REPO"
  exit 1
fi

# Create release
echo ""
echo "🚀 Creating release $RELEASE_TAG..."
gh release create "$RELEASE_TAG" \
  --repo "$REPO" \
  --title "$RELEASE_TITLE" \
  --notes "$(cat <<EOF
## Ryan White MSA Simulations

Pre-computed simulation data for 31 Metropolitan Statistical Areas.

### Contents
- **31 cities** × **4 scenarios** = **124 files**
- Scenarios: baseline, cessation, brief_interruption, prolonged_interruption

### File Naming Convention
\`\`\`
{CITY_CODE}_base.Rdata
{CITY_CODE}_cessation.Rdata
{CITY_CODE}_brief_interruption.Rdata
{CITY_CODE}_prolonged_interruption.Rdata
\`\`\`

### Usage
Used by the generate-msa workflow to extract plot data for the JHEEM Portal.

### Source
Original simulations from jheem-container-minimal model runs.
EOF
)"

echo "✅ Release created"

# Upload files in batches
echo ""
echo "☁️  Uploading $TOTAL_FILES files..."
echo "   (This may take several minutes)"

# Upload all files at once - gh cli handles this well
cd "$STAGING_DIR"
gh release upload "$RELEASE_TAG" \
  --repo "$REPO" \
  *.Rdata

echo ""
echo "✅ Upload complete!"

# Verify upload
echo ""
echo "🔍 Verifying upload..."
UPLOADED_COUNT=$(gh release view "$RELEASE_TAG" --repo "$REPO" --json assets --jq '.assets | length')
echo "   Assets in release: $UPLOADED_COUNT"

if [[ "$UPLOADED_COUNT" -eq "$TOTAL_FILES" ]]; then
  echo "   ✅ All files uploaded successfully!"
else
  echo "   ⚠️  Expected $TOTAL_FILES, got $UPLOADED_COUNT"
fi

echo ""
echo "=========================================="
echo "🎉 MIGRATION COMPLETE"
echo "=========================================="
echo ""
echo "Release: https://github.com/$REPO/releases/tag/$RELEASE_TAG"
echo ""
echo "Next steps:"
echo "  1. Update models.json to use GitHub-Release source"
echo "  2. Run sync-config in jheem-portal"
echo "  3. Test the generate-msa workflow"
echo ""
