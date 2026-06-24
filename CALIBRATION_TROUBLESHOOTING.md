# 🔧 Guia de Troubleshooting - Calibração SpectrumIA

## Problema: Tela Preta na Página de Calibração

Quando você clica em "Calibration", uma tela preta aparece e nada é executado.

---

## 🚀 Solução Rápida - Usar Debug Page

Criamos uma página de debug automática. Acesse em **`http://localhost:8501/?page=debug_calibration`** ou:

1. Abra a aplicação: `streamlit run app/main.py`
2. No sidebar, navegue para **"Debug - Calibração"**
3. Siga os testes de diagnóstico

A página vai:
- ✅ Verificar todas as dependências Python
- ✅ Testar carregamento de módulos SpectrumIA
- ✅ Testar acesso à câmera
- ✅ Detectar rostos em tempo real
- ✅ Mostrar logs detalhados de erros

---

## 🔍 Problemas Comuns e Soluções

### Problema 1: "Erro ao carregar modelos: MediaPipe não encontrado"

**Causa:** MediaPipe não está instalado ou quebrado

**Solução:**
```bash
# Reinstalar MediaPipe
pip uninstall mediapipe -y
pip install mediapipe==0.10.9

# Ou reinstalar tudo
pip install -r requirements.txt --force-reinstall
```

---

### Problema 2: "Câmera não funciona / Tela preta ao clicar em camera_input"

**Causa:**
- Navegador não tem permissão de câmera
- st.camera_input() não está funcionando

**Solução:**

**a) Se em localhost:**
```
✅ OK - HTTP://localhost:8501 funciona
❌ PROBLEMA - HTTPS://localhost:8501 (câmera não funciona em HTTPS local)
```

**b) Verificar permissões do navegador:**
- Chrome: Clique no ícone de câmera na barra de endereço → Permitir
- Firefox: Menu → Privacidade → Câmera → Permitir para localhost
- Safari: Preferências → Câmera → Permitir localhost

**c) Se ainda não funcionar:**
```bash
# Teste com Python puro (sem Streamlit)
python3 << 'EOF'
import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    print("✅ Câmera funciona!")
    ret, frame = cap.read()
    if ret:
        print(f"✅ Captura funcionou: {frame.shape}")
    cap.release()
else:
    print("❌ Câmera não acessível")
EOF
```

---

### Problema 3: "Nenhum rosto detectado / Erro ao detectar face"

**Causa:**
- FaceDetector falhando silenciosamente
- MediaPipe não carregando modelo corretamente

**Solução:**
```bash
# 1. Verify MediaPipe is working
python3 << 'EOF'
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

print("✅ MediaPipe importado")

# Check if model files exist
import os
model_path = os.path.expanduser("~/.mediapipe")
print(f"Modelos em: {model_path}")
if os.path.exists(model_path):
    print(f"✅ Diretório de modelos existe")
    for root, dirs, files in os.walk(model_path):
        for f in files[:5]:  # Show first 5 files
            print(f"  - {f}")
else:
    print(f"❌ Diretório de modelos não existe - será criado na primeira execução")
EOF

# 2. Reinstall MediaPipe with models
pip install --upgrade --force-reinstall mediapipe
```

---

### Problema 4: "Erro de Database / Supabase"

**Causa:** Credenciais Supabase não configuradas

**Solução:**
```bash
# 1. Verify .env file exists and has credentials
cat .env

# Should show:
# SUPABASE_URL=https://xxx.supabase.co
# SUPABASE_KEY=eyJhbGc...

# 2. If missing, copy from .env.example
cp .env.example .env
# Then edit .env with real credentials from https://supabase.com

# 3. Test connection
python3 << 'EOF'
from core.config import SUPABASE_URL, SUPABASE_KEY
print(f"URL: {SUPABASE_URL}")
print(f"Key length: {len(SUPABASE_KEY)}")

from models.database import get_db
db = get_db()
print("✅ Database conectado!")
EOF
```

---

### Problema 5: "ModuleNotFoundError: No module named 'core'"

**Causa:** Python path não configurado corretamente

**Solução:**
```bash
# Run from project root, NOT from app/ folder
cd /path/to/SpectrumIA
streamlit run app/main.py

# NOT from app folder
cd app
streamlit run main.py  # ❌ ERRADO
```

---

### Problema 6: "ImportError: cannot import name 'FaceDetector'"

**Causa:** Módulos core não estão sendo encontrados

**Solução:**
```bash
# 1. Verify file structure
ls -la core/
# Should show: face_detection.py, gaze_estimation.py, etc.

# 2. Reinstall package
pip install -e .

# 3. Or verify sys.path in main.py
python3 << 'EOF'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.face_detection import FaceDetector
print("✅ Import OK")
EOF
```

---

## 📋 Checklist de Diagnóstico

Siga este checklist para identificar o problema:

```
☐ 1. Python 3.10+ instalado?
     python3 --version

☐ 2. requirements.txt instalado?
     pip list | grep mediapipe
     pip list | grep streamlit

☐ 3. .env file existe com credenciais Supabase?
     cat .env

☐ 4. Câmera funciona em Python?
     python3 -c "import cv2; cap = cv2.VideoCapture(0); print(cap.isOpened())"

☐ 5. Browser permite câmera?
     Abrir DevTools (F12) → Console → Testar st.camera_input()

☐ 6. Módulos SpectrumIA importam?
     python3 -c "from core.face_detection import FaceDetector; print('OK')"

☐ 7. Rodar debug_calibration.py e passar em todos os testes?
     Abrir http://localhost:8501/?page=debug_calibration
```

---

## 🛠️ Soluções Nucleares (Reset Completo)

Se nada funcionar, faça um reset completo:

```bash
# 1. Remove cache e instalações
pip cache purge
rm -rf ~/.mediapipe  # Remove MediaPipe cache
rm -rf .streamlit/   # Remove Streamlit cache

# 2. Reinstalar tudo do zero
pip uninstall -r requirements.txt -y
pip install -r requirements.txt --force-reinstall --no-cache-dir

# 3. Limpar cache Python
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# 4. Rodar com debug máximo
streamlit run app/main.py --logger.level=debug --client.showErrorDetails=true
```

---

## 📝 Coletar Logs para Debug

Se o problema persistir, colete logs:

```bash
# 1. Capture full error output
streamlit run app/main.py --logger.level=debug 2>&1 | tee calibration_debug.log

# 2. Try to calibrate (will fail with error in log)

# 3. Share calibration_debug.log for analysis
```

---

## 🆘 Modo Manual (Workaround Temporário)

Se câmera ou face detection falharem, use este workaround:

**Edite `app/pages/calibration.py` linha 299:**

```python
# OLD (broken):
run = st.checkbox("Iniciar Câmera", value=False)

# NEW (manual mode without camera):
run = st.checkbox("Modo Manual (sem câmera)", value=False)

if run:
    st.info("Modo manual: Digite valores de gaze manualmente")
    # ... adicionar inputs manuais
```

---

## 🚀 Próximos Passos

1. **Execute a debug page** (app/pages/debug_calibration.py)
2. **Anote qual teste falha**
3. **Siga a solução correspondente acima**
4. **Se persistir, compartilhe output de:**
   ```bash
   streamlit run app/main.py --logger.level=debug 2>&1 | head -100
   ```

---

**Status:** Se conseguir passar em todos os testes da debug page, a calibração funcionará!
