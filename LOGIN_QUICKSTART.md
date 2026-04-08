# 🚀 Quick Start - Sistema de Login

## O que mudou?

Agora o SpectrumIA **requer login** antes de acessar qualquer funcionalidade. Isso aumenta a segurança e permite rastrear sessões de usuários.

## Como Testar

### 1️⃣ Inicie o Streamlit (se não estiver rodando)

```bash
cd /Users/marcelocarvalho/SpectrumIA
streamlit run app/main.py
```

### 2️⃣ Acesse http://localhost:8501

Você verá uma mensagem:
```
👋 Please login first to access the screening tool
```

### 3️⃣ Clique em "🔐 Login" na sidebar

### 4️⃣ Use as credenciais de demo

**Email:** `demo@spectrumia.com`
**Password:** `demo123`

### 5️⃣ Clique em "🔓 Login"

Se houver um diálogo do Chrome sobre senha:
- Clique "Cancel" ou "OK" para fechar
- O login já terá sido processado

### 6️⃣ Você será redirecionado para a página home!

Agora você pode:
- ✅ Ver o dashboard home
- ✅ Clicar em "Calibration"
- ✅ Clicar em "Assessment"
- ✅ Clicar em "Results"

## Estrutura de Páginas

```
Sidebar:
├── 🏠 Home → Página de boas-vindas (requer login)
├── 🔐 Login → Login/Registro (qualquer um acessa)
├── 📍 Calibration → Calibração (requer login)
├── 📹 Assessment → Avaliação (requer login)
├── 📊 Results → Resultados (requer login)
└── 🔧 Debug Calibration → Debug (qualquer um acessa)
```

## Credenciais de Demo para Testar

### Conta Paciente
```
Email: demo@spectrumia.com
Password: demo123
Role: patient
```

### Conta Médico
```
Email: doctor@spectrumia.com
Password: doctor123
Role: clinician
```

### Conta Pesquisador
```
Email: patient@spectrumia.com
Password: patient123
Role: patient
```

## Criar Sua Própria Conta

1. Na página de login, clique em "📝 Register"
2. Preencha:
   - Email: seu-email@exemplo.com
   - Password: mínimo 6 caracteres
   - Confirme a senha
   - Nome (opcional)
   - Role (paciente, médico ou pesquisador)
3. Clique em "📝 Register"
4. Agora faça login com sua conta

## Fazer Logout

1. Na sidebar, veja seu email: `👤 Logged in as: demo@spectrumia.com`
2. Clique no botão "🚪 Logout"
3. Você será redirecionado para a página de login

## O que é o Modo Demo?

Se você não tem Supabase configurado (variáveis `SUPABASE_URL` e `SUPABASE_KEY`):
- ✅ O sistema funciona em **modo demo**
- ✅ As credenciais acima funcionam
- ✅ Você pode testar tudo normalmente
- ✅ É perfeito para desenvolvimento

Para usar com Supabase real:
```bash
export SUPABASE_URL="https://seu-projeto.supabase.co"
export SUPABASE_KEY="sua-chave-anonima"
```

## Segurança

- ✅ Senhas precisam de mínimo 6 caracteres
- ✅ Cada página verifica se você está autenticado
- ✅ Logout limpa sua sessão
- ✅ Dados armazenados em session state (seguro)

## Troubleshooting

### "❌ Please login first"
→ Você não está autenticado. Clique em "🔐 Login"

### "Invalid email or password"
→ Credenciais erradas. Verifique email e senha

### "Email not registered. Please sign up first."
→ A conta não existe. Use "📝 Register" ou credenciais de demo

### Diálogo do Chrome aparece
→ É normal. Clique "Cancel" ou "OK" para continuar

## Arquivos Novos

- `core/auth.py` - Módulo de autenticação
- `app/pages/1_login.py` - Página de login
- `app/pages/0_home.py` - Dashboard home
- `AUTHENTICATION_SYSTEM.md` - Documentação completa

---

**Pronto! Agora SpectrumIA é mais seguro e rastreia usuários!** 🔐
