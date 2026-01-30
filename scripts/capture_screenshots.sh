#!/bin/bash
#
# Screenshot Capture Script for Helix Documentation
#
# Captures consistent screenshots of the Helix UI using Playwright.
# Requires: Node.js, Playwright
#
# Usage:
#   ./capture_screenshots.sh [OPTIONS]
#
# Options:
#   --page <name>     Capture specific page only
#   --all             Capture all pages (default)
#   --list            List available pages
#   --help            Show this help
#
# Example:
#   ./capture_screenshots.sh --page dashboard
#   ./capture_screenshots.sh --all

set -e

# Configuration
FRONTEND_URL="${HELIX_FRONTEND_URL:-http://localhost:3000}"
OUTPUT_DIR="docs/images"
VIEWPORT_WIDTH=1920
VIEWPORT_HEIGHT=1080

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Available pages to capture
declare -A PAGES
PAGES[dashboard]="/dashboard"
PAGES[qa-list]="/qa-pairs"
PAGES[qa-import]="/qa-pairs/import"
PAGES[prompts]="/prompts"
PAGES[prompt-editor]="/prompts/1"
PAGES[analytics]="/analytics"
PAGES[settings]="/settings"

# Help message
show_help() {
    echo "Helix Screenshot Capture Tool"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --page <name>  Capture specific page"
    echo "  --all          Capture all pages (default)"
    echo "  --list         List available pages"
    echo "  --help         Show this help"
    echo ""
    echo "Environment:"
    echo "  HELIX_FRONTEND_URL  Frontend URL (default: http://localhost:3000)"
}

# List available pages
list_pages() {
    echo "Available pages:"
    for page in "${!PAGES[@]}"; do
        echo "  - $page (${PAGES[$page]})"
    done
}

# Check prerequisites
check_prerequisites() {
    if ! command -v node &> /dev/null; then
        echo -e "${RED}Error: Node.js is required${NC}"
        exit 1
    fi

    if ! command -v npx &> /dev/null; then
        echo -e "${RED}Error: npx is required${NC}"
        exit 1
    fi

    # Check if Playwright is available
    if ! npx playwright --version &> /dev/null 2>&1; then
        echo -e "${YELLOW}Installing Playwright...${NC}"
        npm install -g playwright
        npx playwright install chromium
    fi
}

# Generate Playwright script
generate_script() {
    local page_name="$1"
    local page_path="$2"
    local output_file="$3"

    cat << EOF
const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch();
    const context = await browser.newContext({
        viewport: { width: $VIEWPORT_WIDTH, height: $VIEWPORT_HEIGHT }
    });
    const page = await context.newPage();

    try {
        await page.goto('$FRONTEND_URL$page_path');
        await page.waitForLoadState('networkidle');
        await page.waitForTimeout(1000); // Wait for animations
        await page.screenshot({ path: '$output_file', fullPage: false });
        console.log('Captured: $output_file');
    } catch (error) {
        console.error('Error capturing $page_name:', error.message);
        process.exit(1);
    } finally {
        await browser.close();
    }
})();
EOF
}

# Capture a single page
capture_page() {
    local page_name="$1"
    local page_path="${PAGES[$page_name]}"

    if [ -z "$page_path" ]; then
        echo -e "${RED}Unknown page: $page_name${NC}"
        list_pages
        exit 1
    fi

    # Create output directory
    local output_dir="$OUTPUT_DIR/$(dirname "$page_name" 2>/dev/null || echo "")"
    mkdir -p "$OUTPUT_DIR"

    local output_file="$OUTPUT_DIR/${page_name}.png"
    local script_file="/tmp/capture_${page_name}.js"

    echo -e "Capturing: ${YELLOW}$page_name${NC} ($page_path)"

    # Generate and run Playwright script
    generate_script "$page_name" "$page_path" "$output_file" > "$script_file"

    if node "$script_file"; then
        echo -e "${GREEN}✓${NC} $output_file"
        rm "$script_file"
        return 0
    else
        echo -e "${RED}✗${NC} Failed to capture $page_name"
        rm "$script_file"
        return 1
    fi
}

# Capture all pages
capture_all() {
    echo "Capturing all screenshots..."
    echo "Frontend URL: $FRONTEND_URL"
    echo "Output directory: $OUTPUT_DIR"
    echo ""

    local success=0
    local failed=0

    for page_name in "${!PAGES[@]}"; do
        if capture_page "$page_name"; then
            ((success++))
        else
            ((failed++))
        fi
    done

    echo ""
    echo "=============================="
    echo -e "Complete: ${GREEN}$success captured${NC}, ${RED}$failed failed${NC}"

    if [ $failed -gt 0 ]; then
        exit 1
    fi
}

# Parse arguments
PAGE=""
ACTION="all"

while [[ $# -gt 0 ]]; do
    case $1 in
        --page)
            ACTION="page"
            PAGE="$2"
            shift 2
            ;;
        --all)
            ACTION="all"
            shift
            ;;
        --list)
            list_pages
            exit 0
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Check prerequisites
check_prerequisites

# Execute action
case $ACTION in
    page)
        if [ -z "$PAGE" ]; then
            echo -e "${RED}Error: --page requires a page name${NC}"
            list_pages
            exit 1
        fi
        capture_page "$PAGE"
        ;;
    all)
        capture_all
        ;;
esac
