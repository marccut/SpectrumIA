# 🚀 Streamlit Cloud Deploy - Guia Passo-a-Passo

## Status Atual
✅ Código pronto no GitHub
✅ Arquivo `streamlit_app.py` criado (entry point para Streamlit Cloud)
🟡 Aguardando push para GitHub e configuração final no Streamlit Cloud

---

## ⚡ Passos Rápidos (5 minutos)

### Passo 1: Fazer Push do Novo Arquivo para GitHub (GitHub Desktop)

1. **Abra GitHub Desktop** no seu Mac
2. **Procure por `streamlit_app.py`** na lista de mudanças (lado esquerdo, "Changes")
3. **Digite a mensagem de commit:**
   ```
   Add Streamlit Cloud entry point
   ```
4. **Clique em "Commit to main"**
5. **Clique em "Push origin"** (lado superior direito)
6. Espere a mensagem de confirmação

### Passo 2: Configurar Streamlit Cloud

1. **Volte para https://streamlit.io/cloud** (na aba do navegador onde você estava)
2. **Clique em "New app"** novamente
3. **Selecione:**
   - Repository: `seu-usuario/SpectrumIA`
   - Branch: `main`
   - **Main file path: `streamlit_app.py`** ← Use ESTE caminho agora!
4. **Clique em "Deploy"**

> Se ainda tiver erro, tente: `app/main.py` como segunda opção

### Passo 3: Aguarde o Primeiro Deploy (2-3 minutos)

Você verá uma mensagem:
```
Building your app...
App is running
```

### Passo 4: Adicionar Secrets (Variáveis de Ambiente)

1. **Clique no ⋮ (menu) → Settings** na página da sua app
2. **Vá para a aba "Secrets"**
3. **Cole o conteúdo do seu `.env` (do seu computador):**

```toml
SUPABASE_URL = "https://seu-projeto.supabase.co"
SUPABASE_ANON_KEY = "eyJ..."
SUPABASE_SERVICE_ROLE_KEY = "eyJ..."
DATABASE_URL = "postgresql://postgres:T%3F5MX%217y%25Z2V@eeqtgpbnqlgkgwtgpiof.supabase.co:5432/postgres"
JWT_SECRET = "seu-jwt-secret"
ENV = "production"
```

4. **Clique em "Save"**
5. A app será reiniciada automaticamente (⏳ 1 minuto)

### Passo 5: Testar a App

Sua app estará em:
```
https://seu-usuario-spectrumia.streamlit.app
```

Verifique:
- [ ] Página carrega sem erros
- [ ] Navega entre abas
- [ ] Webcam funciona (pede permissão)
- [ ] Conexão com Supabase OK

---

## ✅ Verificação Pré-Deploy (Opcional)

Para garantir que tudo está pronto:

```bash
cd /Users/marcelocarvalho/Documents/Claude/Projects/SpectrumIA
python scripts/pre_deploy_check.py
```

Você verá:
```
✅ PRONTO PARA DEPLOY NO STREAMLIT CLOUD!
```

---

## 🐛 Problemas Comuns

### Erro: "File not found"
**Solução:** Certifique-se que fizeram push do arquivo `streamlit_app.py` para GitHub

### Erro: "ModuleNotFoundError"
**Solução:** Verificar se todas as dependências estão em `requirements.txt`

### Erro: "Connection refused" ao Supabase
**Solução:** Verificar se os secrets foram adicionados corretamente no Streamlit Cloud

### App carrega mas não funciona
**Solução:**
1. Clique em **Logs** (canto inferior direito) no Streamlit Cloud dashboard
2. Procure pela mensagem de erro
3. Compartilhe o erro comigo

---

## 📊 Resumo dos URLs

- **Seu Repositório:** https://github.com/seu-usuario/SpectrumIA
- **Seu App:** https://seu-usuario-spectrumia.streamlit.app
- **Supabase Dashboard:** https://app.supabase.com

---

## ⏭️ Próximas Fases

Após Phase 8.2 estar funcional:

- **Phase 8.3** - Docker Containerization
- **Phase 8.4** - Monitoring & Logging (APM)
- **Phase 9** - Models & Database Integration

---

**Resumo:** Em 3 passos simples você terá sua app ao vivo! 🎉
