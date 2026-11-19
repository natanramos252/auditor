# Análise dos critérios de avaliação da ferramenta x ABNT NBR ISO 22301:2020

Data: 06/11/2026. Base: catálogo de 90 perguntas, prompt da IA, regras de nota e a rodada 2 do PCN do grupo (avaliação 11).

## 1. O que a análise encontrou

| # | Problema | Efeito na resposta da IA | Correção feita |
|---|----------|--------------------------|----------------|
| 1 | A IA recebia só a pergunta e dava um nível "no olho". A norma, porém, lista requisitos por alínea (a, b, c…). | Respostas variavam entre rodadas e entre modelos; não dava para saber *o que* faltava | Cada pergunta ganhou **critérios** tirados da norma (1 a 11 por pergunta, 243 no total, após a cobertura das alíneas da v2). A IA avalia critério a critério e o **nível é calculado por código** |
| 2 | A mesma exigência de "execução" valia para tudo. A norma distingue o que deve **existir** (política, escopo, BIA, plano) do que deve ser **executado e registrado** (exercícios, auditoria, análise crítica, ação corretiva, competência). | Planos bem escritos eram rebaixados por falta de registro que a norma nem pede; planos sem execução recebiam "Atende" | Cada pergunta ganhou o tipo **documento** (55) ou **registro** (35). A trava de execução só vale para "registro" |
| 3 | Perguntas compostas valiam como uma só (ex.: 83 tem 7 entradas da análise crítica, 53 tem 8 tipos de recurso, 61 tem 8 elementos do plano). | Um "Parcial" escondia o que estava faltando | Os critérios aparecem na tela com ✓ atendido, ◐ parcial e ✕ ausente |
| 4 | 10 perguntas estavam sem cláusula (31, 33, 36 a 38, 86 a 90) e nenhuma tinha a alínea. | Impossível rastrear a pergunta até a norma | Todas passaram a ter a referência (ex.: 8.4.4.3 a–h). Aparece na tela |
| 5 | A aprovação do documento (7.5.2 c) não era conferida. | Documento com "data de aprovação: a preencher" não era penalizado | Virou critério nas perguntas de política (18) e de informação documentada (35) |
| 6 | Requisitos bloqueantes incompletos: faltavam três que costumam gerar não conformidade maior na certificação. | Empresa "pronta" sem processo legal, estratégias ou estrutura de resposta | Entraram **6** (processo legal, 4.2.2), **50** (estratégias, 8.3.1) e **56** (estrutura de resposta, 8.4.2.1). Total: 15 |
| 7 | Siglas: o PCN usa MTD, a norma usa MTPD. | Item 45 saía "Não atende" por causa do nome | Prompt informa que são equivalentes |
| 8 | Citação sem trecho verificável contava como "atendido". | Alucinação virava nota | Critério sem citação literal confirmada cai para "parcial" |

## 2. Perguntas que vão além ou ficam fora do texto da norma

- **55** (RPO/RTO de TI, backup e restauração): a ISO 22301 não fala de RPO nem de backup; isso vem da ISO/IEC 27031. Mantida, mas é requisito do auditor da disciplina, não da norma.
- **38** (planos fora do site): vem de 8.4.4.3 e 7.5.3, mas o "fora do site" é boa prática.
- **Sem pergunta própria:** 8.4.1 (generalidades da estrutura de resposta, coberta pelas 56 a 63) e 10.1.1 (determinar oportunidades de melhoria, coberta pela 90).

## 3. Como a nota é decidida agora

1. A IA diz, para cada critério da norma, `atendido`, `parcial` ou `ausente`, e cita o trecho.
2. O código verifica se a citação existe literalmente no documento.
3. Cobertura = (atendidos + 0,5 × parciais) ÷ número de critérios.
4. Cobertura ≥ 85% → **Atende**; > 0 → **Atende parcialmente**; 0 → sem sugestão.
5. Se o tipo é **registro**, "Atende" exige trecho com data passada, "foi realizado", resultado ou ata. Senão vira "Parcial".
6. O profissional continua sendo quem valida.

## 4. Ligação com o Claude para validar cada evidência

O sistema não consegue chamar o Claude Code sozinho (ele só roda numa sessão). Por isso existem três caminhos:

| Caminho | Como | Quando usar |
|---------|------|-------------|
| **Automático** | `LLM_PROVIDER=anthropic` e `ANTHROPIC_API_KEY` no `.env`. A análise de todos os itens já usa o Claude | Uso normal, com custo por chamada |
| **Revisão por sessão do Claude Code** (implementado) | O revisor lê a fila, lê os documentos e envia o parecer pela API | Segunda opinião sobre o resultado de qualquer IA, sem chave de API |
| **Servidor MCP** (não feito) | Empacotaria os endpoints abaixo como ferramentas do Claude Code | Se quiserem uma ligação permanente |

### Endpoints do caminho 2

| Endpoint | Função |
|----------|--------|
| `GET /api/assessments/{id}/review/queue` | Perguntas com critérios da norma, tipo de evidência, resultado da IA e evidências citadas. Aceita `?only=unreviewed` ou `?only=suggested` |
| `GET /api/assessments/{id}/review/documents/{doc}/text` | Texto completo do documento, dividido em trechos |
| `POST /api/assessments/{id}/review` | Parecer por critério (`atendido`, `parcial`, `ausente`) com citações literais e veredito por evidência (`comprova`, `parcial`, `nao_comprova`) |
| `POST /api/assessments/{id}/answers/{n}/adopt-review` | Copia o parecer para a resposta (nível, evidências, lacunas). **Não valida** |

Salvaguardas:
- Cada citação do revisor é procurada no texto; se não existe literalmente, é **rejeitada** e listada na resposta.
- O nível do parecer é calculado pelo mesmo código da análise automática, com a mesma trava de "registro".
- O parecer fica separado da sugestão da IA. Na tela aparece o bloco "Parecer do Claude", com os critérios e cada evidência marcada como *comprova*, *comprova em parte* ou *não comprova*, e o botão "Adotar este parecer".

## 5. Resultado no PCN do grupo (avaliação 11), as 90 perguntas

| | IA automática (freellmapi, rodada 2) | Parecer do Claude |
|---|---|---|
| Atende | 1 | **19** |
| Atende parcialmente | 74 | 56 |
| Não atende | 1 | 0 |
| Sem sugestão | 14 | 15 |

- 81 evidências citadas, **nenhuma rejeitada** (todas existem literalmente no PCN ou nos anexos).
- Divergências entre IA e Claude: 37 perguntas.
- Os 19 "Atende" são de **documento**, todos da cláusula 8 e afins: BIA (42, 45, 46), riscos (48), estratégias (50, 51, 53), estratégias e decisão (52), estrutura de resposta (58), plano (61, 62, 64), acesso e proteção dos planos (36, 38) e alguns de apoio (10, 30, 34, 78, 79).
- Nenhuma pergunta de **registro** ficou em "Atende", porque o PCN ainda não tem exercício, auditoria, ata nem ação corretiva realizados.
- Bloqueantes (15): 6 em "Atende" (42, 45, 46, 48, 50, 61); 8 em "Atende parcialmente" (6, 8, 25, 56, 65, 76, 82, 86); a política (18) ficou sem sugestão, por não haver política de continuidade nos documentos.

### O que o parecer apontou de concreto para fechar

1. Preencher a data de aprovação e as aprovações do histórico (itens 35, 49).
2. Escrever o Plano de Comunicação de Crise (59, 34) e o procedimento de evacuação ou anexar o PE (61).
3. Preencher o Anexo A com titulares, substitutos e contatos (57).
4. Fazer um teste de mesa e emitir o relatório (65, 66, 67, 68, 60).
5. Documentos do SGCN que o PCN não substitui: política (18 a 20), escopo (8 a 11), contexto e partes interessadas (1 a 5), objetivos (25 a 27), análise crítica (82 a 85) e não conformidades (86 a 90).

## 6. Limites desta análise

- Os critérios são **paráfrase minha** dos requisitos da norma, não o texto dela. Convém conferir com a norma antes de entregar ao professor.
- A cobertura de 85% e os pesos são escolhas de projeto. A norma não define percentuais.
- O parecer do Claude é uma segunda opinião de uma só revisão. Os itens 78 e 79 (auditoria interna) saíram "Atende" por o PCN já definir critérios e independência; um auditor pode discordar.
- O caminho automático com a API da Anthropic não foi executado, só o provedor falso nos testes.
- Testes automatizados: 13 passam. O novo fluxo de critérios foi testado com provedor simulado; com o freellmapi a análise nova (por critério) ainda não foi rodada.

## 7. Atualização de 09/11/2026 (v2: cobertura das alíneas)

Os 23 enunciados reescritos e os 243 critérios da pasta `v2_cobertura_alineas` já estavam aplicados nos arquivos do app; o Docker foi reconstruído e agora serve o catálogo novo. Como 20 perguntas ganharam critérios (6, 13, 17, 23, 25, 37, 51, 52, 56, 57, 58, 59, 62, 66, 67, 70, 76, 83, 88, 90), o parecer do Claude nelas foi refeito. A pergunta 56 passou de "Atende" para "Atende parcialmente" (o aviso às partes interessadas depende do PCC, que não está escrito) e a 52 de "Parcial" para "Atende". Totais do parecer: 19 Atende, 56 Parcial, 15 sem sugestão.
