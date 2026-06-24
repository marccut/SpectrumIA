"""
SpectrumIA Assessment Continuous Collection Page (experimental)

Variante experimental com coleta contínua automática durante a duração de cada estímulo.

Integração:
- Supabase: Assessment session, gaze data, e gaze metrics persistence
- Core: Face detection, gaze estimation, feature extraction
- Real-time: Coleta contínua com auto-advance
"""

import sys
from pathlib import Path
import streamlit as st
import numpy as np
from datetime import datetime, timezone, timedelta
import logging
from typing import Optional, List
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.auth import get_auth, initialize_session_state as init_auth_state
from core.config import (
    MEDIAPIPE_FACE_DETECTION_MIN_CONFIDENCE,
    MEDIAPIPE_FACE_MESH_MIN_TRACKING_CONFIDENCE,
)
from core.face_detection import FaceDetector
from core.gaze_estimation import GazeEstimator
from core.feature_extraction import FeatureExtractor
from models.schemas import (
    AssessmentSessionCreate,
    AssessmentSessionResponse,
    GazeDataPoint,
    GazeMetricsModel,
    StimulusRecord,
)
from models.database import get_db

logger = logging.getLogger(__name__)


def initialize_session_state():
    """Initialize Streamlit session state for assessment."""
    if "assessment_session_id" not in st.session_state:
        st.session_state.assessment_session_id = None
    if "assessment_status" not in st.session_state:
        st.session_state.assessment_status = "not_started"
    if "gaze_samples" not in st.session_state:
        st.session_state.gaze_samples: List[GazeDataPoint] = []
    if "current_stimulus_index" not in st.session_state:
        st.session_state.current_stimulus_index = 0
    if "feature_extractor" not in st.session_state:
        st.session_state.feature_extractor = None
    if "face_detector" not in st.session_state:
        st.session_state.face_detector = None
    if "gaze_estimator" not in st.session_state:
        st.session_state.gaze_estimator = None
    if "enable_face_mesh" not in st.session_state:
        st.session_state.enable_face_mesh = False
    if "face_mesh_available" not in st.session_state:
        st.session_state.face_mesh_available = True
    if "face_mesh_init_error" not in st.session_state:
        st.session_state.face_mesh_init_error = None
    # Timed-collection state (replaces while loop anti-pattern)
    if "collecting" not in st.session_state:
        st.session_state.collecting = False
    if "collection_start_time" not in st.session_state:
        st.session_state.collection_start_time = None
    if "collection_end_time" not in st.session_state:
        st.session_state.collection_end_time = None
    if "remaining_at_pause" not in st.session_state:
        st.session_state.remaining_at_pause = None


def _ensure_detection_models() -> bool:
    """Load face detection models only on demand and only once after a failure."""
    if (
        st.session_state.face_detector is not None
        and st.session_state.gaze_estimator is not None
        and st.session_state.feature_extractor is not None
    ):
        return True

    if not st.session_state.enable_face_mesh:
        st.info("Clique em `Ativar análise facial avançada` para carregar os modelos.")
        return False

    if not st.session_state.face_mesh_available:
        st.warning(
            "⚠️ A análise facial avançada não está disponível neste ambiente para esta sessão."
        )
        if st.session_state.face_mesh_init_error:
            st.caption(st.session_state.face_mesh_init_error)
        return False

    try:
        st.session_state.face_detector = FaceDetector(
            min_detection_confidence=MEDIAPIPE_FACE_DETECTION_MIN_CONFIDENCE,
            min_tracking_confidence=MEDIAPIPE_FACE_MESH_MIN_TRACKING_CONFIDENCE,
        )
        st.session_state.gaze_estimator = GazeEstimator()
        st.session_state.feature_extractor = FeatureExtractor()
        st.session_state.face_mesh_init_error = None
        st.success("✅ Modelos de detecção carregados")
        return True
    except Exception as e:
        st.session_state.face_mesh_available = False
        st.session_state.face_mesh_init_error = str(e)
        st.error("Erro ao carregar modelos.")
        st.warning("⚠️ A análise facial avançada foi desativada nesta sessão para evitar looping.")
        st.caption(str(e))
        return False


def get_stimulus_list() -> List[dict]:
    """Get list of stimuli for assessment."""
    return [
        {
            "id": "face_video_01",
            "name": "Rosto Falando",
            "type": "face",
            "duration_ms": 30000,
            "description": "Vídeo de rosto falando (30s)",
        },
        {
            "id": "face_video_02",
            "name": "Rosto Sorrindo",
            "type": "face",
            "duration_ms": 20000,
            "description": "Vídeo de rosto com expressões (20s)",
        },
        {
            "id": "geometric_01",
            "name": "Padrão Geométrico",
            "type": "geometric",
            "duration_ms": 15000,
            "description": "Padrão geométrico em movimento (15s)",
        },
    ]


def create_assessment_session(
    user_id: str,
    calibration_id: str
) -> Optional[AssessmentSessionResponse]:
    """Create a new assessment session in database."""
    try:
        db = get_db()
    except ValueError:
        logger.info("Demo mode: Creating mock assessment session")
        mock_session_id = f"ass_{user_id[:8]}"
        st.session_state.assessment_session_id = mock_session_id
        st.session_state.assessment_status = "in_progress"
        return {
            'session_id': mock_session_id,
            'user_id': user_id,
            'calibration_id': calibration_id,
            'assessment_type': 'asd_screening'
        }

    try:
        session_data = AssessmentSessionCreate(
            user_id=user_id,
            calibration_id=calibration_id,
            assessment_type="asd_screening"
        )
        session: AssessmentSessionResponse = db.create_assessment_session(session_data)
        st.session_state.assessment_session_id = session.session_id
        st.session_state.assessment_status = "in_progress"
        logger.info(f"Assessment session created: {session.session_id}")
        return session
    except Exception as e:
        logger.error(f"Error creating assessment session: {e}")
        st.error(f"Erro ao criar sessão de avaliação: {str(e)}")
        return None


def save_gaze_data(session_id: str, gaze_samples: List[GazeDataPoint]) -> bool:
    """Save gaze data to database."""
    try:
        db = get_db()
    except ValueError:
        logger.info(f"Demo mode: Simulating save of {len(gaze_samples)} gaze samples")
        return True

    try:
        if not gaze_samples:
            st.error("Nenhuma amostra de gaze coletada")
            return False

        count = db.insert_gaze_data(session_id, gaze_samples)
        logger.info(f"Saved {count} gaze samples for session {session_id}")
        st.success(f"✅ {count} amostras de gaze salvas")
        return True

    except Exception as e:
        logger.error(f"Error saving gaze data: {e}")
        st.error(f"Erro ao salvar dados de gaze: {str(e)}")
        return False


def save_stimulus_metrics(
    session_id: str,
    stimulus_id: str,
    metrics: GazeMetricsModel,
    gaze_samples: List[GazeDataPoint]
) -> bool:
    """
    Persist gaze samples and extracted metrics for one stimulus.

    Saves to two tables:
    - gaze_data: raw gaze samples (one row per frame)
    - gaze_metrics: extracted metrics (one row per stimulus)

    Falls back gracefully when Supabase is unavailable or RLS blocks.
    """
    try:
        db = get_db()
    except ValueError:
        logger.info("Demo mode: metrics for stimulus '%s' kept in-memory only", stimulus_id)
        return True

    try:
        # 1. Persist raw gaze samples for this stimulus
        if gaze_samples:
            db.insert_gaze_data(session_id, gaze_samples)

        # 2. Persist extracted metrics
        db.insert_gaze_metrics(session_id, metrics)

        logger.info(
            "Metrics and %d gaze samples saved for stimulus '%s'",
            len(gaze_samples), stimulus_id,
        )
        return True

    except Exception as e:
        error_text = " ".join([str(e), repr(e)]).lower()
        rls_blocked = (
            "row-level security" in error_text
            or "42501" in error_text
            or "permission denied" in error_text
        )
        if rls_blocked:
            logger.warning(
                "RLS blocked metrics save for stimulus '%s' — continuing locally: %s",
                stimulus_id, e,
            )
        else:
            logger.error("Error saving metrics for stimulus '%s': %s", stimulus_id, e)
        return False


def collect_gaze_sample(
    gaze_estimator: GazeEstimator,
    face_landmarks,
    is_blink: bool = False
) -> Optional[GazeDataPoint]:
    """Collect a single gaze sample."""
    try:
        if face_landmarks is None or not face_landmarks.face_detected:
            return None

        gaze_point = gaze_estimator.estimate_gaze(face_landmarks)

        if gaze_point is None:
            return None

        gaze_x, gaze_y = gaze_point.gaze_x, gaze_point.gaze_y

        sample = GazeDataPoint(
            timestamp=datetime.now(timezone.utc).timestamp(),
            gaze_x=gaze_x,
            gaze_y=gaze_y,
            confidence=gaze_point.gaze_confidence,
            is_blink=is_blink,
            head_pitch=0.0,
            head_yaw=0.0,
            head_roll=0.0,
        )

        st.session_state.gaze_samples.append(sample)
        return sample

    except Exception as e:
        logger.error(f"Error collecting gaze sample: {e}")
        return None


def finish_assessment_session(session_id: str) -> bool:
    """Mark assessment session as completed."""
    try:
        db = get_db()
    except ValueError:
        logger.info("Demo mode: Simulating assessment session completion")
        st.session_state.assessment_status = "completed"
        logger.info(f"Demo mode: Assessment completed with {len(st.session_state.gaze_samples)} samples")
        st.success("✅ Avaliação finalizada com sucesso! (modo demo)")
        return True

    try:
        updates = {
            "status": "completed",
            "samples_count": len(st.session_state.gaze_samples),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

        db.update_assessment_session(session_id, updates)
        st.session_state.assessment_status = "completed"
        logger.info(f"Assessment session completed: {session_id}")
        return True

    except Exception as e:
        logger.error(f"Error completing assessment: {e}")
        st.error(f"Erro ao finalizar avaliação: {str(e)}")
        return False


def render_assessment_interface():
    """Render main assessment interface (continuous collection variant)."""
    init_auth_state()
    auth = get_auth()
    if not auth.is_authenticated():
        st.error("❌ Please login first")
        st.info("Go to the main page and authenticate before opening Assessment Continuous.")
        st.stop()

    st.title("🎬 Avaliação — Coleta Contínua (experimental)")
    st.markdown(
        "Coleta automática de dados durante toda a duração de cada estímulo"
    )

    initialize_session_state()

    if "user_id" not in st.session_state:
        st.warning("Por favor, faça login primeiro na página principal")
        st.stop()

    user_id = st.session_state.user_id

    if not st.session_state.get("is_calibrated", False) and "calibration_id" not in st.session_state:
        st.warning("⚠️ Você deve calibrar seu eye-tracker primeiro")
        st.info("👉 Vá para a página de Calibração")
        st.stop()

    calibration_id = st.session_state.get("calibration_id") or st.session_state.get("calibration_session_id")

    if not calibration_id:
        st.error("⚠️ Calibration ID não encontrado. Por favor, recalibre.")
        st.stop()

    # ========================================================================
    # SIDEBAR - Session Info
    # ========================================================================

    with st.sidebar:
        st.header("📋 Informações da Sessão")

        if st.session_state.assessment_session_id:
            st.write(f"**ID da Sessão:** {st.session_state.assessment_session_id[:8]}...")
        st.write(f"**Usuário:** {user_id[:8]}...")
        st.write(f"**Status:** {st.session_state.assessment_status}")

        if st.session_state.gaze_samples:
            st.write(f"**Amostras Coletadas:** {len(st.session_state.gaze_samples)}")

        st.divider()

        if st.button("🎬 Iniciar Nova Avaliação", use_container_width=True):
            session = create_assessment_session(user_id, calibration_id)
            if session:
                st.success("✅ Avaliação iniciada!")
                st.rerun()

    # ========================================================================
    # MAIN CONTENT
    # ========================================================================

    if not st.session_state.assessment_session_id:
        st.info("👉 Clique em 'Iniciar Nova Avaliação' para começar")
        return

    st.subheader("📝 Instruções")
    st.write("""
    1. **Observe os estímulos** apresentados na tela
    2. **Mantenha a cabeça fixa** na posição calibrada
    3. **Siga o movimento** com os olhos
    4. **Não pisque excessivamente** durante a avaliação
    5. A sessão completa leva aproximadamente **2 minutos**
    """)

    st.divider()

    action_col1, action_col2 = st.columns([1.2, 1])
    with action_col1:
        if not st.session_state.enable_face_mesh and st.button(
            "🧠 Ativar análise facial avançada",
            use_container_width=True,
            type="primary",
        ):
            st.session_state.enable_face_mesh = True
            st.rerun()
    with action_col2:
        if not st.session_state.face_mesh_available:
            st.info("Modo compatibilidade ativo: Face Mesh indisponível.")

    # ========================================================================
    # STIMULUS PRESENTATION
    # ========================================================================

    stimuli_list = get_stimulus_list()
    current_stimulus_idx = st.session_state.current_stimulus_index

    if current_stimulus_idx >= len(stimuli_list):
        st.success("✅ Todas as avaliações foram completadas!")
        st.info("👉 Vá para a página de Resultados para ver os resultados")

        col1, col2 = st.columns(2)

        with col1:
            if st.button("💾 Salvar Dados", use_container_width=True, type="primary"):
                if save_gaze_data(
                    st.session_state.assessment_session_id,
                    st.session_state.gaze_samples
                ):
                    if finish_assessment_session(st.session_state.assessment_session_id):
                        st.balloons()

        with col2:
            if st.button("📊 Ver Resultados", use_container_width=True):
                st.switch_page("pages/4_Results.py")

        return

    stimulus = stimuli_list[current_stimulus_idx]
    stimulus_duration_sec = stimulus['duration_ms'] / 1000.0

    progress = (current_stimulus_idx + 1) / len(stimuli_list)
    st.progress(progress, text=f"Estímulo {current_stimulus_idx + 1}/{len(stimuli_list)}")

    st.subheader(f"🎯 {stimulus['name']}")
    st.write(stimulus['description'])

    col1, col2 = st.columns([2, 1])

    with col1:
        st.info(f"⏱️ Duração: {stimulus_duration_sec:.0f} segundos")

    with col2:
        st.metric("Tipo", stimulus['type'].upper())

    st.divider()

    # ========================================================================
    # STIMULUS PRESENTATION & GAZE COLLECTION
    # ========================================================================

    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.subheader("🎬 Estímulo Visual")
        stimulus_container = st.container()

        if stimulus['type'] == 'face':
            stimulus_container.markdown(f"""
            <div style="
                width: 100%;
                aspect-ratio: 4/3;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 24px;
                font-weight: bold;
            ">
                😊 {stimulus['name']}
            </div>
            """, unsafe_allow_html=True)
        elif stimulus['type'] == 'geometric':
            stimulus_container.markdown(f"""
            <div style="
                width: 100%;
                aspect-ratio: 4/3;
                background: linear-gradient(45deg, #f093fb 0%, #f5576c 100%);
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-size: 24px;
                font-weight: bold;
            ">
                🔷 {stimulus['name']}
            </div>
            """, unsafe_allow_html=True)

    with col2:
        st.subheader("📷 Feed da Câmera")
        webcam_placeholder = st.empty()
        metrics_placeholder = st.empty()

    if not _ensure_detection_models():
        return

    st.divider()

    import time as _time

    # =========================================================================
    # STATE-BASED TIMED COLLECTION
    # Streamlit idiom: no while loops with widgets.
    # Each render cycle processes one frame; st.rerun() drives the loop.
    # =========================================================================

    # ── Not yet collecting ────────────────────────────────────────────────────
    if not st.session_state.collecting:
        col_start, col_cancel = st.columns(2)
        with col_start:
            if st.button("▶️ Iniciar Coleta", type="primary", use_container_width=True):
                now = _time.time()
                # If resuming after pause, use remaining time; otherwise start fresh
                duration = (
                    st.session_state.remaining_at_pause
                    if st.session_state.remaining_at_pause is not None
                    else stimulus_duration_sec
                )
                st.session_state.remaining_at_pause = None  # consumed
                st.session_state.collecting = True
                st.session_state.collection_start_time = now
                st.session_state.collection_end_time = now + duration
                st.rerun()
        with col_cancel:
            if st.button("🛑 Cancelar Avaliação", use_container_width=True):
                st.session_state.collecting = False
                st.session_state.assessment_session_id = None
                st.session_state.assessment_status = "cancelled"
                st.session_state.gaze_samples = []
                st.warning("❌ Avaliação cancelada.")
                st.rerun()
        return

    # ── Time window expired — process, save, advance ──────────────────────────
    elapsed = _time.time() - st.session_state.collection_start_time
    remaining = st.session_state.collection_end_time - _time.time()

    if remaining <= 0:
        st.session_state.collecting = False
        st.success(
            f"✅ Coleta de {stimulus['name']} completa! "
            f"({len(st.session_state.gaze_samples)} amostras)"
        )

        if st.session_state.gaze_samples:
            try:
                if st.session_state.feature_extractor is None:
                    st.session_state.feature_extractor = FeatureExtractor()

                import dataclasses as _dc
                _raw = st.session_state.feature_extractor.extract_features(
                    stimulus_id=stimulus['id']
                )
                metrics = GazeMetricsModel(**_dc.asdict(_raw))
                save_stimulus_metrics(
                    st.session_state.assessment_session_id,
                    stimulus['id'],
                    metrics,
                    st.session_state.gaze_samples,
                )
                st.session_state.gaze_samples = []
                if hasattr(st.session_state, 'feature_extractor') and st.session_state.feature_extractor:
                    st.session_state.feature_extractor.reset()
                st.session_state.current_stimulus_index += 1
                st.rerun()

            except Exception as e:
                logger.error(f"Erro ao salvar métricas: {e}")
                st.error(f"Erro ao processar: {str(e)}")
        else:
            st.warning("Nenhuma amostra coletada neste estímulo. Avançando...")
            if hasattr(st.session_state, 'feature_extractor') and st.session_state.feature_extractor:
                st.session_state.feature_extractor.reset()
            st.session_state.current_stimulus_index += 1
            st.rerun()
        return

    # ── Active collection frame ───────────────────────────────────────────────
    prog = min(elapsed / stimulus_duration_sec, 1.0)
    st.progress(
        prog,
        text=(
            f"Coletando... {elapsed:.1f}s / {stimulus_duration_sec:.0f}s"
            f" | {len(st.session_state.gaze_samples)} amostras"
        ),
    )

    # Pause / cancel — always visible during collection
    col_pause, col_cancel2 = st.columns(2)
    with col_pause:
        if st.button("⏸️ Pausar Coleta", use_container_width=True):
            st.session_state.collecting = False
            # Preserve remaining time so resume continues from where it stopped
            st.session_state.remaining_at_pause = max(
                st.session_state.collection_end_time - _time.time(), 0.0
            )
            st.info("⏸️ Coleta pausada. Clique em ▶️ Iniciar para retomar.")
            return  # Stay on page; user decides next action
    with col_cancel2:
        if st.button("🛑 Cancelar Avaliação", key="cancel_active", use_container_width=True):
            st.session_state.collecting = False
            st.session_state.assessment_session_id = None
            st.session_state.assessment_status = "cancelled"
            st.session_state.gaze_samples = []
            st.warning("❌ Avaliação cancelada.")
            st.rerun()
            return

    # Single camera_input per render — stable key per stimulus (no loop)
    from PIL import Image, ImageDraw
    import cv2

    camera_input = st.camera_input("Câmera", key=f"cam_stimulus_{current_stimulus_idx}")

    if camera_input is not None:
        try:
            image = Image.open(camera_input)
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            face_list = st.session_state.face_detector.detect(image_cv)

            if face_list:
                sample = collect_gaze_sample(
                    gaze_estimator=st.session_state.gaze_estimator,
                    face_landmarks=face_list[0],
                )
                if sample:
                    st.session_state.feature_extractor.add_gaze_sample(
                        gaze_x=sample.gaze_x,
                        gaze_y=sample.gaze_y,
                        timestamp=sample.timestamp,
                        confidence=sample.confidence,
                        is_blink=sample.is_blink,
                    )
                    draw = ImageDraw.Draw(image)
                    gx = int(sample.gaze_x * image.width)
                    gy = int(sample.gaze_y * image.height)
                    draw.ellipse([(gx - 10, gy - 10), (gx + 10, gy + 10)], outline="red", width=3)
                    webcam_placeholder.image(image, use_container_width=True)
                    with metrics_placeholder.container():
                        c1, c2 = st.columns(2)
                        c1.metric("Amostras", len(st.session_state.gaze_samples))
                        c2.metric("Confiança", f"{sample.confidence:.0%}")
            else:
                webcam_placeholder.warning("⚠️ Rosto não detectado")

        except Exception as e:
            logger.error(f"Erro durante coleta: {e}")
            st.error(f"Erro: {str(e)}")

    # Auto-trigger next render cycle — this is the Streamlit equivalent of loop iteration
    _time.sleep(0.05)
    st.rerun()


render_assessment_interface()
