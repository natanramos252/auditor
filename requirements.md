# Requisitos — Plataforma de Autoavaliação e Prontidão para Certificação

Versão 0.2 · rascunho para validação
(v0.1 tratava o produto como ferramenta do auditor; agora o cliente é a empresa que se autoavalia.)

## 1. Visão

Plataforma web em que **empresas respondem a um questionário** baseado em uma norma (primeira: ABNT NBR ISO 22301:2020, continuidade de negócios) e recebem ao final um **relatório de prontidão** com:

- **grau de maturidade** geral e por cláusula;
- **pontos fortes**;
- **lacunas** em relação à norma;
- **sugestões de melhoria priorizadas** e um plano de ação para chegar preparada a uma **auditoria externa de certificação**.

A IA ajuda a interpretar respostas e evidências, explica os requisitos em linguagem simples e redige o relatório. O resultado é um diagnóstico de preparação; **não substitui nem emite a certificação**, que é concedida por organismo certificador acreditado.

Execução em **contêineres** (Docker), por `docker compose` em desenvolvimento e em produção.

## 2. Atores

| Ator | Descrição |
|------|-----------|
| Administrador da empresa | Cria a conta da empresa, convida pessoas, vê todos os relatórios |
| Respondente | Funcionário que responde parte do questionário (ex.: TI, RH, jurídico, diretoria) |
| Revisor interno | Valida respostas e evidências antes de gerar o relatório (opcional) |
| Leitor | Visualiza resultados (diretoria, consultor externo convidado) |
| Administrador da plataforma | Opera o SaaS: empresas, planos, catálogo de normas, métricas |

## 3. Jornada do usuário

1. A empresa se cadastra e informa seu perfil (setor, porte, escopo pretendido).
2. Cria uma **avaliação** escolhendo a norma.
3. Distribui as cláusulas entre respondentes.
4. Cada respondente responde às perguntas (escala de maturidade), explica e anexa evidências.
5. A IA analisa as respostas e evidências, aponta inconsistências e pede esclarecimentos.
6. A empresa revisa e fecha a avaliação.
7. A plataforma gera o **relatório de prontidão** e o plano de melhorias.
8. Após executar ações, a empresa faz uma **nova rodada** e compara a evolução.

## 4. Modelo de maturidade

Cada pergunta é respondida em uma escala (proposta, a validar):

| Nível | Nome | Significado |
|-------|------|-------------|
| 0 | Inexistente | Não é feito, nem há planejamento |
| 1 | Inicial | Feito de forma informal, depende de pessoas |
| 2 | Definido | Existe processo documentado, mas sem registros de execução consistentes |
| 3 | Implementado | Documentado, executado e com **evidências** de que acontece |
| 4 | Gerenciado | Medido e monitorado com indicadores e análise crítica |
| 5 | Otimizado | Melhoria contínua comprovada |

- Há também a opção **Não se aplica** (exige justificativa; a IA avalia se é plausível).
- **Maturidade por cláusula** = média ponderada dos itens. Peso padrão por item, ajustável no catálogo; itens críticos (política, BIA, planos, exercícios, auditoria interna, análise crítica pela direção) têm peso maior.
- **Maturidade geral** = média ponderada das cláusulas, convertida em faixa:

| Faixa | Interpretação |
|-------|---------------|
| < 1,5 | Inicial: longe da certificação |
| 1,5 a 2,5 | Em estruturação |
| 2,5 a 3,5 | Parcialmente pronta: ainda há lacunas relevantes |
| ≥ 3,5 | Pronta para auditoria externa (se não houver itens bloqueantes) |

- **Itens bloqueantes:** requisitos obrigatórios da norma (cláusulas 4 a 10) que, se estiverem abaixo do nível 3, impedem a classificação como "pronta", mesmo com média alta. (Inclui informação documentada exigida, auditoria interna e análise crítica pela direção realizadas ao menos uma vez.)
- **Nível de confiança do diagnóstico:** reduz quando as respostas altas não têm evidência anexada ou a IA encontra inconsistências.

## 5. Requisitos funcionais

Prioridade: **M** = MVP · **D** = depois · **F** = futuro.

### 5.1 Contas e empresas (multi-tenant)
| ID | Requisito | P |
|----|-----------|---|
| RF-01 | Cadastro de empresa com perfil (setor, porte, escopo) e dados isolados das demais | M |
| RF-02 | Convite de usuários por e-mail e papéis (Admin, Respondente, Revisor, Leitor) | M |
| RF-03 | Login com e-mail/senha, recuperação de senha e MFA | M |
| RF-04 | SSO (Google/Microsoft) | D |
| RF-05 | Planos e cobrança por assinatura | D |

### 5.2 Catálogo de normas
| ID | Requisito | P |
|----|-----------|---|
| RF-10 | Catálogo com: cláusula, pergunta, explicação em linguagem simples, exemplos de evidência, peso, indicador de bloqueante | M |
| RF-11 | Carga inicial da ISO 22301 a partir de `checklist_auditoria_ISO22301.xlsx` (90 itens) | M |
| RF-12 | Versionamento do catálogo; a avaliação fica presa à versão usada | M |
| RF-13 | Outras normas (ISO 27001, ISO 9001, LGPD) e perguntas condicionais ao perfil da empresa | D |
| RF-14 | Edição do catálogo pelo administrador da plataforma, sem mexer em código | D |

### 5.3 Questionário e evidências
| ID | Requisito | P |
|----|-----------|---|
| RF-20 | Criar avaliação: norma, escopo, prazo e distribuição de cláusulas entre respondentes | M |
| RF-21 | Responder cada pergunta com nível 0 a 5 ou N/A, comentário e salvamento automático | M |
| RF-22 | Ajuda por pergunta: o que a norma exige, por que importa, exemplo de boa resposta e de evidência, tudo em linguagem simples | M |
| RF-23 | Anexar evidências (PDF, DOCX, XLSX, imagens) a cada resposta, com descrição | M |
| RF-24 | Acompanhamento do progresso (% respondido por cláusula e por pessoa) | M |
| RF-25 | Atribuir pergunta a outra pessoa e comentar entre colegas | D |
| RF-26 | Responder por importação de planilha | D |

### 5.4 Análise por IA
| ID | Requisito | P |
|----|-----------|---|
| RF-30 | Extrair texto das evidências (com OCR) e indexar | M |
| RF-31 | Para cada resposta, a IA verifica se a evidência sustenta o nível declarado e sugere o nível "provável", com justificativa e citação do trecho | M |
| RF-32 | Autoavaliações inflacionadas: quando o nível declarado ≥ 3 sem evidência, sinalizar e pedir o que anexar | M |
| RF-33 | Verificar qualidade da evidência: data, responsável, recência, versão | D |
| RF-34 | Detectar contradições entre respostas e documentos (ex.: RTO diferente no BIA e no plano) | D |
| RF-35 | Chat de apoio que tira dúvidas sobre a norma e sobre a avaliação em andamento | D |
| RF-36 | O usuário pode contestar a sugestão da IA; prevalece a decisão humana, registrada | M |

### 5.5 Relatório de prontidão
| ID | Requisito | P |
|----|-----------|---|
| RF-40 | Maturidade geral e por cláusula, com gráfico radar e barras | M |
| RF-41 | Pontos fortes: itens com nível ≥ 4 e evidências sólidas | M |
| RF-42 | Lacunas: itens abaixo do nível 3, destacando os bloqueantes | M |
| RF-43 | Sugestões de melhoria priorizadas por impacto na certificação, esforço estimado e dependência entre ações (ex.: fazer o BIA antes do plano de continuidade) | M |
| RF-44 | Para cada sugestão: o que fazer, por quê (cláusula da norma), exemplo/modelo de documento e evidência que comprovaria | M |
| RF-45 | Parecer final de prontidão (faixa de maturidade, bloqueantes, nível de confiança) e estimativa do esforço restante | M |
| RF-46 | Resumo executivo de uma página para a diretoria | M |
| RF-47 | Exportar PDF; DOCX/XLSX depois | M / D |
| RF-48 | Checklist para o dia da auditoria externa: documentos a ter à mão, pessoas a preparar, perguntas prováveis do auditor | D |
| RF-49 | Modelos prontos (política de continuidade, modelo de BIA, relatório de exercício, ata de análise crítica) preenchíveis | D |

### 5.6 Plano de ação e evolução
| ID | Requisito | P |
|----|-----------|---|
| RF-50 | Converter sugestões em tarefas com responsável, prazo e status | M |
| RF-51 | Nova rodada de avaliação reaproveitando respostas anteriores | M |
| RF-52 | Comparativo entre rodadas e linha do tempo de maturidade | D |
| RF-53 | Alertas de prazos e lembretes por e-mail | D |
| RF-54 | Comparação anônima com empresas do mesmo setor e porte (benchmark) | F |

### 5.7 Provedor de IA intercambiável
| ID | Requisito | P |
|----|-----------|---|
| RF-60 | Interface única `LLMProvider` (`complete`, `embed`) com adaptadores para nuvem (Anthropic, OpenAI) e local (Ollama) | M |
| RF-61 | Troca de provedor e modelo por **configuração** (variáveis de ambiente), sem alterar código | M |
| RF-62 | Saída estruturada em JSON validada por esquema, com nova tentativa em caso de falha | M |
| RF-63 | Registro por chamada: provedor, modelo, versão do prompt, tokens, latência e custo | M |
| RF-64 | Opção por empresa de usar apenas modelo local | D |
| RF-65 | Fallback automático entre provedores | D |
| RF-66 | Rodar a mesma avaliação com dois modelos e comparar (teste de qualidade) | F |

### 5.8 Plataforma
| ID | Requisito | P |
|----|-----------|---|
| RF-70 | Trilha de auditoria: quem respondeu, alterou, anexou, exportou e quando | M |
| RF-71 | Painel do administrador da plataforma (empresas, uso, custo de IA) | D |
| RF-72 | API REST documentada (OpenAPI) | D |

### 5.9 Auditoria técnica (código e infraestrutura)
Módulo posterior, reaproveitando `architecture.md` (SAST, segredos, SCA, IaC). Seus achados alimentariam controles da ISO 27001. **Fora do MVP.** | F |

## 6. Regras de negócio

- **RN-01:** A IA **sugere**; o nível final é decidido pela empresa. Quando difere do sugerido pela IA, a divergência e a justificativa aparecem no relatório.
- **RN-02:** Todo apontamento da IA cita o trecho da evidência ou diz que não há evidência.
- **RN-03:** Nível ≥ 3 declarado sem evidência conta como **nível 2 para fins de pontuação** e reduz a confiança. (Valor declarado e valor efetivo são exibidos separadamente.)
- **RN-04:** A classificação "pronta para auditoria externa" exige: maturidade geral ≥ 3,5, nenhum item bloqueante abaixo de 3 e ao menos um ciclo de auditoria interna e de análise crítica pela direção comprovado.
- **RN-05:** O relatório sempre traz o aviso de que é um diagnóstico preparatório e não substitui a auditoria de certificação.
- **RN-06:** Relatório emitido é imutável; novas respostas geram nova versão.
- **RN-07:** Sugestões são ordenadas por: bloqueante primeiro, depois impacto na nota, depois menor esforço.
- **RN-08:** Evidências de uma empresa jamais são usadas para outra nem para treinar modelos.

## 7. Requisitos não funcionais

| ID | Categoria | Requisito |
|----|-----------|-----------|
| RNF-01 | Segurança | Isolamento por empresa (`tenant_id` obrigatório + row-level security no PostgreSQL) |
| RNF-02 | Segurança | TLS em trânsito; criptografia em repouso para banco e arquivos |
| RNF-03 | Segurança | Segredos fora do código e dos logs (variáveis, Docker secrets) |
| RNF-04 | Segurança | Arquivos enviados validados por tipo e tamanho, varridos por antivírus (ClamAV) e processados em worker isolado |
| RNF-05 | Segurança | Proteção contra prompt injection: o conteúdo dos documentos é dado, nunca instrução; saída limitada ao esquema |
| RNF-06 | Segurança | Senhas com hash forte (argon2/bcrypt), limite de tentativas, MFA |
| RNF-07 | Privacidade | LGPD: base legal, política de privacidade, retenção configurável, exportação e exclusão de dados, contrato de operador |
| RNF-08 | Desempenho | Análise de IA assíncrona; relatório gerado em até 2 min; telas respondem em até 2 s |
| RNF-09 | Disponibilidade | Meta de 99,5% no MVP; backup diário do banco e dos arquivos com teste de restauração |
| RNF-10 | Qualidade da IA | Conjunto de referência rotulado por especialista; meta de ≥ 80% de concordância dentro de ±1 nível |
| RNF-11 | Observabilidade | Logs estruturados, métricas e alertas (fila, erros de IA, custo) |
| RNF-12 | Usabilidade | Interface em português, linguagem simples, responsiva, acessível (WCAG AA) |
| RNF-13 | Custo | Limite de gasto de IA por empresa e por avaliação, com aviso |
| RNF-14 | Portabilidade | Tudo em contêineres; sem dependência exclusiva de fornecedor de nuvem |

## 8. Arquitetura em contêineres

```
                    ┌────────────────────────────┐
 Navegador ─HTTPS─► │ proxy (Caddy/Traefik) TLS  │
                    └──────┬──────────────┬──────┘
                           ▼              ▼
                    ┌──────────┐   ┌─────────────┐
                    │ web      │   │ api         │
                    │ React/TS │   │ FastAPI     │
                    └──────────┘   └──┬───┬───┬──┘
                                      │   │   │
                         ┌────────────┘   │   └─────────────┐
                         ▼                ▼                 ▼
                  ┌────────────┐   ┌────────────┐    ┌─────────────┐
                  │ postgres   │   │ redis      │    │ minio (S3)  │
                  │ + pgvector │   │ fila/cache │    │ evidências  │
                  └────────────┘   └─────┬──────┘    └─────────────┘
                                         ▼
                                  ┌─────────────┐   ┌─────────┐
                                  │ worker      │──►│ clamav  │
                                  │ extração,   │   └─────────┘
                                  │ OCR, IA,    │
                                  │ relatórios  │
                                  └──────┬──────┘
                       ┌─────────────────┴─────────────────┐
                       ▼                                   ▼
              API de nuvem (Anthropic/OpenAI)      ollama (contêiner opcional)
```

| Contêiner | Função |
|-----------|--------|
| `proxy` | Entrada HTTPS, certificados automáticos |
| `web` | Front-end React + TypeScript |
| `api` | FastAPI: autenticação, regras, endpoints |
| `worker` | Tarefas assíncronas: extração de texto, OCR, análise por IA, geração de PDF |
| `postgres` | Dados e vetores (pgvector) |
| `redis` | Fila e cache |
| `minio` | Armazenamento de arquivos compatível com S3 |
| `clamav` | Varredura de uploads |
| `ollama` | Modelo local (perfil opcional do compose) |

- `docker-compose.yml` com perfis: `dev`, `prod` e `local-llm`.
- Configuração só por variáveis de ambiente: `LLM_PROVIDER=anthropic|openai|ollama`, `LLM_MODEL=...`, `EMBED_PROVIDER=...`.
- Imagens versionadas, executando como usuário não-root, com health checks.
- Migrações de banco automatizadas (Alembic).
- Pipeline de CI: testes, análise estática, varredura de imagens (Trivy), construção das imagens.
- Evolução futura: Kubernetes, se a escala exigir.

**Fluxo de análise de uma resposta (RAG):**
1. Buscar os trechos mais relevantes das evidências para a pergunta.
2. Montar o prompt com pergunta, critério da norma, nível declarado e trechos numerados.
3. LLM devolve JSON: `nivel_sugerido`, `justificativa`, `citacoes[]`, `confianca`, `evidencias_faltantes[]`.
4. Validar o esquema e confirmar que as citações existem nos trechos enviados.
5. Gravar a sugestão para a empresa aceitar ou contestar.

**Geração do relatório:** os números (notas, faixas, bloqueantes, prioridade) são calculados por **código determinístico**. A IA só redige textos (resumo, explicações, sugestões) a partir desses números, para que a pontuação seja reproduzível e auditável.

## 9. Modelo de dados (principais entidades)

`empresa`, `usuario`, `norma`, `catalogo_versao`, `item_catalogo`, `avaliacao`, `designacao`, `resposta` (nível declarado, nível efetivo, comentário), `evidencia`, `trecho_evidencia` (vetor), `analise_ia` (nível sugerido, justificativa, modelo, versão do prompt), `relatorio`, `sugestao_melhoria`, `tarefa`, `chamada_llm`, `evento_auditoria`.

## 10. Roadmap

**MVP — ISO 22301, ponta a ponta:** RF-01 a 03, 10 a 12, 20 a 24, 30 a 32, 36, 40 a 47, 50, 51, 60 a 63, 70. Requisitos não funcionais de segurança (RNF-01 a 06) e LGPD (RNF-07).
Entrega: cadastro → questionário → evidências → análise de IA → relatório de prontidão com plano de melhorias → nova rodada.

**Fase 2:** RF-25, 33, 35, 48, 49, 52, 53, 64, 65, SSO e cobrança.

**Fase 3:** outras normas, benchmark, módulo técnico (RF-13, 54, 5.9).

## 11. Riscos

| Risco | Mitigação |
|-------|-----------|
| Empresa entender o relatório como garantia de certificação | RN-05, aviso visível, linguagem de "prontidão" |
| Respondentes inflam as notas | RN-03, análise de evidências, nível de confiança |
| IA inventa ou erra | RN-02, checagem de citações, nota calculada por código, decisão final humana |
| Vazamento de documentos sensíveis | Isolamento por empresa, criptografia, opção de modelo local, contratos com provedores de IA |
| Modelo local com qualidade inferior | Medir com o conjunto de referência (RNF-10); nuvem como padrão |
| Prompt injection via documentos | RNF-05 |
| Upload malicioso | RNF-04 |
| Custo de IA | RF-63, RNF-13 |
| Catálogo desatualizado quando a norma mudar | Versionamento (RF-12) e edição sem código (RF-14) |

## 12. Questões em aberto

1. **Escala de maturidade:** os 6 níveis e as faixas da seção 4 servem, ou há um modelo de maturidade que o TCC/professor exige (ex.: CMMI)?
2. **Quantidade de perguntas:** usar as 90 do checklist ou uma versão enxuta para autoavaliação (muitas empresas pequenas desistem de questionários longos)?
3. **Quem valida as sugestões de melhoria?** Um especialista em continuidade deve revisar o catálogo de recomendações e os modelos de documentos.
4. **Modelo de negócio:** assinatura mensal, avaliação avulsa, ou gratuito no TCC?
5. **Hospedagem inicial:** local (docker compose na própria máquina), VPS ou nuvem?
6. **Escopo do TCC:** o MVP inteiro, ou só o fluxo questionário → relatório?
