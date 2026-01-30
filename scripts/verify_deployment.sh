#!/bin/bash
#
# Helix Deployment Verification Script
#
# Performs automated smoke tests to verify a Helix deployment.
#
# Usage:
#   ./verify_deployment.sh <API_URL> [API_KEY] [FB_VERIFY_TOKEN]
#
# Example:
#   ./verify_deployment.sh https://helix-api.example.com my-api-key my-fb-token
#
# Exit codes:
#   0 - All checks passed
#   1 - One or more checks failed
#   2 - Invalid arguments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
SKIPPED=0

# Parse arguments
API_URL="${1:-}"
API_KEY="${2:-}"
FB_VERIFY_TOKEN="${3:-}"

if [ -z "$API_URL" ]; then
    echo "Usage: $0 <API_URL> [API_KEY] [FB_VERIFY_TOKEN]"
    echo ""
    echo "Example:"
    echo "  $0 https://helix-api.example.com my-api-key"
    exit 2
fi

# Remove trailing slash from URL
API_URL="${API_URL%/}"

echo ""
echo "Helix Deployment Verification"
echo "=============================="
echo "Target: $API_URL"
echo ""

# Function to print result
print_result() {
    local status="$1"
    local check="$2"
    local detail="${3:-}"

    case $status in
        PASS)
            echo -e "[${GREEN}PASS${NC}] $check"
            ((PASSED++))
            ;;
        FAIL)
            echo -e "[${RED}FAIL${NC}] $check"
            [ -n "$detail" ] && echo "       $detail"
            ((FAILED++))
            ;;
        SKIP)
            echo -e "[${YELLOW}SKIP${NC}] $check"
            [ -n "$detail" ] && echo "       $detail"
            ((SKIPPED++))
            ;;
    esac
}

# Check 1: Health endpoint
check_health() {
    local response
    local status

    response=$(curl -s -w "\n%{http_code}" "$API_URL/health" 2>/dev/null)
    status=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$status" = "200" ]; then
        local app_status=$(echo "$body" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
        if [ "$app_status" = "ok" ]; then
            print_result "PASS" "Health check"
        else
            print_result "FAIL" "Health check" "Status is '$app_status', expected 'ok'"
        fi
    else
        print_result "FAIL" "Health check" "HTTP $status"
    fi
}

# Check 2: Branding endpoint
check_branding() {
    local response
    local status

    response=$(curl -s -w "\n%{http_code}" "$API_URL/branding" 2>/dev/null)
    status=$(echo "$response" | tail -n1)

    if [ "$status" = "200" ]; then
        print_result "PASS" "Branding endpoint"
    else
        print_result "FAIL" "Branding endpoint" "HTTP $status"
    fi
}

# Check 3: Chat endpoint
check_chat() {
    local response
    local status

    response=$(curl -s -w "\n%{http_code}" -X POST "$API_URL/chat" \
        -H "Content-Type: application/json" \
        -d '{"message": "Hello", "device_id": "verify-test"}' 2>/dev/null)
    status=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')

    if [ "$status" = "200" ]; then
        local has_message=$(echo "$body" | grep -c '"message"' || true)
        if [ "$has_message" -gt 0 ]; then
            print_result "PASS" "Chat endpoint"
        else
            print_result "FAIL" "Chat endpoint" "Response missing 'message' field"
        fi
    else
        print_result "FAIL" "Chat endpoint" "HTTP $status"
    fi
}

# Check 4: Admin authentication
check_admin_auth() {
    if [ -z "$API_KEY" ]; then
        print_result "SKIP" "Admin authentication" "No API_KEY provided"
        return
    fi

    # Without API key should fail
    local response_noauth
    response_noauth=$(curl -s -w "\n%{http_code}" "$API_URL/prompts" 2>/dev/null)
    status_noauth=$(echo "$response_noauth" | tail -n1)

    if [ "$status_noauth" != "401" ]; then
        print_result "FAIL" "Admin authentication" "Expected 401 without key, got $status_noauth"
        return
    fi

    # With API key should succeed
    local response_auth
    response_auth=$(curl -s -w "\n%{http_code}" "$API_URL/prompts" \
        -H "X-API-Key: $API_KEY" 2>/dev/null)
    status_auth=$(echo "$response_auth" | tail -n1)

    if [ "$status_auth" = "200" ]; then
        print_result "PASS" "Admin authentication"
    else
        print_result "FAIL" "Admin authentication" "Expected 200 with key, got $status_auth"
    fi
}

# Check 5: Facebook webhook verification
check_fb_webhook() {
    if [ -z "$FB_VERIFY_TOKEN" ]; then
        print_result "SKIP" "Facebook webhook" "No FB_VERIFY_TOKEN provided"
        return
    fi

    local challenge="test_challenge_123"
    local response
    response=$(curl -s "$API_URL/messenger/webhook?hub.mode=subscribe&hub.verify_token=$FB_VERIFY_TOKEN&hub.challenge=$challenge" 2>/dev/null)

    if [ "$response" = "$challenge" ]; then
        print_result "PASS" "Facebook webhook"
    else
        print_result "FAIL" "Facebook webhook" "Challenge not returned"
    fi
}

# Check 6: Response time
check_response_time() {
    local start_time
    local end_time
    local duration

    start_time=$(date +%s%3N)
    curl -s "$API_URL/health" > /dev/null 2>&1
    end_time=$(date +%s%3N)
    duration=$((end_time - start_time))

    if [ "$duration" -lt 1000 ]; then
        print_result "PASS" "Response time" "${duration}ms"
    else
        print_result "FAIL" "Response time" "${duration}ms (expected < 1000ms)"
    fi
}

# Check 7: SSL certificate
check_ssl() {
    local domain
    domain=$(echo "$API_URL" | sed -E 's|https?://([^/]+).*|\1|')

    local expiry
    expiry=$(echo | openssl s_client -servername "$domain" -connect "$domain:443" 2>/dev/null | openssl x509 -noout -enddate 2>/dev/null | cut -d= -f2)

    if [ -n "$expiry" ]; then
        local expiry_epoch
        expiry_epoch=$(date -d "$expiry" +%s 2>/dev/null || echo "0")
        local now_epoch
        now_epoch=$(date +%s)
        local days_left=$(( (expiry_epoch - now_epoch) / 86400 ))

        if [ "$days_left" -gt 30 ]; then
            print_result "PASS" "SSL certificate" "Expires in $days_left days"
        elif [ "$days_left" -gt 0 ]; then
            print_result "FAIL" "SSL certificate" "Expires in $days_left days (< 30)"
        else
            print_result "FAIL" "SSL certificate" "Expired"
        fi
    else
        print_result "SKIP" "SSL certificate" "Could not check (non-HTTPS or unavailable)"
    fi
}

# Run all checks
check_health
check_branding
check_chat
check_admin_auth
check_fb_webhook
check_response_time
check_ssl

# Print summary
echo ""
echo "=============================="
echo -e "Results: ${GREEN}$PASSED passed${NC}, ${RED}$FAILED failed${NC}, ${YELLOW}$SKIPPED skipped${NC}"
echo ""

# Exit with appropriate code
if [ "$FAILED" -gt 0 ]; then
    exit 1
fi

exit 0
