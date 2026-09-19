#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Aplica os dois ajustes combinados na agenda da Melody:
1) Mentoria Liberta: de semanal (toda segunda) para mensal, 1a e 3a segunda-feira.
2) Cria a aula mensal nova, 1a quinta-feira do mes, 10h-13h.
"""
import json
import urllib.parse
import urllib.request
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent / ".env"
EVENTO_ML_ID = "dqgftbbjia3b1ei26olg94kass"


def carregar_env():
    cfg = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            cfg[k.strip()] = v.strip()
    return cfg


CFG = carregar_env()


def obter_access_token():
    dados = urllib.parse.urlencode({
        "client_id": CFG["GOOGLE_CLIENT_ID"],
        "client_secret": CFG["GOOGLE_CLIENT_SECRET"],
        "refresh_token": CFG["GOOGLE_REFRESH_TOKEN"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=dados, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["access_token"]


def api(token, metodo, url, payload=None):
    dados = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=dados, method=metodo, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = resp.read()
        return json.loads(body) if body else {}


def main():
    token = obter_access_token()

    # 1) Corrige a recorrencia da Mentoria Liberta para 1a e 3a segunda-feira do mes
    url_ml = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{EVENTO_ML_ID}"
    nova_recorrencia = {"recurrence": ["RRULE:FREQ=MONTHLY;UNTIL=20261214T210000Z;BYDAY=1MO,3MO"]}
    r1 = api(token, "PATCH", url_ml, nova_recorrencia)
    print("Mentoria Liberta atualizada. Nova recorrencia:", r1.get("recurrence"))

    # 2) Cria a aula mensal nova (1a quinta-feira do mes, 10h-13h)
    novo_evento = {
        "summary": "Aula",
        "start": {"dateTime": "2026-10-01T10:00:00-03:00", "timeZone": "America/Sao_Paulo"},
        "end": {"dateTime": "2026-10-01T13:00:00-03:00", "timeZone": "America/Sao_Paulo"},
        "recurrence": ["RRULE:FREQ=MONTHLY;BYDAY=1TH"],
    }
    url_criar = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
    r2 = api(token, "POST", url_criar, novo_evento)
    print("Aula mensal criada. ID:", r2.get("id"), "| Link:", r2.get("htmlLink"))


if __name__ == "__main__":
    main()
