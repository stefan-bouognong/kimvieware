#!/bin/bash

echo "🚀 Lancement avec terminaux..."

BASE_DIR=$(pwd)

# Fonction
open_terminal () {
    gnome-terminal -- bash -c "cd $1; source $BASE_DIR/env/bin/activate; $2; exec bash"
}

# Phase 0
open_terminal "$BASE_DIR/kimvieware-phase0-validator" "python3 src/validator_service.py"

# Phase 1
open_terminal "$BASE_DIR/kimvieware-phase1-extractor" "python3 src/extractor_service.py"

# Phase 2
open_terminal "$BASE_DIR/kimvieware-phase2-sgats" "python3 src/sgats_service.py"

# Phase 3
open_terminal "$BASE_DIR/kimvieware-phase3-evopath" "python3 src/evopath_service.py"

# Phase 4
open_terminal "$BASE_DIR/kimvieware-phase4-executor" "python3 src/executor_service.py"

# Orchestrator
open_terminal "$BASE_DIR/kimvieware-orchestrator" "python3 run_orchestrator.py"

echo "✅ Tous les services sont lancés"
echo "🌐 http://localhost:8080"