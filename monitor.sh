#!/bin/bash

# Real-time monitoring script

echo "📊 Tunisia Parks - System Monitor"
echo "================================="

while true; do
    clear
    echo "🕐 $(date '+%Y-%m-%d %H:%M:%S')"
    echo "================================="
    
    # Docker stats
    echo "🐳 Docker Containers:"
    docker-compose ps --format "table {{.Name}}\t{{.Status}}"
    
    echo ""
    echo "💾 Resource Usage:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
    
    echo ""
    echo "📈 Recent Logs:"
    docker-compose logs --tail=5 app
    
    sleep 5
done
# To stop monitoring, press Ctrl+C