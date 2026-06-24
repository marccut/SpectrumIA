#!/bin/bash

REPO="$HOME/Documents/Claude/Projects/SpectrumIA"
mkdir -p "$REPO/.github/workflows"
mkdir -p "$REPO/monitoring/prometheus"
mkdir -p "$REPO/monitoring/grafana/dashboards"
mkdir -p "$REPO/monitoring/logstash"
mkdir -p "$REPO/core"

echo "✅ Pastas criadas"
echo "Agora copie os arquivos .yml de: /sessions/zealous-laughing-hamilton/mnt/SpectrumIA/.github/workflows/"
echo "Para: $REPO/.github/workflows/"
