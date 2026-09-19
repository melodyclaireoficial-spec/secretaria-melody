#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cérebro do sistema de disciplina da Melody (versão com Agenda do Google ao vivo).

Em vez de uma grade fixa, consulta a Agenda do Google da Melody (calendário
principal) toda vez que roda, pega o(s) compromisso(s) que estão começando
agora (dentro da janela de tolerância) e manda a mensagem de transição
correspondente no WhatsApp. Assim, qualquer ajuste que ela fizer direto na
agenda (mover, renomear, cancelar um compromisso) já reflete no aviso.

Dois horários continuam fixos, por não serem blocos da agenda:
- 08:55, resumo da manhã (lista os compromissos do dia, lidos da agenda).
- 20:30, pergunta de check-in do dia (1/2/3).

Uso:
    python3 rotina_diaria.py                 # checa a hora atual e envia se bater
    python3 rotina_diaria.py --dry-run       # mostra o que enviaria, sem enviar
    python3 rotina_diaria.py --listar-hoje   # lista os eventos de hoje na agenda
"""
import sys
import subprocess
from datetime import datetime, date
from pathlib import Path

import google_calendar as cal

JANELA_MIN = 5  # tolerância em minutos, mesma cadência do disparo externo

# (palavra-chave no título do evento, mensagem). A primeira que bater no título
# (case-insensitive, substring) é usada. Fallback genérico no final.
MENSAGENS_POR_PALAVRA_CHAVE = [
    ("treino", "Bom dia, Mel. Hora de treinar. A academia é o bloco que você decidiu não falhar. Começa o dia ganhando de você mesma."),
    ("almoco", "Hora do almoço. Para de verdade, come com calma. Você rende mais na tarde se descansar agora."),
    ("almoço", "Hora do almoço. Para de verdade, come com calma. Você rende mais na tarde se descansar agora."),
    ("danca", "Hora da dança. Uns 30 minutinhos só pra você, pra soltar o corpo e desacelerar. Já já é hora de ir pra cama."),
    ("dança", "Hora da dança. Uns 30 minutinhos só pra você, pra soltar o corpo e desacelerar. Já já é hora de ir pra cama."),
    ("estudo", "Bloco de estudo. Cabeça no aprendizado agora, é inegociável."),
]

MENSAGEM_GENERICA = "Hora de: {titulo}."


def _horario_local(iso_dt):
    """'2026-09-21T17:00:00-03:00' -> datetime local (sem tzinfo, já em -03:00)."""
    dt = datetime.fromisoformat(iso_dt)
    return dt.replace(tzinfo=None)


def montar_mensagem(titulo):
    baixo = titulo.lower()
    for chave, msg in MENSAGENS_POR_PALAVRA_CHAVE:
        if chave in baixo:
            return msg
    return MENSAGEM_GENERICA.format(titulo=titulo)


def montar_resumo_do_dia(eventos):
    if not eventos:
        return "Bom dia, Mel. Sua agenda de hoje está livre por enquanto."
    linhas = ["Bom dia, Mel. Compromissos de hoje:"]
    for e in eventos:
        hora = _horario_local(e["inicio"]).strftime("%H:%M")
        linhas.append(f"- {hora} {e['titulo']}")
    return "\n".join(linhas)


def eventos_que_batem_agora(eventos, agora):
    """Eventos cujo início cai na janela [agora - JANELA_MIN, agora)."""
    minutos_agora = agora.hour * 60 + agora.minute
    casados = []
    for e in eventos:
        inicio = _horario_local(e["inicio"])
        minutos_evento = inicio.hour * 60 + inicio.minute
        if 0 <= (minutos_agora - minutos_evento) < JANELA_MIN:
            casados.append(e)
    return casados


def enviar(texto):
    script = Path(__file__).resolve().parent / "enviar.py"
    subprocess.run([sys.executable, str(script), texto], check=True)


def main():
    args = sys.argv[1:]
    agora = datetime.now()
    dry_run = "--dry-run" in args

    if "--listar-hoje" in args:
        eventos = cal.eventos_do_dia(date.today())
        for e in eventos:
            hora = _horario_local(e["inicio"]).strftime("%H:%M")
            print(f"{hora}  {e['titulo']}")
        return

    minutos_agora = agora.hour * 60 + agora.minute

    # --- Horários fixos, não vêm do calendário ---
    if 0 <= (minutos_agora - (8 * 60 + 55)) < JANELA_MIN:
        eventos = cal.eventos_do_dia(date.today())
        texto = montar_resumo_do_dia(eventos)
        if dry_run:
            print(f"[DRY-RUN] bomdia:\n{texto}")
        else:
            enviar(texto)
            print("Enviado: bomdia")
        return

    if 0 <= (minutos_agora - (20 * 60 + 30)) < JANELA_MIN:
        texto = ("E aí, Mel, como foi o dia hoje? Conseguiu cumprir a rotina? Responde:\n\n"
                 "1 (sim, mandei bem)\n2 (parcialmente)\n3 (não rolou)")
        if dry_run:
            print(f"[DRY-RUN] checkin:\n{texto}")
        else:
            enviar(texto)
            print("Enviado: checkin")
        return

    # --- Blocos da agenda (o resto do dia) ---
    eventos = cal.eventos_do_dia(date.today())
    casados = eventos_que_batem_agora(eventos, agora)
    if not casados:
        print(f"{agora:%a %H:%M} - nenhum compromisso começando agora.")
        return
    for e in casados:
        texto = montar_mensagem(e["titulo"])
        if dry_run:
            print(f"[DRY-RUN] {e['titulo']}:\n{texto}\n")
        else:
            enviar(texto)
            print(f"Enviado: {e['titulo']}")


if __name__ == "__main__":
    main()
