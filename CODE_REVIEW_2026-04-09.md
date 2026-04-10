# Revisão de Código — SpectrumIA (2026-04-09)

## Escopo
Revisão técnica rápida baseada em:
- Execução de validações automatizadas (`pytest`, `ruff`).
- Inspeção de configuração de projeto (`pyproject.toml`).
- Busca de padrões de risco (`except:` sem tipo específico).

## Achados principais

### 1) **Bloqueador de qualidade de build** (Corrigido)
- **Arquivo:** `pyproject.toml`
- **Problema:** chave duplicada `testpaths` em `[tool.pytest.ini_options]`, quebrando parse TOML para ferramentas (`pytest`, `ruff`).
- **Impacto:** impede execução consistente de lint e pode quebrar CI/CD.
- **Ação aplicada:** removida a duplicidade de `testpaths`.

### 2) **Testes não executam no ambiente atual por dependência nativa**
- **Sintoma:** `pytest` falha ao importar `cv2` por ausência de `libGL.so.1`.
- **Impacto:** impede validação completa da suíte em ambientes headless/minimais sem libs de OpenCV.
- **Recomendação:** documentar dependências de sistema (ex.: `libgl1`) e/ou criar camada de fallback/mocks para testes sem backend gráfico.

### 3) **Débito técnico de lint/estilo elevado**
- **Sintoma:** `ruff check .` reporta centenas de violações (docstrings, imports, typing legado, etc.).
- **Impacto:** reduz manutenibilidade e confiança em mudanças; alto ruído em PRs.
- **Recomendação:** plano em fases:
  1. Ajustar baseline (gerar/aceitar exceções temporárias por diretório).
  2. Corrigir módulos críticos primeiro (`core/`, `models/`).
  3. Habilitar gate incremental no CI (falhar apenas em novos erros).

### 4) **Tratamento de exceção genérico**
- **Arquivo:** `app/main.py`
- **Sintoma:** uso de `except:` sem tipo específico.
- **Impacto:** pode mascarar erros inesperados e dificultar observabilidade.
- **Recomendação:** capturar exceções explícitas (`except Exception as e` já seria melhor que bare except; idealmente tipos específicos) e registrar contexto.

## Resumo executivo
- A configuração quebrada de `pyproject.toml` foi corrigida.
- A suíte ainda depende de bibliotecas nativas ausentes no ambiente atual.
- O projeto se beneficia de uma trilha de saneamento de lint em etapas para reduzir risco operacional.
