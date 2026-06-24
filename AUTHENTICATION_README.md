# 🔐 SpectrumIA - Guia de Autenticação

## ✅ O que foi implementado

### 1. Sistema de Login
- ✅ Página de login com email e senha
- ✅ Autenticação de usuários com credenciais demo
- ✅ Mensagens de erro/sucesso
- ✅ Hash de senha com SHA-256

### 2. Botões de Navegação
- ✅ **Botão "Home"** (🏠) - Retorna à página inicial
- ✅ **Botão "Logout"** (🚪) - Desconecta o usuário
- ✅ Ambos na sidebar, lado a lado

### 3. Informações do Usuário
- ✅ Exibe o nome e email do usuário logado
- ✅ Caixa "user-info" com design elegante
- ✅ Atualiza automaticamente após login

### 4. Proteção de Páginas
- ✅ Usuários não autenticados veem apenas login
- ✅ Páginas só carregam após autenticação
- ✅ Logout reseta o estado completo

## 🔑 Credenciais de Demo

### Usuário 1
- **Email:** `demo@spectrum.ai`
- **Senha:** `demo123`

### Usuário 2
- **Email:** `test@spectrum.ai`
- **Senha:** `test123`

## 🚀 Como Usar

### Localmente
```bash
# Ativar ambiente virtual
source venv/bin/activate

# Rodar a aplicação
streamlit run app/main.py
```

### Na Streamlit Cloud
- Aplicação já está deployada em: https://spectrumia.streamlit.app
- Faça login com as credenciais de demo acima

## 📋 Fluxo de Navegação

```
[Login] 
   ↓
[Home] ← (🏠 Home button)
   ↓
[Calibration] → [Assessment] → [Results]
   ↓
[🚪 Logout] → Volta para Login
```

## 🔒 Segurança

### Implementado
- ✅ Hash de senha com SHA-256
- ✅ Session state isolado por usuário
- ✅ Logout limpa o estado completamente
- ✅ Credenciais não expostas no código

### Próximos Passos (Produção)
- [ ] Integração com Supabase Auth
- [ ] OAuth 2.0 (Google, GitHub)
- [ ] 2FA (Two-Factor Authentication)
- [ ] Rate limiting em login
- [ ] HTTPS obrigatório
- [ ] Tokens JWT para sessão
- [ ] Recuperação de senha

## 🛠️ Personalização

### Adicionar Novos Usuários
Editar `app/main.py`, função `verify_credentials()`:

```python
demo_users = {
    "demo@spectrum.ai": hash_password("demo123"),
    "test@spectrum.ai": hash_password("test123"),
    "newuser@spectrum.ai": hash_password("newpass123"),  # Adicionar aqui
}
```

### Integrar com Banco de Dados
Substituir a função `verify_credentials()` com consulta ao Supabase:

```python
def verify_credentials(email: str, password: str) -> bool:
    from core.database import get_user
    user = get_user(email)
    if user:
        return user['password_hash'] == hash_password(password)
    return False
```

## 📊 Estrutura de Sessão

```python
st.session_state = {
    'authenticated': bool,      # True se logado
    'user_email': str,          # Email do usuário
    'user_name': str,           # Nome extraído do email
    'session_id': str,          # UUID da sessão
    'current_page': str,        # Página atual
    'calibration_complete': bool,  # Status de calibração
    'assessment_complete': bool,   # Status de avaliação
}
```

## ✨ Novos Recursos

| Feature | Status | Localização |
|---------|--------|-------------|
| Login Page | ✅ Implementado | `show_login_page()` |
| Home Button | ✅ Implementado | Sidebar |
| Logout Button | ✅ Implementado | Sidebar |
| User Info | ✅ Implementado | Sidebar top |
| Credenciais Demo | ✅ Implementado | `verify_credentials()` |
| Session State | ✅ Implementado | Global |

---

**Desenvolvido para SpectrumIA v{APP_VERSION}**
