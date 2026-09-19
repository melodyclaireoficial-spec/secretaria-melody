#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Teste rápido: lista os calendários e os eventos de hoje. Não envia WhatsApp."""
import json
import urllib.parse
import urllib.request
from datetime import datetime, timezone
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
    print("Token obtido com sucesso.\n")

    cals = api_get(token, "https://www.googleapis.com/calendar/v3/users/me/calendarList")
    print("=== Calendários ===")
    for c in cals.get("items", []):
        print(f"  id={c['id']!r}  nome={c.get('summary')!r}  principal={c.get('primary', False)}")

    hoje = datetime.now().astimezone()
    inicio = hoje.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    fim = hoje.replace(hour=23, minute=59, second=59, microsecond=0).isoformat()

    print("\n=== Eventos de hoje (calendário principal) ===")
    url = ("https://www.googleapis.com/calendar/v3/calendars/primary/events?"
           + urllib.parse.urlencode({"timeMin": inicio, "timeMax": fim, "singleEvents": "true", "orderBy": "startTime"}))
    eventos = api_get(token, url)
    for e in eventos.get("items", []):
        inicio_ev = e.get("start", {}).get("dateTime") or e.get("start", {}).get("date")
        print(f"  {inicio_ev}  {e.get('summary')}")


if __name__ == "__main__":
    main()
