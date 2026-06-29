#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Envia uma mensagem de WhatsApp para a Melody via Z-API.

Lê as credenciais das variáveis de ambiente (na nuvem, via GitHub Actions
Secrets) ou, se rodar localmente, de um arquivo .env. Nunca imprime o token.

Uso:
    python3 enviar.py "texto da mensagem"
"""
import os
import sys
import json
import urllib.request
from pathlib import Path


def carregar_env():
    """Procura um .env subindo a partir deste arquivo. Pode voltar vazio."""
    cfg = {}
    cur = Path(__file__).resolve().parent
    while cur.parent != cur:
        candidate = cur / ".env"
        if candidate.exists():
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                chave, valor = line.split("=", 1)
                cfg[chave.strip()] = valor.strip().strip('"').strip("'")
            break
        cur = cur.parent
    return cfg


def cred(cfg, chave):
    """Prioriza variável de ambiente; cai pro .env local."""
    return os.environ.get(chave) or cfg.get(chave)


def enviar_whatsapp(mensagem, instance_id, token, client_token, numero):
    url = f"https://api.z-api.io/instances/{instance_id}/token/{token}/send-text"
    payload = json.dumps({"phone": numero, "message": mensagem}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json", "Client-Token": client_token},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def main():
    if len(sys.argv) > 1:
        mensagem = sys.argv[1]
    else:
        mensagem = sys.stdin.read().strip()
    if not mensagem:
        raise SystemExit("Nenhuma mensagem informada.")

    cfg = carregar_env()
    instance_id = cred(cfg, "ZAPI_INSTANCE_ID")
    token = cred(cfg, "ZAPI_TOKEN")
    client_token = cred(cfg, "ZAPI_CLIENT_TOKEN")
    numero = cred(cfg, "DISCIPLINA_WHATSAPP_NUMERO")

    faltando = [k for k, v in {
        "ZAPI_INSTANCE_ID": instance_id,
        "ZAPI_TOKEN": token,
        "ZAPI_CLIENT_TOKEN": client_token,
        "DISCIPLINA_WHATSAPP_NUMERO": numero,
    }.items() if not v]
    if faltando:
        raise SystemExit("Faltam credenciais: " + ", ".join(faltando))

    resposta = enviar_whatsapp(mensagem, instance_id, token, client_token, numero)
    num_mascarado = numero[:4] + "..." + numero[-2:]
    print(f"Mensagem enviada para {num_mascarado}. Z-API: {resposta.get('messageId', resposta)}")


if __name__ == "__main__":
    main()
