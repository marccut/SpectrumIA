"""
SpectrumIA - Eye-tracking based screening tool for Autism Spectrum Disorder

Main Streamlit application entry point.
"""

import sys
from pathlib import Path
import streamlit as st

# Add core to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import APP_VERSION, APP_DEBUG, validate_config

# Page Configuration
st.set_page_config(
    page_title="SpectrumIA - ASD Screening Tool",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Validate configuration on startup
try:
    validate_config()
except ValueError as e:
    st.error(f"Configuration Error: {e}")
    st.stop()

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        margin-bottom: 1rem;
    }
    .card {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
    }
    .warning-card {
        background-color: #fff3cd;
        padding: 1.5rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #ff9800;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = str(uuid.uuid4())

if "calibration_complete" not in st.session_state:
    st.session_state.calibration_complete = False

if "assessment_complete" not in st.session_state:
    st.session_state.assessment_complete = False

# Main Title
st.markdown("""
<div class='main-header'>
    <h1>🧠 SpectrumIA</h1>
    <p class='subtitle'>Eye-Tracking Based Screening Tool for Autism Spectrum Disorder</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Select a page:",
    ["Home", "Calibration", "Assessment", "Results"],
    help="Navigate through different sections of the application"
)

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Version:** {APP_VERSION}")
if APP_DEBUG:
    st.sidebar.markdown("🔧 **Debug Mode ON**")
    st.sidebar.markdown(f"Session ID: `{st.session_state.session_id[:8]}...`")

# Main Content
if page == "Home":
    st.markdown("""
    <div class='card'>
        <h3>Welcome to SpectrumIA</h3>
        <p>
        SpectrumIA is an <strong>eye-tracking based screening tool</strong> designed to assist in the identification
        of Autism Spectrum Disorder (ASD), with special focus on reducing diagnostic delays in women and adults.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🎯 Key Features")
        st.markdown("""
        - **Real-time Eye Tracking** — Webcam-based gaze estimation
        - **Social Attention Analysis** — Measures attention patterns
        - **Validated Biomarkers** — Based on peer-reviewed research
        - **Female Phenotype Focus** — Detects camouflaging patterns
        - **Explainable AI** — Transparent results
        """)

    with col2:
        st.markdown("### ⚠️ Important Disclaimer")
        st.markdown("""
        **This is a screening tool, NOT a diagnostic instrument.**

        - Results should be interpreted by qualified healthcare professionals
        - Positive screening should be followed by comprehensive clinical evaluation
        - Not intended to replace established diagnostic procedures
        """)

    st.markdown("---")
    st.markdown("### 🚀 Getting Started")
    st.markdown("""
    1. **Calibration** — Complete a 9-point gaze calibration
    2. **Assessment** — View assessment stimuli while eye-tracking records your gaze
    3. **Results** — Review eye-tracking metrics and screening indicators
    """)

elif page == "Calibration":
    st.header("📍 Gaze Calibration")
    st.markdown("""
    <div class='warning-card'>
        <strong>⚠️ Calibration Required</strong><br>
        Before taking the assessment, please complete a 9-point gaze calibration to ensure accurate eye-tracking.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### Setup Instructions")
    st.markdown("""
    1. Position yourself 60-80 cm from the screen
    2. Ensure adequate lighting on your face
    3. Keep your head relatively still during calibration
    4. Follow the calibration points with your eyes (not your head)
    """)

    if st.button("Start Calibration", key="calibration_btn"):
        st.info("Calibration interface would load here in the next phase of development.")
        st.session_state.calibration_complete = True

    if st.session_state.calibration_complete:
        st.success("✓ Calibration completed successfully!")

elif page == "Assessment":
    st.header("📹 Assessment Session")

    if not st.session_state.calibration_complete:
        st.warning("Please complete calibration first before starting the assessment.")
        st.info("Go to the **Calibration** page to get started.")
    else:
        st.markdown("""
        <div class='card'>
            <strong>Assessment Setup</strong><br>
            The assessment will show you short video clips of social scenes.
            Your eye-tracking data will be recorded and analyzed.
        </div>
        """, unsafe_allow_html=True)

        if st.button("Start Assessment", key="assessment_btn"):
            st.info("Assessment interface would load here in the next phase of development.")
            st.session_state.assessment_complete = True

        if st.session_state.assessment_complete:
            st.success("✓ Assessment completed!")

elif page == "Results":
    st.header("📊 Assessment Results")

    if not st.session_state.assessment_complete:
        st.warning("Please complete the assessment first to view results.")
    else:
        st.markdown("""
        <div class='card'>
            <strong>Results Analysis</strong><br>
            Detailed eye-tracking metrics and screening indicators would be displayed here.
        </div>
        """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #999; font-size: 0.9rem;'>
    <p>SpectrumIA v{} | Built with ❤️ for neurodiversity awareness</p>
    <p>⚠️ <strong>Disclaimer:</strong> This is a screening tool, not a diagnostic instrument.
    Results must be interpreted by qualified healthcare professionals.</p>
</div>
""".format(APP_VERSION), unsafe_allow_html=True)
