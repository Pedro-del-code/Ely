"""Autenticação: hash de senha, tokens assinados e limite de tentativas."""
import os
import re
import time
from collections import defaultdict

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

import db

SECRET_KEY = os.getenv("SECRET_KEY") or "dev-inseguro-troque-em-producao"
_serializer = URLSafeTimedSerializer(SECRET_KEY, salt="ely-session")

USERNAME_RE = re.compile(r"^[a-z0-9_.]{3,20}$")
EMAIL_RE = re.compile(r"^\S+@\S+\.\S+$")


def make_token(username: str) -> str:
    return _serializer.dumps(username)


def read_token(token: str, days: int = 30):
    """Devolve o usuário do token ou None se inválido/expirado."""
    try:
        return _serializer.loads(token, max_age=days * 86400)
    except (BadSignature, SignatureExpired):
        return None


def register(username: str, email: str, name: str, password: str):
    """Retorna (usuario, None) ou (None, mensagem_de_erro)."""
    username, email, name = username.strip().lower(), email.strip().lower(), name.strip()
    if not USERNAME_RE.match(username) or not EMAIL_RE.match(email) or len(password) < 6:
        return None, "Dados inválidos (usuário 3-20 letras/números, e-mail válido, senha de 6+ caracteres)."
    if db.get_user(username) or db.get_user(email):
        return None, "Usuário ou e-mail já cadastrado."
    db.create_user(username, email, name or username, generate_password_hash(password))
    return db.get_user(username), None


def login(identifier: str, password: str):
    user = db.get_user(identifier.strip().lower())
    if user and check_password_hash(user["pass_hash"], password):
        return user
    return None


def seed_admin():
    """Cria um usuário inicial a partir das variáveis ADMIN_USER / ADMIN_PASS.
    Localmente (SQLite) cria aluno/ely123 só para teste."""
    user, pw = os.getenv("ADMIN_USER"), os.getenv("ADMIN_PASS")
    if not user and not db.USE_PG:
        user, pw = "aluno", "ely123"
    if user and pw and not db.get_user(user.lower()):
        register(user, f"{user.lower()}@escola.local", "Administrador" if os.getenv("ADMIN_USER") else "Aluno Teste", pw)


# ---- limite de tentativas de login (em memória, por IP) ----
_tries = defaultdict(list)


def too_many_attempts(ip: str, limit: int = 8, window: int = 60) -> bool:
    _tries[ip] = [t for t in _tries[ip] if t > time.time() - window]
    return len(_tries[ip]) >= limit


def register_failure(ip: str):
    _tries[ip].append(time.time())
