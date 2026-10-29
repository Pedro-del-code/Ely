"""Busca nos documentos da escola (BM25) para dar contexto à Ely."""
import json
import math
import os
import re
import unicodedata

KNOWLEDGE = os.path.join(os.path.dirname(__file__), "data", "knowledge.json")
STOP = set("para com que uma dos das nos nas por como mais sao ser seu sua ele ela esta este isso mas foi tem sera sobre entre onde qual quais quando".split())


def tokenize(text: str):
    text = unicodedata.normalize("NFD", text.lower())
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return [w for w in re.findall(r"[a-z0-9]{3,}", text) if w not in STOP]


class Index:
    def __init__(self, path=KNOWLEDGE):
        with open(path, encoding="utf-8") as f:
            self.docs = json.load(f)
        self.freqs, self.lens, self.df = [], [], {}
        for d in self.docs:
            toks = tokenize(d["text"])
            freq = {}
            for t in toks:
                freq[t] = freq.get(t, 0) + 1
            self.freqs.append(freq)
            self.lens.append(len(toks))
            for t in freq:
                self.df[t] = self.df.get(t, 0) + 1
        self.avg = sum(self.lens) / max(len(self.lens), 1)

    def search(self, query: str, k: int = 6):
        terms, n, scored = set(tokenize(query)), len(self.docs), []
        for i, freq in enumerate(self.freqs):
            score = 0.0
            for t in terms:
                f = freq.get(t)
                if not f:
                    continue
                idf = math.log(1 + (n - self.df[t] + 0.5) / (self.df[t] + 0.5))
                score += idf * f * 2.2 / (f + 1.2 * (0.25 + 0.75 * self.lens[i] / self.avg))
            if score > 0:
                scored.append((score, self.docs[i]["text"]))
        scored.sort(reverse=True)
        return [text for _, text in scored[:k]]
