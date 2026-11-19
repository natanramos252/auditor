# Prontidão ISO 22301 — MVP

Plataforma web em que a empresa anexa seus documentos, a análise pré-preenche o questionário (90 perguntas da ISO 22301)
com trechos recortados como evidência, o profissional valida, e o sistema gera o relatório de maturidade e melhorias.

## Rodar (contêineres)
```bash
cp .env.example .env      # ajuste LLM_PROVIDER e a chave, se for usar IA
docker compose up --build # abre em http://localhost:8080
```
Sem configurar nada, roda em modo `mock` (busca por palavras, sem IA, confiança baixa). Para IA real:

| Provedor | Variáveis |
|----------|-----------|
| Anthropic (nuvem) | `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY`, `LLM_MODEL` (padrão `claude-sonnet-5-5`) |
| OpenAI ou compatível | `LLM_PROVIDER=openai`, `OPENAI_API_KEY`, `OPENAI_BASE_URL` |
| Local (Ollama) | `LLM_PROVIDER=ollama`, `OLLAMA_URL`, `LLM_MODEL`; subir com `--profile local-llm` |

Trocar entre nuvem e local é só mudar essas variáveis e reiniciar o `api`.

## Desenvolvimento
```bash
cd backend && python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload          # API em :8000 (SQLite em ./data)
.venv/bin/pytest tests                           # testes
cd ../frontend && npm install && npm run dev     # interface em :5173
```
`samples/` tem três documentos fictícios para testar o fluxo.

## Como funciona
1. **Documentos:** 21 tipos esperados (política, BIA, PCN, atas...). Cada tipo aponta quais perguntas costuma sustentar (`backend/tools/build_catalog.py`).
2. **Análise:** o texto é extraído e dividido em trechos; para cada pergunta a busca traz os mais relevantes (com reforço para o tipo de documento esperado) e a IA sugere nível, justificativa e citações. Citações que não existem literalmente nos trechos são descartadas.
3. **Validação:** nada conta na pontuação até o profissional validar. Nível 3+ sem evidência aceita vale 2.
4. **Relatório:** notas e prioridades são calculadas por código (`scoring.py`), não pela IA.

## Limitações conhecidas do esqueleto
- Sem login/multiempresa: qualquer um com acesso vê todas as avaliações. **Não expor à internet assim.**
- Sem OCR (PDF escaneado não é lido); sem antivírus nos uploads; sem Redis/MinIO (análise roda em thread da API, arquivos em volume).
- Busca é lexical; embeddings (pgvector) ficam para depois.
- Sugestões de melhoria derivam do catálogo; ainda falta o texto de recomendação revisado por especialista.
- Caminho com IA real (`anthropic`/`openai`/`ollama`) coberto só por teste com provedor falso; não foi executado contra a API real.
