#!/bin/bash
#
# check-branding.sh - Verify no prohibited branding terms in source files
#
# Usage: ./scripts/check-branding.sh [directory]
#
# Exits with code 0 if clean, 1 if violations found.
#
# Prohibited terms: palai, philrice
#

set -e

# Default to current directory if not specified
SEARCH_DIR="${1:-.}"

# Prohibited terms (case-insensitive)
PROHIBITED_TERMS=("palai" "philrice")

# File extensions to scan
EXTENSIONS="py ts tsx js jsx json yaml yml md"

# Directories to exclude
EXCLUDED_DIRS=(
    ".git"
    "node_modules"
    "venv"
    ".venv"
    "__pycache__"
    ".pytest_cache"
    "dist"
    "build"
    "coverage"
    ".mypy_cache"
    "archive"  # Archived phases may contain historical references
    "00_project_roadmap"  # Planning docs may discuss history
    "01_documentation"  # Product docs may explain origin
)

# Files to exclude
EXCLUDED_FILES=(
    "check-branding.sh"
    "test_branding_hook.py"
    "test_complete_rebrand.py"
    "test_no_palai_references.py"
    "test_third_party_refs.py"
    "test_error_messages.py"
    "test_db_content_audit.py"
    "test_demo_prompts_seed.py"  # Demo seeds may use test terms
    "CHANGELOG.md"
    "improve.md"
    "improve_p4.md"
    "README.md"
    ".pre-commit-config.yaml"  # Config describes what it checks
)

# Build grep exclude patterns
build_exclude_args() {
    local args=""
    for dir in "${EXCLUDED_DIRS[@]}"; do
        args="$args --exclude-dir=$dir"
    done
    for file in "${EXCLUDED_FILES[@]}"; do
        args="$args --exclude=$file"
    done
    echo "$args"
}

# Build include patterns for file extensions
build_include_args() {
    local args=""
    for ext in $EXTENSIONS; do
        args="$args --include=*.$ext"
    done
    echo "$args"
}

# Check for prohibited terms
check_branding() {
    local search_dir="$1"
    local exit_code=0
    local found_violations=false

    EXCLUDE_ARGS=$(build_exclude_args)
    INCLUDE_ARGS=$(build_include_args)

    echo "Checking for prohibited branding terms in: $search_dir"
    echo "Prohibited terms: ${PROHIBITED_TERMS[*]}"
    echo ""

    for term in "${PROHIBITED_TERMS[@]}"; do
        # Run grep and capture output
        # shellcheck disable=SC2086
        matches=$(grep -r -i -n $INCLUDE_ARGS $EXCLUDE_ARGS "$term" "$search_dir" 2>/dev/null || true)

        if [ -n "$matches" ]; then
            found_violations=true
            echo "Found prohibited term '$term':"
            echo "$matches" | while read -r line; do
                echo "  $line"
            done
            echo ""
        fi
    done

    if [ "$found_violations" = true ]; then
        echo "ERROR: Prohibited branding terms found in source files."
        echo ""
        echo "Please replace these terms with appropriate alternatives:"
        echo "  - 'palai' -> 'helix' or use config values"
        echo "  - 'philrice' -> client-specific or remove"
        echo ""
        exit_code=1
    else
        echo "OK: No prohibited branding terms found."
    fi

    return $exit_code
}

# Main
check_branding "$SEARCH_DIR"
