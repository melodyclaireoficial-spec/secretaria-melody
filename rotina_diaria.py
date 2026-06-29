#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cérebro do sistema de disciplina da Melody.

Conhece a grade semanal inteira. Cada bloco tem um horário local (America/Sao_Paulo).
Na nuvem (GitHub Actions), cada horário tem um agendamento próprio que chama este
script com --fire HH:MM. O script descobre qual bloco corresponde àquele horário
NO DIA DA SEMANA atual e envia a mensagem. Assim, atrasos do agendador não fazem
o lembrete ser pulado nem duplicado.

Uso:
    python3 rotina_diaria.py --fire 09:00     # envia o bloco das 09:00 de hoje
    python3 rotina_diaria.py --slot academia  # força um slot (teste)
    python3 rotina_diaria.py --listar         # lista todos os slots
    acrescente --dry-run pra ver sem enviar
"""
import sys
import subprocess
from datetime import datetime
from pathlib import Path

SEG, TER, QUA, QUI, SEX, SAB, DOM = 0, 1, 2, 3, 4, 5, 6
UTEIS = {SEG, TER, QUA, QUI, SEX}
TODOS = {SEG, TER, QUA, QUI, SEX, SAB, DOM}

# (id, dias, "HH:MM", mensagem). bomdia usa resumo dinâmico (mensagem = None).
SCHEDULE = [
    ("academia", UTEIS, "05:45",
     "Bom dia, Mel. 5:45, hora de levantar e ir treinar. A academia é o bloco que você decidiu não falhar. Começa o dia ganhando de você mesma."),
    ("bomdia", UTEIS, "08:55", None),
    ("almoco", UTEIS, "13:00",
     "13h, hora do almoço. Para de verdade, come com calma. Você rende mais na tarde se descansar agora."),
    ("danca", TODOS, "19:30",
     "19:30, hora da dança. 30 minutinhos só pra você, pra soltar o corpo e desacelerar. Já já é hora de ir pra cama (21:30)."),
    ("checkin", UTEIS, "20:30",
     "E aí, Mel, como foi o dia hoje? Conseguiu cumprir a rotina? Responde:\n\n1 (sim, mandei bem)\n2 (parcialmente)\n3 (não rolou)"),

    ("seg-dados", {SEG}, "09:00",
     "9h. Começa atualizando os dados do Google das alunas (Uillian e Catarina). Isso já dispara os relatórios da IA pra você analisar depois."),
    ("seg-estudo", {SEG}, "09:30",
     "9:30, bloco de estudo (2h). Enquanto isso a IA está montando os relatórios. Cabeça no aprendizado agora."),
    ("seg-analise1", {SEG}, "11:30",
     "11:30, hora de analisar as alunas. Lê os relatórios e decide as otimizações. Casos simples você resolve rápido."),
    ("seg-analise2", {SEG}, "14:00",
     "14h, parte 2 da análise das alunas. Foco pra fechar tudo antes das 17h, que é a sua Mentoria."),

    ("ter-estudo", {TER}, "09:00",
     "9h, bloco de estudo (2h). Terça é seu dia de câmera mais tarde, então aproveita a manhã pra estudar com a mente fresca."),
    ("ter-youtube", {TER}, "11:00",
     "11h, gravar o vídeo longo do YouTube no teleprompter. Roteiro pronto da quinta, é só seguir. Energia de começo de semana."),
    ("ter-leraula", {TER}, "11:40",
     "11:40, dá uma lida no conteúdo da aula antes de gravar. 15 minutinhos pra entrar afiada."),
    ("ter-aula", {TER}, "12:00",
     "12h, gravar a aula do curso no teleprompter. Mesma pegada da câmera, aproveita o embalo."),
    ("ter-curtos", {TER}, "14:00",
     "14h, bloco grande de gravação: vídeo longo do IG + os 4 curtos. Esse é o coração da terça. Vai com tudo."),

    ("qua-estudo", {QUA}, "09:00",
     "9h, estudo (1h30 hoje, já que a constelação da Ana Franco começa 10:30). Aproveita bem essa janela."),
    ("qua-constela", {QUA}, "14:00",
     "14h, bloco das constelações (as 2 vagas da tarde). Respira, você está em modo atendimento agora."),

    ("qui-estudo", {QUI}, "09:00",
     "9h, estudo. Hoje é o dia mais folgado, dá pra esticar pra 3h se você quiser. Aproveita."),
    ("qui-roteiros", {QUI}, "11:00",
     "11h, roteiros (YouTube + 4 curtos). Lembra: o que você escreve hoje vira a gravação da terça que vem. Adianta seu futuro."),
    ("qui-afiliado", {QUI}, "14:00",
     "14h, bloco do Projeto Afiliado, tudo de uma vez: pegar os links, baixar os 21 vídeos, subir e programar no mLabs. Modo execução."),

    ("sex-trafego", {SEX}, "10:30",
     "10:30, análise de tráfego. Sexta é só tráfego, sem complicar. Olha os números e decide."),
    ("sex-estudo", {SEX}, "14:00",
     "14h, bloco de estudo. Já é sexta, mas o estudo é inegociável. Mais 2h de avanço."),
    ("sex-admin", {SEX}, "16:00",
     "16h, administrativo e financeiro da empresa. Hora das tarefas avulsas: mensagem do Daison, extrato do BB, o que estiver pendente. Fecha a semana limpa."),
]

RESUMO_DIA = {
    SEG: ("Bom dia, Mel. Hoje é dia de cuidar das alunas:\n"
          "- 9h atualizar dados do Google\n- 9:30 estudo\n- 11:30 e 14h análise das alunas\n- 17h Mentoria Liberta\n"
          "Foco em fechar a análise antes das 17h. Bora."),
    TER: ("Bom dia, Mel. Hoje é dia de câmera:\n"
          "- 9h estudo\n- 11h gravar vídeo do YouTube\n- 12h gravar a aula do curso\n- 14h vídeo do IG + 4 curtos\n"
          "Começo de semana, sua energia de exposição está no auge. Aproveita."),
    QUA: ("Bom dia, Mel. Hoje é dia de constelações:\n"
          "- 9h estudo\n- 10:30 Ana Franco\n- 14h as outras 2 constelações\n"
          "Dia de presença e atendimento. Respira e entrega."),
    QUI: ("Bom dia, Mel. Hoje é dia de adiantar o futuro:\n"
          "- 9h estudo (pode esticar pra 3h)\n- 11h roteiros\n- 14h Projeto Afiliado\n"
          "Dia mais leve. Aproveita a folga pra render."),
    SEX: ("Bom dia, Mel. Sexta tranquila, pode estar de roupa de academia:\n"
          "- 8:30 reunião do comercial\n- 9h Mastermind\n- 10:30 tráfego\n- 13h Copy\n- 14h estudo\n- 16h administrativo\n"
          "Fecha a semana com chave de ouro."),
}


def texto_do_slot(sid, weekday):
    if sid == "bomdia":
        return RESUMO_DIA.get(weekday)
    for s, dias, hora, msg in SCHEDULE:
        if s == sid:
            return msg
    return None


def slots_no_horario(hhmm, weekday):
    """Slots agendados para 'hhmm' (HH:MM) que valem hoje (weekday)."""
    achados = []
    for sid, dias, hora, msg in SCHEDULE:
        if hora == hhmm and weekday in dias:
            texto = RESUMO_DIA.get(weekday) if sid == "bomdia" else msg
            if texto:
                achados.append((sid, texto))
    return achados


def enviar(texto):
    script = Path(__file__).resolve().parent / "enviar.py"
    subprocess.run([sys.executable, str(script), texto], check=True)


def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    hoje = datetime.now()

    if "--listar" in args:
        nome = {0: "seg", 1: "ter", 2: "qua", 3: "qui", 4: "sex", 5: "sab", 6: "dom"}
        for sid, dias, hora, msg in SCHEDULE:
            dd = ",".join(nome[d] for d in sorted(dias))
            print(f"{hora}  [{dd}]  {sid}")
        return

    if "--slot" in args:
        sid = args[args.index("--slot") + 1]
        texto = texto_do_slot(sid, hoje.weekday())
        if not texto:
            raise SystemExit(f"Slot '{sid}' sem mensagem para hoje.")
        print(f"[DRY-RUN] {sid}:\n{texto}") if dry else (enviar(texto), print(f"Enviado: {sid}"))
        return

    if "--fire" in args:
        hhmm = args[args.index("--fire") + 1]
        achados = slots_no_horario(hhmm, hoje.weekday())
        if not achados:
            print(f"Nada agendado para {hhmm} em {hoje:%a}.")
            return
        for sid, texto in achados:
            if dry:
                print(f"[DRY-RUN] {sid}:\n{texto}\n")
            else:
                enviar(texto)
                print(f"Enviado: {sid}")
        return

    print("Use --fire HH:MM, --slot ID, ou --listar.")


if __name__ == "__main__":
    main()
