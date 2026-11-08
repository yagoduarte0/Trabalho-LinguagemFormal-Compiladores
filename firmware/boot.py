# boot.py — o MicroPython roda este arquivo antes do main.py.
#
# Liga o WiFi aqui, com a memória ainda livre. O main.py gerado é grande, e
# compilá-lo faz o MicroPython ocupar a RAM interna de que o driver do WiFi
# precisa: ligado depois, o WiFi falha com "Wifi Out of Memory". O firmware
# só reaproveita a conexão (wifi.connect vê que já está conectado).
#
# Lê o mesmo config.json do firmware; sem ele, usa a rede aberta do Wokwi,
# como os padrões do abrigo.aeg (USAR_REDE, WIFI_SSID, WIFI_SENHA).
import gc

try:
    import json
    import network
    import time

    try:
        with open("config.json") as f:
            config = json.load(f)
    except (OSError, ValueError):
        config = {}
    if config.get("usar_rede", True):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        ssid = config.get("wifi_ssid", "Wokwi-GUEST")
        if ssid and not wlan.isconnected():
            print("[boot] conectando ao WiFi", ssid)
            wlan.connect(ssid, config.get("wifi_senha", ""))
            for _ in range(100):                 # até 10 s
                if wlan.isconnected():
                    break
                time.sleep_ms(100)
        print("[boot] WiFi", "conectado" if wlan.isconnected() else "sem conexao")
        del wlan
    del config
except Exception as erro:
    print("[boot] WiFi falhou:", erro)

gc.collect()
