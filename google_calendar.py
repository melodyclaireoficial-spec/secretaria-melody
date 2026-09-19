#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Leitura da Agenda do Google da Melody. Sem dependências externas (urllib puro).

Credenciais no .env: GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN.
Gerado por autorizar_google.py.
"""
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


def _carregar_env():
    cfg = {}
    cur = Path(__file__).resolve().parent
    while cur.parent != cur:
        candidate = cur / ".env"
        if candidate.exists():
            for line in candidate.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    cfg[k.strip()] = v.strip()
            break
        cur = cur.parent
    return cfg


_CFG = _carregar_env()


def _cred(k):
    v = os.environ.get(k) or _CFG.get(k)
    if not v:
        raise SystemExit(f"Falta {k} (env var ou .env) para acessar a Agenda do Google.")
    return v


def obter_access_token():
    dados = urllib.parse.urlencode({
        "client_id": _cred("GOOGLE_CLIENT_ID"),
        "client_secret": _cred("GOOGLE_CLIENT_SECRET"),
        "refresh_token": _cred("GOOGLE_REFRESH_TOKEN"),
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=dados, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())["access_token"]


def eventos_do_dia(data, token=None):
    """Devolve a lista de eventos (dict com 'summary', 'inicio', 'fim') do dia informado
    (objeto date), ordenados por horário de início. Ignora eventos de dia inteiro."""
    token = token or obter_access_token()
    inicio_dia = data.strftime("%Y-%m-%dT00:00:00-03:00")
    fim_dia = data.strftime("%Y-%m-%dT23:59:59-03:00")
    url = ("https://www.googleapis.com/calendar/v3/calendars/primary/events?"
           + urllib.parse.urlencode({
               "timeMin": inicio_dia, "timeMax": fim_dia,
               "singleEvents": "true", "orderBy": "startTime",
           }))
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        dados = json.loads(resp.read())

    eventos = []
    for e in dados.get("items", []):
        inicio = e.get("start", {}).get("dateTime")
        fim = e.get("end", {}).get("dateTime")
        if not inicio:  # evento de dia inteiro, sem hora; ignora
            continue
        eventos.append({
            "titulo": e.get("summary", "(sem título)"),
            "inicio": inicio,
            "fim": fim,
        })
    return eventos
