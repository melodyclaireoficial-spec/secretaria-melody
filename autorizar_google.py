#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Autorização única do Google Calendar (fluxo OAuth desktop, sem dependências externas).

Abre o navegador para a Melody logar e autorizar. Captura o código de retorno
num servidor local, troca pelo refresh_token e grava no .env desta pasta.

Uso:
    python3 autorizar_google.py
"""
import http.server
import json
import os
import subprocess
import sys
import threading
import urllib.parse
import urllib.request
from pathlib import Path

PORTA = 8721
ESCOPO = "https://www.googleapis.com/auth/calendar"
ENV_PATH = Path(__file__).resolve().parent / ".env"


def carregar_env():
    cfg = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg


CFG = carregar_env()
CLIENT_ID = CFG.get("GOOGLE_CLIENT_ID")
CLIENT_SECRET = CFG.get("GOOGLE_CLIENT_SECRET")
if not CLIENT_ID or not CLIENT_SECRET:
    raise SystemExit("Faltam GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET no .env")

REDIRECT_URI = f"http://localhost:{PORTA}"
codigo_capturado = {}


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        qs = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(qs)
        if "code" in params:
            codigo_capturado["code"] = params["code"][0]
            corpo = "Autorizado. Pode fechar esta aba e voltar para o Claude."
        else:
            corpo = "Não recebi o código. Feche esta aba e tente de novo."
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(corpo.encode("utf-8"))

    def log_message(self, *args):
        pass  # silencia log do servidor


def main():
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": ESCOPO,
        "access_type": "offline",
        "prompt": "consent",
    })

    servidor = http.server.HTTPServer(("localhost", PORTA), Handler)
    thread = threading.Thread(target=servidor.handle_request)
    thread.start()

    print("Abrindo o navegador para autorizar. Faça login e clique em Permitir.")
    subprocess.run(["open", auth_url])

    thread.join(timeout=180)
    servidor.server_close()

    if "code" not in codigo_capturado:
        raise SystemExit("Não recebi a autorização a tempo (180s). Rode de novo.")

    dados = urllib.parse.urlencode({
        "code": codigo_capturado["code"],
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=dados, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        tokens = json.loads(resp.read())

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise SystemExit(
            "Google não devolveu refresh_token (provavelmente já tinha autorizado antes "
            "sem revogar). Revogue o acesso em myaccount.google.com/permissions e rode de novo."
        )

    linhas = ENV_PATH.read_text(encoding="utf-8").splitlines()
    linhas = [l for l in linhas if not l.startswith("GOOGLE_REFRESH_TOKEN=")]
    linhas.append(f"GOOGLE_REFRESH_TOKEN={refresh_token}")
    ENV_PATH.write_text("\n".join(linhas) + "\n", encoding="utf-8")

    print("Autorização concluída. Refresh token salvo no .env.")


if __name__ == "__main__":
    main()
