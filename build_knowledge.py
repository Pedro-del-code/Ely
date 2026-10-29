"""Lê os documentos da pasta docs/ (PDF, TXT, MD) e gera data/knowledge.json.

Uso:  python build_knowledge.py
Coloque novos arquivos em docs/ e rode de novo para alimentar a Ely.
O resultado já vem pronto no projeto; só rode se mudar os documentos.
"""
import json
import os
import re

from pypdf import PdfReader

BASE = os.path.dirname(os.path.abspath(__file__))
DOCS, OUT = os.path.join(BASE, "docs"), os.path.join(BASE, "data", "knowledge.json")
MAX_CHUNK = 1400


def read_text(path: str) -> str:
    if path.lower().endswith(".pdf"):
        return "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def chunk(text: str):
    """Divide por artigo ('Art. 12') e junta artigos pequenos até ~1400 caracteres."""
    text = re.sub(r"[ \t]+", " ", text)
    parts = re.split(r"\n(?=\s*Art\. ?\d+)", text)
    chunks, cur = [], ""
    for p in parts:
        p = re.sub(r"\n{2,}", "\n", p).strip()
        if not p:
            continue
        if len(cur) + len(p) < MAX_CHUNK:
            cur += "\n" + p
            continue
        if cur:
            chunks.append(cur.strip())
        cur = p
        while len(cur) > 2200:  # artigo muito longo: corta
            chunks.append(cur[:1800])
            cur = cur[1800:]
    if cur.strip():
        chunks.append(cur.strip())
    return chunks


def main():
    out = []
    for name in sorted(os.listdir(DOCS)):
        if name.lower().endswith((".pdf", ".txt", ".md")):
            pieces = chunk(read_text(os.path.join(DOCS, name)))
            out += [{"id": len(out) + i, "source": name, "text": c} for i, c in enumerate(pieces)]
            print(f"{name}: {len(pieces)} trechos")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    print(f"Total: {len(out)} trechos -> {OUT}")


if __name__ == "__main__":
    main()
