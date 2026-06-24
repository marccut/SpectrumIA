# 🏗️ Arquitetura de Autenticação - SpectrumIA

---

## 📊 Diagrama de Fluxo Completo

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SpectrumIA Application                          │
│                        (app/main.py)                                    │
└─────────────────────────────────────────────────────────────────────────┘

                              START
                                │
                                ▼
                    ┌────────────────────────┐
                    │ Check Configuration    │
                    │ Load CSS & Session ST  │
                    └────────────┬───────────┘
                                 │
                                 ▼
                      ┌──────────────────────┐
                      │ Autenticado?         │
                      │ (session_state)      │
                      └──────┬──────┬────────┘
                            /       \
                           /         \
                          NÃO        SIM
                         /             \
                        /               \
                       ▼                 ▼
              ┌──────────────────┐   ┌────────────────────┐
              │  show_login_page │   │  Render Main App   │
              │  ()              │   │                    │
              └────────┬─────────┘   └────────┬───────────┘
                       │                      │
                       ├─ Página: Email       ├─ User Info
                       ├─ Campo: Senha        ├─ Home Button
                       ├─ Botão: Login        ├─ Logout Button
                       ├─ Demo Creds          ├─ Navigation
                       └─ st.stop()           ├─ Pages
                           │                  │  ├─ Home
                           │                  │  ├─ Calibration
                    ┌──────▼──────┐           │  ├─ Assessment
                    │ Login Btn   │           │  └─ Results
                    └──────┬──────┘           └────────┬──────────┘
                           │                           │
                    ┌──────▼──────────────────┐        │
                    │ verify_credentials()    │        │
                    │ (email, password)       │        │
                    └──────┬───────┬──────────┘        │
                          /         \                   │
                    VÁLIDO        INVÁLIDO             │
                    /               \                  │
                   ▼                 ▼                 ▼
           ┌──────────────────┐  ┌──────────────┐  ┌─────────┐
           │ set session_state│  │ show error   │  │ Uso da  │
           │ ✓ authenticated  │  │ "Invalid..." │  │ app...  │
           │ ✓ user_email     │  │              │  │         │
           │ ✓ user_name      │  └──────────────┘  │ Paginas │
           │                  │                    │         │
           │ st.success()     │                    │ User    │
           │ st.rerun()       │                    │ logged  │
           └────────┬─────────┘                    │ in ✓    │
                    │                              │         │
                    ├──────────────────────────────┤         │
                    │                              │         │
                    ▼                              ▼         │
           ┌────────────────────────────────────────────┐    │
           │         Sidebar Navigation               │    │
           │ ┌────────────────────────────────────┐   │    │
           │ │ 👤 Logged in as: Demo              │   │    │
           │ │    demo@spectrum.ai                │   │    │
           │ ├────────────────────────────────────┤   │    │
           │ │ [🏠 Home] [🚪 Logout]              │   │    │
           │ ├────────────────────────────────────┤   │    │
           │ │ Navigation:                        │   │    │
           │ │ ○ Home                             │   │    │
           │ │ ○ Calibration                      │   │    │
           │ │ ○ Assessment                       │   │    │
           │ │ ○ Results                          │   │    │
           │ └────────────────────────────────────┘   │    │
           └────────────────────────────────────────────┘    │
                    │                                        │
           Clica: Home, Calibration, etc ─────────────────┘

          ┌────────────────────────────────────────┐
          │       Logout Button Clicado             │
          └────────────┬───────────────────────────┘
                       │
                       ▼
          ┌────────────────────────────────┐
          │ Reset Session State:            │
          │ ✗ authenticated = False         │
          │ ✗ user_email = None             │
          │ ✗ user_name = None              │
          │ ✗ calibration_complete = False  │
          │ ✗ assessment_complete = False   │
          │                                │
          │ st.success()                   │
          │ st.rerun()                     │
          └────────────┬───────────────────┘
                       │
                       ▼
                  [LOGIN PAGE]
```

---

## 🔐 Componentes de Autenticação

### 1. Estrutura de Credenciais

```python
┌─────────────────────────────────────┐
│     Credenciais de Demo              │
├──────────────────┬──────────────────┤
│ Email            │ Senha (Hash)     │
├──────────────────┼──────────────────┤
│ demo@spectrum.ai │ SHA256(demo123)  │
│ test@spectrum.ai │ SHA256(test123)  │
└──────────────────┴──────────────────┘
```

### 2. Fluxo de Verificação

```
        Input User
        └─────┬──────┐
              │      │
        ┌─────▼─┐  ┌─▼──────────┐
        │ Email │  │ Password   │
        └─────┬─┘  └─┬──────────┘
              │      │
              └──┬───┘
                 │
                 ▼
        ┌─────────────────────────┐
        │ verify_credentials()    │
        │ 1. Check if email exists│
        │ 2. Hash input password  │
        │ 3. Compare with stored  │
        └────────┬────────────────┘
                 │
         ┌───────┴────────┐
         │                │
        Valid          Invalid
         │                │
         ▼                ▼
      ✅ TRUE          ❌ FALSE
```

### 3. Session State Lifecycle

```
                    START
                      │
        ┌─────────────▼──────────────┐
        │ Initialize Session State   │
        │ authenticated = False       │
        │ user_email = None           │
        │ user_name = None            │
        │ calibration_complete = False│
        │ assessment_complete = False │
        └─────────────┬──────────────┘
                      │
        ┌─────────────▼────────────────┐
        │ User Submits Login Form       │
        └─────────────┬────────────────┘
                      │
        ┌─────────────▼────────────────┐
        │ Credentials Valid?            │
        └────┬────────────┬────────────┘
             │            │
            YES            NO
             │            │
        ┌────▼────┐    ┌─▼──┐
        │UPDATE:  │    │ERR │
        │authent..│    └────┘
        │user_name│
        │user_email
        └────┬────┘
             │
        ┌────▼──────────────────┐
        │ User Navigates Pages  │
        │ (Calibration, etc)    │
        └────┬──────────────────┘
             │
        ┌────▼──────────────────┐
        │ User Clicks Logout    │
        └────┬──────────────────┘
             │
        ┌────▼──────────────────┐
        │ Reset Session State:  │
        │ authenticated = False  │
        │ all = None/False       │
        └────┬──────────────────┘
             │
        ┌────▼──────────────────┐
        │ Back to Login Page     │
        └───────────────────────┘
```

---

## 🎨 Componentes de UI

### Login Form

```
┌──────────────────────────────────────────┐
│          🧠 SpectrumIA                   │
│  Eye-Tracking Based Screening Tool       │
├──────────────────────────────────────────┤
│               Login                      │
│                                          │
│  Email:                                  │
│  [________________________________]      │
│  demo@spectrum.ai                        │
│                                          │
│  Password:                               │
│  [________________________________]      │
│                                          │
│          [      Login     ]              │
│                                          │
│  Demo Credentials:                       │
│  • demo@spectrum.ai / demo123            │
│  • test@spectrum.ai / test123            │
│                                          │
└──────────────────────────────────────────┘
```

### Sidebar (Authenticated)

```
┌──────────────────────────────┐
│ 👤 Logged in as:             │
│    Demo                      │
│    demo@spectrum.ai          │
├──────────────────────────────┤
│ [🏠 Home] [🚪 Logout]        │
├──────────────────────────────┤
│ Navigation                   │
│ ○ Home                       │
│ ○ Calibration                │
│ ○ Assessment                 │
│ ○ Results                    │
├──────────────────────────────┤
│ Version: 1.0.0               │
│ Session: abc123de...         │
└──────────────────────────────┘
```

---

## 🔄 Ciclo Completo

```
┌────────────────────────────────────────────────────────────┐
│                   1. USUÁRIO ABRE APP                      │
└──────────────────────┬─────────────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────────────┐
│              2. VERIFICA AUTENTICAÇÃO                      │
│          (if not st.session_state.authenticated)          │
└──────────────────────┬─────────────────────────────────────┘
                       │
                    [NÃO]
                       │
┌──────────────────────▼─────────────────────────────────────┐
│              3. MOSTRA PÁGINA DE LOGIN                     │
│                                                             │
│  • Campo de Email                                           │
│  • Campo de Senha                                           │
│  • Botão "Login"                                            │
│  • Credenciais de Demo                                      │
└──────────────────────┬─────────────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────────────┐
│          4. USUÁRIO CLICA "LOGIN"                          │
└──────────────────────┬─────────────────────────────────────┘
                       │
┌──────────────────────▼─────────────────────────────────────┐
│    5. VERIFICA CREDENCIAIS                                 │
│                                                             │
│  verify_credentials(email, password)                        │
│  ├─ Hash a senha inserida                                  │
│  ├─ Compara com hash armazenado                            │
│  └─ Retorna True/False                                     │
└──────────────────────┬─────────────────────────────────────┘
                       │
           ┌───────────┴───────────┐
           │                       │
        [VÁLIDO]              [INVÁLIDO]
           │                       │
           ▼                       ▼
    ┌─────────────┐         ┌──────────┐
    │ SET STATE:  │         │ ERROR:   │
    │ ✓ auth=True │         │ "Invalid"│
    │ ✓ email     │         └──┬───────┘
    │ ✓ name      │            │
    └─────┬───────┘            │
          │                    │
          ▼                    ▼
    [RECARREGA]            [VOLTA PARA
      (rerun)               FORMULÁRIO]
          │
┌─────────▼──────────────────────────────────────────────────┐
│       6. USUÁRIO AUTENTICADO = MOSTRA APP PRINCIPAL        │
│                                                             │
│  • Sidebar com Home e Logout                               │
│  • Informações do usuário                                  │
│  • Navegação para páginas                                  │
│  • Content das páginas                                     │
└──────────────────────┬─────────────────────────────────────┘
                       │
           ┌───────────┴────────────────────┐
           │                                │
      [NAVEGA]                         [CLICA LOGOUT]
           │                                │
           ▼                                ▼
    ┌─────────────┐              ┌──────────────────┐
    │ Calibration │              │ RESET STATE:     │
    │ Assessment  │              │ • auth = False   │
    │ Results     │              │ • email = None   │
    │ Home        │              │ • name = None    │
    └──────┬──────┘              │ • cal_comp=False │
           │                     │ • assess_comp=F  │
           └─────────────┬────────┤                  │
                         │        └────┬─────────────┘
                         │             │
                         ▼             ▼
                    [RECARREGA]
                         │
                         ▼
                  [VOLTA AO LOGIN]
                         │
                         ▼
                    [CICLO RECOMEÇA]
```

---

## 📝 Funções Principais

### `hash_password(password: str) -> str`
```
Input:  "demo123"
Process: SHA-256 hash
Output: "d3ad9315b7be5dd5e..."
```

### `verify_credentials(email: str, password: str) -> bool`
```
Inputs: "demo@spectrum.ai", "demo123"
├─ Check if email exists
├─ Hash password
├─ Compare hashes
Output: True/False
```

### `extract_name_from_email(email: str) -> str`
```
Input:  "john.doe@spectrum.ai"
Process: split("@"), replace(".", " "), title()
Output: "John Doe"
```

### `show_login_page()`
```
Renders:
├─ Header (title + subtitle)
├─ Login Form (email + password)
├─ Login Button
├─ Demo Credentials
└─ Info Text
```

---

## 🔒 Segurança - Camadas

```
┌────────────────────────────────────────┐
│         LAYER 1: PASSWORD              │
│  Hash: SHA-256 (não reversível)        │
└────────────────┬───────────────────────┘
                 │
┌────────────────▼───────────────────────┐
│    LAYER 2: SESSION STATE              │
│  Isolado por usuário                   │
│  st.session_state (seguro)             │
└────────────────┬───────────────────────┘
                 │
┌────────────────▼───────────────────────┐
│    LAYER 3: ACCESS CONTROL             │
│  st.stop() se não autenticado          │
│  Nenhuma página sem login              │
└────────────────┬───────────────────────┘
                 │
┌────────────────▼───────────────────────┐
│    LAYER 4: LOGOUT RESET               │
│  Limpa tudo ao desconectar             │
│  Estado completamente zerado           │
└────────────────────────────────────────┘
```

---

## 📊 Fluxo de Dados

```
USER INPUT (email, senha)
        │
        ▼
hash_password(senha)
        │
        ▼
verify_credentials(email, hash)
        │
        ▼
¿Válido?
   /    \
  /      \
SIM      NÃO
 │        │
 ▼        ▼
UPDATE   ERROR
STATE    MSG
 │        │
 ▼        ▼
set:   show_error
auth   (rerun)
email
name
 │
 ▼
RERUN
 │
 ▼
CHECK AUTH
 │
 ▼
SHOW MAIN APP
```

---

## 🎯 Checklist de Funcionalidades

- [x] Login form
- [x] Email input
- [x] Password input (masked)
- [x] Login button
- [x] Error messages
- [x] Success messages
- [x] Password hashing
- [x] Credential verification
- [x] Session state management
- [x] Home button
- [x] Logout button
- [x] User info display
- [x] Logout reset
- [x] Access control
- [x] Page protection

---

*SpectrumIA Authentication System - Built 2026-04-08*
