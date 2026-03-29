# 🚀 Phase 8.2 - Streamlit Cloud Deployment

**Objetivo:** Deploy da aplicação SpectrumIA no Streamlit Cloud
**Duração:** 1-2 horas
**Status:** 🟡 Ready to Start

---

## 📋 O que é Streamlit Cloud?

Streamlit Cloud é a plataforma oficial para hospedar aplicações Streamlit gratuitamente:
- ✅ Deploy automático via GitHub
- ✅ HTTPS automático
- ✅ Fácil compartilhamento
- ✅ Logs em tempo real
- ✅ Gerenciamento de secrets (variáveis sensíveis)

---

## 🎯 Phase 8.2 Roadmap (4 etapas)

### **Step 1: Preparar Código para Deploy** (15 min)
- Verificar requirements.txt
- Configurar .streamlit/config.toml
- Validar app/main.py

### **Step 2: Configurar GitHub** (10 min)
- Criar repositório GitHub público
- Fazer push do código
- Configurar branch para deploy

### **Step 3: Deploy no Streamlit Cloud** (10 min)
- Conectar GitHub ao Streamlit Cloud
- Criar aplicação
- Configurar variáveis de ambiente (secrets)

### **Step 4: Testar & Monitorar** (15 min)
- Acessar aplicação ao vivo
- Testar funcionalidades
- Verificar logs

---

## ✅ Pre-requisitos

Antes de começar, certifique-se que tem:

- [ ] GitHub account (grátis em github.com)
- [ ] Streamlit Cloud account (grátis em streamlit.io/cloud)
- [ ] Code pronto em `/Users/marcelocarvalho/Documents/Claude/Projects/SpectrumIA`
- [ ] requirements.txt atualizado
- [ ] app/main.py funcionando localmente
- [ ] Credenciais Supabase (.env pronto)

---

## 🔧 Step 1: Preparar Código para Deploy (15 minutos)

### 1.1: Verificar requirements.txt

Seu `requirements.txt` deve ter:

```
streamlit>=1.28.0
supabase-py>=2.3.0
python-dotenv>=1.0.0
numpy>=1.24.0
pandas>=2.0.0
opencv-python>=4.8.0
mediapipe>=0.10.0
tensorflow>=2.13.0
scikit-learn>=1.3.0
scipy>=1.11.0
plotly>=5.17.0
```

**Verificar:**
```bash
cat /Users/marcelocarvalho/Documents/Claude/Projects/SpectrumIA/requirements.txt
```

### 1.2: Criar arquivo .streamlit/config.toml

Na pasta do projeto, crie `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[client]
showErrorDetails = true
toolbarMode = "minimal"

[logger]
level = "info"
```

### 1.3: Validar app/main.py

O arquivo `app/main.py` deve ter:
- Imports corretos
- Configuração de página
- Navegação entre páginas
- Tratamento de erro

---

## 🔐 Step 2: Configurar Secrets para Streamlit Cloud

Streamlit Cloud usa `secrets.toml` para variáveis sensíveis (não committir no Git!)

### 2.1: Criar arquivo .streamlit/secrets.toml (LOCAL ONLY)

```toml
# Nunca commitar este arquivo no Git!
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_ANON_KEY = "eyJ..."
SUPABASE_SERVICE_ROLE_KEY = "eyJ..."
DATABASE_URL = "postgresql://postgres:SENHA@eeqtgpbnqlgkgwtgpiof.supabase.co:5432/postgres"
JWT_SECRET = "seu-jwt-secret"
ENV = "production"
```

### 2.2: Adicionar ao .gitignore

Certifique-se que `.gitignore` tem:

```
.streamlit/secrets.toml
.env
.env.production
```

---

## 📤 Step 3: Configurar GitHub e Deploy

### 3.1: Criar repositório GitHub

1. Abra https://github.com/new
2. Nome: `SpectrumIA`
3. Descrição: `Eye-tracking based ASD screening tool`
4. Público (necessário para Streamlit Cloud gratuito)
5. Crie

### 3.2: Fazer push do código

```bash
cd /Users/marcelocarvalho/Documents/Claude/Projects/SpectrumIA

git init
git add .
git commit -m "Initial commit: Phase 8.1 Supabase setup complete"
git branch -M main
git remote add origin https://github.com/seu-usuario/SpectrumIA.git
git push -u origin main
```

### 3.3: Deploy no Streamlit Cloud

1. Abra https://streamlit.io/cloud
2. Clique em **"New app"**
3. Selecione seu repositório `SpectrumIA`
4. Branch: `main`
5. Path: `app/main.py`
6. Clique em **"Deploy"**

---

## 🔐 Step 4: Configurar Secrets no Streamlit Cloud

### 4.1: Adicionar variáveis de ambiente

1. Na página da aplicação (após deploy), clique em **⋮ (menu)** → **Settings**
2. Vá para aba **Secrets**
3. Cole seu `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://eeqtgpbnqlgkgwtgpiof.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
DATABASE_URL = "postgresql://postgres:T%3F5MX%217y%25Z2V@eeqtgpbnqlgkgwtgpiof.supabase.co:5432/postgres"
JWT_SECRET = "seu-jwt-secret"
ENV = "production"
```

4. Clique em **Save**
5. A aplicação será reiniciada automaticamente

---

## 🧪 Step 5: Testar Aplicação

### 5.1: Verificar deployment

Sua aplicação estará disponível em:
```
https://seu-usuario-spectrumia.streamlit.app
```

### 5.2: Testar funcionalidades

- [ ] Página de calibração carrega
- [ ] Webcam funciona (permissão do navegador)
- [ ] Conexão com Supabase OK
- [ ] Tabelas são acessadas corretamente
- [ ] Nenhum erro no console

### 5.3: Verificar logs

No Streamlit Cloud dashboard:
1. Clique na aplicação
2. **Logs** (canto inferior direito)
3. Procure por erros

---

## 📊 Monitoramento Pós-Deploy

### Métricas para acompanhar:

```
App URL:        https://seu-usuario-spectrumia.streamlit.app
Region:         Closest AWS region
Status:         Running / Error
Last Update:    Automatic via GitHub push
Uptime:         99.9%
```

### Health Check:

```bash
# Verificar se aplicação está online
curl -I https://seu-usuario-spectrumia.streamlit.app
# Esperado: HTTP/1.1 200 OK
```

---

## 🚀 Resumo do Timeline

| Etapa | Tempo | Status |
|-------|-------|--------|
| 1. Preparar Código | 15 min | 🟡 Pronto |
| 2. Configurar GitHub | 10 min | 🟡 Pronto |
| 3. Deploy Streamlit Cloud | 10 min | 🟡 Pronto |
| 4. Testar & Monitorar | 15 min | 🟡 Pronto |
| **Total** | **50 min** | **🟡** |

---

## ⚠️ Possíveis Problemas & Soluções

### Problema: "Module not found: cv2"
**Solução:** Streamlit Cloud tem limitações. Usar versão simplificada ou usar `opencv-python-headless`

### Problema: "Timeout connecting to Supabase"
**Solução:** Usar Connection Pooler URL (porta 6543) ao invés de direta (5432)

### Problema: "Secrets not loading"
**Solução:** Verificar `.streamlit/secrets.toml` está correto, reiniciar app

### Problema: "Webcam não funciona"
**Solução:** Usar `streamlit-webrtc` library para melhor suporte a webcam

---

## 📚 Próximos Passos

Após Phase 8.2 estar completo:

- **Phase 8.3** - Docker Containerization (deploy em produção)
- **Phase 8.4** - Monitoring & Logging (APM, error tracking)
- **Phase 9** - Models & Database Integration (ML pipeline completo)

---

## 📞 Recursos Úteis

- Streamlit Cloud Docs: https://docs.streamlit.io/streamlit-cloud
- GitHub Setup: https://github.com/first-time-setup
- Supabase Connection: https://supabase.com/docs/guides/ai-python
- Streamlit Secrets: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management

---

**Status:** 🟡 Ready to implement
**Last Updated:** 2026-03-27
**Owner:** Marcelo Carvalho (Médico Psiquiatra)
