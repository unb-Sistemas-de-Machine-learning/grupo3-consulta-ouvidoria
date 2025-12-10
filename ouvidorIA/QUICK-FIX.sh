#!/bin/bash

echo "=============================================="
echo "  🔧 Fix: Memory Error - Switch to Light Model"
echo "=============================================="
echo ""
echo "Current issue: phi3 requires 50GB, only 8.6GB available"
echo "Solution: Switch to gemma2:2b (only 1.6GB)"
echo ""
echo "This script will:"
echo "  1. Stop all containers"
echo "  2. Remove old Ollama models (phi3)"
echo "  3. Start with gemma2:2b (1.6GB)"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]
then
    echo "Cancelled."
    exit 1
fi

echo ""
echo "Step 1: Stopping containers..."
docker-compose down

echo ""
echo "Step 2: Removing old Ollama models..."
docker volume rm grupo3-consulta-ouvidoria_ollama_data 2>/dev/null || echo "  (No volume to remove - OK)"

echo ""
echo "Step 3: Starting with new lightweight model (gemma2:2b)..."
echo "  This will download ~1.6GB (takes 1-2 minutes)"
echo ""
docker-compose up

echo ""
echo "=============================================="
echo "  ✅ Done! Check browser at:"
echo "     http://localhost:8501"
echo "=============================================="

