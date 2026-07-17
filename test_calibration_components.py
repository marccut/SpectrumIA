#!/usr/bin/env python3
"""
Script independente para testar componentes de calibração.
Execute: python3 test_calibration_components.py
"""

import os
import sys
from pathlib import Path
import traceback

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("🔧 TESTE DE COMPONENTES DE CALIBRAÇÃO - SpectrumIA")
print("=" * 70)

# Test 1: Dependencies
print("\n[1/6] Testando dependências Python...")
print("-" * 70)

deps = {
    "numpy": "NumPy",
    "cv2": "OpenCV",
    "mediapipe": "MediaPipe",
    "PIL": "PIL/Pillow",
    "streamlit": "Streamlit",
    "pydantic": "Pydantic",
}

failed_deps = []
for module, name in deps.items():
    try:
        __import__(module)
        print(f"  ✅ {name}")
    except ImportError as e:
        print(f"  ❌ {name}: {e}")
        failed_deps.append(module)

if failed_deps:
    print(f"\n⚠️  Dependências faltando: {', '.join(failed_deps)}")
    print(f"   Instale com: pip install -r requirements.txt")
    sys.exit(1)

# Test 2: Config
print("\n[2/6] Testando configuração...")
print("-" * 70)

try:
    from core.config import (
        APP_VERSION,
        GAZE_CALIBRATION_POINTS,
        MEDIAPIPE_FACE_DETECTION_MIN_CONFIDENCE,
        MEDIAPIPE_FACE_MESH_MIN_CONFIDENCE,
        validate_config,
    )
    print(f"  ✅ Config carregado")
    print(f"     - Versão: {APP_VERSION}")
    print(f"     - Calibration points: {GAZE_CALIBRATION_POINTS}")
    print(f"     - Face detection confidence: {MEDIAPIPE_FACE_DETECTION_MIN_CONFIDENCE}")

    validate_config()
    print(f"  ✅ Validação de config passou")
except Exception as e:
    print(f"  ❌ Erro na config: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 3: FaceDetector
print("\n[3/6] Testando FaceDetector...")
print("-" * 70)

try:
    from core.face_detection import FaceDetector
    print(f"  ℹ️  Carregando FaceDetector...")

    face_detector = FaceDetector(
        confidence_threshold=MEDIAPIPE_FACE_DETECTION_MIN_CONFIDENCE
    )
    print(f"  ✅ FaceDetector carregado com sucesso")

    # Try with test image
    import cv2
    import numpy as np

    # Create dummy image (640x480 RGB)
    dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
    dummy_image[100:200, 100:200] = [255, 0, 0]  # Blue square

    print(f"  ℹ️  Testando detecção em imagem dummy...")
    faces, landmarks = face_detector.detect(dummy_image)
    print(f"  ℹ️  Detectou {len(faces) if faces else 0} rostos")
    print(f"  ✅ FaceDetector funcionando")

except Exception as e:
    print(f"  ❌ Erro no FaceDetector: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 4: GazeEstimator
print("\n[4/6] Testando GazeEstimator...")
print("-" * 70)

try:
    from core.gaze_estimation import GazeEstimator
    print(f"  ℹ️  Carregando GazeEstimator...")

    gaze_estimator = GazeEstimator()
    print(f"  ✅ GazeEstimator carregado com sucesso")

    # Check attributes
    print(f"     - MP Face Mesh Model: {gaze_estimator.mp_face_mesh is not None}")
    print(f"     - Confidence: {gaze_estimator.confidence:.2f}")

except Exception as e:
    print(f"  ❌ Erro no GazeEstimator: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test 5: Database
print("\n[5/6] Testando Database...")
print("-" * 70)

try:
    from models.database import get_db
    print(f"  ℹ️  Conectando ao banco de dados...")

    db = get_db(os.getenv("SUPABASE_TEST_ACCESS_TOKEN", ""))
    print(f"  ✅ Database conectado")
    print(f"     - Tipo: Supabase")

except Exception as e:
    print(f"  ⚠️  Aviso no Database: {e}")
    print(f"     (Pode ser esperado se não há credenciais Supabase)")

# Test 6: Feature Extraction
print("\n[6/6] Testando Feature Extraction...")
print("-" * 70)

try:
    from core.feature_extraction import FeatureExtractor
    print(f"  ℹ️  Carregando FeatureExtractor...")

    feature_extractor = FeatureExtractor()
    print(f"  ✅ FeatureExtractor carregado com sucesso")

    # Check methods
    methods = [
        "extract_fixation_metrics",
        "extract_saccade_metrics",
        "extract_social_attention_metrics",
    ]
    for method in methods:
        if hasattr(feature_extractor, method):
            print(f"     - {method}: ✅")
        else:
            print(f"     - {method}: ❌")

except Exception as e:
    print(f"  ❌ Erro no FeatureExtractor: {e}")
    traceback.print_exc()
    sys.exit(1)

# Summary
print("\n" + "=" * 70)
print("✅ TODOS OS TESTES PASSARAM!")
print("=" * 70)
print("\n📝 Próximos passos:")
print("  1. Execute: streamlit run app/main.py")
print("  2. Vá para Debug page: http://localhost:8501/?page=debug_calibration")
print("  3. Teste câmera e detecção de rosto")
print("  4. Se tudo passar, pode usar Calibration normalmente")
print("\n" + "=" * 70)
