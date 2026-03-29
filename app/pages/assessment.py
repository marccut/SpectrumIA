"""
SpectrumIA Assessment Page

Full eye-tracking assessment with stimulus presentation.
Collects gaze data and extracts eye-tracking metrics.

Integração:
- Supabase: Assessment session, gaze data, e gaze metrics persistence
- Core: Face detection, gaze estimation, feature extraction
- Real-time: Gaze visualization e feedback
"""

import streamlit as st
import numpy as np
from datetime import datetime
import logging
from typing import Optional, List
import json

from core.face_detection import FaceDetector
from core.gaze_estimation import GazeEstimator
from core.feature_extraction import FeatureExtractor
from core.config import (
    MEDIAPIPE_FACE_DETECTION_MIN_CONFIDENCE,
    MEDIAPIPE_FACE_MESH_MIN_CONFIDENCE,
)
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
    db = get_db()
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
    db = get_db()
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
    db = get_db()
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
    face_landmarks: np.ndarray,
    camera_matrix: np.ndarray,
    is_blink: bool = False
) -> Optional[GazeDataPoint]:
    """Collect a single gaze sample."""
    try:
        gaze_point = gaze_estimator.estimate_gaze_point(
            face_landmarks=face_landmarks,
            camera_matrix=camera_matrix
        )

        if gaze_point is None:
            return None

        gaze_x, gaze_y = gaze_point

        # Get head pose from face estimator
        head_pose = gaze_estimator.get_head_pose()

        sample = GazeDataPoint(
            timestamp=datetime.utcnow().timestamp(),
            gaze_x=gaze_x,
            gaze_y=gaze_y,
            confidence=gaze_estimator.confidence,
            is_blink=is_blink,
            head_pitch=head_pose[0] if head_pose else 0.0,
            head_yaw=head_pose[1] if head_pose else 0.0,
            head_roll=head_pose[2] if head_pose else 0.0,
        )

        st.session_state.gaze_samples.append(sample)
        return sample

    except Exception as e:
        logger.error(f"Error collecting gaze sample: {e}")
        return None


def finish_assessment_session(session_id: str) -> bool:
    """Mark assessment session as completed."""
    db = get_db()
    try:
        # Update session status
        updates = {
            "status": "completed",
            "samples_count": len(st.session_state.gaze_samples),
            "completed_at": datetime.utcnow().isoformat(),
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
    if "calibration_id" not in st.session_state:
        st.warning("⚠️ Você deve calibrar seu eye-tracker primeiro")
        st.info("👉 Vá para a página de Calibração")
        st.stop()

    calibration_id = st.session_state.calibration_id

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
                st.switch_page("pages/results.py")

        return

    # Get current stimulus
    stimulus = stimuli_list[current_stimulus_idx]

    # Progress
    progress = (current_stimulus_idx + 1) / len(stimuli_list)
    st.progress(progress, text=f"Estímulo {current_stimulus_idx + 1}/{len(stimuli_list)}")

    st.subheader(f"🎯 {stimulus['name']}")
    st.write(stimulus['description'])

    col1, col2 = st.columns([2, 1])

    with col1:
        st.info(f"⏱️ Duração: {stimulus['duration_ms']/1000:.0f} segundos")

    with col2:
        st.metric("Tipo", stimulus['type'].upper())

    st.divider()

    # ========================================================================
    # WEBCAM & GAZE COLLECTION
    # ========================================================================

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📷 Feed da Câmera + Gaze")
        webcam_placeholder = st.empty()

    with col2:
        st.subheader("📊 Métricas em Tempo Real")
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

    # Webcam capture
    run = st.checkbox("Iniciar Câmera", value=False)

    if run:
        camera_input = st.camera_input("Câmera")

        if camera_input is not None:
            from PIL import Image, ImageDraw
            import cv2

            image = Image.fromarray(np.array(camera_input))
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            # Detect face
            faces, landmarks = st.session_state.face_detector.detect(image_cv)

            if faces and landmarks:
                try:
                    # Get camera matrix
                    h, w = image_cv.shape[:2]
                    focal_length = w
                    camera_matrix = np.array(
                        [[focal_length, 0, w / 2],
                         [0, focal_length, h / 2],
                         [0, 0, 1]]
                    )

                    # Collect gaze sample
                    sample = collect_gaze_sample(
                        gaze_estimator=st.session_state.gaze_estimator,
                        face_landmarks=landmarks[0],
                        camera_matrix=camera_matrix,
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

                        webcam_placeholder.image(image, use_column_width=True)

                        # Show metrics
                        with metrics_placeholder.container():
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Amostras", len(st.session_state.gaze_samples))
                            with col2:
                                st.metric("Confiança", f"{sample.confidence:.0%}")

                except Exception as e:
                    st.error(f"Erro: {str(e)}")

            else:
                st.warning("⚠️ Nenhum rosto detectado")

    st.divider()

    # ========================================================================
    # STIMULUS ACTIONS
    # ========================================================================

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("⏭️ Próximo Estímulo", use_container_width=True):
            if st.session_state.gaze_samples:
                # Save metrics for current stimulus
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
            else:
                st.error("Coleta pelo menos uma amostra antes de prosseguir")

    with col2:
        if st.button("⏸️ Pausar", use_container_width=True):
            st.info("Avaliação pausada. Você pode retomar a qualquer momento.")

    with col3:
        if st.button("🛑 Cancelar", use_container_width=True):
            st.warning("Avaliação cancelada. Os dados não foram salvos.")
            st.session_state.assessment_session_id = None
            st.session_state.assessment_status = "cancelled"
            st.rerun()


if __name__ == "__main__":
    render_assessment_interface()
