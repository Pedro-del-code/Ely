# Ely – IA do CEPMG (Python + Render)

## Estrutura
| Arquivo | Função |
|---|---|
| `app.py` | Servidor Flask: rotas `/api/login`, `/api/register`, `/api/chat`, `/healthz` |
| `auth.py` | Cadastro/login, hash de senha, token assinado, limite de tentativas |
| `db.py` | Banco: PostgreSQL na Render, SQLite no PC |
| `rag.py` | Busca BM25 nos trechos do regimento |
| `ely.py` | Monta o prompt da Ely e chama a Groq |
| `build_knowledge.py` | Lê `docs/*.pdf` e gera `data/knowledge.json` |
| `render.yaml` | Configuração da Render (site + banco) |
| `public/index.html` | Tela de login (verde/amarelo) + chat |

## Rodar no PC
```
pip install -r requirements.txt
cp .env.example .env   # (ou exporte GROQ_API_KEY no terminal)
python app.py          # http://localhost:3000  | teste: aluno / ely123
```

## Publicar na Render
1. Suba esta pasta para um repositório no GitHub (sem o `.env`).
2. Na Render: **New > Blueprint** e escolha o repositório. Ela lê o `render.yaml`.
3. Preencha quando pedir: `GROQ_API_KEY`, `ADMIN_USER` e `ADMIN_PASS` (conta inicial).
4. Aguarde o deploy e abra a URL `https://ely-cepmg.onrender.com`.

## Atenções
- Plano grátis: o site "dorme" após 15 min sem uso (1º acesso demora ~50 s) e o banco grátis expira em 30 dias; para uso real da escola, use plano pago.
- Novos documentos: coloque em `docs/`, rode `python build_knowledge.py` e faça commit.
- Mude a variável `GROQ_API_KEY` só no painel da Render; nunca no código.
