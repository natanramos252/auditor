import json
import re


class LLMError(Exception):
    pass


class LLMProvider:
    name = "base"
    model = ""

    def complete(self, system: str, user: str) -> str:  # devolve texto bruto
        raise NotImplementedError

    def complete_json(self, system: str, user: str, retries: int = 1) -> dict:
        last = None
        for _ in range(retries + 1):
            raw = self.complete(system, user)
            try:
                return parse_json(raw)
            except ValueError as e:
                last = e
                user += "\n\nSua resposta anterior não era JSON válido. Responda SOMENTE com o objeto JSON."
        raise LLMError(f"Resposta sem JSON válido: {last}")


def parse_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.M).strip()
    start, end = raw.find("{"), raw.rfind("}")
    if start < 0 or end <= start:
        raise ValueError(raw[:200])
    try:
        return json.loads(raw[start:end + 1])
    except json.JSONDecodeError as e:
        raise ValueError(str(e))
