#!/bin/bash
# Test script for datavint.io deployment

echo "🧪 Testing DataVint Deployment"
echo "================================"
echo ""

# Test 1: Check www DNS
echo "1️⃣  Checking www.datavint.io DNS..."
www_dns=$(dig www.datavint.io +short | head -1)
if [ -z "$www_dns" ]; then
    echo "   ❌ www.datavint.io DNS not propagated yet"
    echo "   ⏳ Wait 5-10 minutes and try again"
else
    echo "   ✅ www.datavint.io → $www_dns"
fi
echo ""

# Test 2: Check root domain DNS
echo "2️⃣  Checking datavint.io DNS..."
root_dns=$(dig datavint.io +short | head -1)
if [ -z "$root_dns" ]; then
    echo "   ❌ datavint.io DNS not configured"
else
    echo "   ✅ datavint.io → $root_dns"
fi
echo ""

# Test 3: Test landing page
echo "3️⃣  Testing landing page..."
landing_status=$(curl -s -o /dev/null -w "%{http_code}" https://www.datavint.io 2>/dev/null || echo "000")
if [ "$landing_status" = "200" ]; then
    echo "   ✅ https://www.datavint.io → 200 OK"
elif [ "$landing_status" = "000" ]; then
    echo "   ⏳ DNS not ready yet (curl error)"
else
    echo "   ⚠️  HTTP $landing_status"
fi
echo ""

# Test 4: Test dashboard
echo "4️⃣  Testing dashboard..."
dashboard_status=$(curl -s -o /dev/null -w "%{http_code}" https://www.datavint.io/playground 2>/dev/null || echo "000")
if [ "$dashboard_status" = "200" ]; then
    echo "   ✅ https://www.datavint.io/playground → 200 OK"
elif [ "$dashboard_status" = "000" ]; then
    echo "   ⏳ DNS not ready yet (curl error)"
else
    echo "   ⚠️  HTTP $dashboard_status"
fi
echo ""

# Summary
echo "📊 Summary"
echo "================================"
if [ "$landing_status" = "200" ] && [ "$dashboard_status" = "200" ]; then
    echo "✅ All tests passed! Your site is live."
    echo ""
    echo "🎉 Open your site:"
    echo "   Landing page: https://datavint.io"
    echo "   Dashboard: https://datavint.io/playground"
    echo ""
    echo "💡 Tip: Click 'Get Started Free' button to navigate to dashboard"
elif [ -n "$www_dns" ]; then
    echo "⏳ DNS propagated, but site not responding yet."
    echo "   Wait 2-3 more minutes for SSL certificate provisioning."
else
    echo "⏳ Waiting for DNS propagation (5-10 minutes)"
    echo ""
    echo "Run this script again in a few minutes:"
    echo "   ./test-deployment.sh"
fi
echo ""
