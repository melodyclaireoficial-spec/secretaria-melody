#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lê a resposta da Melody ao check-in da noite e envia a mensagem certa.

Roda ~30 min depois da pergunta das 20:30. Busca as últimas mensagens da conversa
na Z-API, pega a resposta mais recente dela (1, 2 ou 3) e dispara o retorno:
  1 = comemoração
  2 = motivação / reflexão
  3 = reflexão + alfinetada (sonho de ser mãe)
Se não encontrar resposta, manda um lembrete gentil, sem cobrança.
"""
import os
import sys
import json
import re
import urllib.request
from datetime import datetime
from pathlib import Path

BRANCHES = {
    "1": ("Isso, Mel. Que orgulho de você. Cada dia cumprido é um tijolo no caminho do "
          "que você mais quer. Descansa tranquila hoje, amanhã a gente repete."),
    "2": ("Tudo bem, Mel. Dia parcial ainda é avanço. Pensa rápido: o que travou hoje e "
          "o que dá pra ajustar amanhã? Confia, amanhã você chega mais inteira. Um passo "
          "de cada vez te leva pra mais perto de ser mãe."),
    "3": ("Sem culpa, Mel, mas com verdade. Me diz: o que você vai fazer diferente amanhã? "
          "E lembra do que você mesma me falou: não cumprir a sua rotina te afasta do maior "
          "sonho da sua vida, que é ser mãe. Amanhã é uma nova chance de escolher esse "
          "sonho. Eu acredito em você."),
}
SEM_RESPOSTA = ("Mel, não consegui ver sua resposta de hoje. Como foi o dia? Se quiser, me "
                "conta amanhã de manhã. O importante é não desistir de você.")


def carregar_env():
    cfg = {}
    cur = Path(__file__).resolve().parent
    while cur.parent != cur:
        candidate = cur / ".env"
        if candidate.exists():
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    cfg[k.strip()] = v.strip().strip('"').strip("'")
            break
        cur = cur.parent
    return cfg


def cred(cfg, k):
    return os.environ.get(k) or cfg.get(k)


def buscar_mensagens(instance_id, token, client_token, numero, amount=15):
    url = (f"https://api.z-api.io/instances/{instance_id}/token/{token}"
           f"/chat-messages/{numero}?amount={amount}")
    req = urllib.request.Request(url, headers={"Client-Token": client_token})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def extrair_texto(msg):
    """A Z-API varia o formato do texto conforme o tipo de mensagem."""
    if isinstance(msg.get("text"), dict):
        return msg["text"].get("message", "")
    return msg.get("text") or msg.get("message") or msg.get("body") or ""


def escolher_resposta(mensagens):
    """Procura a opção (1/2/3) na mensagem dela mais recente."""
    # Ordena por momento decrescente quando possível
    def momento(m):
        return m.get("momment") or m.get("moment") or m.get("timestamp") or 0
    try:
        mensagens = sorted(mensagens, key=momento, reverse=True)
    except Exception:
        pass
    for m in mensagens:
        if m.get("fromMe"):
            continue
        texto = extrair_texto(m).strip().lower()
        if not texto:
            continue
        if re.search(r"\b1\b", texto) or "sim" in texto or "mandei bem" in texto:
            return "1"
        if re.search(r"\b2\b", texto) or "parcial" in texto:
            return "2"
        if re.search(r"\b3\b", texto) or "não" in texto or "nao" in texto:
            return "3"
        return None  # primeira mensagem dela não bate com 1/2/3
    return None


def enviar(texto):
    script = Path(__file__).resolve().parent / "enviar.py"
    import subprocess
    subprocess.run([sys.executable, str(script), texto], check=True)


def main():
    cfg = carregar_env()
    instance_id = cred(cfg, "ZAPI_INSTANCE_ID")
    token = cred(cfg, "ZAPI_TOKEN")
    client_token = cred(cfg, "ZAPI_CLIENT_TOKEN")
    numero = cred(cfg, "DISCIPLINA_WHATSAPP_NUMERO")
    if not all([instance_id, token, client_token, numero]):
        raise SystemExit("Faltam credenciais Z-API.")

    try:
        mensagens = buscar_mensagens(instance_id, token, client_token, numero)
    except Exception as e:
        print(f"Não foi possível ler as mensagens: {e}")
        enviar(SEM_RESPOSTA)
        return

    opcao = escolher_resposta(mensagens if isinstance(mensagens, list) else [])
    if opcao in BRANCHES:
        enviar(BRANCHES[opcao])
        print(f"Resposta enviada para opção {opcao}.")
    else:
        enviar(SEM_RESPOSTA)
        print("Sem resposta clara. Enviado lembrete gentil.")


if __name__ == "__main__":
    main()
