"""Descobre o chat do bot do Telegram e grava no firmware/config.json.

    python3 firmware/telegram_chat.py

Antes de rodar:
  1. No Telegram, fale com o @BotFather, mande /newbot e copie o token.
  2. Copie firmware/config.exemplo.json para firmware/config.json e ponha o
     token em "telegram_token".
  3. Mande qualquer mensagem (por exemplo /start) para o seu bot.

O script lista quem falou com o bot, grava o chat mais recente em
"telegram_chat" e manda uma mensagem de teste. O token nunca sai do
config.json, que fica fora do Git.
"""

import json
import os
import subprocess
import sys
import urllib.request

CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")


def api(token, metodo, dados):
    url = "https://api.telegram.org/bot" + token + "/" + metodo
    corpo = json.dumps(dados).encode()
    try:
        pedido = urllib.request.Request(url, data=corpo, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(pedido, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception:
        # alguns Pythons do macOS vêm sem os certificados raiz: o curl do sistema tem
        saida = subprocess.run(
            ["curl", "-sS", "-m", "15", "-H", "Content-Type: application/json", "-d", corpo.decode(), url],
            capture_output=True, text=True,
        )
        if saida.returncode != 0:
            sys.exit("nao consegui falar com o Telegram: " + saida.stderr.strip())
        return json.loads(saida.stdout)


def principal():
    if not os.path.exists(CONFIG):
        sys.exit("crie o firmware/config.json a partir do config.exemplo.json primeiro")
    with open(CONFIG, encoding="utf-8") as f:
        config = json.load(f)
    token = config.get("telegram_token", "")
    if not token or token.startswith("TOKEN_"):
        sys.exit('ponha o token do @BotFather em "telegram_token" no firmware/config.json')

    eu = api(token, "getMe", {})
    if not eu.get("ok"):
        sys.exit("o Telegram recusou o token: " + str(eu.get("description")))
    print("bot: @" + eu["result"]["username"])

    chats = {}
    for u in api(token, "getUpdates", {"limit": 100}).get("result", []):
        m = u.get("message") or {}
        chat = m.get("chat", {})
        if "id" in chat:
            chats[chat["id"]] = chat.get("first_name") or chat.get("title") or "?"
    if not chats:
        sys.exit("ninguem falou com o bot ainda: mande /start para @" + eu["result"]["username"] + " e rode de novo")

    for chat_id, nome in chats.items():
        print("  chat", chat_id, "-", nome)
    chat_id = list(chats)[-1]
    config["telegram_chat"] = str(chat_id)
    with open(CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("gravei telegram_chat =", chat_id, "no config.json")

    r = api(token, "sendMessage", {"chat_id": chat_id, "text": "🛡 AEGIS: bot configurado. Os alertas do abrigo chegam aqui."})
    print("mensagem de teste:", "enviada" if r.get("ok") else r.get("description"))


if __name__ == "__main__":
    principal()
