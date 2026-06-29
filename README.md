# Secretária da Melody

Robô pessoal que envia lembretes de disciplina no WhatsApp ao longo do dia,
seguindo a grade semanal de blocos de tempo, e faz o check-in da noite.

Roda sozinho na nuvem (GitHub Actions), sem depender do computador ligado.

## Arquivos
- `rotina_diaria.py` — a grade da semana e todas as mensagens de cada bloco.
- `responder_checkin.py` — lê a resposta do check-in da noite (1/2/3) e responde.
- `enviar.py` — envio de WhatsApp via Z-API.
- `.github/workflows/disciplina.yml` — os horários (em UTC, Brasília + 3h).

## Chaves (GitHub Secrets, nunca no código)
`ZAPI_INSTANCE_ID`, `ZAPI_TOKEN`, `ZAPI_CLIENT_TOKEN`, `DISCIPLINA_WHATSAPP_NUMERO`.

## Testar agora
Aba **Actions** → **Secretaria da Melody** → **Run workflow** (faz um envio de teste).

## Mudar um horário ou uma mensagem
Edite `rotina_diaria.py` (mensagens) ou `.github/workflows/disciplina.yml` (horários)
e salve. As mudanças entram no ar sozinhas.
