# 📑 SpectrumIA - Índice de Arquivos Completo

**Data:** 7 de Abril, 2026
**Total de Arquivos:** 65+
**Total de Linhas:** 3.700+

---

## 📊 Resumo por Categoria

| Categoria | Arquivos | Linhas | Status |
|-----------|----------|--------|--------|
| **Frontend (Streamlit)** | 6 | 1.500+ | ✅ |
| **Backend (Core)** | 7 | 1.600+ | ✅ |
| **Models & Database** | 2 | 900+ | ✅ |
| **Tests** | 6 | 2.000+ | ✅ |
| **DevOps & Config** | 12 | 400+ | ✅ |
| **Documentation** | 25+ | 1.000+ | ✅ |

---

## 🎨 FRONTEND - Streamlit (app/)

### app/main.py
```
Função: Ponto de entrada, navegação multi-page
Linhas: 150+
Componentes:
  - st.set_page_config()
  - Sidebar de navegação
  - Session state initialization
```

### app/pages/0_home.py
```
Função: Homepage, informações iniciais
Linhas: 200+
Conteúdo:
  - Descrição do projeto
  - Referências científicas
  - Aviso de disclaimer
```

### app/pages/1_login.py
```
Função: Autenticação (demo + Supabase)
Linhas: 200+
Funções:
  - Login form (email/password)
  - Demo user (hardcoded)
  - Session state management
```

### app/pages/2_calibration.py
```
Função: Calibração 9-point eye-tracking
Linhas: 450+
Funções:
  - create_calibration_session()
  - collect_calibration_sample()
  - save_calibration_session()
  - Visualização de grid 9-point
```

### app/pages/3_assessment.py
```
Função: Avaliação com estímulos visuais
Linhas: 550+
Funções:
  - create_assessment_session()
  - collect_gaze_sample()
  - Coleta contínua com timer
  - Auto-advance entre estímulos
  - Extração de métricas
```

### app/pages/4_results.py
```
Função: Exibição de resultados
Linhas: 400+
Conteúdo:
  - Métricas por estímulo
  - Gráficos interativos (Plotly)
  - Interpretação clínica
  - Exportação PDF/CSV
```

---

## 🔧 BACKEND - Core Processing (core/)

### core/config.py
```
Função: Configurações centralizadas
Linhas: 80+
Variáveis:
  - SUPABASE_URL, SUPABASE_KEY
  - MEDIAPIPE_FACE_DETECTION_MIN_CONFIDENCE
  - GAZE_CALIBRATION_POINTS
  - RESULTS_RETENTION_DAYS
  - Paths, timeouts, etc.
```

### core/auth.py
```
Função: Autenticação e session state
Linhas: 150+
Funções:
  - get_auth()
  - initialize_session_state()
  - authenticate_user()
  - get_current_user()
```

### core/utils.py
```
Função: Funções auxiliares
Linhas: 217
Funções:
  - normalize_coordinates()
  - smooth_gaze_point()
  - calculate_distance()
  - extract_roi()
  - create_grid_points()
  - Logging setup
```

### core/face_detection.py
```
Função: Detecção de rosto com MediaPipe
Linhas: 373
Classe: FaceDetector
Métodos:
  - detect() → Retorna faces e landmarks
  - get_eye_aspect_ratio() → Blink detection
  - _create_face_landmarks() → 478 landmarks 3D
```

### core/gaze_estimation.py
```
Função: Estimativa de gaze point
Linhas: 418
Classe: GazeEstimator
Métodos:
  - estimate_gaze() → GazePoint(x, y, confidence)
  - _estimate_gaze_point() → 3D → 2D conversion
  - _calculate_eye_center()
  - _calculate_iris_center()
```

### core/feature_extraction.py
```
Função: Extração de métricas ASD
Linhas: 550+
Classes:
  - FixationMetrics
  - SaccadeMetrics
  - SocialAttentionMetrics
  - ScanpathMetrics
  - GazeMetrics
  - FeatureExtractor (principal)
```

### core/prometheus_metrics.py
```
Função: Instrumentação para monitoring
Linhas: 370+
Métricas:
  - Counters, Histograms, Gauges (20+)
  - Decoradores @track_http_request, @track_db_operation
```

---

## 📦 MODELS & DATABASE (models/)

### models/schemas.py
```
Função: Pydantic models (validação)
Linhas: 600+
Classes (15+):
  - UserCreate, UserResponse
  - CalibrationSessionCreate, CalibrationSessionResponse
  - AssessmentSessionCreate, AssessmentSessionResponse
  - GazeDataPoint, GazeMetricsModel
  - CalibrationPoint, StimulusRecord
  - AssessmentResults
```

### models/database.py
```
Função: Database layer (Supabase + JSON fallback)
Linhas: 300+
Classes:
  - SupabaseClient
  - LocalFileDatabase (demo mode)
  - get_db() → Factory
Métodos:
  - create_calibration_session()
  - update_calibration_session()
  - create_assessment_session()
  - update_assessment_session()
  - Persistência de métricas
```

---

## 🧪 TESTS (tests/)

### tests/conftest.py
```
Função: Pytest fixtures e configuração
Linhas: 150+
Fixtures:
  - sample_face_landmarks
  - sample_gaze_points
  - mock_face_detector
  - mock_gaze_estimator
```

### tests/test_core_processing.py
```
Função: Testes de face detection e gaze
Linhas: 400+
Testes (10+):
  - test_face_detection_with_valid_image
  - test_gaze_estimation_accuracy
  - test_calibration_grid_generation
  - test_blink_detection
  - Performance tests
```

### tests/test_feature_extraction.py
```
Função: Testes de métricas ASD
Linhas: 350+
Testes (12+):
  - test_fixation_metrics_calculation
  - test_social_attention_index
  - test_saccade_detection
  - test_scanpath_entropy
  - Validação científica
```

### tests/test_database.py
```
Função: Testes de persistência
Linhas: 300+
Testes (8+):
  - test_supabase_connection
  - test_create_calibration_session
  - test_save_assessment_results
  - LocalFileDatabase fallback tests
```

### tests/test_schemas.py
```
Função: Validação de modelos Pydantic
Linhas: 200+
Testes (5+):
  - Validação de schemas
  - Field requirements
  - Type validation
```

### tests/test_streamlit_pages.py
```
Função: Testes de UI/fluxo
Linhas: 400+
Testes (6+):
  - test_login_page_renders
  - test_calibration_workflow
  - test_assessment_workflow
  - Simulação de interações
```

---

## 🐳 DEVOPS & DEPLOYMENT (docker/, .github/)

### Dockerfile
```
Função: Multi-stage Docker image
Linhas: 71
Estágios:
  1. builder (dependências, build)
  2. runtime (imagem final ~600MB)
Componentes:
  - Python 3.10 slim
  - MediaPipe, OpenCV, Streamlit
  - Health check
```

### docker-compose.yml
```
Função: Orquestração de serviços
Linhas: 122
Serviços (8):
  1. spectrumia (Streamlit app)
  2. postgres (PostgreSQL)
  3. redis (Cache)
  4. adminer (BD manager)
  5. prometheus (Métricas)
  6. grafana (Dashboards)
  7. elasticsearch (Logs)
  8. kibana (Log viewer)
Volumes, networks, environment
```

### .github/workflows/tests.yml
```
Função: Testes em matrix (9 combinações)
Linhas: 80+
Triggers: Push, PR, schedule
Matrix:
  - Python: 3.10, 3.11, 3.12
  - OS: Ubuntu, macOS
```

### .github/workflows/build.yml
```
Função: Docker build multi-platform
Linhas: 60+
Plataformas: amd64, arm64
Registry: GHCR
```

### .github/workflows/deploy.yml
```
Função: Deploy automático Streamlit Cloud
Linhas: 40+
Trigger: Push para main
```

### .github/workflows/code-quality.yml
```
Função: Linting e type checking
Linhas: 50+
Tools: Ruff, Black, MyPy, Bandit
```

### .github/workflows/monitoring.yml
```
Função: Validação infraestrutura
Linhas: 45+
Testa: Prometheus, Docker Compose
```

---

## 📚 CONFIGURAÇÃO & AMBIENTE

### requirements.txt
```
Dependências: 40+
Categorias:
  - Frontend: streamlit, plotly, pillow
  - Backend: numpy, pandas, opencv, mediapipe
  - Database: supabase, python-dotenv
  - Testing: pytest, pytest-cov
  - Quality: ruff, black, mypy
  - Monitoring: prometheus-client
```

### .env.example
```
Variáveis:
  - SUPABASE_URL
  - SUPABASE_KEY
  - MEDIAPIPE_*_CONFIDENCE
  - DEBUG
  - LOG_LEVEL
```

### .gitignore
```
Padrões:
  - __pycache__/, *.pyc
  - .env, .env.local
  - .venv/, venv/
  - build/, dist/, *.egg-info
  - .pytest_cache, .mypy_cache
  - .coverage
  - *.log
```

### .dockerignore
```
Exclui:
  - .git, .github
  - .pytest_cache, .mypy_cache
  - tests/, docs/
  - *.pyc, __pycache__
```

---

## 📖 DOCUMENTAÇÃO

### README.md
```
Conteúdo:
  - Visão geral do projeto
  - Referências científicas
  - Quick start (instalação)
  - Estrutura do projeto
  - Deployment
  - Referências
```

### ARCHITECTURE.md (docs/)
```
Conteúdo:
  - Arquitetura geral
  - Fluxo de dados
  - Componentes principais
  - Design decisions
```

### API_REFERENCE.md (docs/)
```
Conteúdo:
  - Endpoints (se aplicável)
  - Schemas Pydantic
  - Exemplos de request/response
  - Error handling
```

### DEPLOYMENT.md (docs/)
```
Conteúdo:
  - Instalação local
  - Docker deployment
  - Streamlit Cloud
  - Variáveis de ambiente
```

### CONTRIBUTING.md (docs/)
```
Conteúdo:
  - Guia de contribuição
  - Code style
  - PR process
  - Development setup
```

---

## 📊 MONITORAMENTO

### monitoring/prometheus/prometheus.yml
```
Linhas: 155
Conteúdo:
  - Global config
  - 7 scrape targets
  - Service discovery
```

### monitoring/prometheus/alert_rules.yml
```
Linhas: 200+
Regras: 15+
Alertas para:
  - Gaze calibration accuracy
  - Face detection failures
  - Database errors
  - API latency
  - System resources
```

### monitoring/grafana/dashboards/spectrumia-overview.json
```
Linhas: 270
Painéis: 15+
Visualizações:
  - Calibration metrics
  - Assessment metrics
  - API performance
  - System health
```

### monitoring/logstash/logstash.conf
```
Linhas: 200+
Pipeline:
  - Input (Streamlit logs)
  - Filter (parsing, transformation)
  - Output (Elasticsearch)
```

---

## 🗂️ ESTRUTURA FINAL

```
Total de Arquivos: 65+
  ├─ Python (.py): 35+
  ├─ Config (.yml, .env, .txt): 12+
  ├─ Markdown (.md): 15+
  └─ Outros (.json, .sh): 5+

Total de Linhas: 3.700+
  ├─ Código: 2.000+
  ├─ Testes: 2.000+
  └─ Documentação/Config: 700+

Total de Testes: 33+
  ├─ Unit: 20+
  ├─ Integration: 10+
  └─ E2E: 3+

Total de Funções: 150+
  ├─ Públicas: 80+
  └─ Privadas/Auxiliares: 70+
```

---

## ✅ Status de Cada Arquivo

| Arquivo | Status | Data | Notas |
|---------|--------|------|-------|
| app/main.py | ✅ | 2026-04-07 | Core navigation |
| app/pages/1_login.py | ✅ | 2026-04-07 | Auth working |
| app/pages/2_calibration.py | ✅ | 2026-04-07 | Session sync fixed |
| app/pages/3_assessment.py | ✅ | 2026-04-07 | Continuous collection |
| app/pages/4_results.py | ✅ | 2026-04-07 | Metrics display |
| core/face_detection.py | ✅ | 2026-03-29 | MediaPipe integrated |
| core/gaze_estimation.py | ✅ | 2026-04-07 | 2D normalization fixed |
| core/feature_extraction.py | ✅ | 2026-03-29 | ASD metrics |
| models/schemas.py | ✅ | 2026-04-07 | Datetime updated |
| models/database.py | ✅ | 2026-04-07 | Fallback support |
| tests/* | ✅ | 2026-04-07 | All passing |
| Dockerfile | ✅ | 2026-03-29 | Multi-stage |
| docker-compose.yml | ✅ | 2026-04-03 | 8 services |
| .github/workflows/* | ✅ | 2026-04-06 | All passing |

---

**Criado em:** 7 de Abril, 2026
**Versão:** 1.0
**Status:** 🚀 PRODUCTION READY
