"""
SpectrumIA Calibration Page

Gaze calibration session with 9-point calibration grid.
Collects calibration samples and validates eye-tracking accuracy.

Integração:
- Supabase: CalibrationSession storage
- Core: Face detection e gaze estimation
- Real-time: Validation feedback
"""

import sys
from pathlib import Path
import streamlit as st
import numpy as np
from datetime import datetime, timezone
import logging
import uuid
from typing import Optional, List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.auth import get_access_token, get_auth, initialize_session_state as init_auth_state
from core.config import (
    GAZE_CALIBRATION_POINTS,
    MEDIAPIPE_FACE_DETECTION_MIN_CONFIDENCE,
    MEDIAPIPE_FACE_MESH_MIN_TRACKING_CONFIDENCE,
)
from core.face_detection import FaceDetector
from core.gaze_estimation import GazeEstimator
from models.schemas import (
    CalibrationPoint,
    CalibrationSessionCreate,
    CalibrationSessionResponse,
)
from models.database import get_db

logger = logging.getLogger(__name__)


def _is_permission_error(exc: Exception) -> bool:
    """Detect Supabase permission/RLS failures that should fall back to demo mode."""
    error_text = " | ".join(
        part for part in [str(exc), repr(exc), str(getattr(exc, "args", ""))] if part
    ).lower()
    return (
        "row-level security" in error_text
        or "violates row-level security" in error_text
        or "42501" in error_text
        or "permission denied" in error_text
    )


def _should_use_local_mode() -> bool:
    """Use local mode when there is no persisted Supabase auth session."""
    user_data = st.session_state.get("user_data") or {}
    return not user_data.get("session")


def _start_demo_calibration_session(user_id: str, num_points: int):
    """Create an in-memory calibration session when persistence is unavailable."""
    logger.info("Demo mode: Creating mock calibration session")
    mock_session_id = str(uuid.uuid4())
    st.session_state.calibration_session_id = mock_session_id
    st.session_state.calibration_id = mock_session_id
    st.session_state.calibration_status = "in_progress"
    return {
        "calibration_id": mock_session_id,
        "num_points": num_points,
        "calibration_distance_cm": 50.0,
    }


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
    if "enable_face_mesh" not in st.session_state:
        st.session_state.enable_face_mesh = False
    if "face_mesh_available" not in st.session_state:
        st.session_state.face_mesh_available = True
    if "face_mesh_init_error" not in st.session_state:
        st.session_state.face_mesh_init_error = None


def _ensure_detection_models() -> bool:
    """Load face detection models only on demand and only once after a failure."""
    if st.session_state.face_detector is not None and st.session_state.gaze_estimator is not None:
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
        st.session_state.face_mesh_init_error = None
        st.success("✅ Detectores de rosto e estimador de gaze carregados")
        return True
    except Exception as e:
        st.session_state.face_mesh_available = False
        st.session_state.face_mesh_init_error = str(e)
        st.error("Erro ao carregar modelos.")
        st.warning("⚠️ A análise facial avançada foi desativada nesta sessão para evitar looping.")
        st.caption(str(e))
        return False


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
    if _should_use_local_mode():
        logger.info("Calibration running in local mode: no Supabase session available")
        return _start_demo_calibration_session(user_id, num_points)

    try:
        db = get_db(get_access_token())
    except ValueError:
        return _start_demo_calibration_session(user_id, num_points)

    try:
        calibration_data = CalibrationSessionCreate(
            user_id=user_id,
            num_points=num_points,
            calibration_distance_cm=50.0
        )
        session: CalibrationSessionResponse = db.create_calibration_session(calibration_data)
        st.session_state.calibration_session_id = session.calibration_id
        st.session_state.calibration_id = session.calibration_id  # ← Also set calibration_id for Assessment
        st.session_state.calibration_status = "in_progress"
        logger.info(f"Calibration session created: {session.calibration_id}")
        return session
    except Exception as e:
        logger.error(f"Error creating calibration session: {e}")
        warning_message = (
            "Não foi possível criar a sessão no Supabase. "
            "Continuando em modo demo/local para você seguir com a calibração."
        )
        if _is_permission_error(e):
            warning_message = (
                "Sem permissão para gravar no Supabase com a política atual. "
                "Continuando em modo demo/local para você seguir com a calibração."
            )
        st.warning(warning_message)
        return _start_demo_calibration_session(user_id, num_points)


def collect_calibration_sample(
    session_id: str,
    point_index: int,
    screen_x: float,
    screen_y: float,
    gaze_estimator: GazeEstimator,
    face_landmarks,
) -> Optional[CalibrationPoint]:
    """
    Collect a single calibration sample.

    Args:
        session_id: Calibration session ID
        point_index: Index of calibration point
        screen_x: Target X coordinate (0-1)
        screen_y: Target Y coordinate (0-1)
        gaze_estimator: GazeEstimator instance
        face_landmarks: FaceLandmarks object

    Returns:
        CalibrationPoint if successful, None otherwise
    """
    try:
        if face_landmarks is None:
            logger.error("Invalid face landmarks")
            return None

        if not face_landmarks.face_detected:
            logger.warning("Face not detected in landmarks")
            return None

        gaze_point = gaze_estimator.estimate_gaze(face_landmarks)

        if gaze_point is None:
            logger.warning(f"Gaze estimation returned None for point {point_index}")
            return None

        gaze_x, gaze_y = gaze_point.gaze_x, gaze_point.gaze_y

        point = CalibrationPoint(
            point_id=f"{session_id}_{point_index}",
            screen_x=screen_x,
            screen_y=screen_y,
            gaze_x=gaze_x,
            gaze_y=gaze_y,
            timestamp=datetime.now(timezone.utc).timestamp(),
            confidence=gaze_point.gaze_confidence,
            distance_pixels=np.sqrt(
                (gaze_x - screen_x) ** 2 + (gaze_y - screen_y) ** 2
            ) * 1000,
        )

        st.session_state.calibration_points.append(point)
        logger.info(f"Calibration sample {point_index} collected successfully")
        return point

    except Exception as e:
        logger.error(f"Error collecting calibration sample: {str(e)}", exc_info=True)
        return None


def save_calibration_session(session_id: str) -> bool:
    """Save completed calibration session to database."""
    if _should_use_local_mode():
        logger.info("Saving calibration in local mode: no Supabase session available")
        if not st.session_state.calibration_points:
            st.error("Nenhum ponto de calibração coletado")
            return False

        points = st.session_state.calibration_points
        distances = [p.distance_pixels for p in points]
        mean_error = float(np.mean(distances)) if distances else 0.0
        st.session_state.calibration_status = "completed"
        st.session_state.calibration_id = session_id
        st.session_state.active_calibration_id = session_id
        st.session_state.is_calibrated = True
        st.success(f"✅ Calibração concluída localmente (erro médio: {mean_error:.1f}px)")
        return True

    try:
        db = get_db(get_access_token())
    except ValueError:
        logger.info("Demo mode: Simulating calibration session save")
        if not st.session_state.calibration_points:
            st.error("Nenhum ponto de calibração coletado")
            return False

        points = st.session_state.calibration_points
        distances = [p.distance_pixels for p in points]
        mean_error = float(np.mean(distances)) if distances else 0.0

        st.session_state.calibration_status = "completed"
        st.session_state.calibration_id = session_id
        st.session_state.active_calibration_id = session_id
        st.session_state.is_calibrated = True

        logger.info(f"Demo mode: Calibration saved with mean error {mean_error:.1f}px")
        st.success("✅ Calibração salva com sucesso! (modo demo)")
        return True

    try:
        if not st.session_state.calibration_points:
            st.error("Nenhum ponto de calibração coletado")
            return False

        points = st.session_state.calibration_points
        distances = [p.distance_pixels for p in points]

        mean_error = float(np.mean(distances)) if distances else 0.0
        max_error = float(np.max(distances)) if distances else 0.0

        validity_score = max(0.0, 1.0 - (mean_error / 100.0))

        updates = {
            "status": "completed",
            "calibration_points": [p.model_dump() for p in points],
            "mean_error_pixels": mean_error,
            "max_error_pixels": max_error,
            "validity_score": validity_score,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

        session = db.update_calibration_session(session_id, updates)
        logger.info(f"Calibration session saved: {session_id}")

        st.session_state.calibration_status = "completed"
        st.session_state.calibration_id = session_id
        st.session_state.active_calibration_id = session_id
        st.session_state.is_calibrated = True

        return True

    except Exception as e:
        logger.error(f"Error saving calibration session: {e}")
        distances = [p.distance_pixels for p in st.session_state.calibration_points]
        mean_error = float(np.mean(distances)) if distances else 0.0
        st.session_state.calibration_status = "completed"
        st.session_state.calibration_id = session_id
        st.session_state.active_calibration_id = session_id
        st.session_state.is_calibrated = True
        if _is_permission_error(e):
            logger.info(
                "Permission denied while saving calibration. "
                "Keeping the session locally in demo mode."
            )
            st.warning(
                "Sem permissão para salvar a calibração no Supabase. "
                "A calibração foi mantida localmente para você continuar o fluxo."
            )
        else:
            st.warning(
                "Falha ao salvar no banco. "
                "A calibração foi mantida localmente para você continuar o fluxo."
            )
        st.success(f"✅ Calibração concluída localmente (erro médio: {mean_error:.1f}px)")
        return True


def render_calibration_interface():
    """Render main calibration interface."""
    init_auth_state()
    auth = get_auth()
    if not auth.is_authenticated():
        st.error("❌ Please login first")
        st.info("Go to the main page and authenticate before opening Calibration.")
        st.stop()

    st.title("👁️ Calibração de Rastreamento Ocular")
    st.markdown(
        "Calibração de 9 pontos para otimizar a precisão do rastreamento ocular"
    )

    initialize_session_state()

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
    # WEBCAM FEED & CALIBRATION GRID
    # ========================================================================

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📷 Feed da Câmera")
        webcam_placeholder = st.empty()

    with col2:
        st.subheader("🎯 Grade de Calibração")
        grid_placeholder = st.empty()

    if not _ensure_detection_models():
        return

    calibration_grid = get_calibration_grid(GAZE_CALIBRATION_POINTS)

    run = st.checkbox("Iniciar Câmera", value=False)

    if run:
        camera_input = st.camera_input("Câmera")

        if camera_input is not None:
            from PIL import Image
            import cv2

            image = Image.open(camera_input)
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            face_list = st.session_state.face_detector.detect(image_cv)

            if face_list:
                st.success(f"✅ Rosto detectado")

                current_idx = st.session_state.current_calibration_index
                if current_idx < len(calibration_grid):
                    target_x, target_y = calibration_grid[current_idx]

                    col1, col2 = st.columns(2)

                    with col1:
                        webcam_placeholder.image(image, use_container_width=True)

                    with col2:
                        grid_image = Image.new("RGB", (400, 400), color="white")
                        pixels = grid_image.load()

                        for idx, (x, y) in enumerate(calibration_grid):
                            px, py = int(x * 400), int(y * 400)
                            color = (255, 0, 0) if idx == current_idx else (200, 200, 200)
                            for dx in range(-8, 9):
                                for dy in range(-8, 9):
                                    if 0 <= px + dx < 400 and 0 <= py + dy < 400:
                                        pixels[px + dx, py + dy] = color

                        if current_idx < len(calibration_grid):
                            px, py = int(target_x * 400), int(target_y * 400)
                            for i in range(-20, 21):
                                if 0 <= px + i < 400:
                                    pixels[px + i, py] = (255, 0, 0)
                                if 0 <= py + i < 400:
                                    pixels[px, py + i] = (255, 0, 0)

                        grid_placeholder.image(grid_image, use_container_width=True)

                    if st.button(
                        f"📍 Coletar Amostra {current_idx + 1}/9",
                        use_container_width=True,
                    ):
                        try:
                            h, w = image_cv.shape[:2]
                            focal_length = w
                            camera_matrix = np.array(
                                [[focal_length, 0, w / 2],
                                 [0, focal_length, h / 2],
                                 [0, 0, 1]]
                            )

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
                                    f"✅ Amostra {current_idx + 1} coletada "
                                    f"(erro: {sample.distance_pixels:.1f}px)"
                                )
                                st.session_state.current_calibration_index += 1
                                st.rerun()
                            else:
                                st.error("❌ Falha ao coletar amostra. Verifique o console para detalhes.")
                                st.info("💡 Dica: Certifique-se de que o rosto está bem visível e a câmera está clara.")

                        except Exception as e:
                            st.error(f"❌ Erro ao coletar amostra: {str(e)}")
                            logger.exception(f"Exception during sample collection: {e}")

            else:
                st.warning("⚠️ Nenhum rosto detectado. Ajuste a posição.")

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

        st.line_chart({
            "Erro (pixels)": distances,
            "Limiar": [30] * len(distances),
        })

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


render_calibration_interface()
