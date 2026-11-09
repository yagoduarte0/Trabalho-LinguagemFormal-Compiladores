# Demonstração ao vivo no Wokwi (sem a placa)

Roteiro para mostrar o AEGIS funcionando na aula, só com o Mac: o simulador Wokwi roda o
mesmo firmware da placa, o painel web abre no navegador e o bot do Telegram avisa no celular.
Cerca de 5 minutos.

## Antes da aula (uma vez)

- Internet no Mac (o Wokwi e o Telegram precisam).
- `firmware/config.json` com o token do bot (já está no Mac; fica fora do Git).
- Teste completo em casa, seguindo "Na hora" abaixo.

## Na hora

1. VS Code aberto no repositório, com `firmware/diagram.json` aberto e **a aba do diagrama
   visível** (o Wokwi pausa a simulação quando a aba fica escondida).
2. Aperte **play (▶)** no diagrama.
3. No Terminal:
   ```sh
   cd ~/Faculdade/Trabalho-LinguagemFormal-Compiladores
   ./firmware/wokwi.sh demo
   ```
   Ele espera o simulador, compila o `abrigo.aeg`, envia o firmware e abre
   `http://localhost:8180` quando o painel responder (uns 30 s). O celular recebe
   "🛡 AEGIS ligado e vigiando".
4. Deixe a tela dividida: **Wokwi à esquerda, painel à direita**. Celular com o Telegram à mão.
5. **Espere 20 s** depois de ligar antes de mexer no gás: é o aquecimento dos MQ, em que o
   firmware aprende a base de ar limpo (o painel mostra "aquecendo").

Se o `demo` disser que o Wokwi não respondeu: aba do diagrama visível, stop (■), play (▶) e
rode de novo.

## O que mostrar (clique na peça do Wokwi para abrir o controle dela)

| # | No Wokwi | O que acontece |
|---|---|---|
| 1 | nada | LED verde, OLED alternando as 3 páginas, painel em **NORMAL** |
| 2 | **DHT22** → temperatura em **45 °C** | LED amarelo, OLED e painel em **ATENÇÃO: calor**, mensagem no Telegram. Volte para 25 °C |
| 3 | **MQ-2** (sensor de gás) → arraste o ppm para o máximo | **ALARME: FUMAÇA/GÁS**: LED vermelho, sirene de dois tons, LED azul do exaustor (relé), alerta no Telegram |
| 4 | botão **silenciar** (vermelho) ou "Silenciar sirene" no painel | a sirene cala por 60 s; o LED vermelho e o alarme continuam |
| 5 | MQ-2 de volta ao mínimo | volta a NORMAL; o exaustor segue ligado mais 30 s e depois desliga |
| 6 | **chuva** (potenciômetro do telhado) girado para a esquerda | **ATENÇÃO: chovendo** |
| 7 | **solo** (potenciômetro do quintal) todo para a esquerda, com a chuva ainda alta | **ALARME: DESLIZAMENTO**. Baixe a chuva: o alarme continua até o solo secar (gire o solo de volta para a direita) |
| 8 | **HC-SR04** → distância abaixo de **20 cm** | **ALARME: ENCHENTE**. Volte para 100 cm |
| 9 | Telegram: mande `/status`, depois `/ajuda` | o bot responde com as leituras e a lista de comandos (até ~20 s no Wokwi) |
| 10 | Terminal: `./firmware/wokwi.sh dedo` e o dedo no Touch ID | **armado pela digital** (bipe, mensagem 🔒). Depois de 30 s, clique no **PIR** → ATENÇÃO "use a digital"; espere 15 s → **ALARME: INTRUSO**. `./firmware/wokwi.sh dedo` de novo desarma |

Frases que ajudam a explicar:
- "O que está rodando no simulador é o Python que o **nosso compilador** gerou do `abrigo.aeg`;
  é o mesmo arquivo que vai para a placa."
- "O painel é servido **pelo próprio ESP32**, na rede local: não tem nuvem no meio."
- "Nenhum canal remoto desarma o abrigo: o Telegram e o painel só calam a sirene; desarmar
  exige a digital."

## Plano B: sem Wokwi (sem internet)

```sh
./firmware/wokwi.sh pc        # o mesmo firmware no Mac, painel em http://localhost:8080
```
Digite no terminal os eventos: `fumaca`, `calor`, `chuva`, `deslizamento`, `agua`, `ar`,
`dedo`, `estranho`, `intruso`, `botao`, `normal`. O painel e (com internet) o Telegram reagem igual.

## Se algo der errado

| Sintoma | O que fazer |
|---|---|
| `could not enter raw repl` / Wokwi não responde | aba do diagrama visível, stop (■), play (▶), `./firmware/wokwi.sh demo` |
| painel não abre | espere o WiFi no terminal do Wokwi; recarregue `http://localhost:8180` |
| Telegram não responde | internet do Mac; o bot lê comandos a cada 15 s (no Wokwi cada pedido leva ~5 s) |
| gás não dispara | esperou os 20 s de aquecimento? Volte o ppm ao mínimo, espere, e suba de novo |
