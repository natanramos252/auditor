"""Gera app/data/criteria.json: para cada pergunta, a referência na norma, o tipo de evidência exigido e os
critérios (paráfrase curta dos requisitos da ISO 22301:2020 que a pergunta verifica).

kind = "documento": a norma pede que exista/esteja definido e aprovado (política, escopo, BIA, planos).
kind = "registro":  a norma pede que seja executado e que haja informação documentada como evidência
                    (exercícios, auditoria interna, análise crítica, ações corretivas, competência).
Uso: python tools/build_criteria.py ../../perguntas_x_norma_ISO22301.md app/data/criteria.json
"""
import json
import re
import sys

C = {
1: ["Questões externas relevantes identificadas", "Questões internas relevantes identificadas", "Ligadas ao propósito e aos resultados pretendidos do SGCN"],
2: ["Considera objetivos gerais, produtos e serviços", "Considera o apetite a risco da organização"],
3: ["Contexto revisado com periodicidade ou após mudanças, com registro"],
4: ["Partes interessadas pertinentes ao SGCN identificadas"],
5: ["Requisitos de cada parte interessada documentados"],
6: ["Processo definido para identificar e avaliar requisitos legais e regulamentares", "Requisitos aplicáveis listados (leis, regulações, contratos)"],
7: ["Registro legal documentado", "Mantido atualizado (data de revisão)"],
8: ["Escopo documentado e disponível", "Considera contexto, partes interessadas e obrigações da organização"],
9: ["Partes da organização incluídas, considerando localização, porte e complexidade"],
10: ["Produtos e serviços incluídos identificados"],
11: ["Exclusões documentadas e justificadas", "Exclusões não afetam a capacidade de continuidade (BIA, riscos e requisitos legais)"],
12: ["Processos do SGCN e suas interações definidos", "SGCN estabelecido, implementado, mantido e melhorado"],
13: ["Política e objetivos estabelecidos e alinhados à estratégia", "Alta direção demonstra liderança nas decisões e no apoio"],
14: ["Requisitos do SGCN integrados aos processos de negócio"],
15: ["Recursos necessários (orçamento, pessoas, ferramentas) disponibilizados pela direção"],
16: ["Direção comunica a importância da gestão de continuidade eficaz"],
17: ["Direção dirige e apoia pessoas e gestores a contribuírem com o SGCN"],
18: ["Política de continuidade existe", "Adequada ao propósito da organização", "Aprovada pela Alta Direção, com data e versão"],
19: ["Fornece estrutura para os objetivos de continuidade", "Compromisso de satisfazer requisitos aplicáveis", "Compromisso com a melhoria contínua"],
20: ["Política documentada e disponível", "Comunicada na organização", "Disponível às partes interessadas, quando apropriado"],
21: ["Papéis, responsabilidades e autoridades atribuídos", "Comunicados na organização"],
22: ["Responsável por assegurar a conformidade do SGCN com a norma", "Responsável por reportar o desempenho à Alta Direção"],
23: ["Riscos e oportunidades que afetam a eficácia do SGCN determinados"],
24: ["Ações para abordar riscos e oportunidades planejadas", "Como integrá-las ao SGCN", "Como avaliar a eficácia dessas ações"],
25: ["Objetivos definidos nas funções e níveis pertinentes", "Coerentes com a política e mensuráveis"],
26: ["Objetivos monitorados", "Comunicados e atualizados", "Informação documentada retida"],
27: ["O que será feito", "Recursos necessários", "Responsável", "Prazo", "Como os resultados serão avaliados"],
28: ["Mudanças no SGCN planejadas", "Consideram consequências, integridade do sistema, recursos e responsabilidades"],
29: ["Recursos para o SGCN determinados", "Recursos efetivamente fornecidos"],
30: ["Competências necessárias das pessoas determinadas"],
31: ["Pessoas competentes por educação, treinamento ou experiência", "Ações para adquirir competência quando necessário", "Registros como evidência de competência"],
32: ["Pessoas conhecem a política de continuidade", "Conhecem sua contribuição para a eficácia do SGCN", "Conhecem seu papel antes, durante e depois de disrupções"],
33: ["Pessoas cientes das implicações de não cumprir os requisitos do SGCN"],
34: ["O que comunicar", "Quando", "Com quem", "Como", "Quem comunica"],
35: ["Informação documentada exigida existe", "Identificação (título, data, autor ou número)", "Formato e meio definidos", "Análise crítica e aprovação"],
36: ["Disponível onde e quando necessário", "Protegida contra perda de confidencialidade, uso impróprio e perda de integridade"],
37: ["Distribuição, acesso e uso", "Armazenamento e legibilidade", "Controle de alterações e versão", "Retenção e descarte"],
38: ["Planos acessíveis durante uma disrupção (cópia fora do site principal, digital e impressa)"],
39: ["Critérios estabelecidos para os processos", "Controle conforme os critérios", "Informação documentada de que os processos foram conduzidos como planejado"],
40: ["Mudanças planejadas são controladas", "Mudanças não intencionais analisadas e efeitos adversos mitigados"],
41: ["Processos terceirizados controlados", "Cadeia de suprimentos controlada"],
42: ["Processo sistemático de BIA definido", "BIA executado e documentado"],
43: ["Tipos de impacto definidos para o contexto", "Critérios/escala de impacto definidos"],
44: ["Atividades que sustentam produtos e serviços identificadas", "Impactos avaliados ao longo do tempo"],
45: ["Período máximo tolerável de disrupção (MTPD/MTD) definido para as atividades"],
46: ["Objetivo de tempo de recuperação (RTO) definido, dentro do MTPD", "Capacidade mínima aceitável especificada"],
47: ["Atividades priorizadas identificadas", "Recursos necessários determinados", "Dependências e interdependências (fornecedores e parceiros) identificadas"],
48: ["Riscos de disrupção das atividades priorizadas identificados", "Riscos analisados e avaliados", "Definido quais riscos exigem tratamento"],
49: ["BIA e riscos revisados em intervalos planejados", "Revisados após mudanças significativas"],
50: ["Estratégias para antes, durante e depois da disrupção"],
51: ["Atendem ao RTO e à capacidade aceitável", "Protegem as atividades priorizadas", "Reduzem probabilidade, duração ou impacto da disrupção"],
52: ["Considera o apetite a risco", "Considera custo e benefício", "Decisão de seleção registrada"],
53: ["Pessoas", "Informações e dados", "Infraestrutura física", "Equipamentos", "Sistemas de TIC", "Transporte e logística", "Finanças", "Parceiros e fornecedores"],
54: ["Soluções de continuidade implementadas", "Mantidas e disponíveis para uso quando necessário"],
55: ["RPO e RTO dos sistemas críticos definidos", "Backup e infraestrutura de recuperação suportam esses valores", "Restauração testada com sucesso"],
56: ["Estrutura de resposta com equipes responsáveis definida"],
57: ["Papéis e relacionamento entre as equipes definidos", "Titulares e suplentes identificados"],
58: ["Avaliar natureza e impacto da disrupção", "Critério para iniciar a resposta formal", "Acionar a resposta adequada", "Prioridades definidas, com a vida em primeiro lugar", "Monitorar efeitos da disrupção", "Comunicar partes interessadas, autoridades e mídia"],
59: ["Comunicação interna e externa (o que, quando, com quem, como)", "Receber e responder a alertas de autoridades", "Meios de comunicação disponíveis durante o incidente", "Registro do incidente, ações e decisões"],
60: ["Procedimentos de aviso e comunicação exercitados em testes ou simulações"],
61: ["Propósito, escopo e objetivos", "Papéis e responsabilidades", "Ações para implementar as soluções", "Critérios de ativação", "Interdependências internas e externas", "Recursos necessários", "Requisitos de relatório", "Processo de evacuação"],
62: ["Limites predefinidos para ativar o plano", "Ações para continuar ou recuperar as atividades em prazos predeterminados", "Entrega de produtos e serviços na capacidade acordada"],
63: ["Bem-estar das pessoas", "Prevenção de perda adicional ou indisponibilidade", "Impacto no ambiente"],
64: ["Procedimentos documentados para restaurar e retornar das medidas temporárias à operação normal"],
65: ["Programa de exercícios e testes planejado, com frequência", "Exercícios efetivamente realizados"],
66: ["Cenários apropriados", "Escopo e objetivos claramente definidos", "Consistentes com os objetivos do SGCN"],
67: ["Relatório formal pós-exercício", "Resultados, recomendações e ações de melhoria"],
68: ["Ações de melhoria dos exercícios implementadas e concluídas"],
69: ["Exercícios em intervalos planejados", "Exercício após mudanças significativas"],
70: ["BIA, riscos, estratégias, planos e procedimentos avaliados quanto à adequação e eficácia", "Por revisões, exercícios, testes ou relatórios pós-incidente"],
71: ["Capacidade de continuidade de parceiros e fornecedores pertinentes avaliada"],
72: ["Conformidade com requisitos legais avaliada", "Conformidade com boas práticas, política e objetivos avaliada"],
73: ["Documentação e procedimentos atualizados em tempo hábil", "Atualização após incidente ou ativação"],
74: ["Definido o que, como, quando e por quem monitorar e medir", "Resultados analisados e avaliados"],
75: ["Desempenho e eficácia do SGCN avaliados", "Informação documentada retida como evidência dos resultados"],
76: ["Programa de auditoria interna com frequência, métodos e responsáveis", "Auditoria interna efetivamente realizada"],
77: ["Considera a importância dos processos e resultados de auditorias anteriores"],
78: ["Critérios e escopo definidos para cada auditoria"],
79: ["Auditores selecionados com objetividade e imparcialidade"],
80: ["Resultados relatados aos gestores pertinentes", "Informação documentada retida como evidência"],
81: ["Ações corretivas realizadas sem atraso injustificado", "Verificação das ações e reporte dos resultados"],
82: ["Análise crítica pela direção em intervalos planejados", "Análise crítica efetivamente realizada (ata)"],
83: ["Situação de ações de análises anteriores", "Mudanças em questões internas e externas", "Desempenho do SGCN e tendências (NCs, medições, auditorias)", "Feedback das partes interessadas", "BIA, riscos e resultados da avaliação da capacidade", "Lições de quase acidentes e disrupções", "Oportunidades de melhoria"],
84: ["Decisões sobre melhoria e mudanças no SGCN (escopo, BIA, riscos, estratégias, planos)", "Como a eficácia dos controles será medida"],
85: ["Informação documentada retida como evidência", "Resultados comunicados às partes interessadas", "Ações apropriadas realizadas"],
86: ["Reação à não conformidade: controle, correção e consequências"],
87: ["Causa da não conformidade determinada", "Verificado se existem ou podem ocorrer não conformidades similares"],
88: ["Ação implementada", "Eficácia da ação analisada criticamente", "Mudanças no SGCN quando necessário"],
89: ["Registro da natureza das não conformidades e ações tomadas", "Resultados das ações corretivas registrados"],
90: ["Melhoria com base em medidas qualitativas e quantitativas", "Considera resultados da análise e da análise crítica pela direção"],
}

# ---- Cobertura das alíneas da norma (revisão de 09/11/2026) ----------------------------------------------------
# Comparação alínea a alínea da ISO 22301:2020 x critérios acima. SUBST troca um critério por outro (mais fiel à
# alínea); DIVIDE troca a lista inteira (critérios que estavam juntos viram independentes); ADD acrescenta critérios
# às perguntas que já tratam da cláusula (sem criar pergunta nova: o catálogo continua com 90 perguntas).
SUBST = {
    8: {1: "Considera contexto, partes interessadas, missões, metas e obrigações da organização"},
    57: {1: "Titulares e suplentes identificados, com responsabilidade, autoridade e competência"},
    61: {3: "Informações para ativar (critérios de ativação), operar, coordenar e comunicar as ações da equipe"},
    74: {1: "Quando e por quem os resultados são analisados e avaliados"},
}
DIVIDE = {
    51: ["Atendem ao RTO e à capacidade aceitável", "Protegem as atividades priorizadas", "Reduzem a probabilidade de disrupção",
         "Diminuem o período de disrupção", "Limitam o impacto nos produtos e serviços", "Fornecem a disponibilidade de recursos adequados"],
    83: ["Situação de ações de análises anteriores", "Mudanças em questões internas e externas",
         "Desempenho do SGCN e tendências (NCs, medições, auditorias)", "Feedback das partes interessadas",
         "Necessidade de mudanças no SGCN, incluindo política e objetivos",
         "Procedimentos e recursos que podem melhorar o desempenho e a eficácia do SGCN",
         "Informação do processo de avaliação de riscos e da BIA", "Resultados da avaliação da documentação e da capacidade (8.6)",
         "Riscos ou questões não endereçados adequadamente em avaliações de riscos anteriores",
         "Lições de quase acidentes e disrupções", "Oportunidades de melhoria"],
}
ADD = {
    6: ["Requisitos legais e regulamentares considerados na implementação e manutenção do SGCN"],
    13: ["Direção assegura que o SGCN alcance os resultados pretendidos"],
    17: ["Direção promove a melhoria contínua"],
    23: ["Considera o contexto (4.1) e os requisitos das partes interessadas (4.2)",
         "Visa assegurar os resultados, prevenir ou reduzir efeitos indesejados e alcançar melhoria contínua"],
    25: ["Levam em conta os requisitos aplicáveis (contexto e partes interessadas)"],
    37: ["Informação documentada de origem externa identificada e controlada"],
    52: ["Atende aos requisitos de prazo e capacidade aceitável"],
    56: ["Estrutura permite aviso e comunicação oportuna às partes interessadas",
         "Planos e procedimentos para gerenciar a organização durante a disrupção e ativar as soluções"],
    57: ["Procedimentos documentados para guiar cada equipe (ativação, operação, coordenação e comunicação)"],
    58: ["Planejar as ações que precisam ser realizadas", "Acionar as soluções de continuidade"],
    59: ["Comunicação estruturada com equipes de emergência", "Estratégia de comunicação com a mídia após o incidente",
         "Alertar as partes interessadas potencialmente impactadas por incidente real ou iminente",
         "Coordenação e comunicação entre múltiplas organizações"],
    62: ["Procedimentos específicos sobre as medidas imediatas durante a disrupção",
         "Procedimentos flexíveis às mudanças de condições internas e externas",
         "Focados no impacto dos eventos e efetivos para minimizá-lo",
         "Monitoramento do impacto da disrupção e da resposta da organização"],
    66: ["Desenvolvem trabalho em equipe, competência, confiança e conhecimento de quem tem papel na resposta",
         "Validam as estratégias e soluções de continuidade em conjunto ao longo do tempo"],
    67: ["Exercícios analisados criticamente para promover a melhoria contínua"],
    70: ["Avaliações em intervalos planejados e diante de mudanças significativas"],
    76: ["Auditoria verifica conformidade com os requisitos da organização e da norma e se o SGCN é eficaz"],
    88: ["Ações corretivas apropriadas aos efeitos das não conformidades"],
    90: ["Oportunidades de melhoria determinadas e ações implementadas para alcançar os resultados pretendidos"],
}
# alíneas citadas no campo "norma" (substituem a referência lida do .md)
REFS = {
    6: "4.2.2 a, b", 13: "5.1 a, e", 17: "5.1 f, g, h", 23: "6.1.1 a–c", 25: "6.2.1 a, b, c", 37: "7.5.3.2",
    51: "8.3.2 a–f", 52: "8.3.3 a, b, c", 56: "8.4.1; 8.4.2.1", 57: "8.4.2.2; 8.4.2.4 a, b",
    59: "8.4.3.1 a–f; 8.4.3.2 a, b", 62: "8.4.1 a–d; 8.4.4.2 a, b, c", 66: "8.5 a, b, c, d", 67: "8.5 e, f",
    90: "10.1.1; 10.2",
}
for n, subs in SUBST.items():
    for i, txt in subs.items():
        C[n][i] = txt
C.update(DIVIDE)
for n, extra in ADD.items():
    C[n] = C[n] + extra

REGISTRO = {3, 24, 26, 31, 32, 33, 39, 40, 41, 49, 55, 60, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90}


def main(md_path, out):
    refs = {}
    for line in open(md_path, encoding="utf-8"):
        m = re.match(r"\|\s*(\d+)\s*\|.*\|\s*([\d.]+[^|]*?)\s*\|[^|]*\|[^|]*\|$", line.rstrip())
        if m:
            refs[int(m.group(1))] = m.group(2).strip()
    assert set(C) == set(range(1, 91)) and len(refs) == 90, (len(C), len(refs))
    refs.update(REFS)
    data = {str(n): {"norma": refs[n], "kind": "registro" if n in REGISTRO else "documento", "criteria": C[n]} for n in range(1, 91)}
    json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(data), "itens;", sum(1 for d in data.values() if d["kind"] == "registro"), "exigem registro de execução")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
