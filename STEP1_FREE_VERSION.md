# 🚀 STEP 1: Create Supabase Project (FREE TIER)

**Estimated Time**: 15 minutes
**Plano**: FREE (para testes)
**Status**: PRONTO PARA COMEÇAR

---

## 🎯 Quick Steps (usando Free)

### 1. Acesse Supabase
```
Ir para: https://app.supabase.com
Fazer login (ou criar conta se não tiver)
```

### 2. Create New Project
```
Clique: "New project" (botão azul)
```

### 3. Preencha o Formulário

**Campo 1: Name (Nome)**
```
Coloque: spectrumia-production
(Mesmo nome, vamos testar e depois fazer upgrade)
```

**Campo 2: Password (Senha do Banco)**
```
Clique: "Generate a password"
OU digite uma senha forte (min 16 caracteres)

IMPORTANTE: Salve essa senha!
Você precisará para o DATABASE_URL
```

**Campo 3: Region**
```
Escolha a região mais próxima de você
Opções:
  - us-east-1 (Virginia) - se for USA
  - eu-west-1 (Irlanda) - se for Europa
  - ap-southeast-1 (Singapore) - se for Ásia
```

**Campo 4: Pricing Plan** ⭐ IMPORTANTE
```
NÃO clique em "Pro"
CLIQUE EM: "Free"  ← Este aqui!

Isso vai economizar dinheiro durante testes
```

### 4. Clique "Create project"
```
Aguarde 2-3 minutos
Supabase inicializa automaticamente
```

### 5. Copie as Credenciais

Quando o projeto estiver pronto, vá para:
```
Settings → API
```

Copie esses 5 valores:

**1. SUPABASE_URL**
```
Procure: "Project URL"
Exemplo: https://abcdefgh123456.supabase.co
```

**2. SUPABASE_ANON_KEY**
```
Procure: "Anon key"
Clique: "Copy"
```

**3. SUPABASE_SERVICE_ROLE_KEY**
```
Procure: "Service role key"
Clique: "Copy"
⚠️ Mantenha este secreto!
```

**4. JWT_SECRET**
```
Procure: "JWT Settings" ou "JWT secret"
Clique: "Show" depois "Copy"
```

**5. DATABASE_URL**
```
Vá para: Settings → Database (ou Connections)
Procure: "Connection string"

Ou construa manualmente:
postgresql://postgres:[senha]@db.[project-id].supabase.co:5432/postgres

Onde:
  [senha] = a senha que você gerou no passo 2
  [project-id] = o ID do seu projeto
```

### 6. Salve Credenciais
```
Crie um arquivo temporário com:

SUPABASE_URL=https://...
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
JWT_SECRET=...
DATABASE_URL=postgresql://...
```

---

## ✅ Pronto!

Quando terminar o Step 1, você terá:
- ✅ Projeto Supabase criado (Free)
- ✅ 5 credenciais salvas
- ✅ Dashboard acessível
- ✅ Pronto para Step 2

---

## 📝 Nota Importante

**Free vs Pro agora**:
- Free é perfeito para testes
- Depois você faz upgrade para Pro (1 clique) quando precisar
- Todos os dados/config transferem automaticamente
- Sem perda de código ou configuração

---

**Próximo passo após Step 1**:
→ Venha contar que terminou e vou guiar Steps 2-6!

