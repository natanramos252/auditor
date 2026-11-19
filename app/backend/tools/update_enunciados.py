"""Atualiza os enunciados (e exemplos de evidência) das perguntas que ganharam critérios na revisão das alíneas.
Altera checklist_auditoria_ISO22301.xlsx e perguntas_x_norma_ISO22301.md; depois rode build_catalog.py e build_criteria.py.
Uso: python tools/update_enunciados.py ../../checklist_auditoria_ISO22301.xlsx ../../perguntas_x_norma_ISO22301.md
"""
import re
import sys

from openpyxl import load_workbook

Q = {
 6: "Existe processo para identificar, acessar e avaliar requisitos legais e regulamentares sobre continuidade (ex.: LGPD, regulações setoriais, contratos/SLAs) e esses requisitos são considerados na implementação e manutenção do SGCN?",
 8: "O escopo do SGCN está documentado e disponível, considerando contexto, partes interessadas, missões, metas e obrigações da organização?",
 13: "A Alta Direção estabeleceu política e objetivos alinhados à estratégia e assegura que o SGCN alcance os resultados pretendidos?",
 17: "A Direção apoia os gestores de área no seu papel no SGCN e promove a melhoria contínua?",
 23: "Foram determinados riscos e oportunidades que afetam a eficácia do SGCN, considerando o contexto e as partes interessadas, para assegurar os resultados, prevenir ou reduzir efeitos indesejados e alcançar melhoria contínua?",
 25: "Os objetivos de continuidade estão estabelecidos nas funções e níveis pertinentes, coerentes com a política, mensuráveis e levando em conta os requisitos aplicáveis?",
 37: "Há controle de versão, distribuição, acesso, armazenamento, retenção e descarte, inclusive da informação documentada de origem externa?",
 51: "As estratégias atendem ao RTO, protegem atividades priorizadas, reduzem a probabilidade e a duração da disrupção, limitam o impacto e fornecem a disponibilidade de recursos adequados?",
 52: "A seleção considerou prazo e capacidade aceitável, apetite a risco e custo-benefício?",
 56: "Existe estrutura de resposta com equipes responsáveis por responder a disrupções, com aviso e comunicação oportuna às partes interessadas e planos para gerenciar a organização e ativar as soluções?",
 57: "Papéis, responsabilidades e relacionamento entre equipes estão definidos? Há titulares e suplentes com autoridade e competência, e procedimentos documentados para cada equipe?",
 58: "As equipes sabem avaliar a natureza e extensão da disrupção, decidir a ativação, planejar as ações, priorizar (vida em primeiro lugar), monitorar, acionar as soluções de continuidade e se comunicar com partes interessadas e mídia?",
 59: "Existem procedimentos de aviso e comunicação: interna/externa, alertas de autoridades, meios de comunicação alternativos, comunicação com equipes de emergência e mídia, alerta às partes impactadas, coordenação entre organizações, registro de incidente, ações e decisões?",
 61: "Os planos de continuidade (PCN) estão documentados e contêm propósito, escopo, objetivos, papéis, ações, informações para ativar (critérios), operar, coordenar e comunicar, interdependências, recursos, requisitos de relatório e evacuação?",
 62: "Os planos definem limites/gatilhos de ativação, medidas imediatas específicas e flexíveis, foco no impacto, monitoramento da disrupção e como manter a entrega de produtos e serviços na capacidade acordada?",
 66: "Os exercícios têm cenários realistas, escopo e objetivos definidos, são coerentes com os objetivos do SGCN, desenvolvem a equipe e validam as estratégias ao longo do tempo?",
 67: "Há relatório formal pós-exercício com resultados, recomendações e ações de melhoria, analisado criticamente?",
 70: "BIA, riscos, estratégias, planos e procedimentos são avaliados quanto à adequação e eficácia, em intervalos planejados e após mudanças significativas?",
 74: "O que deve ser monitorado, por quais métodos, quando e por quem está definido, inclusive quando e por quem os resultados são analisados?",
 76: "Há programa de auditoria interna com frequência, métodos, responsabilidades e relatórios, que verifique a conformidade e a eficácia do SGCN?",
 83: "As entradas incluem: ações anteriores, mudanças de contexto, desempenho e tendências (NC, medições, auditorias), feedback das partes interessadas, necessidade de mudanças, procedimentos e recursos de melhoria, BIA/riscos, resultados da avaliação de 8.6, riscos não tratados, lições de quase-acidentes e disrupções, oportunidades de melhoria?",
 88: "A eficácia das ações corretivas é analisada criticamente, as ações são apropriadas aos efeitos e o SGCN é alterado quando necessário?",
 90: "Há evidência de melhoria contínua da adequação, suficiência e eficácia do SGCN com base em medidas qualitativas e quantitativas, e as oportunidades de melhoria são determinadas e implementadas?",
}
EV = {
 37: "Lista mestra de documentos (inclusive externos), controle de versões, permissões de acesso, política de retenção",
 59: "Procedimentos de comunicação em crise, árvore de contatos, protocolo de alerta às partes impactadas e a órgãos/equipes de emergência, acordos de coordenação, registro de teste de comunicação",
 62: "Plano de continuidade (PCN) com critérios de ativação, medidas imediatas, papéis, recursos e evacuação; observação do plano acessível",
}
REF = {  # coluna "Cláusula da norma" do .md
 6: "4.2.2 a, b", 13: "5.1 a, e", 17: "5.1 f, g, h", 23: "6.1.1 a–c", 25: "6.2.1 a, b, c", 51: "8.3.2 a–f", 52: "8.3.3 a, b, c",
 56: "8.4.1; 8.4.2.1", 57: "8.4.2.2; 8.4.2.4 a, b", 59: "8.4.3.1 a–f; 8.4.3.2 a, b", 62: "8.4.1 a–d; 8.4.4.2 a, b, c",
 66: "8.5 a, b, c, d", 67: "8.5 e, f", 90: "10.1.1; 10.2",
}


def main(xlsx, md):
    wb = load_workbook(xlsx)
    ws = wb["Checklist"]
    n_x = 0
    for row in ws.iter_rows(min_row=2):
        n = row[0].value
        if n in Q:
            row[3].value = Q[n]
            if n in EV:
                row[4].value = EV[n]
            ws.row_dimensions[row[0].row].height = None
            n_x += 1
    wb.save(xlsx)
    out, n_m = [], 0
    for line in open(md, encoding="utf-8"):
        m = re.match(r"\|\s*(\d+)\s*\|(.*)$", line.rstrip("\n"))
        if m and int(m.group(1)) in Q:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            n = int(cells[0])
            cells[1] = Q[n]
            if n in REF:
                cells[2] = REF[n]
            line = "| " + " | ".join(cells[:5]) + " |\n" if len(cells) >= 5 else line
            n_m += 1
        out.append(line)
    open(md, "w", encoding="utf-8").write("".join(out))
    print(n_x, "linhas no xlsx;", n_m, "linhas no md")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
