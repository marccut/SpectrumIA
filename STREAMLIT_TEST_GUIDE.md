# 🧪 SpectrumIA - Guia de Teste Streamlit

**Data:** 8 de Abril, 2026
**Objetivo:** Validar todas as correções implementadas na Assessment workflow

---

## ✅ Checklist de Verificação

### Pré-Teste
- [ ] Python 3.10+ instalado
- [ ] Dependências do `requirements.txt` instaladas
- [ ] Arquivo `.env` configurado (ou modo demo)
- [ ] Webcam disponível e testada

### Teste 1: Login & Inicialização
- [ ] Página Home carrega corretamente
- [ ] Página Login funciona
- [ ] Demo login: `demo@spectrumia.com / demo123` aceito
- [ ] Session state inicializado após login

**Comandos:**
```bash
cd /path/to/marcelocarvalho--SpectrumIA
streamlit run app/main.py
```

**Resultado esperado:** Interface Streamlit abre em `http://localhost:8501`

---

### Teste 2: Calibração 9-Point
**O quê testar:**
- Apresentação do grid 9-point
- Coleta de 9 amostras de calibração
- Salvamento da sessão de calibração
- **CRÍTICO:** Sincronização de session state após salvar

**Passos:**
1. Login com `demo@spectrumia.com / demo123`
2. Clique em "2_calibration" no sidebar
3. Clique "Iniciar Calibração"
4. Siga os 9 pontos (clique em cada ponto e tire foto)
5. Clique "💾 Salvar Calibração"

**Validações esperadas:**
```
✅ Grid 9-point apresentado
✅ Cada ponto mostra coordenadas
✅ Câmera captura imagem para cada ponto
✅ Mensagem: "✅ Calibração salva com sucesso!"
✅ Session state atualizado:
   - st.session_state.calibration_id = <session_id>
   - st.session_state.is_calibrated = True
   - st.session_state.active_calibration_id = <session_id>
```

**Logs esperados no terminal:**
```
INFO: Calibration session created: <uuid>
INFO: Calibration data saved successfully
```

---

### Teste 3: Assessment - Fluxo Completo
**O quê testar:**
- Verificação de calibração prévia
- Apresentação visual de estímulos (cores corretas)
- Coleta contínua de amostras durante duração
- Auto-avança entre estímulos
- Conclusão sem erros

**Passos:**
1. Após calibração salva, vá para "3_assessment"
2. Clique "Iniciar Nova Avaliação"
3. Para cada estímulo:
   - Verifique estímulo visual
   - Clique "Iniciar Câmera & Coleta"
   - Observe coleta contínua por X segundos
   - Sistema auto-avança automaticamente

**Validações esperadas:**

#### Estímulo 1: "Rosto Falando" (30s)
```
✅ Fundo gradiente roxo (#667eea → #764ba2)
✅ Emoji 😊 visível
✅ "Rosto Falando" exibido
✅ Câmera coleta por ~30 segundos
✅ Progresso mostra: "Amostras: X | Y segundos / 30 total"
✅ Mensagem: "✅ Coleta de Rosto Falando completa!"
✅ Auto-avança para Estímulo 2
```

#### Estímulo 2: "Rosto Sorrindo" (20s)
```
✅ Mesmo fundo roxo (face stimulus)
✅ "Rosto Sorrindo" exibido
✅ Coleta por ~20 segundos
✅ Auto-avança para Estímulo 3
```

#### Estímulo 3: "Padrão Geométrico" (15s)
```
✅ Fundo gradiente rosa (#f093fb → #f5576c)
✅ Emoji 🔷 visível
✅ "Padrão Geométrico" exibido
✅ Coleta por ~15 segundos
✅ Após conclusão: "✅ Todas as avaliações foram completadas!"
```

**Logs esperados:**
```
INFO: Assessment session created: <uuid>
INFO: Face detected, confidence: X.XX
INFO: Gaze sample collected
INFO: Assessment stimulus collected: <stimulus_id>
INFO: Assessment completed successfully
```

---

### Teste 4: Resultados
**O quê testar:**
- Carregamento dos dados coletados
- Exibição de métricas por estímulo
- Gráficos interativos (Plotly)
- Exportação PDF/CSV

**Passos:**
1. Clique "📊 Ver Resultados" ou acesse "4_results"
2. Visualize métricas por estímulo
3. Tente exportar PDF

**Validações esperadas:**
```
✅ Página carrega sem erros
✅ Métricas exibidas por estímulo:
   - Social Attention Index (SAI)
   - Fixation Metrics
   - Saccade Metrics
   - Scanpath Entropy
✅ Gráficos interativos funcionam
✅ Botão "📥 Baixar PDF" funciona
```

---

## 🔍 Erros Conhecidos & Soluções

### ❌ Erro: "⚠️ Você deve calibrar seu eye-tracker primeiro"
**Causa:** Calibração não sincronizou session state
**Solução:** Verifique se `st.session_state.is_calibrated = True` foi setado após salvar calibração
**Debug:**
```python
st.write(st.session_state)  # Adicione na Assessment page para debugar
```

### ❌ Erro: "Could not find page"
**Causa:** `st.switch_page()` apontando para páginas antigas ou caminho inconsistente
**Solução:** Use os nomes atuais das páginas numeradas
**Código correto:**
```python
st.switch_page("pages/0_home.py")
st.switch_page("pages/2_calibration.py")
st.switch_page("pages/3_assessment.py")
st.switch_page("pages/4_results.py")
```

### ❌ Erro: "AttributeError: 'NoneType' object has no attribute 'extract_features'"
**Causa:** feature_extractor não inicializado
**Solução:** Código agora inicializa com try/except e fallback
**Confirmado em:** app/pages/3_assessment.py linhas 448-458

### ❌ Erro: "TypeError: Cannot handle this data type"
**Causa:** Image processing issue
**Solução:** Confirmado que PIL + cv2 convertem corretamente

### ❌ DeprecationWarning: "use_column_width parameter deprecated"
**Solução:** Substituído por `use_container_width=True`
**Confirmado em:** Linhas com st.image()

### ❌ DeprecationWarning: "datetime.utcnow() is deprecated"
**Solução:** Substituído por `datetime.now(timezone.utc)`
**Confirmado em:**
- app/pages/2_calibration.py
- app/pages/3_assessment.py
- models/database.py
- models/schemas.py

### ✅ Convenção Atual de Páginas
```text
pages/0_home.py
pages/1_login.py
pages/2_calibration.py
pages/3_assessment.py
pages/4_results.py
```

---

## 📊 Métricas para Validar

Após Assessment completo, espere extrair:

### Social Attention Index (SAI)
```
Formula: (Eye region time + Mouth region time) / Total gaze time
Expected: 0.3 - 0.8 (mais alto em faces, mais baixo em padrões geométricos)
```

### Fixation Metrics
```
- Fixation Count: ~2-10 por estímulo
- Fixation Duration: ~200-500ms
- Fixation Dispersion: ~30-100px
```

### Saccade Metrics
```
- Saccade Amplitude: ~100-500px
- Saccade Velocity: ~100-500 deg/s
- Saccade Peak Velocity: ~300-700 deg/s
```

### Scanpath Entropy
```
- Lower entropy = mais previsível/focado
- Higher entropy = mais exploratório
```

---

## 🐛 Debug Mode

Para ativar logs detalhados, adicione antes de rodar Streamlit:

```bash
# Terminal
export STREAMLIT_LOGGER_LEVEL=debug
export PYTHONUNBUFFERED=1
streamlit run app/main.py --logger.level=debug
```

Ou adicione no início de `app/main.py`:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("SpectrumIA initialized")
```

---

## ⏱️ Tempo de Teste Esperado

| Fase | Tempo |
|------|-------|
| Setup + Login | 1-2 min |
| Calibração 9-point | 3-5 min |
| Assessment 3 estímulos | 2-3 min |
| Resultados + Exportação | 1 min |
| **Total** | **~10-15 min** |

---

## ✅ Acceptance Criteria

Projeto considerado **pronto para produção** se:

- [x] Calibração salva e sincroniza estado
- [x] Assessment reconhece calibração sem warnings
- [x] Estímulos apresentados com cores corretas
- [x] Coleta contínua ocorre durante duração
- [x] Auto-avança funciona entre estímulos
- [x] Resultados carregam sem erros
- [x] Nenhum crash durante fluxo completo
- [x] Logs mostram coleta de dados

---

**Status:** 🚀 PRONTO PARA TESTE
**Data da Última Atualização:** 8 de Abril, 2026
