"""Gera app/data/catalog.json a partir de checklist_auditoria_ISO22301.xlsx.

Uso: python tools/build_catalog.py ../../checklist_auditoria_ISO22301.xlsx app/data/catalog.json
"""
import json
import sys

from openpyxl import load_workbook

# Documentos que a empresa anexa no início. Cada um aponta os itens do checklist que costuma sustentar.
SLOTS = [
    ("politica", "Política de Continuidade de Negócios", "Política aprovada pela Alta Direção, com data e versão.", [13, 18, 19, 20]),
    ("escopo", "Escopo do SGCN", "Documento que define limites, unidades, produtos e serviços cobertos e exclusões.", [8, 9, 10, 11, 12]),
    ("contexto", "Análise de contexto e partes interessadas", "SWOT/PESTEL, matriz de partes interessadas e seus requisitos.", [1, 2, 3, 4, 5]),
    ("legal", "Requisitos legais, regulatórios e contratuais", "Registro de leis, regulações e cláusulas contratuais aplicáveis (ex.: LGPD, SLAs).", [6, 7]),
    ("papeis", "Organograma e papéis do SGCN", "Organograma, nomeações e responsabilidades de continuidade.", [21, 22]),
    ("objetivos", "Objetivos e indicadores de continuidade", "Objetivos com metas, indicadores e acompanhamento.", [25, 26, 27, 74, 75]),
    ("riscos_sgcn", "Riscos e oportunidades do SGCN", "Registro de riscos e oportunidades do sistema de gestão e plano de ação.", [23, 24, 28]),
    ("bia", "Análise de Impacto nos Negócios (BIA)", "Relatório do BIA com MTPD, RTO, atividades prioritárias, recursos e dependências.", [42, 43, 44, 45, 46, 47]),
    ("riscos", "Avaliação de riscos de disrupção", "Relatório de avaliação e tratamento dos riscos que podem interromper atividades prioritárias.", [48, 49]),
    ("estrategias", "Estratégias e soluções de continuidade", "Estratégias selecionadas, recursos necessários, site alternativo, redundâncias.", [29, 50, 51, 52, 53, 54]),
    ("pcn", "Plano(s) de Continuidade e Recuperação (PCN)", "PCN, planos de resposta a incidentes e de recuperação de TI (DRP).", [56, 57, 58, 61, 62, 63, 64]),
    ("comunicacao", "Plano de comunicação e contatos de emergência", "Procedimentos de comunicação em crise, árvore de contatos, alertas.", [34, 59, 60]),
    ("exercicios", "Programa e relatórios de exercícios/testes", "Calendário de testes e relatórios pós-exercício com ações.", [65, 66, 67, 68, 69]),
    ("treinamento", "Competências, treinamentos e conscientização", "Matriz de competências, listas de presença, certificados, material de treinamento.", [30, 31, 32, 33]),
    ("doc_ctrl", "Controle de informação documentada", "Procedimento de controle de documentos, lista mestra, regras de retenção.", [35, 36, 37, 38, 39, 40]),
    ("fornecedores", "Fornecedores críticos e contratos", "Lista de fornecedores críticos, contratos e avaliações de continuidade.", [41, 71]),
    ("backup", "Backup e testes de restauração", "Política de backup, logs e relatórios de restauração, RPO/RTO de TI.", [55]),
    ("auditoria", "Programa e relatórios de auditoria interna", "Programa de auditoria interna, relatórios e acompanhamento de ações.", [76, 77, 78, 79, 80, 81]),
    ("analise_critica", "Atas de análise crítica pela direção", "Atas com entradas e saídas, decisões e comunicação dos resultados.", [14, 15, 16, 17, 82, 83, 84, 85]),
    ("nc", "Não conformidades e ações corretivas", "Registro de NCs, causa raiz, ações e verificação de eficácia.", [86, 87, 88, 89, 90]),
    ("pos_incidente", "Relatórios pós-incidente e avaliações", "Análises pós-incidente e avaliações da capacidade de continuidade.", [70, 72, 73]),
]

# Requisitos obrigatórios que impedem a classificação "pronta" se ficarem abaixo do nível 3.
BLOCKING = {8, 18, 25, 42, 45, 46, 48, 61, 65, 76, 82, 86}


def main(xlsx, out):
    ws = load_workbook(xlsx)["Checklist"]
    items = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        n, clause, sub, question, ev = row[:5]
        if not n:
            continue
        items.append({
            "n": int(n),
            "clause": clause,
            "clause_no": int(clause.split(".")[0]),
            "subclause": sub or "",
            "question": question,
            "evidence_examples": ev or "",
            "weight": 2 if int(n) in BLOCKING else 1,
            "blocking": int(n) in BLOCKING,
            "slots": [s[0] for s in SLOTS if int(n) in s[3]],
        })
    slots = [{"id": s[0], "name": s[1], "description": s[2], "items": s[3]} for s in SLOTS]
    covered = {n for s in SLOTS for n in s[3]}
    missing = [i["n"] for i in items if i["n"] not in covered]
    json.dump({"norm": "ABNT NBR ISO 22301:2020", "version": "1.0", "slots": slots, "items": items},
              open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(items), "itens;", len(slots), "slots; sem documento sugerido:", missing)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
