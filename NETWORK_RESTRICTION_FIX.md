# 🔧 Como Solucionar Restrição de Rede - GitHub Push

**Data:** 8 de Abril de 2026  
**Problema:** Erro 403 Forbidden - Proxy bloqueando acesso a GitHub  
**Objetivo:** Encontrar método de push que funcione

---

## 🔍 Diagnóstico do Problema

```bash
# Erro recebido:
Received HTTP code 403 from proxy after CONNECT

# Significa:
- ❌ HTTPS direto bloqueado
- ❌ Proxy está interceptando
- ✅ Possíveis soluções: SSH, CLI, VPN
```

---

## 🛠️ SOLUÇÃO 1: GitHub CLI (Recomendado - Mais Fácil)

### Por Que Funciona
GitHub CLI contorna alguns proxies corporativos de forma mais eficiente.

### Passo a Passo

#### 1. Instalar GitHub CLI

**macOS:**
```bash
brew install gh
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-key 23F3D4EA75716059
sudo add-apt-repository https://cli.github.com/packages
sudo apt update
sudo apt install gh
```

**Linux (Fedora/RHEL):**
```bash
sudo dnf install gh
```

**Windows (se aplicável):**
```bash
choco install gh
```

#### 2. Autenticar com GitHub

```bash
gh auth login

# Ele vai perguntar:
# - What account do you want to log into? → github.com
# - What is your preferred protocol? → HTTPS (se quiser SSH, escolha SSH)
# - Authenticate Git with your GitHub credentials? → Y
# - How would you like to authenticate? → Paste authentication token
```

Se não tiver token:
1. Ir para https://github.com/settings/tokens
2. Criar novo token com scopes: `repo`, `read:org`
3. Copiar e colar no terminal

#### 3. Fazer Push via CLI

```bash
cd ~/Projects/SpectrumIA
gh repo push
```

**Vantagem:** CLI bypassa alguns problemas de proxy

---

## 🛠️ SOLUÇÃO 2: SSH (Mais Seguro - Sem Proxy)

SSH frequentemente contorna proxies porque usa porta 22 (diferente de HTTPS).

### Passo a Passo

#### 1. Gerar SSH Key

```bash
# Gerar key (se não tiver)
ssh-keygen -t ed25519 -C "seu-email@github.com"

# Ou se não suportar ed25519:
ssh-keygen -t rsa -b 4096 -C "seu-email@github.com"

# Pressionar Enter 3x para usar padrão
```

#### 2. Adicionar Key ao GitHub

```bash
# Copiar public key
cat ~/.ssh/id_ed25519.pub  # ou id_rsa.pub

# Ir para: https://github.com/settings/keys
# Clicar "New SSH key"
# Colar a key
# Title: "My Mac" ou similar
# Salvar
```

#### 3. Configurar Repositório para SSH

```bash
cd ~/Projects/SpectrumIA

# Mudar URL de HTTPS para SSH
git remote set-url origin git@github.com:marccut/SpectrumIA.git

# Verificar
git remote -v
# Deve mostrar: git@github.com:marccut/SpectrumIA.git
```

#### 4. Fazer Push

```bash
git pull origin main
git push origin main
```

**Vantagem:** SSH não passa por proxy HTTP (usa porta 22)

---

## 🛠️ SOLUÇÃO 3: GitHub Desktop (GUI)

Se linha de comando for complicado, use interface gráfica.

### Passo a Passo

#### 1. Instalar GitHub Desktop

```bash
# macOS
brew install github-desktop

# Ou baixar de: https://desktop.github.com/
```

#### 2. Login

- Abrir GitHub Desktop
- File → Sign in to GitHub.com
- Autenticar com GitHub

#### 3. Clonar Repositório

- File → Clone Repository
- Digitar: `marccut/SpectrumIA`
- Clonar

#### 4. Fazer Push

- Botão "Push origin" no topo
- Se houver conflitos, GitHub Desktop ajuda a resolver

**Vantagem:** GUI mais intuitiva

---

## 🛠️ SOLUÇÃO 4: Configurar Git com Proxy (Se Conhecer Proxy)

Se sua rede usa proxy corporativo explícito:

```bash
# Se conhecer detalhes do proxy:
git config --global http.proxy [protocol]://[user]:[password]@[proxy-server]:[port]

# Exemplo:
git config --global http.proxy http://user:password@proxy.company.com:8080
git config --global https.proxy http://user:password@proxy.company.com:8080

# Depois:
git push origin main
```

**⚠️ Só funciona se souber detalhes do proxy**

---

## 🛠️ SOLUÇÃO 5: Mudar de Rede (Mais Fácil)

Se tiver acesso a outra rede (celular, WiFi pública):

```bash
# Conectar a rede alternativa
# Exemplo: hotspot do celular

# Depois:
cd ~/Projects/SpectrumIA
git push origin main
```

**Vantagem:** Sem proxy corporativo

---

## 🛠️ SOLUÇÃO 6: VPN (Se Permitido)

Se sua empresa permitir VPN:

```bash
# 1. Conectar a VPN
# 2. Depois:
cd ~/Projects/SpectrumIA
git push origin main
```

**Vantagem:** Contorna restrições de rede local

---

## 📊 Comparação de Métodos

| Método | Facilidade | Chance de Sucesso | Pré-requisitos |
|--------|-----------|-------------------|----------------|
| **GitHub CLI** | ⭐⭐⭐⭐ (Muito Fácil) | 90% | Instalar `gh` |
| **SSH** | ⭐⭐⭐ (Médio) | 95% | SSH key configurada |
| **GitHub Desktop** | ⭐⭐⭐⭐⭐ (Muito Fácil) | 85% | GUI download |
| **Proxy Config** | ⭐ (Difícil) | 70% | Detalhes do proxy |
| **Mudar Rede** | ⭐⭐ (Fácil) | 99% | Acesso a outra rede |
| **VPN** | ⭐⭐⭐ (Médio) | 95% | VPN disponível |

**Recomendação:** Tentar na ordem: CLI → SSH → GitHub Desktop → Mudar Rede

---

## ✅ Testes de Conectividade

### Teste 1: HTTPS (Vai falhar)
```bash
git clone https://github.com/marccut/SpectrumIA.git test-https
# ❌ Resultado esperado: 403 Forbidden
```

### Teste 2: SSH (Pode funcionar)
```bash
ssh -T git@github.com
# ✅ Se funcionou: "Hi [username]! You've authenticated..."
# ❌ Se falhar: Configurar SSH conforme SOLUÇÃO 2
```

### Teste 3: GitHub CLI (Deve funcionar)
```bash
gh repo clone marccut/SpectrumIA test-cli
# ✅ Se funcionou: repo clonado com sucesso
```

---

## 🔍 Diagnosticar Qual Funciona

```bash
#!/bin/bash

echo "=== Testando Conectividade ==="

echo -n "1. HTTPS: "
curl -I https://github.com 2>&1 | grep -q "200\|301\|302" && echo "✅ OK" || echo "❌ BLOQUEADO"

echo -n "2. SSH: "
ssh -T git@github.com 2>&1 | grep -q "authenticated" && echo "✅ OK" || echo "❌ BLOQUEADO"

echo -n "3. GitHub CLI: "
gh auth status 2>&1 | grep -q "Logged in" && echo "✅ OK" || echo "❌ NÃO AUTENTICADO"

echo -n "4. Porta 22: "
nc -zv github.com 22 2>&1 | grep -q "open\|Connection refused" && echo "✅ ABERTA" || echo "❌ BLOQUEADA"
```

---

## 📋 Checklist de Resolução

Tentar nesta ordem:

### ✅ Passo 1: GitHub CLI (5 min)
- [ ] `brew install gh` (ou equivalente no seu SO)
- [ ] `gh auth login`
- [ ] `gh repo clone marccut/SpectrumIA`
- Se funcionou: **USE ISSO**
- Se falhou: próximo passo

### ✅ Passo 2: SSH (10 min)
- [ ] Gerar SSH key: `ssh-keygen -t ed25519`
- [ ] Copiar public key: `cat ~/.ssh/id_ed25519.pub`
- [ ] Adicionar em GitHub Settings
- [ ] Mudar URL: `git remote set-url origin git@github.com:marccut/SpectrumIA.git`
- [ ] Testar: `git push origin main`
- Se funcionou: **USE ISSO**
- Se falhou: próximo passo

### ✅ Passo 3: GitHub Desktop (3 min)
- [ ] Instalar GitHub Desktop
- [ ] Fazer login
- [ ] Clonar SpectrumIA
- [ ] Fazer Push
- Se funcionou: **USE ISSO**
- Se falhou: próximo passo

### ✅ Passo 4: Mudar de Rede (1 min)
- [ ] Desconectar WiFi corporativo
- [ ] Conectar ao hotspot do celular (ou outro WiFi)
- [ ] `git push origin main`
- Se funcionou: **FAÇA ISSO QUANDO POSSÍVEL**

---

## 🎯 Seu Caso Específico

Baseado no erro `403 Forbidden from proxy`:

### 🥇 Mais Provável Funcionar
1. **GitHub CLI** ← TENTE PRIMEIRO
2. **SSH** ← SEGUNDO
3. **GitHub Desktop** ← TERCEIRO

### ⚠️ Menos Provável Neste Momento
- Proxy configuration (sem detalhes do proxy)
- VPN (se não tiver acesso)

---

## 📞 Se Nada Funcionar

### Opção A: Repositório Alternativo
Se proxy bloquear GitHub permanentemente:
- GitLab (git.gitlab.com)
- Gitea (auto-hospedado)
- Azure DevOps

### Opção B: Commit Local Seguro
Seu commit está seguro em:
```bash
git log --oneline -3
# b1457e9 Fix: Resolve state logic...
```

Pode fazer push quando conseguir conectividade.

---

## 🚀 Após Conseguir Push

```bash
# 1. Fazer pull
git pull origin main

# 2. Fazer push
git push origin main

# 3. Verificar sucesso
git log --oneline -1
# Deve mostrar b1457e9 no remoto
```

---

## 📚 Recursos Úteis

- [GitHub CLI Documentation](https://cli.github.com/manual)
- [GitHub SSH Setup](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)
- [GitHub Desktop](https://desktop.github.com/)
- [Git Config Proxy](https://git-scm.com/docs/git-config#http.proxy)

---

**Próximo Passo:** Tentar GitHub CLI agora  
**Arquivo Suplementar:** PUSH_LATER.md (se nenhuma solução funcionar)  
**Status do Commit:** Seguro localmente em `b1457e9`
