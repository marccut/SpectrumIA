#!/usr/bin/env python3
"""
Pre-deployment validation for Streamlit Cloud
Verifica se o projeto está pronto para deploy
"""

import os
import sys
from pathlib import Path

def check_files_exist():
    """Verifica se arquivos essenciais existem"""
    print("\n🔍 Verificando arquivos essenciais...")

    project_root = Path(__file__).parent.parent
    required_files = [
        'streamlit_app.py',
        'app/main.py',
        'requirements.txt',
        '.env.example',
        '.gitignore',
        'README.md'
    ]

    all_exist = True
    for file in required_files:
        file_path = project_root / file
        if file_path.exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} FALTANDO")
            all_exist = False

    return all_exist

def check_requirements():
    """Verifica se requirements.txt existe e tem dependências"""
    print("\n🔍 Verificando requirements.txt...")

    req_file = Path(__file__).parent.parent / 'requirements.txt'
    if not req_file.exists():
        print("  ❌ requirements.txt não existe")
        return False

    with open(req_file, 'r') as f:
        lines = [l.strip() for l in f.readlines() if l.strip() and not l.startswith('#')]

    required_packages = ['streamlit', 'supabase-py', 'python-dotenv', 'mediapipe']

    for pkg in required_packages:
        found = any(pkg.lower() in line.lower() for line in lines)
        if found:
            print(f"  ✅ {pkg}")
        else:
            print(f"  ❌ {pkg} não encontrado em requirements.txt")
            return False

    print(f"  ✅ Total de {len(lines)} dependências configuradas")
    return True

def check_env_template():
    """Verifica se .env.example está configurado"""
    print("\n🔍 Verificando .env.example...")

    env_file = Path(__file__).parent.parent / '.env.example'
    if not env_file.exists():
        print("  ❌ .env.example não existe")
        return False

    with open(env_file, 'r') as f:
        content = f.read()

    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
        'SUPABASE_SERVICE_ROLE_KEY'
    ]

    for var in required_vars:
        if var in content:
            print(f"  ✅ {var}")
        else:
            print(f"  ❌ {var} não encontrado")
            return False

    return True

def check_streamlit_config():
    """Verifica se .streamlit/config.toml está pronto"""
    print("\n🔍 Verificando configuração Streamlit...")

    config_dir = Path(__file__).parent.parent / '.streamlit'
    config_file = config_dir / 'config.toml'

    if not config_dir.exists():
        print(f"  ⚠️  Pasta .streamlit não existe (será criada no deploy)")
        return True

    if config_file.exists():
        print(f"  ✅ .streamlit/config.toml existe")
        return True
    else:
        print(f"  ⚠️  .streamlit/config.toml não existe (opcional)")
        return True

def main():
    print("\n" + "="*60)
    print("🚀 VERIFICAÇÃO PRÉ-DEPLOY STREAMLIT CLOUD")
    print("="*60)

    results = {
        'Arquivos Essenciais': check_files_exist(),
        'requirements.txt': check_requirements(),
        '.env.example': check_env_template(),
        'Configuração Streamlit': check_streamlit_config()
    }

    print("\n" + "="*60)
    print("📊 RESUMO DA VERIFICAÇÃO")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for check, result in results.items():
        status = "✅ OK" if result else "❌ ERRO"
        print(f"{check:.<40} {status}")

    print(f"\nResult: {passed}/{total} verificações passaram")

    if passed == total:
        print("\n✅ PRONTO PARA DEPLOY NO STREAMLIT CLOUD!")
        print("\nPróximas etapas:")
        print("1. Faça push do arquivo 'streamlit_app.py' para GitHub (use GitHub Desktop)")
        print("2. No Streamlit Cloud, use 'streamlit_app.py' como Main file path")
        print("3. Adicione as secrets (variáveis de ambiente) no Streamlit Cloud")
    else:
        print("\n⚠️  Alguns problemas foram encontrados. Resolva-os antes do deploy.")

    print("="*60 + "\n")

    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
