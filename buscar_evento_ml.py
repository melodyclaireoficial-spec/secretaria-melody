#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Busca o evento recorrente da Mentoria Liberta pra eu ver o ID e a recorrência atual."""
import json
import urllib.parse
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

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


def api_get(token, url):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def main():
    token = obter_access_token()
    agora = datetime.now().astimezone()
    inicio = (agora - timedelta(days=7)).isoformat()
    fim = (agora + timedelta(days=30)).isoformat()
    url = ("https://www.googleapis.com/calendar/v3/calendars/primary/events?"
           + urllib.parse.urlencode({
               "timeMin": inicio, "timeMax": fim, "singleEvents": "false", "q": "Mentoria Liberta",
           }))
    eventos = api_get(token, url)
    for e in eventos.get("items", []):
        print(json.dumps({
            "id": e.get("id"),
            "summary": e.get("summary"),
            "start": e.get("start"),
            "end": e.get("end"),
            "recurrence": e.get("recurrence"),
            "recurringEventId": e.get("recurringEventId"),
        }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
