#!/bin/bash

echo "🚀 Installation + lancement avec terminaux..."

BASE_DIR=$(pwd)

# Activer environnement
source env/bin/activate

# Installer shared
cd kimvieware-shared
pip install -e .
cd "$BASE_DIR"

# Fonction pour ouvrir terminal
open_terminal () {
    gnome-terminal -- bash -c "cd $1; source $BASE_DIR/env/bin/activate; $2; exec bash"
}

# Phase 0
cd kimvieware-phase0-validator
pip install -r requirements.txt
cd "$BASE_DIR"
open_terminal "$BASE_DIR/kimvieware-phase0-validator" "python3 src/validator_service.py"

# Phase 1
cd kimvieware-phase1-extractor
pip install -r requirements.txt
cd "$BASE_DIR"
open_terminal "$BASE_DIR/kimvieware-phase1-extractor" "python3 src/extractor_service.py"

# Phase 2
cd kimvieware-phase2-sgats
pip install -r requirements.txt
cd "$BASE_DIR"
open_terminal "$BASE_DIR/kimvieware-phase2-sgats" "python3 src/sgats_service.py"

# Phase 3
cd kimvieware-phase3-evopath
pip install -r requirements.txt
cd "$BASE_DIR"
open_terminal "$BASE_DIR/kimvieware-phase3-evopath" "python3 src/evopath_service.py"

# Phase 4
cd kimvieware-phase4-executor
pip install -r requirements.txt
cd "$BASE_DIR"
open_terminal "$BASE_DIR/kimvieware-phase4-executor" "python3 src/executor_service.py"

# Orchestrator
cd kimvieware-orchestrator
pip install -r requirements.txt
cd "$BASE_DIR"
open_terminal "$BASE_DIR/kimvieware-orchestrator" "python3 run_orchestrator.py"

echo "✅ Tous les services sont lancés dans des terminaux séparés"
echo "🌐 http://localhost:8080"