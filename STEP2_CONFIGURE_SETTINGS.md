# ⚙️ STEP 2: Configure Project Settings

**Estimated Time**: 15 minutes
**Status**: PRONTO PARA COMEÇAR
**Pré-requisito**: Step 1 completo ✅

---

## 🎯 O que fazer neste passo

Habilitar extensões e configurar limites de banco de dados no Supabase.

---

## 📋 3 Tarefas Rápidas

### **Tarefa 1: Enable UUID Extension (2 min)**

No dashboard Supabase:

```
1. Clique em "SQL Editor" (no menu esquerdo)
2. Clique em "New Query"
3. Cole este SQL:

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

4. Clique "Run"
5. Você verá: "Success. No rows returned"
```

✅ **Feito!** UUID extension habilitada.

---

### **Tarefa 2: Configure Database Connection Limits (5 min)**

```
1. Clique em "Settings" (gear icon, canto inferior esquerdo)
2. Procure por "Database" ou "Connections"
3. Você verá campos como:

   ┌─────────────────────────────────┐
   │ Max connections: [100]          │
   │ Idle timeout: [5 minutes]       │
   │ Statement timeout: [30 seconds] │
   └─────────────────────────────────┘

4. Deixe os valores como estão (defaults são bons)
5. Desça um pouco mais
```

✅ **Feito!** Connection limits configurados.

---

### **Tarefa 3: Configure Backups (5 min)**

Ainda em Settings:

```
1. Procure por "Backups" na sidebar
2. Você verá opções de backup

   ┌──────────────────────────────────┐
   │ ☐ Enable automated backups       │
   │ Frequency: Daily                 │
   │ Retention: 30 days               │
   └──────────────────────────────────┘

3. Se "Enable automated backups" estiver disponível:
   ☑ Marque a checkbox

4. Deixe outras opções com valores default

5. Scroll para baixo e clique "Save" (se houver)
```

⚠️ **Nota**: No FREE tier, alguns recursos de backup são limitados.
Isso é OK para testes! Quando fazer upgrade para PRO, ficam mais robustos.

✅ **Feito!** Backups configurados (ou preparados para PRO).

---

## ✅ Step 2 Checklist

- [ ] Extensões habilitadas (uuid-ossp, pgcrypto)
- [ ] SQL query executada com sucesso
- [ ] Connection limits verificados
- [ ] Database configurado
- [ ] Backup settings verificados

---

## 🎯 Resultado Final do Step 2

Seu banco de dados agora está configurado com:
- ✅ UUID support (para IDs únicos)
- ✅ Connection pooling configurado
- ✅ Backups preparados (ou habilitados no PRO)

---

## ⏭️ Próximo Passo

→ **Step 3: Apply Database Migrations**

Você vai copiar e colar o `models/migrations.sql` no SQL Editor.

Avise quando terminar Step 2! 👍

