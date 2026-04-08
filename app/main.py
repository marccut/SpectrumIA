"""
SpectrumIA - Eye-tracking based screening tool for Autism Spectrum Disorder

Main Streamlit application entry point with authentication.
"""

import sys
from pathlib import Path
import streamlit as st
import hashlib
import uuid

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
    .login-container {
        max-width: 400px;
        margin: 2rem auto;
        padding: 2rem;
        background-color: #f8f9fa;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .user-info {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #17a2b8;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "user_email" not in st.session_state:
    st.session_state.user_email = None

if "user_name" not in st.session_state:
    st.session_state.user_name = None

if "calibration_complete" not in st.session_state:
    st.session_state.calibration_complete = False

if "assessment_complete" not in st.session_state:
    st.session_state.assessment_complete = False

# IMPORTANT: Initialize current_page BEFORE authentication check
if "current_page" not in st.session_state:
    st.session_state.current_page = "Home"


# Authentication functions
def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_credentials(email: str, password: str) -> bool:
    """Verify user credentials. In production, this would query a database."""
    # Demo credentials - In production, replace with database query
    demo_users = {
        "demo@spectrum.ai": hash_password("demo123"),
        "test@spectrum.ai": hash_password("test123"),
    }

    if email in demo_users:
        return demo_users[email] == hash_password(password)
    return False


def extract_name_from_email(email: str) -> str:
    """Extract a friendly name from email."""
    return email.split("@")[0].replace(".", " ").title()


def show_login_page():
    """Display login page."""
    st.markdown("""
    <div class='main-header'>
        <h1>🧠 SpectrumIA</h1>
        <p class='subtitle'>Eye-Tracking Based Screening Tool for Autism Spectrum Disorder</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class='login-container'>
    """, unsafe_allow_html=True)

    st.markdown("## Login")

    col1, col2 = st.columns([1, 2], gap="large")

    with col2:
        email = st.text_input(
            "Email",
            placeholder="example@spectrum.ai",
            help="Enter your email address"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
            help="Enter your password"
        )

        if st.button("Login", key="login_btn", use_container_width=True):
            if not email or not password:
                st.error("❌ Please enter both email and password")
            elif verify_credentials(email, password):
                st.session_state.authenticated = True
                st.session_state.user_email = email
                st.session_state.user_name = extract_name_from_email(email)
                st.success(f"✅ Welcome, {st.session_state.user_name}!")
                st.rerun()
            else:
                st.error("❌ Invalid email or password")

        st.markdown("---")
        st.markdown("### 📝 Demo Credentials")
        st.markdown("""
        **Email:** `demo@spectrum.ai`
        **Password:** `demo123`

        or

        **Email:** `test@spectrum.ai`
        **Password:** `test123`
        """)

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("""
    ### ℹ️ About SpectrumIA

    SpectrumIA is an **eye-tracking based screening tool** designed to assist in the identification
    of Autism Spectrum Disorder (ASD), with special focus on reducing diagnostic delays in women and adults.

    **Note:** This is a screening tool, not a diagnostic instrument. Results must be interpreted
    by qualified healthcare professionals.
    """)

# Check authentication
if not st.session_state.authenticated:
    show_login_page()
    st.stop()

# Main Title (only shown when authenticated)
st.markdown("""
<div class='main-header'>
    <h1>🧠 SpectrumIA</h1>
    <p class='subtitle'>Eye-Tracking Based Screening Tool for Autism Spectrum Disorder</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Navigation - User Info and Logout
st.sidebar.markdown(f"""
<div class='user-info'>
    <strong>👤 Logged in as:</strong><br>
    {st.session_state.user_name}<br>
    <span style='font-size: 0.9rem; color: #666;'>{st.session_state.user_email}</span>
</div>
""", unsafe_allow_html=True)

col_home, col_logout = st.sidebar.columns(2)
with col_home:
    if st.button("🏠 Home", use_container_width=True, key="home_btn"):
        st.session_state.current_page = "Home"

with col_logout:
    if st.button("🚪 Logout", use_container_width=True, key="logout_btn"):
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.session_state.user_name = None
        st.session_state.calibration_complete = False
        st.session_state.assessment_complete = False
        st.success("✅ Logged out successfully!")
        st.rerun()

st.sidebar.markdown("---")

# Sidebar Navigation
st.sidebar.title("Navigation")

# Create page list
pages = ["Home", "Calibration", "Assessment", "Results"]

# Get current page index safely
try:
    current_index = pages.index(st.session_state.current_page)
except (ValueError, IndexError):
    current_index = 0
    st.session_state.current_page = "Home"

page = st.sidebar.radio(
    "Select a page:",
    pages,
    index=current_index,
    help="Navigate through different sections of the application",
    key="page_radio"
)

# Update current page
st.session_state.current_page = page

st.sidebar.markdown("---")
st.sidebar.markdown(f"**Version:** {APP_VERSION}")
st.sidebar.markdown(f"**Session ID:** `{st.session_state.session_id[:8]}...`")
if APP_DEBUG:
    st.sidebar.markdown("🔧 **Debug Mode ON**")

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

    # Track calibration status in this session
    if "calibration_status" not in st.session_state:
        st.session_state.calibration_status = "not_started"

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

    # Show button if not in progress or completed
    if st.session_state.calibration_status == "not_started":
        if st.button("▶️ Start Calibration", key="calibration_btn", use_container_width=True):
            st.session_state.calibration_status = "in_progress"
            st.session_state.calibration_complete = True
            st.rerun()

    # Show progress if in calibration
    elif st.session_state.calibration_status == "in_progress":
        st.info("📹 Calibration interface would load here in the next phase of development.")
        st.info("In development: 9-point gaze calibration with real-time feedback")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Complete Calibration", use_container_width=True):
                st.session_state.calibration_status = "completed"
                st.session_state.calibration_complete = True
                st.rerun()
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.calibration_status = "not_started"
                st.session_state.calibration_complete = False
                st.rerun()

    # Show completion message
    if st.session_state.calibration_status == "completed":
        st.success("✅ Calibration completed successfully!")
        st.info("You can now proceed to the Assessment page.")

        if st.button("🔄 Redo Calibration", key="redo_calibration_btn", use_container_width=True):
            st.session_state.calibration_status = "not_started"
            st.session_state.calibration_complete = False
            st.rerun()

elif page == "Assessment":
    st.header("📹 Assessment Session")

    # Track assessment status in this session
    if "assessment_status" not in st.session_state:
        st.session_state.assessment_status = "not_started"

    if not st.session_state.calibration_complete:
        st.warning("⚠️ Please complete calibration first before starting the assessment.")
        st.info("📍 Go to the **Calibration** page to get started.")
    else:
        st.markdown("""
        <div class='card'>
            <strong>Assessment Setup</strong><br>
            The assessment will show you short video clips of social scenes.
            Your eye-tracking data will be recorded and analyzed.
        </div>
        """, unsafe_allow_html=True)

        # Show button if not in progress or completed
        if st.session_state.assessment_status == "not_started":
            if st.button("▶️ Start Assessment", key="assessment_btn", use_container_width=True):
                st.session_state.assessment_status = "in_progress"
                st.session_state.assessment_complete = True
                st.rerun()

        # Show progress if in assessment
        elif st.session_state.assessment_status == "in_progress":
            st.info("📹 Assessment interface would load here in the next phase of development.")
            st.info("In development: Assessment with eye-tracking recording and analysis")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Complete Assessment", use_container_width=True):
                    st.session_state.assessment_status = "completed"
                    st.session_state.assessment_complete = True
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", use_container_width=True):
                    st.session_state.assessment_status = "not_started"
                    st.session_state.assessment_complete = False
                    st.rerun()

        # Show completion message
        if st.session_state.assessment_status == "completed":
            st.success("✅ Assessment completed successfully!")
            st.info("You can now view your results in the Results page.")

            if st.button("🔄 Redo Assessment", key="redo_assessment_btn", use_container_width=True):
                st.session_state.assessment_status = "not_started"
                st.session_state.assessment_complete = False
                st.rerun()

elif page == "Results":
    st.header("📊 Assessment Results")

    if not st.session_state.calibration_complete:
        st.warning("⚠️ Please complete calibration first.")
        st.info("📍 Go to the **Calibration** page to get started.")
    elif not st.session_state.assessment_complete:
        st.warning("⚠️ Please complete the assessment first to view results.")
        st.info("📹 Go to the **Assessment** page to get started.")
    else:
        st.success("✅ Assessment completed successfully!")
        st.markdown("""
        <div class='card'>
            <strong>📊 Results Analysis</strong><br>
            Detailed eye-tracking metrics and screening indicators would be displayed here in the next phase of development.

            **Planned metrics:**
            - Social Attention Index (SAI)
            - Fixation patterns
            - Gaze dynamics
            - Risk assessment score
        </div>
        """, unsafe_allow_html=True)

        st.info("ℹ️ Results are generated based on calibration and assessment data.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #999; font-size: 0.9rem;'>
    <p>SpectrumIA v{} | Built with ❤️ for neurodiversity awareness</p>
    <p>⚠️ <strong>Disclaimer:</strong> This is a screening tool, not a diagnostic instrument.
    Results must be interpreted by qualified healthcare professionals.</p>
</div>
""".format(APP_VERSION), unsafe_allow_html=True)
