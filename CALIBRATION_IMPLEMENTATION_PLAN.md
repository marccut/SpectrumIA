# 🎯 Plano de Implementação - Página de Calibração

**Data:** 8 de Abril de 2026  
**Fase:** 11 (Expansão após Produção)  
**Status:** PRONTO PARA DESENVOLVIMENTO

---

## 📊 Estado Atual vs. Esperado

### Estado Atual (Linhas 305-327 em `app/main.py`)

```python
elif page == "Calibration":
    st.header("📍 Gaze Calibration")
    
    # Placeholder - mostra apenas instruções
    st.markdown("### Setup Instructions")
    
    if st.button("Start Calibration", key="calibration_btn"):
        st.info("Calibration interface would load here...")
        st.session_state.calibration_complete = True
    
    if st.session_state.calibration_complete:
        st.success("✓ Calibration completed successfully!")
```

**Características Atuais:**
- ✅ Interface básica com instruções
- ✅ Botão "Start Calibration"
- ✅ State management para `calibration_complete`
- ❌ Sem acesso real à câmera
- ❌ Sem detecção facial
- ❌ Sem pontos de calibração visual
- ❌ Sem coleta de dados gaze

---

## 🎬 Estado Esperado (Fase 11)

### Componentes Necessários

```
Página de Calibração
├── 1. Instruções pré-calibração (EXISTENTE)
├── 2. Acesso à webcam (IMPLEMENTAR)
├── 3. Display de video feed (IMPLEMENTAR)
├── 4. Detecção facial em tempo real (IMPLEMENTAR)
├── 5. 9 pontos de calibração (IMPLEMENTAR)
├── 6. Coleta de gaze samples (IMPLEMENTAR)
├── 7. Cálculo de acurácia (IMPLEMENTAR)
├── 8. Retry logic se falhar (IMPLEMENTAR)
└── 9. Salvamento de dados (IMPLEMENTAR)
```

---

## 📋 Tarefas de Implementação

### Tarefa 1: Criar Componente de Webcam

**Arquivo:** `app/components/webcam_capture.py` (NOVO)

```python
"""Webcam capture component for Streamlit."""

import streamlit as st
import cv2
import numpy as np
from typing import Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class WebcamCapture:
    """Capture video frames from webcam."""
    
    def __init__(self, width: int = 640, height: int = 480):
        self.width = width
        self.height = height
        self.cap = None
    
    def start(self) -> bool:
        """Initialize camera."""
        try:
            self.cap = cv2.VideoCapture(0)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            return self.cap.isOpened()
        except Exception as e:
            logger.error(f"Failed to open camera: {e}")
            return False
    
    def get_frame(self) -> Optional[np.ndarray]:
        """Get single frame from camera."""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return None
    
    def release(self):
        """Release camera resource."""
        if self.cap:
            self.cap.release()
            logger.info("Camera released")

# Streamlit component
def streamlit_webcam():
    """Display webcam feed in Streamlit."""
    # TODO: Implementar component Streamlit
```

**Checklist:**
- [ ] Criar arquivo `app/components/webcam_capture.py`
- [ ] Implementar classe `WebcamCapture`
- [ ] Adicionar error handling para câmera não disponível
- [ ] Testar com câmera real
- [ ] Documentar permissões necessárias

---

### Tarefa 2: Integrar FaceDetector na Calibração

**Arquivo:** `app/pages/calibration.py` (NOVO ou refactor do main.py)

```python
"""Gaze calibration page."""

import streamlit as st
from core.face_detection import FaceDetector
from core.gaze_estimation import GazeEstimator
import numpy as np
import time

def show_calibration_page():
    """Display calibration interface."""
    
    st.header("📍 Gaze Calibration")
    
    # Session state para calibração
    if "calibration_points" not in st.session_state:
        st.session_state.calibration_points = []
    
    if "current_calibration_point" not in st.session_state:
        st.session_state.current_calibration_point = 0
    
    # Instruções
    st.info("Look at each calibration point for 1-2 seconds")
    
    # Layout de 9 pontos (3x3 grid)
    calibration_grid = [
        (0.1, 0.1), (0.5, 0.1), (0.9, 0.1),
        (0.1, 0.5), (0.5, 0.5), (0.9, 0.5),
        (0.1, 0.9), (0.5, 0.9), (0.9, 0.9),
    ]
    
    # Display calibration point
    current_point = calibration_grid[st.session_state.current_calibration_point]
    st.write(f"Point {st.session_state.current_calibration_point + 1}/9")
    
    # Visualizar ponto (pode ser feito com plotly/matplotlib)
    # ... (implementar visualização)
    
    # Botões de ação
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("⬅️ Previous"):
            if st.session_state.current_calibration_point > 0:
                st.session_state.current_calibration_point -= 1
                st.rerun()
    
    with col2:
        if st.button("📹 Capture"):
            st.info("Capturing gaze samples...")
            # Capturar dados gaze para este ponto
            st.session_state.calibration_points.append(current_point)
            
            # Mover para próximo ponto se não for o último
            if st.session_state.current_calibration_point < len(calibration_grid) - 1:
                st.session_state.current_calibration_point += 1
            else:
                st.success("✅ Calibration complete!")
                st.session_state.calibration_complete = True
            
            st.rerun()
    
    with col3:
        if st.button("❌ Cancel"):
            st.session_state.calibration_points = []
            st.session_state.current_calibration_point = 0
            st.info("Calibration cancelled")
            st.rerun()
    
    # Mostrar progresso
    progress = len(st.session_state.calibration_points) / len(calibration_grid)
    st.progress(progress)
    
    # Debug info
    with st.expander("🔍 Debug Info"):
        st.write(f"Points captured: {len(st.session_state.calibration_points)}")
        st.write(f"Current point: {st.session_state.current_calibration_point}")
```

**Checklist:**
- [ ] Criar arquivo `app/pages/calibration.py`
- [ ] Implementar grid de 9 pontos
- [ ] Integrar FaceDetector
- [ ] Implementar coleta de gaze samples
- [ ] Adicionar visualização dos pontos
- [ ] Implementar cálculo de acurácia

---

### Tarefa 3: Implementar Cálculo de Acurácia

**Arquivo:** `core/calibration.py` (NOVO)

```python
"""Calibration accuracy calculation."""

import numpy as np
from typing import List, Tuple

class CalibrationValidator:
    """Validate and calculate calibration accuracy."""
    
    @staticmethod
    def calculate_accuracy(
        gaze_points: List[np.ndarray],
        calibration_targets: List[Tuple[float, float]]
    ) -> float:
        """
        Calculate calibration accuracy.
        
        Args:
            gaze_points: Lista de pontos gaze coletados (pixels)
            calibration_targets: Lista de pontos alvo (normalizados 0-1)
        
        Returns:
            Acurácia em porcentagem (0-100%)
        """
        if not gaze_points or not calibration_targets:
            return 0.0
        
        # Converter targets para pixels (assumindo resolução 640x480)
        target_pixels = [
            (x * 640, y * 480) 
            for x, y in calibration_targets
        ]
        
        # Calcular distâncias
        distances = []
        for gaze, target in zip(gaze_points, target_pixels):
            dist = np.linalg.norm(gaze - np.array(target))
            distances.append(dist)
        
        # Acurácia: quanto menor a distância, melhor
        # Threshold: 50 pixels considerado "sucesso"
        mean_distance = np.mean(distances)
        accuracy = max(0, 100 - (mean_distance / 50 * 100))
        
        return min(100, accuracy)
    
    @staticmethod
    def is_calibration_valid(accuracy: float, min_threshold: float = 85.0) -> bool:
        """Check if calibration is good enough."""
        return accuracy >= min_threshold
```

**Checklist:**
- [ ] Criar arquivo `core/calibration.py`
- [ ] Implementar cálculo de erro angular/euclidiano
- [ ] Definir threshold de acurácia aceitável
- [ ] Testar com dados simulados

---

### Tarefa 4: Refactor `app/main.py` - Extrair Calibração para Componente

**Mudanças em `app/main.py` (linhas 305-327):**

```python
# ANTES:
elif page == "Calibration":
    st.header("📍 Gaze Calibration")
    st.info("Calibration interface would load here...")
    if st.button("Start Calibration", key="calibration_btn"):
        st.session_state.calibration_complete = True

# DEPOIS:
elif page == "Calibration":
    from app.pages.calibration import show_calibration_page
    show_calibration_page()
```

**Checklist:**
- [ ] Refactor linhas 305-327 em main.py
- [ ] Importar função `show_calibration_page()`
- [ ] Remover código placeholder
- [ ] Testar integração

---

## 🧪 Testes Necessários

### Teste de Unidade: `tests/test_calibration.py`

```python
import pytest
import numpy as np
from core.calibration import CalibrationValidator

def test_calibration_accuracy():
    """Test accuracy calculation."""
    # Pontos gaze perfeitos (coincidindo com targets)
    gaze_points = [
        np.array([64, 48]),   # 10%, 10% do alvo
        np.array([320, 240]),  # 50%, 50% perfeito
    ]
    targets = [(0.1, 0.1), (0.5, 0.5)]
    
    accuracy = CalibrationValidator.calculate_accuracy(gaze_points, targets)
    assert accuracy > 80.0
    assert accuracy <= 100.0

def test_calibration_validity():
    """Test if calibration passes threshold."""
    high_accuracy = 90.0
    low_accuracy = 70.0
    
    assert CalibrationValidator.is_calibration_valid(high_accuracy) == True
    assert CalibrationValidator.is_calibration_valid(low_accuracy) == False
```

### Teste de Integração: `tests/test_calibration_flow.py`

```python
# Testar fluxo completo:
# 1. Iniciar calibração
# 2. Capturar 9 pontos
# 3. Calcular acurácia
# 4. Validar resultado
```

### Teste Manual (Checklist de QA)

- [ ] Câmera inicializa sem erros
- [ ] FaceDetector detecta rosto corretamente
- [ ] 9 pontos aparecem na tela
- [ ] "Capture" button salva dados
- [ ] Progresso bar atualiza corretamente
- [ ] Acurácia calculada corretamente
- [ ] Mensagem de sucesso aparece quando completo
- [ ] Retry funciona se acurácia < 85%
- [ ] Dados salvo no Supabase

---

## 📅 Cronograma Sugerido

| Tarefa | Duração | Data |
|--------|---------|------|
| **Tarefa 1:** Webcam Component | 2-3 dias | 9-10 Abr |
| **Tarefa 2:** Calibration Page | 3-4 dias | 11-13 Abr |
| **Tarefa 3:** Accuracy Calculator | 1-2 dias | 14-15 Abr |
| **Tarefa 4:** Main.py Refactor | 1 dia | 16 Abr |
| **Testes** | 2-3 dias | 17-19 Abr |
| **Review e Ajustes** | 2 dias | 20-21 Abr |

**Início Recomendado:** 9 de Abril de 2026  
**Conclusão Estimada:** 21 de Abril de 2026

---

## 🔧 Dependências Técnicas

### Já Disponíveis ✅
- FaceDetector (core/face_detection.py)
- GazeEstimator (core/gaze_estimation.py)
- MediaPipe (instalado via requirements.txt)
- OpenCV (instalado via requirements.txt)
- Streamlit (instalado via requirements.txt)

### Necessárias para Implementação ✅
- scipy (para cálculos de distância)
- plotly ou matplotlib (para visualizar grid de pontos)

### Não Necessárias (Nice-to-have)
- tensorflow (para calibration usando NN)
- scikit-learn (para regressão polinomial)

---

## 🚀 Próximos Passos

### Imediato (Hoje - 8 Abr)
1. ✅ Revisar guia de debug
2. ✅ Executar checklist de validação
3. ✅ Rodar testes progressivos

### Curto Prazo (9-13 Abr)
1. [ ] Implementar WebcamCapture component
2. [ ] Implementar página de calibração
3. [ ] Integrar FaceDetector

### Médio Prazo (14-21 Abr)
1. [ ] Calcular acurácia
2. [ ] Refactor main.py
3. [ ] Testes completos
4. [ ] Deploy em produção

---

**Criado:** 8 de Abril de 2026  
**Revisão Última:** 8 de Abril de 2026  
**Status:** PRONTO PARA DESENVOLVIMENTO
