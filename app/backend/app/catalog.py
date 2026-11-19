import json
from functools import lru_cache
from pathlib import Path

PATH = Path(__file__).parent / "data" / "catalog.json"

LEVELS = {
    0: ("Não atende", "Não é feito, ou não há nada definido ou documentado."),
    1: ("Atende parcialmente", "Existe de modo informal, ou está documentado, mas sem registros que comprovem a execução."),
    2: ("Atende", "Está documentado, é executado e há registros que comprovam."),
}
MAX_LEVEL = 2


@lru_cache
def load() -> dict:
    cat = json.loads(PATH.read_text(encoding="utf-8"))
    cat["by_no"] = {i["n"]: i for i in cat["items"]}
    cat["slot_by_id"] = {s["id"]: s for s in cat["slots"]}
    return cat


def item(n: int) -> dict:
    return load()["by_no"][n]
