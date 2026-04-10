"""
SpectrumIA Calibration Page

Gaze calibration session with 9-point calibration grid.
Collects calibration samples and validates eye-tracking accuracy.

Integração:
- Supabase: CalibrationSession storage
- Core: Face detection e gaze estimation
- Real-time: Validation feedback
"""

import streamlit as st
import numpy as np
from datetime import datetime
import logging
from typing import Optional, List

from core.face_detection import FaceDetector, FaceLandmarks
from core.gaze_estimation import GazeEstimator
from core.config import (
    GAZE_CALIBRATION_POINTS,
    MEDIAPIPE_FACE_DETECTION_MIN_CONFIDENCE,
    MEDIAPIPE_FACE_MESH_MIN_CONFIDENCE,
)
from models.schemas import (
    CalibrationPoint,
    CalibrationSessionCreate,
    CalibrationSessionResponse,
)
from models.database import get_db

logger = logging.getLogger(__name__)


def initialize_session_state():
    """Initialize Streamlit session state for calibration."""
    if "calibration_session_id" not in st.session_state:
        st.session_state.calibration_session_id = None
    if "calibration_points" not in st.session_state:
        st.session_state.calibration_points = []
    if "current_calibration_index" not in st.session_state:
        st.session_state.current_calibration_index = 0
    if "calibration_status" not in st.session_state:
        st.session_state.calibration_status = "not_started"
    if "face_detector" not in st.session_state:
        st.session_state.face_detector = None
    if "gaze_estimator" not in st.session_state:
        st.session_state.gaze_estimator = None


def get_calibration_grid(num_points: int = 9) -> List[tuple]:
    """
    Generate calibration points in a grid pattern.

    Args:
        num_points: Number of calibration points (4, 9, or 16)

    Returns:
        List of (x, y) normalized coordinates
    """
    if num_points == 4:
        return [(0.2, 0.2), (0.8, 0.2), (0.2, 0.8), (0.8, 0.8)]
    elif num_points == 9:
        points = []
        for i in [0.25, 0.5, 0.75]:
            for j in [0.25, 0.5, 0.75]:
                points.append((i, j))
        return points
    elif num_points == 16:
        points = []
        for i in [0.2, 0.4, 0.6, 0.8]:
            for j in [0.2, 0.4, 0.6, 0.8]:
                points.append((i, j))
        return points
    else:
        return [(0.5, 0.5)]


def create_calibration_session(user_id: str, num_points: int = 9):
    """Create a new calibration session in database."""
    db = get_db()
    try:
        calibration_data = CalibrationSessionCreate(
            user_id=user_id,
            num_points=num_points,
            calibration_distance_cm=50.0
        )
        session: CalibrationSessionResponse = db.create_calibration_session(calibration_data)
        st.session_state.calibration_session_id = session.calibration_id
        st.session_state.calibration_status = "in_progress"
        logger.info(f"Calibration session created: {session.calibration_id}")
        return session
    except Exception as e:
        logger.error(f"Error creating calibration session: {e}")
        st.error(f"Erro ao criar sessão de calibração: {str(e)}")
        return None


def collect_calibration_sample(
    session_id: str,
    point_index: int,
    screen_x: float,
    screen_y: float,
    gaze_estimator: GazeEstimator,
    face_landmarks: FaceLandmarks,
) -> Optional[CalibrationPoint]:
    """
    Collect a single calibration sample.

    Args:
        session_id: Calibration session ID
        point_index: Index of calibration point
        screen_x: Target X coordinate (0-1)
        screen_y: Target Y coordinate (0-1)
        gaze_estimator: GazeEstimator instance
        face_landmarks: FaceLandmarks object from FaceDetector.detect()

    Returns:
        CalibrationPoint if successful, None otherwise
    """
    try:
        # Estimate gaze point
        gaze_point = gaze_estimator.estimate_gaze(face_landmarks=face_landmarks)

        if gaze_point.gaze_confidence == 0.0:
            return None

        gaze_x = gaze_point.gaze_x
        gaze_y = gaze_point.gaze_y

        # Create calibration point
        point = CalibrationPoint(
            point_id=f"{session_id}_{point_index}",
            screen_x=screen_x,
            screen_y=screen_y,
            gaze_x=gaze_x,
            gaze_y=gaze_y,
            timestamp=datetime.utcnow().timestamp(),
            confidence=gaze_point.gaze_confidence,
            distance_pixels=np.sqrt(
                (gaze_x - screen_x) ** 2 + (gaze_y - screen_y) ** 2
            ) * 1000,  # Approximate pixels
        )

        st.session_state.calibration_points.append(point)
        return point

    except Exception as e:
        logger.error(f"Error collecting calibration sample: {e}")
        return None


def save_calibration_session(session_id: str) -> bool:
    """Save completed calibration session to database."""
    db = get_db()
    try:
        if not st.session_state.calibration_points:
            st.error("Nenhum ponto de calibração coletado")
            return False

        # Calculate validation metrics
        points = st.session_state.calibration_points
        distances = [p.distance_pixels for p in points]

        mean_error = float(np.mean(distances)) if distances else 0.0
        max_error = float(np.max(distances)) if distances else 0.0

        # Validity score: 1.0 if mean_error < 30px, decreases with error
        validity_score = max(0.0, 1.0 - (mean_error / 100.0))

        # Update session
        updates = {
            "status": "completed",
            "calibration_points": [p.model_dump() for p in points],
            "mean_error_pixels": mean_error,
            "max_error_pixels": max_error,
            "validity_score": validity_score,
            "completed_at": datetime.utcnow().isoformat(),
        }

        session = db.update_calibration_session(session_id, updates)
        logger.info(f"Calibration session saved: {session_id}")
        st.session_state.calibration_status = "completed"
        return True

    except Exception as e:
        logger.error(f"Error saving calibration session: {e}")
        st.error(f"Erro ao salvar calibração: {str(e)}")
        return False


def render_calibration_interface():
    """Render main calibration interface."""
    st.set_page_config(
        page_title="Calibração - SpectrumIA",
        page_icon="👁️",
        layout="wide",
    )

    st.title("👁️ Calibração de Rastreamento Ocular")
    st.markdown(
        "Calibração de 9 pontos para otimizar a precisão do rastreamento ocular"
    )

    initialize_session_state()

    # Check user authentication
    if "user_id" not in st.session_state:
        st.warning("Por favor, faça login primeiro na página principal")
        st.stop()

    user_id = st.session_state.user_id

    # ========================================================================
    # SIDEBAR - Session Info
    # ========================================================================

    with st.sidebar:
        st.header("📋 Informações da Sessão")

        if st.session_state.calibration_session_id:
            st.write(f"**ID da Sessão:** {st.session_state.calibration_session_id[:8]}...")
        st.write(f"**Usuário:** {user_id[:8]}...")
        st.write(f"**Status:** {st.session_state.calibration_status}")

        if st.session_state.calibration_points:
            st.write(f"**Pontos Coletados:** {len(st.session_state.calibration_points)}")

        st.divider()

        # Start new calibration
        if st.button("🔄 Iniciar Nova Calibração", use_container_width=True):
            session = create_calibration_session(user_id, GAZE_CALIBRATION_POINTS)
            if session:
                st.success("✅ Calibração iniciada!")
                st.rerun()

    # ========================================================================
    # MAIN CONTENT
    # ========================================================================

    if not st.session_state.calibration_session_id:
        st.info("👉 Clique em 'Iniciar Nova Calibração' para começar")
        return

    # Instructions
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📝 Instruções")
        st.write("""
        1. **Posicione a cabeça** confortavelmente a ~50cm da tela
        2. **Evite movimentos** bruscos de cabeça
        3. **Siga o ponto** com o olhar
        4. **Mantenha os olhos abertos** durante toda a calibração
        5. **Qualidade da luz** é importante
        """)

    with col2:
        st.metric("Progresso", f"{len(st.session_state.calibration_points)}/9")

    st.divider()

    # ========================================================================
    # WEBCAM FEED & CALIBRATION GRID
    # ========================================================================

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📷 Feed da Câmera")
        webcam_placeholder = st.empty()

    with col2:
        st.subheader("🎯 Grade de Calibração")
        grid_placeholder = st.empty()

    # Initialize detectors if not already done
    if st.session_state.face_detector is None:
        try:
            st.session_state.face_detector = FaceDetector(
                min_detection_confidence=MEDIAPIPE_FACE_DETECTION_MIN_CONFIDENCE
            )
            st.session_state.gaze_estimator = GazeEstimator()
            st.info("✅ Detectores de rosto e estimador de gaze carregados")
        except Exception as e:
            st.error(f"Erro ao carregar modelos: {str(e)}")
            return

    # Get calibration points
    calibration_grid = get_calibration_grid(GAZE_CALIBRATION_POINTS)

    # Webcam capture
    run = st.checkbox("Iniciar Câmera", value=False)

    if run:
        from PIL import Image
        import cv2

        # Always show calibration grid immediately so user knows where to look
        current_idx = st.session_state.current_calibration_index
        if current_idx < len(calibration_grid):
            target_x, target_y = calibration_grid[current_idx]

            grid_image = Image.new("RGB", (400, 400), color="white")
            pixels = grid_image.load()

            for idx, (x, y) in enumerate(calibration_grid):
                px, py = int(x * 400), int(y * 400)
                color = (255, 0, 0) if idx == current_idx else (180, 180, 180)
                for dx in range(-10, 11):
                    for dy in range(-10, 11):
                        if dx * dx + dy * dy <= 100:  # circle shape
                            if 0 <= px + dx < 400 and 0 <= py + dy < 400:
                                pixels[px + dx, py + dy] = color

            # Crosshair on current point
            px, py = int(target_x * 400), int(target_y * 400)
            for i in range(-25, 26):
                if 0 <= px + i < 400:
                    pixels[px + i, py] = (200, 0, 0)
                if 0 <= py + i < 400:
                    pixels[px, py + i] = (200, 0, 0)

            grid_placeholder.image(grid_image, use_column_width=True)

            st.info(f"👁️ **Olhe para o ponto vermelho** e clique em 'Capturar' para registrar")

        # Camera capture
        camera_input = st.camera_input("📸 Capturar amostra do olhar")

        if camera_input is not None:
            image = Image.fromarray(np.array(camera_input))
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            webcam_placeholder.image(image, use_column_width=True)

            # Detect face
            face_list = st.session_state.face_detector.detect(image_cv)

            if face_list:
                st.success("✅ Rosto detectado — pronto para coletar")

                current_idx = st.session_state.current_calibration_index
                if current_idx < len(calibration_grid):
                    target_x, target_y = calibration_grid[current_idx]

                    if st.button(
                        f"📍 Registrar Amostra {current_idx + 1}/9",
                        use_container_width=True,
                        type="primary",
                    ):
                        try:
                            sample = collect_calibration_sample(
                                session_id=st.session_state.calibration_session_id,
                                point_index=current_idx,
                                screen_x=target_x,
                                screen_y=target_y,
                                gaze_estimator=st.session_state.gaze_estimator,
                                face_landmarks=face_list[0],
                            )

                            if sample:
                                st.success(
                                    f"✅ Amostra {current_idx + 1} registrada "
                                    f"(erro: {sample.distance_pixels:.1f}px)"
                                )
                                st.session_state.current_calibration_index += 1
                                st.rerun()
                            else:
                                st.error("❌ Falha ao coletar amostra — tente novamente")

                        except Exception as e:
                            st.error(f"Erro: {str(e)}")
            else:
                st.warning("⚠️ Nenhum rosto detectado — ajuste a posição e capture novamente")

    # ========================================================================
    # RESULTS & ACTIONS
    # ========================================================================

    st.divider()

    if st.session_state.calibration_points:
        st.subheader("📊 Resultados da Calibração")

        distances = [p.distance_pixels for p in st.session_state.calibration_points]
        mean_error = float(np.mean(distances))
        max_error = float(np.max(distances))

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Erro Médio", f"{mean_error:.1f}px")

        with col2:
            st.metric("Erro Máximo", f"{max_error:.1f}px")

        with col3:
            validity = max(0.0, 1.0 - (mean_error / 100.0))
            st.metric("Validade", f"{validity:.0%}")

        # Chart of errors
        st.line_chart({
            "Erro (pixels)": distances,
            "Limiar": [30] * len(distances),
        })

        # Save calibration
        col1, col2 = st.columns(2)

        with col1:
            if st.button(
                "💾 Salvar Calibração",
                use_container_width=True,
                type="primary",
            ):
                if save_calibration_session(st.session_state.calibration_session_id):
                    st.success("✅ Calibração salva com sucesso!")
                    st.balloons()

        with col2:
            if st.button("🔄 Recalibrar", use_container_width=True):
                st.session_state.calibration_points = []
                st.session_state.current_calibration_index = 0
                st.rerun()


if __name__ == "__main__":
    render_calibration_interface()
