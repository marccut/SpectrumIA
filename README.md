# 🧠 SpectrumIA

**Eye-tracking based screening tool for Autism Spectrum Disorder (ASD)**

SpectrumIA uses scientifically validated eye-tracking biomarkers to assist in ASD screening, with special focus on reducing diagnostic delays in women and adults.

## ⚠️ Important Disclaimer

**This is a screening tool, NOT a diagnostic instrument.**

- Results should be interpreted by qualified healthcare professionals
- Positive screening should be followed by comprehensive clinical evaluation
- Not intended to replace established diagnostic procedures (ADOS-2, ADI-R)

## 🎯 Key Features

- **Real-time Eye Tracking** — WebRTC-based gaze estimation using webcam
- **Social Attention Analysis** — Measures attention to eyes, mouth, and social stimuli
- **Validated Biomarkers** — Based on Harvard/MGH, Duke, and meta-analysis research
- **Female Phenotype Focus** — Designed to detect camouflaging patterns
- **Explainable AI** — SHAP-based interpretability for clinical trust

## 📊 Scientific Foundation

| Metric | Accuracy | Source |
|--------|----------|--------|
| Eye-tracking meta-analysis | 81% | 24 studies, n=1,396 |
| Deep learning models | 98% | Recent CNN approaches |
| AVC (Harvard/MGH 2024) | 88-100% sens | Attention-to-Voice Congruence |
| SenseToKnow | AUC 0.92 | Duke University |

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- Webcam
- Modern web browser
- 60-80 cm distance from screen

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/spectrumaid.git
cd spectrumaid

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file and configure
cp .env.example .env
# Edit .env with your Supabase credentials
```

### First Run

```bash
# Validate configuration
python core/config.py

# Run the application
streamlit run app/main.py
```

Open `http://localhost:8501` in your browser.

## 📁 Project Structure

```
spectrumaid/
├── app/                          # Streamlit application
│   ├── main.py                  # Entry point
│   ├── pages/                   # Application pages
│   │   ├── calibration.py       # Gaze calibration
│   │   ├── assessment.py        # Assessment session
│   │   └── results.py           # Results dashboard
│   └── components/              # Reusable components
│       ├── webcam.py            # Webcam capture
│       ├── gaze_display.py      # Gaze visualization
│       └── heatmap.py           # Attention heatmap
│
├── core/                         # Core processing modules
│   ├── config.py                # Configuration management
│   ├── face_detection.py        # MediaPipe Face Mesh
│   ├── gaze_estimation.py       # Gaze point estimation
│   └── feature_extraction.py    # Eye-tracking metrics
│
├── models/                       # Data models
│   ├── schemas.py               # Pydantic schemas
│   └── database.py              # Supabase client
│
├── stimuli/                      # Visual stimuli
│   └── videos/                  # Assessment videos
│
├── tests/                        # Test suite
│   ├── test_config.py
│   ├── test_gaze_estimation.py
│   └── test_feature_extraction.py
│
├── requirements.txt              # Python dependencies
├── .env.example                  # Environment variables template
├── README.md                      # This file
└── .gitignore                    # Git ignore file
```

## 🔬 Metrics Extracted

### Social Attention
- **Social Attention Index (SAI)** — Time on eyes+mouth / total time on face
- **Eye Region Preference** — Relative attention to eye area
- **Geometric Preference** — Patterns vs faces preference

### Gaze Dynamics
- **Fixation Metrics** — Duration, count, spatial dispersion
- **Saccade Metrics** — Amplitude, velocity, peak velocity
- **Scanpath Entropy** — Predictability of gaze patterns

### Temporal Analysis
- **Time to First Fixation** — Latency to social regions
- **AOI Transitions** — Movement patterns between areas of interest
- **Gaze Stability** — Variability of gaze position

## 🛠️ Development

### Running Tests

```bash
pytest tests/ -v
pytest tests/ --cov=core --cov=models
```

### Code Quality

```bash
# Format code (Black)
black .

# Lint code (Ruff)
ruff check .

# Type checking (Mypy)
mypy core/ models/
```

### Configuration Validation

```bash
python core/config.py
```

## 🔗 Environment Variables

Create a `.env` file from `.env.example`:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key

# Eye-Tracking Configuration
GAZE_CALIBRATION_POINTS=9
GAZE_SMOOTHING_FACTOR=0.7
MIN_FIXATION_DURATION_MS=100

# Assessment Configuration
NUM_AOI_REGIONS=4
MIN_SAMPLES_PER_STIMULUS=30

# Application Settings
APP_DEBUG=False
LOG_LEVEL=INFO
```

## 📚 Scientific References

1. **Klin, A., et al.** (2002). Visual fixation patterns during viewing of naturalistic social situations. *Archives of General Psychiatry*, 59(9), 809-816.

2. **Jones, W., & Klin, A.** (2013). Attention to eyes is present but in decline in 2–6-month-old infants later diagnosed with autism. *Nature*, 504(7480), 427-431.

3. **Frazier, T. W., et al.** (2018). A meta-analysis of gaze differences to social and nonsocial information between individuals with and without autism. *Journal of Autism and Developmental Disorders*, 48(3), 845-855.

4. **Carpenter, K. L., et al.** (2021). Digital behavioral phenotyping detects atypical pattern of facial expression in toddlers with autism. *Autism Research*, 14(2), 357-368.

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Code Standards

- Follow PEP 8 (enforced by Black)
- Write tests for new features
- Include docstrings for all functions and classes
- Update README for significant changes

## 📄 License

MIT License — See LICENSE file for details.

---

**Built with ❤️ for neurodiversity awareness**

For questions or support, please open an issue on GitHub or contact the development team.
# SpectrumIA
# SpectrumIA
