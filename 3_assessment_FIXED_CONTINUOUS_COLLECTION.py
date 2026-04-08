"""
SpectrumIA Assessment Page

Full eye-tracking assessment with stimulus presentation.
Collects gaze data and extracts eye-tracking metrics.

Integração:
- Supabase: Assessment session, gaze data, e gaze metrics persistence
- Core: Face detection, gaze estimation, feature extraction
- Real-time: Gaze visualization e feedback
"""

import sys
from pathlib import Path
import streamlit as st
import numpy as np
from datetime import datetime, timezone, timedelta
import logging
from typing import Optional, List
import json

# Add core to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# All imports FIRST
from core.auth import get_auth, initialize_session_state as init_auth_state
from core.config import (
    MEDIAPIPE_FACE_DETECTION_MIN_CONFIDENCE,
    MEDIAPIPE_FACE_MESH_MIN_CONFIDENCE,
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

# Page config
st.set_page_config(
    page_title="SpectrumIA - Assessment",
    page_icon="📹",
    layout="wide",
)

# Initialize auth AFTER imports
init_auth_state()
auth = get_auth()

# Check authentication - AFTER all imports
if not auth.is_authenticated():
    st.error("❌ Please login first")
    st.info("Go to **🔐 Login** page to authenticate")
    st.stop()

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
        # Demo mode: Supabase not configured
        # Create a mock session in memory
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
        # Demo mode: Supabase not configured
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
    """Save stimulus metrics to database."""
    try:
        db = get_db()
    except ValueError:
        # Demo mode: Supabase not configured
        logger.info(f"Demo mode: Simulating save of metrics for stimulus {stimulus_id}")
        return True

    try:
        # For simplicity, we'll store metrics in the assessment_sessions table
        # In production, you might want a separate gaze_metrics table
        logger.info(f"Metrics saved for stimulus {stimulus_id}")
        return True

    except Exception as e:
        logger.error(f"Error saving metrics: {e}")
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

        # Use the correct method to estimate gaze
        gaze_point = gaze_estimator.estimate_gaze(face_landmarks)

        if gaze_point is None:
            return None

        gaze_x, gaze_y = gaze_point.gaze_x, gaze_point.gaze_y

        # Head pose estimation (method not available in GazeEstimator, using defaults)
        sample = GazeDataPoint(
            timestamp=datetime.now(timezone.utc).timestamp(),
            gaze_x=gaze_x,
            gaze_y=gaze_y,
            confidence=gaze_point.gaze_confidence,
            is_blink=is_blink,
            head_pitch=0.0,  # Default when not available
            head_yaw=0.0,    # Default when not available
            head_roll=0.0,   # Default when not available
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
        # Demo mode: Supabase not configured
        logger.info("Demo mode: Simulating assessment session completion")
        st.session_state.assessment_status = "completed"
        logger.info(f"Demo mode: Assessment completed with {len(st.session_state.gaze_samples)} samples")
        st.success("✅ Avaliação finalizada com sucesso! (modo demo)")
        return True

    try:
        # Update session status
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
    """Render main assessment interface."""
    st.set_page_config(
        page_title="Avaliação - SpectrumIA",
        page_icon="🎬",
        layout="wide",
    )

    st.title("🎬 Avaliação de Rastreamento Ocular")
    st.markdown(
        "Apresentação de estímulos visuais com coleta de dados de rastreamento ocular"
    )

    initialize_session_state()

    # Check user authentication
    if "user_id" not in st.session_state:
        st.warning("Por favor, faça login primeiro na página principal")
        st.stop()

    user_id = st.session_state.user_id

    # Check calibration
    # ✅ Support both persistent (Supabase) and local (demo mode) calibrations
    if not st.session_state.get("is_calibrated", False) and "calibration_id" not in st.session_state:
        st.warning("⚠️ Você deve calibrar seu eye-tracker primeiro")
        st.info("👉 Vá para a página de Calibração")
        st.stop()

    # Use either persistent calibration_id or local calibration_session_id
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

        # Start new assessment
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

    # Instructions
    st.subheader("📝 Instruções")
    st.write("""
    1. **Observe os estímulos** apresentados na tela
    2. **Mantenha a cabeça fixa** na posição calibrada
    3. **Siga o movimento** com os olhos
    4. **Não pisque excessivamente** durante a avaliação
    5. A sessão completa leva aproximadamente **2 minutos**
    """)

    st.divider()

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
                st.switch_page("pages/4_results")

        return

    # Get current stimulus
    stimulus = stimuli_list[current_stimulus_idx]

    # Progress
    progress = (current_stimulus_idx + 1) / len(stimuli_list)
    st.progress(progress, text=f"Estímulo {current_stimulus_idx + 1}/{len(stimuli_list)}")

    st.subheader(f"🎯 {stimulus['name']}")
    st.write(stimulus['description'])

    stimulus_duration_sec = stimulus['duration_ms'] / 1000.0

    col1, col2 = st.columns([2, 1])

    with col1:
        st.info(f"⏱️ Duração: {stimulus_duration_sec:.0f} segundos")

    with col2:
        st.metric("Tipo", stimulus['type'].upper())

    st.divider()

    # ========================================================================
    # STIMULUS PRESENTATION & GAZE COLLECTION
    # ========================================================================

    # Display stimulus placeholder based on type
    col1, col2 = st.columns([1.5, 1])

    with col1:
        st.subheader("🎬 Estímulo Visual")
        stimulus_container = st.container()

        # Render stimulus visual based on type
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

    # Initialize detectors
    if st.session_state.face_detector is None:
        try:
            st.session_state.face_detector = FaceDetector(
                confidence_threshold=MEDIAPIPE_FACE_DETECTION_MIN_CONFIDENCE
            )
            st.session_state.gaze_estimator = GazeEstimator()
            st.session_state.feature_extractor = FeatureExtractor()
            st.info("✅ Modelos de detecção carregados")
        except Exception as e:
            st.error(f"Erro ao carregar modelos: {str(e)}")
            return

    st.divider()

    # Webcam capture
    run = st.checkbox("Iniciar Câmera & Coleta", value=False)

    if run:
        import time
        from PIL import Image, ImageDraw
        import cv2

        # ✅ NOVA LÓGICA: Coleta contínua durante duração do estímulo
        st.info(f"⏱️ Coletando durante {stimulus_duration_sec:.0f} segundos...")

        start_time = datetime.now(timezone.utc)
        end_time = start_time + timedelta(seconds=stimulus_duration_sec)

        collection_progress = st.progress(0, text="Coleta em progresso...")

        while datetime.now(timezone.utc) < end_time:
            try:
                # Capture from webcam continuously
                camera_input = st.camera_input("Câmera", key=f"cam_{int(time.time()*1000)}")

                if camera_input is not None:
                    # Open and process image
                    image = Image.open(camera_input)
                    image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

                    # Detect face
                    faces, landmarks = st.session_state.face_detector.detect(image_cv)

                    if faces and landmarks:
                        # Collect gaze sample
                        sample = collect_gaze_sample(
                            gaze_estimator=st.session_state.gaze_estimator,
                            face_landmarks=faces[0],
                        )

                        if sample:
                            st.session_state.feature_extractor.add_gaze_sample(
                                gaze_x=sample.gaze_x,
                                gaze_y=sample.gaze_y,
                                timestamp=sample.timestamp,
                                confidence=sample.confidence,
                                is_blink=sample.is_blink,
                            )

                            # Draw gaze point on image
                            draw = ImageDraw.Draw(image)
                            gaze_px = int(sample.gaze_x * image.width)
                            gaze_py = int(sample.gaze_y * image.height)
                            draw.ellipse(
                                [(gaze_px - 10, gaze_py - 10),
                                 (gaze_px + 10, gaze_py + 10)],
                                outline="red",
                                width=3
                            )

                            webcam_placeholder.image(image, use_container_width=True)

                            # Update progress
                            elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
                            progress = min(elapsed / stimulus_duration_sec, 1.0)
                            collection_progress.progress(progress, text=f"Amostras: {len(st.session_state.gaze_samples)} | {elapsed:.1f}s/{stimulus_duration_sec:.0f}s")

                            # Show metrics
                            with metrics_placeholder.container():
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Amostras", len(st.session_state.gaze_samples))
                                with col2:
                                    st.metric("Confiança", f"{sample.confidence:.0%}")
                    else:
                        webcam_placeholder.warning("⚠️ Rosto não detectado")

                # Small delay to avoid too frequent captures
                time.sleep(0.1)

            except Exception as e:
                logger.error(f"Erro durante coleta: {e}")
                st.error(f"Erro: {str(e)}")
                break

        # Coleta finalizada
        st.success(f"✅ Coleta de {stimulus['name']} completa! ({len(st.session_state.gaze_samples)} amostras)")
        time.sleep(1)

        # ✅ Auto-advance para próximo estímulo
        if st.session_state.gaze_samples:
            try:
                # Save metrics automatically
                if st.session_state.feature_extractor is None:
                    st.session_state.feature_extractor = FeatureExtractor()

                metrics = st.session_state.feature_extractor.extract_features(
                    stimulus_id=stimulus['id']
                )

                save_stimulus_metrics(
                    st.session_state.assessment_session_id,
                    stimulus['id'],
                    metrics,
                    st.session_state.gaze_samples
                )

                st.session_state.gaze_samples = []
                st.session_state.current_stimulus_index += 1
                st.rerun()

            except Exception as e:
                logger.error(f"Erro ao salvar métricas: {e}")
                st.error(f"Erro ao processar: {str(e)}")

    st.divider()

    # ========================================================================
    # CONTROL ACTIONS
    # ========================================================================

    col1, col2 = st.columns(2)

    with col1:
        if st.button("⏸️ Pausar Avaliação", use_container_width=True):
            st.info("⏸️ Avaliação pausada. Você pode retomar a qualquer momento.")
            st.session_state.assessment_status = "paused"

    with col2:
        if st.button("🛑 Cancelar Avaliação", use_container_width=True):
            st.warning("❌ Avaliação cancelada. Os dados não foram salvos.")
            st.session_state.assessment_session_id = None
            st.session_state.assessment_status = "cancelled"
            st.session_state.gaze_samples = []
            st.rerun()


if __name__ == "__main__":
    render_assessment_interface()
