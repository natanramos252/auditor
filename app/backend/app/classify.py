"""Identifica, por regras em Python, quais dos 21 tipos de documento um arquivo consolidado cobre.

Cada tipo tem padrões (já sem acento e em minúsculas). Um tipo é considerado coberto quando o texto tem
pelo menos MIN_DISTINCT padrões diferentes dele, ou um padrão "forte" (típico de título de seção).
"""
import re

from .textutil import fold

# slot -> (padrões fortes, padrões de apoio)
RULES: dict[str, tuple[list[str], list[str]]] = {
    "politica": ([r"politica de continuidade"], [r"compromisso com a melhoria continua", r"aprovad[ao] pela (alta )?direcao"]),
    "escopo": ([r"escopo do (sgcn|sistema de gestao|pcn|plano)"], [r"exclus(ao|oes) do escopo", r"limites e aplicabilidade", r"unidades abrangidas"]),
    "contexto": ([r"analise de contexto", r"partes interessadas"], [r"\bswot\b", r"\bpestel?\b", r"questoes (internas|externas)"]),
    "legal": ([r"requisitos (legais|regulat|regulament)"], [r"\blgpd\b", r"banco central|\bbacen\b|resolucao (cmn|bcb)", r"\banpd\b", r"legislac", r"regulador"]),
    "papeis": ([r"papeis e responsabilidades", r"organograma"], [r"suplente", r"lider do (pcn|plano)", r"patrocinador", r"comite de crise", r"\bequipe\b"]),
    "objetivos": ([r"objetivos de continuidade"], [r"\bindicador(es)?\b", r"\bkpis?\b", r"\bmetas?\b"]),
    "riscos_sgcn": ([r"riscos e oportunidades"], [r"oportunidades de melhoria"]),
    "bia": ([r"analise de impacto", r"\bbia\b"], [r"\brto\b", r"\bmtp?d\b", r"\bwrt\b", r"\bmbco\b", r"atividades? (prioritari|critic)", r"processos? critico"]),
    "riscos": ([r"analise de riscos?", r"avaliacao de riscos?", r"matriz de risco"], [r"probabilidade", r"ameaca", r"vulnerabilidade", r"risco (inerente|residual)"]),
    "estrategias": ([r"estrategias? de (continuidade|recuperacao)", r"site alternativo"], [r"hot site|warm site|cold site", r"redundan", r"espelhad", r"failover", r"contingencia"]),
    "pcn": ([r"plano de continuidade", r"regras de acionamento", r"plano de recuperacao de desastres"], [r"acionamento", r"ativacao", r"\bprd\b|\bdrp\b", r"procedimento de recuperacao", r"\bpco\b"]),
    "comunicacao": ([r"comunicacao de crise", r"plano de comunicacao", r"\bpcc\b"], [r"imprensa|relacoes publicas", r"arvore de contatos|lista de contatos", r"comunicar (clientes|reguladores|partes)"]),
    "exercicios": ([r"teste de mesa", r"programa de (exercicios|testes)"], [r"simulac", r"\bexercicios?\b", r"teste de failover", r"teste de restaurac"]),
    "treinamento": ([r"treinamento", r"conscientizacao"], [r"competencias?", r"capacitac", r"lista de presenca"]),
    "doc_ctrl": ([r"historico de revis", r"controle (do documento|de versao|de documentos)", r"lista mestra"], [r"controle de alterac", r"versao em vigor", r"data de aprovacao", r"proxima revisao"]),
    "fornecedores": ([r"fornecedores? critic"], [r"\bcontratos?\b", r"terceiriz", r"\bslas?\b", r"provedor"]),
    "backup": ([r"\bbackups?\b"], [r"restaurac", r"\brpo\b", r"replicac", r"imutavel|\bworm\b"]),
    "auditoria": ([r"auditoria interna"], [r"programa de auditoria", r"auditor(es)? independente", r"plano de acao"]),
    "analise_critica": ([r"analise critica pela direcao", r"analise critica"], [r"alta direcao", r"\bata\b|\batas\b"]),
    "nc": ([r"nao conformidade", r"acao corretiva|acoes corretivas"], [r"causa raiz", r"eficacia das acoes"]),
    "pos_incidente": ([r"pos.incidente", r"relatorio de incidente", r"licoes aprendidas"], [r"formulario de incidente", r"encerramento do incidente"]),
}
MIN_DISTINCT = 3


def classify(text: str) -> list[dict]:
    """Devolve [{slot, score, reason}] dos tipos que o texto cobre, do mais forte ao mais fraco."""
    t = fold(text)
    out = []
    for slot, (strong, support) in RULES.items():
        found, score = [], 0.0
        strong_hit = False
        strong_count = 0
        for pat in strong + support:
            hits = re.findall(pat, t)
            if hits:
                is_strong = pat in strong
                strong_hit |= is_strong
                strong_count += len(hits) if is_strong else 0
                score += (3 if is_strong else 1) + min(len(hits), 10) * 0.2
                m = re.search(pat, t)
                end = m.end()
                while end < len(text) and text[end].isalpha():  # completa a palavra ("redundân" -> "redundância")
                    end += 1
                found.append(text[m.start():end])  # trecho original, com acento
        # coberto: título forte + algum apoio, um título forte repetido, ou vários sinais diferentes
        if strong_hit and (len(found) >= 2 or strong_count >= 2) or len(found) >= MIN_DISTINCT:
            uniq = list(dict.fromkeys(f.lower() for f in found))
            out.append({"slot": slot, "score": round(score, 1), "reason": "Encontrado: " + ", ".join(uniq[:5])})
    out.sort(key=lambda c: c["score"], reverse=True)
    return out
