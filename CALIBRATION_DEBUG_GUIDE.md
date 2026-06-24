# 📍 Guia de Debug - Fase de Calibração

**Data:** 8 de Abril de 2026  
**Objetivo:** Resolver erros identificados durante a implementação da calibração

---

## 🔍 Erros Identificados (6 Categorias)

### 1. FaceDetector - Inicialização e Liberação de Recursos

**Erro Comum:**
```
AttributeError: 'FaceDetector' object has no attribute 'face_mesh'
```

**Causa:** 
- Destrutor (`__del__`) tenta acessar `self.face_mesh` que pode não existir se a inicialização falhar
- MediaPipe pode não estar instalado

**Solução:**
```bash
# Reinstale MediaPipe com atualização
pip install --upgrade mediapipe --break-system-packages

# Ou forçar reinstalação completa
pip install -r requirements.txt --force-reinstall --break-system-packages
```

**Arquivo Afetado:** `core/face_detection.py` (linhas 270-276)  
**Status:** ✅ **CORRIGIDO** com `hasattr()` e try-except

---

### 2. Acesso à Câmera

**Erro Comum:**
```
PermissionError: Camera access denied
RuntimeError: Failed to open camera
```

**Causas:**
- Navegador não tem permissão para acessar câmera
- URL é HTTPS local (restrição de segurança)
- Câmera ocupada por outro aplicativo
- Driver de câmera desatualizado

**Soluções:**

#### 2.1 Verificar Permissões do Navegador
```
✅ Clicar em ícone de câmera na barra de endereço
✅ Confirmar acesso à câmera
✅ Marcar "Lembrar desta decisão"
```

#### 2.2 Usar HTTP (não HTTPS) para Desenvolvimento
```bash
# CORRETO para desenvolvimento local
http://localhost:8501

# ERRADO - pode bloquear câmera
https://localhost:8501
```

#### 2.3 Testar Acesso à Câmera
```python
# Script de teste
import cv2
cap = cv2.VideoCapture(0)
if cap.isOpened():
    print("✅ Câmera acessível")
    ret, frame = cap.read()
    print(f"Frame shape: {frame.shape}")
    cap.release()
else:
    print("❌ Câmera não acessível")
```

#### 2.4 Liberar Câmera Ocupada
```bash
# macOS: Reiniciar o processo Streamlit
pkill -f streamlit

# Linux: Verificar processos usando câmera
lsof | grep /dev/video0
```

---

### 3. Credenciais Supabase

**Erro Comum:**
```
OperationalError: could not connect to server
ProgrammingError: connection failed
```

**Causas:**
- `.env` não configurado com credenciais Supabase
- Credenciais inválidas ou expiradas
- Rede bloqueada (proxy/firewall)

**Solução:**

#### 3.1 Verificar Arquivo `.env`
```bash
# Arquivo deve estar em /sessions/zealous-laughing-hamilton/mnt/Projects--SpectrumIA/.env
cat .env

# Deve conter:
SUPABASE_URL=https://[project-id].supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### 3.2 Testar Conectividade
```bash
# Ping do servidor Supabase
ping api.supabase.co

# Se falhar: Verificar proxy/firewall
curl -I https://api.supabase.co
```

#### 3.3 Validar Credenciais em Python
```python
from core.config import validate_config
try:
    validate_config()
    print("✅ Configuração válida")
except ValueError as e:
    print(f"❌ Erro: {e}")
```

---

### 4. GazeEstimator - Dependências

**Erro Comum:**
```
ModuleNotFoundError: No module named 'mediapipe'
ImportError: cannot import name 'GazeEstimator'
```

**Causas:**
- Dependências não instaladas
- Versões incompatíveis
- Ambientes virtuais conflitantes

**Solução:**
```bash
# Reinstalar todas as dependências
pip install -r requirements.txt --force-reinstall --break-system-packages

# Verificar instalação
python -c "import mediapipe; import cv2; import streamlit; print('✅ Todas as dependências OK')"
```

---

### 5. Logging e Debug em Tempo Real

**Ver logs detalhados:**
```bash
# Debug level
streamlit run app/main.py --logger.level=debug

# Com redirecionamento para arquivo
streamlit run app/main.py --logger.level=debug 2>&1 | tee streamlit.log

# Monitorar em tempo real
tail -f streamlit.log
```

**Níveis de Log:**
```
ERROR    - Erros críticos
WARNING  - Avisos (requerem atenção)
INFO     - Informações gerais
DEBUG    - Informações detalhadas (para troubleshooting)
```

---

### 6. Checklist de Validação - Fase de Calibração

Antes de iniciar testes, validar:

#### Ambiente
- [ ] Python 3.10+ instalado (`python --version`)
- [ ] MediaPipe 0.10+ instalado (`pip show mediapipe`)
- [ ] OpenCV 4.8+ instalado (`pip show opencv-python`)
- [ ] Streamlit 1.35+ instalado (`pip show streamlit`)
- [ ] Supabase client instalado (`pip show supabase`)

#### Configuração
- [ ] Arquivo `.env` presente com credenciais válidas
- [ ] `core/config.py` acessível e validável
- [ ] `app/main.py` sem erros de sintaxe

#### Hardware
- [ ] Câmera funcionando e não ocupada
- [ ] Iluminação adequada para detecção facial
- [ ] Conectividade de internet estável
- [ ] Supabase API acessível

#### Navegador
- [ ] HTTP://localhost:8501 (não HTTPS para desenvolvimento)
- [ ] Permissão de câmera concedida
- [ ] Console do navegador sem erros (F12)

---

## 🧪 Testes Progressivos

### Teste 1: Importações Básicas
```bash
python -c "from core.face_detection import FaceDetector; print('✅ FaceDetector OK')"
python -c "from core.gaze_estimation import GazeEstimator; print('✅ GazeEstimator OK')"
```

### Teste 2: FaceDetector Isolado
```python
import cv2
import numpy as np
from core.face_detection import FaceDetector

detector = FaceDetector()

# Criar frame de teste
frame = np.zeros((480, 640, 3), dtype=np.uint8)
results = detector.detect(frame)

print(f"Detecção: {len(results)} faces")
print(f"Status: {'✅ OK' if detector else '❌ Erro'}")
```

### Teste 3: Acesso à Câmera
```python
import cv2

cap = cv2.VideoCapture(0)
print(f"Câmera aberta: {cap.isOpened()}")

for _ in range(5):
    ret, frame = cap.read()
    if ret:
        print(f"✅ Frame capturado: {frame.shape}")
    else:
        print("❌ Falha ao capturar frame")
        break

cap.release()
```

### Teste 4: Conectividade Supabase
```python
from core.config import load_config

config = load_config()
print(f"URL Supabase: {config.supabase_url}")
print(f"Chave: {'*' * 20}...")
print("✅ Credenciais carregadas")
```

### Teste 5: Streamlit Completo
```bash
streamlit run app/main.py --logger.level=debug
```

---

## 📋 Ordem de Execução para Debug

1. **Validar imports** → Teste 1
2. **Validar FaceDetector** → Teste 2
3. **Validar câmera** → Teste 3
4. **Validar Supabase** → Teste 4
5. **Testar aplicação completa** → Teste 5

Se algum teste falhar, **parar e resolver antes de continuar**.

---

## 🚨 Erros Comuns e Soluções Rápidas

| Erro | Solução |
|------|---------|
| `MediaPipeError` | `pip install --upgrade mediapipe` |
| `Camera not found` | Verificar permissões do navegador + usar HTTP |
| `CORS error` | Supabase precisa de configuração de CORS no dashboard |
| `Database connection failed` | Validar `.env` + testar conectividade |
| `ImportError` | Reinstalar requirements.txt completo |
| `Memory error` | Reduzir resolução da câmera ou fechar outros apps |

---

## 📞 Próximas Ações

1. ✅ **Executar Checklist de Validação** acima
2. ✅ **Rodar Testes Progressivos** na ordem indicada
3. ✅ **Documentar erros encontrados** com screenshots
4. ✅ **Implementar página de Calibração** após validação bem-sucedida
5. ✅ **Realizar testes e2e** com usuário real

---

**Criado:** 8 de Abril de 2026  
**Última atualização:** 8 de Abril de 2026  
**Status:** Pronto para Implementação
