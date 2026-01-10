#!/bin/bash
# Health check script for all SJSU RideShare services
# Usage: ./healthcheck.sh
# Exit code 0 = all healthy, 1 = one or more unhealthy

set -e

SERVICES=(
    "http://localhost:8001/health"  # user-service
    "http://localhost:8002/health"  # ride-service
    "http://localhost:8003/health"  # booking-service
    "http://localhost:8004/health"  # notification-service
    "http://localhost:8005/health"  # tracking-service
)

echo "🏥 SJSU RideShare Health Check"
echo "================================"

ALL_HEALTHY=true

for url in "${SERVICES[@]}"; do
    service_name=$(echo $url | cut -d':' -f3 | cut -d'/' -f1)
    echo -n "Checking port $service_name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" $url || echo "000")

    if [ "$response" = "200" ]; then
        echo "✅ Healthy"
    else
        echo "❌ Unhealthy (HTTP $response)"
        ALL_HEALTHY=false
    fi
done

echo "================================"

if [ "$ALL_HEALTHY" = true ]; then
    echo "✅ All services healthy!"
    exit 0
else
    echo "❌ One or more services unhealthy"
    exit 1
fi
