# Perguntas de Auditoria — ABNT NBR ISO 22301:2020 (SGCN)

Cada pergunta indica a cláusula da norma e a evidência esperada (Ev.).
Resultado por item: **C** (conforme) · **NC** (não conformidade) · **OM** (oportunidade de melhoria) · **NA**.

---

## O que são "evidências" (explicação simples)

Em auditoria, **evidência é a prova de que algo foi feito de verdade**, e não apenas dito. Se alguém responde "sim, nós fazemos backup todo dia", o auditor pergunta: "Pode me mostrar?". O que for mostrado é a evidência.

Uma boa regra: **"Se não está registrado, para o auditor não aconteceu."**

### Os quatro tipos de evidência

| Tipo | O que é | Exemplos |
|------|---------|----------|
| **Documento** | Algo escrito que define como as coisas devem ser feitas | Política de continuidade, plano de contingência, procedimentos, organograma, contratos com fornecedores |
| **Registro** | Prova de que uma atividade ocorreu | Ata de reunião, lista de presença de treinamento, relatório de teste, log do sistema, e-mail de aprovação, ordem de serviço |
| **Observação** | O que o auditor vê com os próprios olhos | Extintores e saídas de emergência, sala do servidor, gerador funcionando, plano impresso em local acessível |
| **Entrevista** | O que as pessoas respondem | Um funcionário que descreve o que faria em caso de incêndio ou de queda do sistema |

### Exemplos práticos

| Pergunta do auditor | Resposta fraca (sem evidência) | Evidência boa |
|---------------------|-------------------------------|---------------|
| A empresa tem política de continuidade? | "Sim, a diretoria sabe disso." | PDF da política, assinado pela diretoria, com data e versão |
| Os funcionários foram treinados? | "Todo mundo já sabe." | Lista de presença, certificados, conteúdo do treinamento |
| O backup funciona? | "Rodamos todo dia." | Log do backup e relatório de um teste de restauração com sucesso |
| A empresa testa o plano? | "Fizemos um simulado ano passado." | Relatório do simulado com data, participantes, falhas e ações corrigidas |
| A diretoria acompanha o assunto? | "Conversamos às vezes." | Ata da reunião de análise crítica, com decisões e responsáveis |

### Como avaliar se a evidência é boa
- **Está datada?** Sem data, não dá para saber se está atual.
- **Tem responsável?** Alguém aprovou, assinou ou executou.
- **É recente?** Um documento de 5 anos atrás, nunca revisado, é suspeito.
- **É verdadeira e consistente?** O que o documento diz bate com o que as pessoas fazem?
- **O auditor consegue verificar sozinho?** O ideal é ver o registro original e não só ouvir uma explicação.
- **Uma só prova basta?** Quanto mais importante o ponto, mais de um tipo de evidência deve confirmar (documento + registro + entrevista).

### Como o auditor usa isso
1. Lê a pergunta e a evidência esperada (indicada como "Ev." em cada item).
2. Pede para ver essa evidência ou algo equivalente.
3. Confere se ela realmente comprova o que a norma exige.
4. Anota o resultado: **C** (conforme), **NC** (não conformidade, sem evidência ou evidência contraria a norma), **OM** (oportunidade de melhoria) ou **NA** (não se aplica).

Observação: a lista "Ev." em cada pergunta é uma **sugestão**. Evidências equivalentes podem servir, desde que provem a mesma coisa.

---

## 4. Contexto da organização

**4.1 Contexto**
1. Foram determinadas as questões internas e externas que afetam a capacidade de o SGCN atingir seus resultados? (Ev.: análise de contexto, SWOT/PESTEL)
2. Essa análise considera objetivos, produtos/serviços e o apetite a risco da organização?
3. Com que frequência o contexto é revisado?

**4.2 Partes interessadas e requisitos legais**
4. As partes interessadas pertinentes ao SGCN estão identificadas (clientes, reguladores, fornecedores, funcionários)? (Ev.: matriz de partes interessadas)
5. Seus requisitos estão documentados?
6. Existe processo para identificar, acessar e avaliar requisitos legais e regulamentares sobre continuidade (ex.: LGPD, regulações setoriais, contratos/SLAs)?
7. O registro legal está documentado e atualizado?

**4.3 Escopo**
8. O escopo do SGCN está documentado e disponível?
9. O escopo considera localização, tamanho, natureza e complexidade da organização?
10. Os produtos e serviços incluídos estão identificados?
11. Há exclusões? Estão justificadas e não afetam a capacidade de continuidade determinada pelo BIA e pela avaliação de riscos?

**4.4 SGCN**
12. Os processos do SGCN e suas interações estão estabelecidos, implementados e mantidos?

---

## 5. Liderança

**5.1 Liderança e comprometimento**
13. A Alta Direção estabeleceu política e objetivos alinhados à estratégia? (Ev.: atas, aprovações)
14. Os requisitos do SGCN estão integrados aos processos de negócio?
15. Os recursos necessários (orçamento, pessoas, tecnologia) são fornecidos? Como a Direção comprova?
16. A Direção comunica a importância da continuidade de negócios? (Ev.: comunicados, treinamentos)
17. A Direção apoia os gestores de área no seu papel no SGCN?

**5.2 Política**
18. Existe política de continuidade aprovada, adequada ao propósito da organização?
19. A política traz estrutura para objetivos, compromisso com requisitos aplicáveis e com a melhoria contínua?
20. É comunicada internamente e disponibilizada às partes interessadas quando apropriado?

**5.3 Papéis e responsabilidades**
21. Papéis, responsabilidades e autoridades do SGCN estão atribuídos e comunicados?
22. Há responsável por assegurar a conformidade do SGCN e por reportar seu desempenho à Direção?

---

## 6. Planejamento

**6.1 Riscos e oportunidades do SGCN**
23. Foram determinados riscos e oportunidades que afetam a eficácia do SGCN?
24. Há plano de ação, integração aos processos e avaliação de eficácia dessas ações?

**6.2 Objetivos**
25. Os objetivos de continuidade estão estabelecidos nas funções e níveis pertinentes, coerentes com a política e mensuráveis?
26. São monitorados, comunicados e atualizados? Há informação documentada?
27. Para cada objetivo: o que será feito, recursos, responsável, prazo e forma de avaliação?

**6.3 Mudanças**
28. Mudanças no SGCN são planejadas considerando finalidade, consequências, integridade do sistema, recursos e responsabilidades? (Ev.: registros de mudança)

---

## 7. Apoio

29. (7.1) Os recursos para estabelecer, manter e melhorar o SGCN foram determinados e providos?
30. (7.2) As competências necessárias das pessoas com impacto na continuidade estão definidas?
31. As pessoas são competentes por educação, treinamento ou experiência? Há registros? (Ev.: certificados, matriz de competências)
32. (7.3) Os colaboradores conhecem a política de continuidade e seu papel antes, durante e depois de uma disrupção? (Ev.: entrevista com amostra)
33. Sabem a implicação de não cumprir os requisitos do SGCN?
34. (7.4) Estão definidos o que, quando, com quem, como e quem comunica, interna e externamente?
35. (7.5) A informação documentada requerida pela norma e pela organização existe, com identificação, formato e aprovação?
36. Está disponível onde e quando necessário e protegida contra perda de confidencialidade e integridade?
37. Há controle de versão, distribuição, acesso, armazenamento, retenção e descarte?
38. Os planos de continuidade estão acessíveis durante uma disrupção (cópia offline, fora do site principal)?

---

## 8. Operação

**8.1 Planejamento e controle operacional**
39. Existem critérios para os processos do SGCN e controle conforme esses critérios?
40. Mudanças planejadas são controladas e as não intencionais são analisadas, com mitigação?
41. Processos terceirizados e a cadeia de suprimentos são controlados?

**8.2 BIA e avaliação de riscos**
42. Existe processo sistemático de BIA? Foi executado e documentado?
43. Os tipos e critérios de impacto foram definidos para o contexto da organização?
44. As atividades que sustentam produtos e serviços foram identificadas?
45. O MTPD (período máximo tolerável de disrupção) foi determinado para cada atividade?
46. O RTO foi definido dentro do MTPD, com capacidade mínima aceitável?
47. As atividades priorizadas, seus recursos e suas dependências (fornecedores, parceiros, interdependências) estão identificados?
48. Existe processo de avaliação de riscos de disrupção (alinhado à ISO 31000)? Riscos são identificados, analisados, avaliados e priorizados para tratamento?
49. BIA e avaliação de riscos são revisados em intervalos planejados e após mudanças significativas?

**8.3 Estratégias e soluções**
50. Há estratégias que cobrem antes, durante e depois da disrupção?
51. As estratégias atendem ao RTO, protegem atividades priorizadas, reduzem probabilidade e duração e limitam o impacto?
52. A seleção considerou apetite a risco e custo-benefício? (Ev.: registro de decisão)
53. Os requisitos de recursos foram determinados para: pessoas, informação/dados, infraestrutura, equipamentos, TIC, transporte/logística, finanças e fornecedores?
54. As soluções estão implementadas e mantidas (site alternativo, backup, redundância, contratos de contingência)?
55. **TI:** os RPO/RTO dos sistemas críticos são suportados pelos backups e pela infraestrutura de recuperação? Já foram restaurados com sucesso?

**8.4 Planos e procedimentos**
56. Existe estrutura de resposta com equipes responsáveis por responder a disrupções?
57. Papéis, responsabilidades e relacionamento entre equipes estão definidos? Há titulares e suplentes?
58. As equipes sabem avaliar a natureza e extensão da disrupção, decidir a ativação, priorizar (vida em primeiro lugar), monitorar e se comunicar com partes interessadas e mídia?
59. Existem procedimentos de aviso e comunicação: interna/externa, uso de alertas de autoridades, meios de comunicação alternativos, registro de incidente, ações e decisões?
60. Esses procedimentos são exercitados no programa de exercícios?
61. Os planos de continuidade (PCN) estão documentados e contêm propósito, escopo, objetivos, papéis, critérios de ativação, ações, interdependências, recursos, requisitos de relatório e evacuação?
62. Os planos definem limites/gatilhos de ativação e como manter a entrega de produtos e serviços na capacidade acordada?
63. Tratam o bem-estar das pessoas e a prevenção de perdas adicionais?
64. Existem procedimentos de recuperação para voltar das medidas temporárias à operação normal?

**8.5 Programa de exercícios**
65. Há programa de exercícios e testes planejado? Qual a frequência?
66. Os exercícios têm cenários realistas, escopo e objetivos definidos, e são coerentes com os objetivos do SGCN?
67. Há relatório formal pós-exercício com resultados, recomendações e ações de melhoria? (Ev.: relatórios dos últimos exercícios)
68. As ações dos exercícios foram implementadas? Há evidência de fechamento?
69. Foram realizados exercícios após mudanças significativas?

**8.6 Avaliação da capacidade de continuidade**
70. BIA, riscos, estratégias, planos e procedimentos são avaliados quanto à adequação e eficácia?
71. A capacidade de continuidade de parceiros e fornecedores críticos é avaliada?
72. Avalia-se a conformidade com requisitos legais, boas práticas do setor e a própria política?
73. Após incidentes reais ou ativações houve análise pós-incidente e atualização da documentação?

---

## 9. Avaliação de desempenho

**9.1 Monitoramento e medição**
74. O que deve ser monitorado, por quais métodos, quando e por quem está definido? (Ev.: indicadores, painéis)
75. Os resultados são retidos como evidência e o desempenho do SGCN é avaliado?

**9.2 Auditoria interna**
76. Há programa de auditoria interna com frequência, métodos, responsabilidades e relatórios?
77. O programa considera a importância dos processos e os resultados de auditorias anteriores?
78. Critérios e escopo de cada auditoria estão definidos?
79. Os auditores são objetivos e imparciais (não auditam o próprio trabalho)?
80. Resultados foram reportados aos gestores responsáveis, com registros retidos?
81. As ações corretivas foram executadas sem atraso injustificado e verificadas?

**9.3 Análise crítica pela direção**
82. A Direção analisa o SGCN em intervalos planejados? (Ev.: atas)
83. As entradas incluem: ações anteriores, mudanças de contexto, desempenho e tendências (NC, medições, auditorias), feedback das partes interessadas, BIA/riscos, resultados da avaliação de 8.6, riscos não tratados, lições de quase-acidentes e disrupções, oportunidades de melhoria?
84. As saídas incluem decisões sobre melhoria, mudanças de escopo, atualização de BIA, riscos, estratégias e planos, e como a eficácia dos controles será medida?
85. Os resultados foram comunicados às partes interessadas e as ações executadas?

---

## 10. Melhoria

86. Ao ocorrer uma não conformidade, a organização reage, controla, corrige e lida com as consequências?
87. A causa raiz é determinada e se verifica se NCs semelhantes existem ou podem ocorrer?
88. A eficácia das ações corretivas é analisada criticamente e o SGCN é alterado quando necessário?
89. Há registros da natureza das NCs, das ações e dos resultados?
90. Há evidência de melhoria contínua da adequação, suficiência e eficácia do SGCN com base em medidas qualitativas e quantitativas?

---

## Perguntas rápidas para entrevista com a Alta Direção
- Quais são as atividades mais críticas da organização e quanto tempo de parada é tolerável?
- Quando foi o último exercício de continuidade e o que mudou depois dele?
- Qual orçamento foi aprovado para o SGCN neste ano?
- Quem assume a decisão de ativar o plano em uma crise?

## Perguntas rápidas para entrevista com operacionais
- Em caso de incêndio, queda de energia ou ataque de ransomware, o que você faz? Onde está o plano?
- Quem é seu suplente se você estiver ausente?
- Você já participou de algum exercício? Qual?
