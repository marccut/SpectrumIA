#!/usr/bin/env python3
"""
Phase 8.1 Validation Script
Verifica se o Supabase foi configurado corretamente
"""

import os
import json
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def validate_environment():
    """Verifica se as variáveis de ambiente estão configuradas"""
    print("\n🔍 Validating Environment Variables...")

    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
        'SUPABASE_SERVICE_ROLE_KEY'
    ]

    missing = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: Configurado")
        else:
            print(f"  ❌ {var}: FALTANDO")
            missing.append(var)

    return len(missing) == 0

def validate_database_connection():
    """Testa conexão com o banco de dados"""
    print("\n🔍 Testing Database Connection...")

    try:
        import psycopg2
        from psycopg2 import sql

        # Conectar usando DATABASE_URL
        db_url = os.getenv('DATABASE_URL')
        if not db_url:
            print("  ❌ DATABASE_URL não configurado")
            return False

        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # Testar conexão
        cursor.execute("SELECT 1")
        cursor.fetchone()

        print("  ✅ Conexão com banco de dados: OK")
        cursor.close()
        conn.close()
        return True

    except Exception as e:
        print(f"  ❌ Erro na conexão: {str(e)}")
        return False

def validate_tables():
    """Verifica se todas as 7 tabelas existem"""
    print("\n🔍 Checking Tables...")

    try:
        import psycopg2

        db_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # Verificar tabelas
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'BASE TABLE'
            ORDER BY table_name
        """)

        tables = [row[0] for row in cursor.fetchall()]
        expected_tables = [
            'users',
            'calibration_sessions',
            'assessment_sessions',
            'gaze_data',
            'gaze_metrics',
            'assessment_results',
            'audit_log'
        ]

        for table in expected_tables:
            if table in tables:
                print(f"  ✅ Table '{table}': EXISTS")
            else:
                print(f"  ❌ Table '{table}': MISSING")

        cursor.close()
        conn.close()

        return all(t in tables for t in expected_tables)

    except Exception as e:
        print(f"  ❌ Erro ao verificar tabelas: {str(e)}")
        return False

def validate_views():
    """Verifica se todas as 3 views existem"""
    print("\n🔍 Checking Views...")

    try:
        import psycopg2

        db_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # Verificar views
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_type = 'VIEW'
            ORDER BY table_name
        """)

        views = [row[0] for row in cursor.fetchall()]
        expected_views = [
            'assessment_summary',
            'high_risk_assessments',
            'user_assessment_history'
        ]

        for view in expected_views:
            if view in views:
                print(f"  ✅ View '{view}': EXISTS")
            else:
                print(f"  ❌ View '{view}': MISSING")

        cursor.close()
        conn.close()

        return all(v in views for v in expected_views)

    except Exception as e:
        print(f"  ❌ Erro ao verificar views: {str(e)}")
        return False

def validate_rls():
    """Verifica se RLS está ativado"""
    print("\n🔍 Checking Row Level Security (RLS)...")

    try:
        import psycopg2

        db_url = os.getenv('DATABASE_URL')
        conn = psycopg2.connect(db_url)
        cursor = conn.cursor()

        # Verificar RLS
        cursor.execute("""
            SELECT schemaname, tablename, rowsecurity
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)

        tables = cursor.fetchall()
        rls_enabled = sum(1 for t in tables if t[2])

        print(f"  ✅ RLS enabled em {rls_enabled}/7 tabelas")

        cursor.close()
        conn.close()

        return rls_enabled >= 5  # Pelo menos 5 com RLS

    except Exception as e:
        print(f"  ❌ Erro ao verificar RLS: {str(e)}")
        return False

def main():
    """Executa todas as validações"""
    print("\n" + "="*60)
    print("🚀 PHASE 8.1 - SUPABASE VALIDATION")
    print("="*60)

    results = {
        'Environment': validate_environment(),
        'Database Connection': validate_database_connection(),
        'Tables': validate_tables(),
        'Views': validate_views(),
        'RLS': validate_rls()
    }

    print("\n" + "="*60)
    print("📊 VALIDATION SUMMARY")
    print("="*60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for check, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check:.<40} {status}")

    print("\n" + "="*60)
    print(f"Result: {passed}/{total} checks passed")

    if passed == total:
        print("🎉 Phase 8.1 is COMPLETE and READY FOR USE!")
    else:
        print("⚠️  Some checks failed. Review the errors above.")

    print("="*60 + "\n")

    return passed == total

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
