"""Extração de texto de PDF, DOCX, XLSX e texto puro, dividido em trechos (chunks)."""
from pathlib import Path

from .textutil import collapse

CHUNK_CHARS = 900


def _split(text: str, page: int | None) -> list[tuple[int | None, str]]:
    paras = [collapse(p) for p in text.replace("\r", "").split("\n")]
    out, buf = [], ""
    for p in paras:
        if not p:
            continue
        if buf and len(buf) + len(p) + 1 > CHUNK_CHARS:
            out.append((page, buf))
            buf = ""
        while len(p) > CHUNK_CHARS * 1.5:  # parágrafo gigante
            cut = p.rfind(". ", 0, CHUNK_CHARS)
            cut = cut + 1 if cut > 200 else CHUNK_CHARS
            out.append((page, p[:cut].strip()))
            p = p[cut:].strip()
        buf = f"{buf} {p}".strip()
    if buf:
        out.append((page, buf))
    return out


def extract(path: Path) -> list[tuple[int | None, str]]:
    ext = path.suffix.lower()
    if ext == ".pdf":
        from pypdf import PdfReader
        chunks = []
        for i, page in enumerate(PdfReader(str(path)).pages, 1):
            chunks += _split(page.extract_text() or "", i)
        return chunks
    if ext == ".docx":
        import docx
        d = docx.Document(str(path))
        lines = [p.text for p in d.paragraphs]
        for t in d.tables:
            for row in t.rows:
                lines.append(" | ".join(c.text.strip() for c in row.cells))
        return _split("\n".join(lines), None)
    if ext == ".xlsx":
        from openpyxl import load_workbook
        wb = load_workbook(str(path), read_only=True, data_only=True)
        chunks = []
        for ws in wb.worksheets:
            lines = [f"[{ws.title}]"]
            for row in ws.iter_rows(values_only=True):
                cells = [str(c) for c in row if c is not None and str(c).strip()]
                if cells:
                    lines.append(" | ".join(cells))
            chunks += _split("\n".join(lines), None)
        return chunks
    if ext in {".txt", ".md", ".csv"}:
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("latin-1")
        return _split(text, None)
    raise ValueError(f"Formato não suportado: {ext}")
