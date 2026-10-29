"""Servidor web da Ely (Flask). Na Render roda com gunicorn: `gunicorn app:app`."""
import os

from flask import Flask, jsonify, request, send_from_directory

import auth
import db
import ely

app = Flask(__name__, static_folder="public", static_url_path="")
app.config["MAX_CONTENT_LENGTH"] = 100_000

os.makedirs(os.path.join(os.path.dirname(__file__), "data"), exist_ok=True)
db.init_db()
auth.seed_admin()


def error(msg, code):
    return jsonify(error=msg), code


def client_ip():
    # Na Render o IP real vem no cabeçalho X-Forwarded-For
    return (request.headers.get("X-Forwarded-For", request.remote_addr) or "").split(",")[0].strip()


@app.get("/healthz")  # usado pela Render para saber se o serviço está vivo
def healthz():
    return "ok"


@app.post("/api/login")
def api_login():
    data = request.get_json(silent=True) or {}
    ip = client_ip()
    if auth.too_many_attempts(ip):
        return error("Muitas tentativas. Aguarde 1 minuto.", 429)
    user = auth.login(str(data.get("user", "")), str(data.get("pass", "")))
    if not user:
        auth.register_failure(ip)
        return error("Usuário ou senha incorretos.", 401)
    return jsonify(token=auth.make_token(user["username"]), name=user["name"])


@app.post("/api/register")
def api_register():
    d = request.get_json(silent=True) or {}
    user, err = auth.register(str(d.get("user", "")), str(d.get("email", "")), str(d.get("name", "")), str(d.get("pass", "")))
    if err:
        return error(err, 409 if "cadastrado" in err else 400)
    return jsonify(token=auth.make_token(user["username"]), name=user["name"])


@app.post("/api/chat")
def api_chat():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    if not auth.read_token(token):
        return error("Sessão expirada. Faça login novamente.", 401)
    msgs = (request.get_json(silent=True) or {}).get("messages")
    if not isinstance(msgs, list) or not msgs or not all(isinstance(m, dict) and "content" in m for m in msgs):
        return error("Mensagem vazia.", 400)
    try:
        return jsonify(reply=ely.ask(msgs))
    except ely.ElyError as e:
        return error(str(e), 500)


@app.get("/")
def index():
    return send_from_directory(app.static_folder, "index.html")


if __name__ == "__main__":  # rodar local: python app.py
    app.run(port=int(os.getenv("PORT", 3000)), debug=True)
