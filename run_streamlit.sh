#!/bin/bash

# SpectrumIA Streamlit Launcher
# Instala dependências e inicia a aplicação

set -e

echo "🚀 SpectrumIA - Streamlit Launcher"
echo "=================================="
echo ""

# Check Python version
echo "📦 Verificando Python..."
python3 --version

# Install dependencies
echo ""
echo "📥 Instalando dependências (pode levar alguns minutos)..."
python3 -m pip install -q --upgrade pip setuptools wheel

# Install from requirements.txt
if [ -f "requirements.txt" ]; then
    echo "📦 Instalando pacotes do requirements.txt..."
    python3 -m pip install -q -r requirements.txt
else
    echo "❌ Arquivo requirements.txt não encontrado!"
    exit 1
fi

echo ""
echo "✅ Dependências instaladas com sucesso!"
echo ""
echo "🌐 Iniciando Streamlit..."
echo "   URL: http://localhost:8501"
echo "   Pressione Ctrl+C para parar"
echo ""
echo "📋 Database Mode:"
echo "   - Tentando conectar a Supabase..."
echo "   - Se não configurado, usará LocalFileDatabase (fallback)"
echo ""

# Run Streamlit
python3 -m streamlit run app/main.py --logger.level=info

