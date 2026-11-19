# Auditor ISO 22301

Plataforma web de **autoavaliação e preparação para a auditoria de certificação na ABNT NBR ISO 22301:2020** (gestão de continuidade de negócios). A empresa anexa os documentos que já tem (PCN, BIA, política, atas...), a plataforma lê tudo, **pré-preenche o questionário com os trechos que comprovam cada requisito** e o profissional só confere e valida. No fim, gera um painel e um relatório com o grau de maturidade, os pontos fortes e o que melhorar antes da auditoria externa.

> **Aviso.** O relatório é um diagnóstico preparatório baseado em autoavaliação. Ele não substitui a auditoria de um organismo certificador acreditado nem garante a certificação. Projeto acadêmico em estágio de MVP: veja [Limitações](#limitações).

![Fluxo](https://img.shields.io/badge/fluxo-documentos%20%E2%86%92%20an%C3%A1lise%20%E2%86%92%20valida%C3%A7%C3%A3o%20%E2%86%92%20relat%C3%B3rio-17305a) ![Docker](https://img.shields.io/badge/roda%20em-Docker-2496ed) ![Sem chaves](https://img.shields.io/badge/chaves%20de%20API-nenhuma%20no%20projeto-brightgreen)

## Sumário

- [O que a plataforma faz](#o-que-a-plataforma-faz)
- [Início rápido](#início-rápido)
- [Configuração](#configuração)
- [Primeiro uso](#primeiro-uso)
- [Como funciona por dentro](#como-funciona-por-dentro)
- [Tecnologias](#tecnologias)
- [Estrutura do repositório](#estrutura-do-repositório)
- [API](#api)
- [Desenvolvimento](#desenvolvimento)
- [Segurança e privacidade](#segurança-e-privacidade)
- [Aviso legal e LGPD](#aviso-legal-e-lgpd)
- [Solução de problemas](#solução-de-problemas)
- [Limitações](#limitações)
- [Créditos e avisos](#créditos-e-avisos)

## O que a plataforma faz

1. **Recebe os documentos.** Há 21 tipos esperados (política, escopo, BIA, riscos, estratégias, PCN, comunicação de crise, exercícios, auditoria interna, análise crítica...). Dá para enviar um **arquivo principal** (por exemplo um PCN completo): um script em Python identifica quais tipos ele cobre, e só os que faltam ficam abertos para anexar.
2. **Analisa.** O texto é extraído (PDF, DOCX, XLSX, TXT) e dividido em trechos. Para cada uma das **90 perguntas** e seus **243 critérios** (tirados das cláusulas 4 a 10 da norma), a busca traz os trechos mais relevantes e uma IA avalia critério a critério, citando o trecho.
3. **Mostra a evidência recortada.** Cada citação é conferida literalmente no documento. O que a IA inventar é descartado. O trecho aparece marcado em amarelo, com o contexto ao redor.
4. **Você valida.** Cada resposta é *Atende*, *Atende parcialmente*, *Não atende* ou *Não se aplica*. **Nada conta na nota até o profissional validar.**
5. **Entrega painel e relatório.** Grau de maturidade em %, radar e barras por cláusula, bloqueantes, pontos fortes e sugestões de melhoria priorizadas. O relatório imprime ou salva em PDF.

Outros recursos: termos de uso com aceite registrado, parecer de um **revisor externo** (por exemplo uma sessão do Claude Code) ao lado da sugestão da IA, e escolha do servidor de IA por configuração (nuvem ou modelo local).

## Início rápido

Requisitos: **Docker com Compose v2.24 ou mais novo**. Não precisa instalar Python nem Node.

```bash
git clone https://github.com/natanramos252/auditor.git
cd auditor/app
cp .env.example .env            # opcional: sem .env tudo usa os padrões
docker compose up -d --build    # primeira vez: alguns minutos
```

| Endereço | O que é |
|----------|---------|
| http://localhost:8080 | O auditor |
| http://localhost:3001 | Painel do freellmapi (gateway de IAs gratuitas), acessível só da sua máquina |

Sem chave de IA, o auditor funciona em **modo sem IA** (busca por palavras, confiança baixa) e avisa isso na tela de análise. Para ligar a IA, veja a próxima seção.

Parar: `docker compose down` (os dados ficam nos volumes). Apagar tudo, inclusive os dados: `docker compose down -v`.

Para testar sem documentos próprios, use os arquivos de [`app/samples/`](app/samples). O `manual_sgcn_acme.docx` é um manual **fictício** que cobre a maior parte dos requisitos.

## Configuração

Toda a configuração fica no arquivo `app/.env` (copie de `app/.env.example`). Depois de editar, recrie a API:

```bash
docker compose up -d --force-recreate api
```

### Ligar a IA com o freellmapi (já incluído no compose)

O `docker compose` sobe o [freellmapi](https://github.com/tashfeenahmed/freellmapi), um gateway que reúne vários provedores com plano gratuito atrás de um único endereço compatível com a API da OpenAI. O auditor já vem apontado para ele (`http://freellmapi:3001/v1`, modelo `auto`). Falta só a **sua** chave:

1. Abra http://localhost:3001 e crie a conta do painel (e-mail e senha, só para você).
2. No painel, adicione chaves de provedores gratuitos **suas** (Groq, Cohere, Google AI Studio, OpenRouter...). Elas ficam criptografadas no volume do freellmapi.
3. Gere a **chave do gateway** no painel e cole em `OPENAI_API_KEY` no `.env`. Essa é a chave que o auditor usa para falar com o freellmapi. O nome da variável é herdado do formato OpenAI, e a chave **não é da OpenAI**.
4. Recrie a API: `docker compose up -d --force-recreate api`.

```
Auditor ──(chave do gateway)──▶ freellmapi ──(suas chaves de provedores)──▶ Groq, Cohere, Google...
OPENAI_API_KEY no .env          painel em :3001
```

Os planos gratuitos têm limite de uso. Por isso o padrão é `LLM_CONCURRENCY=1`, e a análise de 90 perguntas leva alguns minutos. A API tenta de novo sozinha em caso de erro 429 ou 5xx.

### Outras IAs

Troque `LLM_PROVIDER` no `.env`:

| Servidor | Variáveis |
|----------|-----------|
| **freellmapi** (padrão) | `LLM_PROVIDER=openai`, `OPENAI_BASE_URL=http://freellmapi:3001/v1`, `LLM_MODEL=auto`, `OPENAI_API_KEY` |
| **Anthropic (Claude)** | `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY`, `LLM_MODEL` (opcional, padrão `claude-sonnet-5-5`) |
| **OpenAI ou compatível** (OpenRouter, Groq, Gemini, DeepSeek...) | `LLM_PROVIDER=openai`, `OPENAI_BASE_URL`, `OPENAI_API_KEY`, `LLM_MODEL` |
| **Ollama** (modelo local) | `LLM_PROVIDER=ollama`, `OLLAMA_URL=http://host.docker.internal:11434`, `LLM_MODEL=phi3.5:latest`. Ou `docker compose --profile local-llm up -d` com `OLLAMA_URL=http://ollama:11434` |
| **LM Studio, vLLM** (sem chave) | `LLM_PROVIDER=openai`, `OPENAI_BASE_URL`, `OPENAI_ALLOW_NO_KEY=1` |
| **Sem IA** | `LLM_PROVIDER=mock` |

Se o provedor exige chave e ela está vazia, o auditor cai sozinho para o modo sem IA e avisa na tela, em vez de falhar item por item.

### Todas as variáveis

| Variável | Padrão | Descrição |
|----------|--------|-----------|
| `LLM_PROVIDER` | `openai` | `openai`, `anthropic`, `ollama` ou `mock` |
| `OPENAI_BASE_URL` | `http://freellmapi:3001/v1` | Endereço da API compatível com OpenAI |
| `OPENAI_API_KEY` | vazia | Chave do gateway (ou do serviço compatível) |
| `OPENAI_ALLOW_NO_KEY` | vazia | `1` para servidores locais sem chave |
| `ANTHROPIC_API_KEY` | vazia | Chave da Anthropic |
| `OLLAMA_URL` | `http://host.docker.internal:11434` | Endereço do Ollama |
| `LLM_MODEL` | `auto` | Nome do modelo no servidor escolhido |
| `LLM_CONCURRENCY` | `1` | Chamadas de IA em paralelo (IAs gratuitas pedem 1) |
| `LLM_RETRIES` | `4` | Tentativas em erro 429, 5xx ou timeout |
| `LLM_TIMEOUT` | `120` | Segundos por chamada |
| `WEB_PORT` | `8080` | Porta do auditor |
| `FREELLMAPI_PORT` | `3001` | Porta do painel do freellmapi (só `127.0.0.1`) |
| `POSTGRES_PASSWORD` | `auditor` | Senha do banco (interno ao compose) |
| `ENCRYPTION_KEY` | gerada | Chave do freellmapi. Se vazia, é gerada na primeira execução e guardada no volume dele |
| `MAX_UPLOAD_MB` | `25` | Tamanho máximo por arquivo |
| `OPERATOR_NAME`, `OPERATOR_CONTACT` | vazios | Quem responde por esta instalação (aparece nos Termos de Uso) |

## Primeiro uso

1. Abra http://localhost:8080 e leia os **Termos de Uso**. Marque o aceite e informe seu nome (fica registrado).
2. Informe a empresa, o setor e o escopo pretendido.
3. Em **Documentos**, envie o arquivo principal ou os documentos por tipo. Corrija a identificação de tipos, se necessário.
4. Em **Análise**, inicie. Aparece o progresso e a lista dos itens já avaliados.
5. No **Questionário**, revise item por item: critérios da norma (✓ atendido, ◐ parcial, ✕ ausente), evidências recortadas e justificativa. Aceite, recuse ou acrescente evidências, escolha a resposta e clique em **Validar**.
6. O **Painel** mostra o grau de maturidade e os gráficos; o **Relatório** traz pontos fortes, lacunas e melhorias, e pode ser impresso em PDF.

## Como funciona por dentro

```
 Navegador ──▶ web (nginx + React) ──▶ api (FastAPI) ──▶ db (PostgreSQL)
                                          │
                                          ├─▶ arquivos enviados (volume)
                                          └─▶ servidor de IA ──▶ freellmapi | Claude | OpenAI-compatível | Ollama
```

**Pipeline de análise** (`backend/app/analysis.py`)

1. `extract.py` extrai o texto e o divide em trechos de cerca de 900 caracteres.
2. `retrieval.py` faz busca TF-IDF, com reforço para os documentos do tipo esperado e sem repetir trechos idênticos.
3. A IA recebe a pergunta, os **critérios da norma**, o tipo de evidência e os trechos numerados. Ela devolve, por critério, `atendido`, `parcial` ou `ausente` com uma citação literal.
4. O código confere cada citação no texto. Citação inexistente derruba o critério de "atendido" para "parcial".
5. **O nível é calculado por código**, não pela IA: cobertura = (atendidos + 0,5 × parciais) ÷ critérios. De 85% para cima é *Atende*; acima de 0, *Atende parcialmente*; 0 fica sem sugestão.
6. Para requisitos de tipo **registro**, "Atende" exige prova de execução (data passada, "foi realizado", resultado, ata). Sem isso, vira "Atende parcialmente".

**Tipo de evidência.** Cada pergunta é de *documento* (política, escopo, BIA, plano: basta existir e estar definido) ou de *registro* (exercícios, auditoria interna, análise crítica, ação corretiva: exige execução comprovada). 55 são de documento e 35 de registro.

**Nota** (`backend/app/scoring.py`, 100% por código)

- *Atende* = 100%, *Atende parcialmente* = 50%, *Não atende* = 0%, ponderado pelo peso do item.
- 15 requisitos **bloqueantes** (obrigatórios na certificação) têm peso 2.
- "Atende" sem evidência aceita vale "Atende parcialmente".
- Itens não validados contam como 0.
- **Pronta para auditoria externa**: ≥ 80%, nenhum bloqueante abaixo de "Atende" e tudo validado.
- Faixas: abaixo de 30% Inicial, até 55% Em estruturação, até 80% Parcialmente pronta.

**Catálogo.** As perguntas ficam em `backend/app/data/catalog.json` (gerado de `checklist_auditoria_ISO22301.xlsx` por `tools/build_catalog.py`). A referência na norma, o tipo de evidência e os critérios ficam em `backend/app/data/criteria.json` (`tools/build_criteria.py`). Os critérios são **resumos** dos requisitos da norma e devem ser conferidos com o texto oficial.

**Revisor externo.** A API `/api/assessments/{id}/review/*` recebe um parecer por critério de um revisor (por exemplo, uma sessão do Claude Code) e confere cada citação no texto. O parecer aparece na tela, separado da sugestão da IA, com o botão **Adotar este parecer** (por item ou em lote). Adotar **não valida**. A análise detalhada está em [`analise_criterios_x_norma.md`](analise_criterios_x_norma.md).

## Tecnologias

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.12, FastAPI 0.115, Uvicorn, SQLAlchemy 2.0, psycopg 3 |
| Leitura de documentos | pypdf, python-docx, openpyxl |
| Cliente de IA | httpx (adaptadores para OpenAI-compatível, Anthropic e Ollama, com nova tentativa e saída em JSON validada) |
| Frontend | React 18.3, TypeScript 5.6, Vite 5.4 (gráficos em SVG próprio, sem biblioteca) |
| Tipografia | Bricolage Grotesque e Source Serif 4, empacotadas localmente (`@fontsource`) |
| Banco | PostgreSQL 16 (SQLite nos testes e no desenvolvimento local) |
| Contêineres | Docker Compose; nginx-unprivileged serve o frontend e faz proxy da API |
| Gateway de IA | [freellmapi](https://github.com/tashfeenahmed/freellmapi) (terceiros, MIT) |
| Testes | pytest (17 testes do backend) |

## Estrutura do repositório

```
auditor/
├── README.md                          este arquivo
├── requirements.md                    requisitos do produto
├── perguntas_x_norma_ISO22301.md      as 90 perguntas e a cláusula que cada uma verifica
├── checklist_auditoria_ISO22301.xlsx  checklist em planilha
├── analise_criterios_x_norma.md       análise dos critérios contra a norma
├── .githooks/pre-commit               bloqueia commit com chave, .env ou dado pessoal
└── app/
    ├── docker-compose.yml             auditor + freellmapi, já ligados
    ├── .env.example                   configuração, sem nenhum valor secreto
    ├── samples/                       documentos fictícios para testar
    ├── backend/
    │   ├── app/
    │   │   ├── main.py                rotas da API
    │   │   ├── analysis.py            análise: critérios, citações, nível
    │   │   ├── classify.py            tipos de documento cobertos por um arquivo principal
    │   │   ├── retrieval.py           busca de trechos
    │   │   ├── extract.py             leitura de PDF, DOCX, XLSX e texto
    │   │   ├── scoring.py             nota, bloqueantes e sugestões
    │   │   ├── terms.py               termos de uso e hash do texto aceito
    │   │   ├── llm/                   adaptadores de IA
    │   │   └── data/                  catalog.json, criteria.json, terms.json
    │   ├── tools/                     geradores do catálogo e dos critérios
    │   └── tests/
    └── frontend/src/                  telas: início, documentos, análise, questionário, painel, relatório
```

## API

Documentação interativa (Swagger) em `http://localhost:8000/docs` quando a API é executada diretamente com `uvicorn` (veja [Desenvolvimento](#desenvolvimento)). Principais rotas:

| Método e rota | Função |
|---------------|--------|
| `GET /api/catalog` | Perguntas, critérios, tipos de documento e IA em uso |
| `GET /api/terms` | Termos de uso (texto, versão e hash) |
| `POST /api/assessments` | Cria avaliação (exige aceite dos termos) |
| `POST /api/assessments/{id}/documents` | Envia documento (`slot=principal` para arquivo consolidado) |
| `POST /api/assessments/{id}/analyze` | Inicia a análise |
| `GET /api/assessments/{id}/items` | Perguntas com resposta, sugestão e evidências |
| `PUT /api/assessments/{id}/answers/{n}` | Salva e valida uma resposta |
| `GET /api/assessments/{id}/report` | Nota, bloqueantes, pontos fortes e melhorias |
| `GET /api/assessments/{id}/review/queue` | Fila para um revisor externo |
| `POST /api/assessments/{id}/review` | Envia o parecer do revisor |
| `POST /api/assessments/{id}/review/adopt-all` | Adota todos os pareceres (não valida) |

## Desenvolvimento

```bash
# backend
cd app/backend
python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload          # API em :8000, SQLite em ./data
.venv/bin/pytest tests                           # 17 testes

# frontend
cd ../frontend
npm install && npm run dev                       # interface em :5173, com proxy para a API
npm run build                                    # confere os tipos e gera o build
```

Para regenerar o catálogo e os critérios (precisa de `openpyxl`):

```bash
python app/backend/tools/build_catalog.py checklist_auditoria_ISO22301.xlsx app/backend/app/data/catalog.json
python app/backend/tools/build_criteria.py perguntas_x_norma_ISO22301.md app/backend/app/data/criteria.json
```

Antes de contribuir, ative o bloqueio de commit: `git config core.hooksPath .githooks`.

## Segurança e privacidade

- **Nenhuma chave de API está no repositório.** O `.env` não é versionado, e o `.env.example` vem vazio.
- **Bloqueio de commit** (`.githooks/pre-commit`): recusa chaves de API, `.env`, bancos de dados, uploads, o texto da norma, caminhos locais e e-mails pessoais.
- **ENCRYPTION_KEY do freellmapi**: em vez de pôr uma no projeto, o compose gera uma na primeira execução e a guarda no volume `freellmapi-data`, junto do banco que ela protege. Se apagar o volume, as chaves de provedores guardadas no painel se perdem.
- **Seus documentos e a IA.** Com um provedor de nuvem ligado, **trechos dos seus documentos são enviados a esse provedor** (pelo gateway). Isso consta nos Termos de Uso, cujo texto muda conforme o servidor de IA. O freellmapi também consulta periodicamente o catálogo de modelos em `api.freellmapi.co`. Para manter tudo local, use Ollama ou o modo sem IA.
- **Termos de uso.** Criar avaliação, enviar documentos e analisar exigem o aceite na versão atual. O aceite fica na tabela `terms_acceptances` (versão, nome, data e hora, hash do texto). O texto é um **modelo e deve passar por revisão jurídica** antes de uso com terceiros.
- **Sem login e sem separação entre empresas.** Quem acessa a tela vê todas as avaliações. **Não exponha à internet.**

## Aviso legal e LGPD

Este texto é informativo e **não é parecer jurídico**. Quem instala e opera a plataforma é o responsável por usá-la de acordo com a lei.

**Nome, marcas e certificação**
- Este projeto é independente. **Não tem vínculo, patrocínio nem aprovação da ISO, da ABNT ou de qualquer organismo certificador.** "ISO" e "ABNT" são marcas de seus titulares e aparecem aqui só para indicar qual norma a ferramenta avalia.
- Ele avalia a **prontidão** para a ISO 22301. **Não emite certificado, selo ou atestado de conformidade.** Só um organismo certificador acreditado certifica. O relatório traz esse aviso, e o aceite dos Termos de Uso o repete.
- O repositório não usa logotipos da ISO nem da ABNT e não deve usá-los. Ao divulgar, escreva "avalia a prontidão para a ISO 22301", nunca "certificado ISO" nem "aprovado pela ISO".

**Direitos autorais da norma**
- O texto da norma **não é distribuído**. Os critérios e as perguntas são resumos escritos para este projeto, com referência às cláusulas. Compare com a norma oficial, que prevalece.

**LGPD (Lei 13.709/2018)**
- Publicar o código não é tratar dados. A obrigação recai sobre **quem opera** uma instalação (o controlador), que deve ter base legal, informar os titulares e atender a seus direitos.
- Os documentos anexados (PCN, atas, listas de contatos) podem conter **dados pessoais**: nomes, e-mails, telefones, cargos. Eles ficam no banco e na pasta de uploads da instalação, sem prazo de retenção e sem botão de exclusão (veja [Limitações](#limitações)).
- **Trechos dos documentos são enviados ao provedor de IA configurado.** Com a IA em nuvem, isso é uma **transferência internacional de dados** (art. 33 da LGPD). Para dados pessoais ou sigilosos, use o Ollama (local) ou o modo sem IA, ou anonimize antes de anexar.
- Informe o responsável pela instalação em `OPERATOR_NAME` e `OPERATOR_CONTACT`. Eles aparecem nos Termos de Uso.

**Provedores gratuitos de IA (freellmapi)**
- Planos gratuitos de IA costumam **registrar os pedidos e usá-los para melhorar os modelos**. Não envie documentos confidenciais, de clientes ou com dados pessoais por esse caminho.
- O freellmapi alterna entre várias contas e chaves gratuitas para contornar limites de uso. Isso **pode violar os termos de alguns provedores** e levar ao bloqueio da sua conta ou chave. Leia os termos de cada provedor antes de cadastrar a chave. O risco é de quem usa. O freellmapi é de terceiros e não é mantido aqui.
- Use chaves **suas** e nunca compartilhe a chave do gateway nem exponha o painel à internet.

## Solução de problemas

| Sintoma | Causa provável e solução |
|---------|--------------------------|
| A análise diz "sem IA" ou "falta a chave" | `OPENAI_API_KEY` vazia. Gere a chave no painel do freellmapi e recrie a API |
| Erro 401 do freellmapi | Chave do gateway errada ou ausente. Confira `OPENAI_API_KEY` |
| Erro 429 ou itens "falharam" | Limite do plano gratuito. Mantenha `LLM_CONCURRENCY=1`, adicione mais provedores no painel ou espere e use **Reanalisar** |
| Erro 404 "Model not in the catalog" | Use `LLM_MODEL=auto` ou um nome listado em `/v1/models` |
| `env file ... not found` | Use Compose 2.24 ou mais novo (o `.env` é opcional) |
| Porta 8080 ou 3001 ocupada | Mude `WEB_PORT` ou `FREELLMAPI_PORT` no `.env` |
| Avaliações antigas sumiram depois de atualizar | O compose mudou de nome de projeto e criou volumes novos. Os dados antigos continuam nos volumes do projeto anterior |
| PDF não gera trechos | Documento escaneado (imagem). Ainda não há OCR |
| `Aceite os Termos de Uso para continuar` | Avaliação criada antes dos termos, ou versão nova. Aceite na tela |

## Limitações

- Sem login, sem multiempresa e sem trilha completa de alterações.
- Sem OCR (PDF escaneado não é lido) e sem antivírus nos uploads. A análise roda em uma thread da API.
- A busca é por palavras (TF-IDF). Embeddings ficam para uma próxima versão.
- Não há botão para excluir uma avaliação.
- A seleção do servidor de IA é por configuração, não pela interface.
- Os critérios são resumos dos requisitos e podem conter imprecisões. A norma oficial prevalece.
- As sugestões de melhoria derivam do catálogo e ainda não foram revisadas por um especialista em continuidade.

## Créditos e avisos

- **Norma.** O texto da ABNT NBR ISO 22301:2020 tem direitos autorais da ISO e da ABNT e **não é distribuído** neste repositório. Adquira a norma para a certificação.
- **freellmapi** é um projeto de terceiros (licença MIT), usado como gateway de IA e não mantido aqui.
- **Dados de exemplo.** As empresas dos documentos de amostra (Acme, Códon Bank) são fictícias.
- **Licença.** Código sob a [licença MIT](LICENSE). Ela cobre só o código deste repositório: não inclui a norma, as marcas da ISO e da ABNT, nem o freellmapi, que tem a própria licença.
