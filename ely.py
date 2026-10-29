"""A IA Ely: monta o prompt com trechos do regimento e chama a Groq."""
import os

import requests

from rag import Index

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
index = Index()

SYSTEM = """Você é a Ely, a assistente de IA do Colégio Estadual da Polícia Militar de Goiás (CEPMG). Fale em português do Brasil, de forma simpática, clara e respeitosa, como uma ajudante de estudos e orientação escolar.
Regras:
- Para dúvidas sobre normas, deveres, direitos, disciplina, uniforme, avaliação, frequência, etc., responda com base nos TRECHOS DO REGIMENTO ESCOLAR fornecidos e cite o artigo (ex.: "Art. 31").
- Se a resposta não estiver nos trechos, diga que não encontrou no regimento e sugira procurar a coordenação ou a secretaria. Nunca invente regras.
- Para ajuda com estudos em geral (matérias, redação, explicações), ajude normalmente de forma didática.
- Seja objetiva; use listas curtas quando ajudar."""


class ElyError(Exception):
    pass


def ask(messages: list) -> str:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise ElyError("A chave GROQ_API_KEY não está configurada no servidor.")
    users = [m["content"] for m in messages if m["role"] == "user"]
    query = " ".join(users[-2:])  # pergunta atual + anterior, para entender "e sobre isso?"
    context = "\n\n".join(f"[Trecho {i+1}]\n{t}" for i, t in enumerate(index.search(query)))
    payload = {
        "model": MODEL,
        "temperature": 0.3,
        "max_tokens": 900,
        "messages": [
            {"role": "system", "content": SYSTEM + "\n\nTRECHOS DO REGIMENTO ESCOLAR:\n" + (context or "(nenhum trecho relevante)")},
            *[{"role": "assistant" if m["role"] == "assistant" else "user", "content": str(m["content"])[:2000]} for m in messages[-8:]],
        ],
    }
    try:
        r = requests.post(GROQ_URL, json=payload, headers={"Authorization": f"Bearer {key}"}, timeout=45)
    except requests.RequestException:
        raise ElyError("Não consegui falar com a Groq agora. Tente de novo em instantes.")
    if r.status_code == 429:
        raise ElyError("Muitas perguntas ao mesmo tempo. Aguarde alguns segundos e tente de novo.")
    if not r.ok:
        raise ElyError("Erro na Groq: " + r.json().get("error", {}).get("message", str(r.status_code)))
    return r.json()["choices"][0]["message"]["content"]
