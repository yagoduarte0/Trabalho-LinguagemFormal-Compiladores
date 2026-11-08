# main.py — o MicroPython roda este arquivo depois do boot.py.
#
# O firmware de verdade é o abrigo.aeg, compilado para abrigo.py e depois
# pré-compilado no Mac para bytecode (abrigo.mpy) pelo wokwi.sh. Compilar as
# ~1200 linhas do abrigo.py no próprio ESP32 tomava a RAM interna de que o
# WiFi, a UART e o I2C precisam, e o chip travava.
import abrigo

abrigo.main()
