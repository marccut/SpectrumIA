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
from datetime import datetime, timezone
import logging
import uuid
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
    FixationMetricsModel,
    GazeDataPoint,
    GazeMetricsModel,
    SaccadeMetricsModel,
    ScanpathMetricsModel,
    SocialAttentionMetricsModel,
    StimulusRecord,
)
from models.database import get_db
from stimuli.stimuli_config import get_stimuli_for_assessment, stimuli_ready, missing_stimuli

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


def _start_demo_assessment_session(user_id: str, calibration_id: str):
    """Create an in-memory assessment session when persistence is unavailable."""
    logger.info("Demo mode: Creating mock assessment session")
    mock_session_id = str(uuid.uuid4())
    st.session_state.assessment_session_id = mock_session_id
    st.session_state.assessment_status = "in_progress"
    return {
        "session_id": mock_session_id,
        "user_id": user_id,
        "calibration_id": calibration_id,
        "assessment_type": "asd_screening",
    }


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
    """Get list of stimuli for assessment (legacy dict format for compatibility)."""
    return [s.to_legacy_dict() for s in get_stimuli_for_assessment()]


def create_assessment_session(
    user_id: str,
    calibration_id: str
) -> Optional[AssessmentSessionResponse]:
    """Create a new assessment session in database."""
    if _should_use_local_mode():
        logger.info("Assessment running in local mode: no Supabase session available")
        return _start_demo_assessment_session(user_id, calibration_id)

    try:
        db = get_db()
    except ValueError:
        return _start_demo_assessment_session(user_id, calibration_id)

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
        if _is_permission_error(e):
            st.warning(
                "Sem permissão para gravar a sessão de avaliação no Supabase. "
                "Continuando em modo demo/local."
            )
        else:
            st.warning(
                "Falha ao criar a sessão de avaliação no banco. "
                "Continuando em modo demo/local."
            )
        return _start_demo_assessment_session(user_id, calibration_id)


def save_gaze_data(session_id: str, gaze_samples: List[GazeDataPoint]) -> bool:
    """Save gaze data to database."""
    if _should_use_local_mode():
        logger.info("Gaze data kept in local mode: no Supabase session available")
        return True

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
        if _is_permission_error(e):
            st.warning(
                "Sem permissão para salvar gaze data no Supabase. "
                "Os dados seguirão apenas localmente nesta sessão."
            )
        else:
            st.warning(
                "Falha ao salvar gaze data no banco. "
                "Os dados seguirão apenas localmente nesta sessão."
            )
        # Not persisted to the database — report failure honestly so callers
        # do not treat in-memory/local data as saved.
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

    Falls back to local-only (demo mode) when Supabase is unavailable or RLS blocks.
    """
    try:
        db = get_db()
    except ValueError:
        logger.info("Demo mode: metrics for stimulus '%s' kept in-memory only", stimulus_id)
        return True

    try:
        # 1. Persist raw gaze samples
        if gaze_samples:
            db.insert_gaze_data(session_id, gaze_samples)

        # 2. Persist extracted metrics
        db.insert_gaze_metrics(session_id, metrics)

        logger.info("Metrics and %d gaze samples saved for stimulus '%s'", len(gaze_samples), stimulus_id)
        return True

    except Exception as e:
        if _is_permission_error(e):
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
    if _should_use_local_mode():
        logger.info("Assessment completed in local mode: no Supabase session available")
        st.session_state.assessment_status = "completed"
        st.success("✅ Avaliação finalizada com sucesso! (modo local)")
        return True

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
        st.session_state.assessment_status = "completed"
        if _is_permission_error(e):
            st.warning(
                "Sem permissão para finalizar a avaliação no Supabase. "
                "A avaliação foi concluída localmente para você seguir no fluxo."
            )
        else:
            st.warning(
                "Falha ao finalizar a avaliação no banco. "
                "A avaliação foi concluída localmente para você seguir no fluxo."
            )
        return True


def render_assessment_interface():
    """Render main assessment interface."""
    init_auth_state()
    auth = get_auth()
    if not auth.is_authenticated():
        st.error("❌ Please login first")
        st.info("Go to the main page and authenticate before opening Assessment.")
        st.stop()

    st.title("🎬 Avaliação de Rastreamento Ocular")
    st.markdown(
        "Apresentação de estímulos visuais com coleta de dados de rastreamento ocular"
    )

    initialize_session_state()

    if "user_id" not in st.session_state:
        st.warning("Por favor, faça login primeiro na página principal")
        st.stop()

    user_id = st.session_state.user_id

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

    progress = (current_stimulus_idx + 1) / len(stimuli_list)
    st.progress(progress, text=f"Estímulo {current_stimulus_idx + 1}/{len(stimuli_list)}")

    st.subheader(f"🎯 {stimulus['name']}")
    st.write(stimulus['description'])

    col1, col2 = st.columns([2, 1])

    with col1:
        st.info(f"⏱️ Duração: {stimulus['duration_ms']/1000:.0f} segundos")

    with col2:
        st.metric("Tipo", stimulus['type'].replace("_", " ").upper())

    # ── Exibir imagem do estímulo ──────────────────────────────────────────────
    if stimulus.get("image_path"):
        from pathlib import Path as _Path
        img_path = _Path(stimulus["image_path"])
        if img_path.exists():
            st.image(
                str(img_path),
                caption=stimulus["name"],
                use_container_width=True,
            )
        else:
            st.warning(
                f"⚠️ Imagem não encontrada: {img_path.name}. "
                "Execute `python stimuli/generate_placeholders.py` para criar os placeholders."
            )
    else:
        st.info("ℹ️ Sem imagem definida para este estímulo.")

    # ── Configurar AOIs no extrator para este estímulo ────────────────────────
    if (
        st.session_state.get("feature_extractor") is not None
        and stimulus.get("aoi_coords")
    ):
        try:
            st.session_state.feature_extractor.set_aoi_definitions(stimulus["aoi_coords"])
        except Exception as _aoi_err:
            logger.warning(f"Não foi possível definir AOIs para {stimulus['id']}: {_aoi_err}")

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

    if not _ensure_detection_models():
        return

    run = st.checkbox("Iniciar Câmera", value=False)

    if run:
        camera_input = st.camera_input("Câmera")

        if camera_input is not None:
            from PIL import Image, ImageDraw
            import cv2

            image = Image.open(camera_input)
            image_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

            face_list = st.session_state.face_detector.detect(image_cv)

            if face_list:
                try:
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
                        gaze_px = int(sample.gaze_x * image.width)
                        gaze_py = int(sample.gaze_y * image.height)
                        draw.ellipse(
                            [(gaze_px - 10, gaze_py - 10),
                             (gaze_px + 10, gaze_py + 10)],
                            outline="red",
                            width=3
                        )

                        webcam_placeholder.image(image, use_container_width=True)

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
                if st.session_state.feature_extractor is None:
                    try:
                        st.session_state.feature_extractor = FeatureExtractor()
                    except Exception as e:
                        logger.error(f"Error initializing feature extractor: {e}")
                        st.error("Erro ao inicializar extrator de características")
                        st.session_state.gaze_samples = []
                        st.rerun()
                        return

                try:
                    import dataclasses as _dc
                    _raw = st.session_state.feature_extractor.extract_features(
                        stimulus_id=stimulus['id']
                    )
                    metrics = GazeMetricsModel(**_dc.asdict(_raw))
                except Exception as e:
                    logger.error(f"Error extracting features: {e}")
                    import time as _time
                    metrics = GazeMetricsModel(
                        timestamp=_time.time(),
                        stimulus_id=stimulus['id'],
                        fixations=FixationMetricsModel(),
                        saccades=SaccadeMetricsModel(),
                        social_attention=SocialAttentionMetricsModel(),
                        scanpath=ScanpathMetricsModel(),
                        signal_quality=0.0,
                    )
                    st.warning("Falha ao extrair características, usando valores padrão")

                save_stimulus_metrics(
                    st.session_state.assessment_session_id,
                    stimulus['id'],
                    metrics,
                    st.session_state.gaze_samples
                )
                st.session_state.gaze_samples = []
                if hasattr(st.session_state, 'feature_extractor') and st.session_state.feature_extractor:
                    st.session_state.feature_extractor.reset()
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


render_assessment_interface()
