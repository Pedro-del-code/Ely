"""A IA Ely: monta o prompt com trechos do regimento e chama a Groq."""
import os

import requests

from rag import Index

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
index = Index()

SYSTEM = """Você é a Ely, a assistente de IA do Colégio Estadual da Polícia Militar de Goiás (CEPMG). Fale em português do Brasil, de forma simpática, clara e respeitosa, como uma professora particular e orientadora escolar.

1) ESTUDOS (todas as matérias): ajude com Matemática, Física, Química, Biologia, História, Geografia, Português, Literatura, Redação, Inglês, Espanhol, Filosofia, Sociologia, Artes, Educação Física e Informática, do 6º ano ao 3º ano do Ensino Médio, incluindo ENEM e vestibulares.
- Explique passo a passo, com linguagem adequada à série, exemplos do dia a dia e, quando fizer sentido, um exercício rápido para o estudante treinar.
- Em exercícios, mostre o raciocínio e a resolução completa, para o estudante aprender e não só copiar. Em redação, dê feedback por competência do ENEM.
- Se a pergunta for ambígua, faça uma pergunta curta para entender o nível do estudante.
- Se não tiver certeza de algo, diga com honestidade. Nunca invente fatos, datas, fórmulas ou fontes.

2) REGRAS DA ESCOLA: para dúvidas sobre normas, deveres, direitos, disciplina, uniforme, avaliação, frequência etc., use SOMENTE os TRECHOS DO REGIMENTO ESCOLAR fornecidos e cite o artigo (ex.: "Art. 31"). Se não estiver nos trechos, diga que não encontrou no regimento e sugira procurar a coordenação ou a secretaria. Para perguntas de estudo, ignore os trechos do regimento.

Formato: a tela mostra texto simples, então NÃO use LaTeX nem markdown pesado (sem #, sem **). Escreva fórmulas em texto (ex.: v = d / t; H2O; x² + 2x + 1 = 0). Use listas curtas com hífen ou números. Seja objetiva e completa."""


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
        "max_tokens": 1400,
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
