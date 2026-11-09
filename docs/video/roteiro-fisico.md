# Protótipo real: roteiro de gravação (câmera + animação por cima)

Vídeo próprio, de cerca de 1 min 30 s. Também pode substituir a cena 06 do vídeo animado, que hoje mostra uma bancada desenhada.

**Como funciona:**

1. Você filma cada tomada **sem falar**, com o som ambiente ligado (o buzzer faz parte da demonstração).
2. Depois grava **uma narração por tomada**, como antes, lendo o texto abaixo enquanto assiste à tomada.
3. Eu limpo o áudio, transcrevo palavra a palavra e animo por cima do vídeo: etiquetas presas em cada peça, barra de estado, o trecho do código AEGIS que disparou, as mensagens do Telegram entrando e o OLED ampliado.

Tomadas marcadas com ★ são obrigatórias. As outras só entram **se a peça estiver ligada** na placa; se não estiver, pule e o vídeo fica mais curto.

---

## Antes de gravar

### Placa
1. Coloque o WiFi de casa no `firmware/config.json` (abra no editor; não mande o arquivo para ninguém) e grave o firmware:
   ```sh
   cd ~/Faculdade/Trabalho-LinguagemFormal-Compiladores
   ./firmware/wokwi.sh placa
   firmware/.venv/bin/mpremote connect auto repl   # confira "[AEGIS] bot do Telegram ativo"; sair: Ctrl+]
   ```
2. Ligue a placa **3 minutos antes** das tomadas de fumaça. Os MQ precisam aquecer, e até lá o painel mostra "aquecendo".
3. Sem os sensores de chuva e solo ligados, prenda os pinos **VP e VN no 3V3**. Sem isso, o firmware acusa deslizamento falso.
4. Deixe o **Telegram aberto no celular**, na conversa com o @Aegis_IoT_bot. A mensagem "AEGIS ligado e vigiando" traz o link do painel.

### Materiais
- Algodão com **álcool** (para o MQ-2). **Sem chama**: nada de isqueiro aceso perto da protoboard.
- Copo d'água e conta-gotas ou borrifador (chuva e solo).
- Secador de cabelo (opcional, para o calor).

### Câmera
- Celular na **horizontal**, em 1080p a 30 fps (ou 4K), **apoiado**: tripé ou pilha de livros. Enquadre de cima ou a 45°, com a protoboard inteira no quadro.
- **Trave o foco e a exposição**: toque e segure na tela até aparecer "Bloqueio AE/AF". Depois puxe a exposição um pouco para baixo, senão o OLED e os LEDs estouram e ficam ilegíveis.
- Luz de lado, sem reflexo no OLED.

### Regras de cada tomada
- **A câmera não se mexe durante a tomada.** As etiquetas animadas ficam presas na posição de cada peça; se o quadro andar, elas descolam.
- Fique **2 s parado** no começo e no fim.
- Um arquivo por tomada, com o nome dela (`F2.mov`, `F3.mov`…). Errou? Regrave a tomada inteira.
- Mãos entram e saem pelo lado, sem cobrir o OLED.

---

## Tomadas

### F1 · Você na câmera (opcional, fala ao vivo) · ~10 s
**Plano:** você e a placa no quadro.
**Fala (ao vivo):**
> Agora o AEGIS fora do simulador: o protótipo montado, rodando o mesmo programa.

**Animação:** o título "Protótipo real" entra embaixo, na identidade do AEGIS.

---

### F2 ★ · A placa ligando · ~15 s
**Plano:** geral, de cima, protoboard inteira.
**Ação:** com a placa desligada, ligue o cabo. Espere a tela de abertura do OLED e o LED verde acender.
**Narração (`F2.m4a`):**
> Este é o protótipo físico do AEGIS. É o mesmo programa que rodou no simulador, gerado pelo nosso compilador, agora num ESP32 de verdade.

**Animação:** etiquetas surgem uma a uma em cada peça (ESP32, OLED, DHT22, PIR, buzzer, LEDs, botão e o que mais estiver ligado), com uma linha fina até a peça. Uma barra de estado no topo acende em **NORMAL**, verde, junto com o LED.

---

### F3 ★ · O display · ~12 s
**Plano:** close no OLED. Aproxime o celular em vez de usar zoom.
**Ação:** nada; deixe o display trocar de página pelo menos três vezes (troca a cada 3 s).
**Narração (`F3.m4a`):**
> O display mostra o estado do abrigo e alterna entre três páginas de leituras: clima, gases, e água e presença.

**Animação:** o nome de cada página aparece ao lado quando ela entra, e um cartão mostra o trecho `mission atualizar_tela` do código.

---

### F4 ★ · Temperatura · ~15 s
**Plano:** médio, DHT22 e OLED no quadro.
**Ação, versão A:** segure o DHT22 entre os dedos por uns 10 s. A temperatura sobe alguns graus.
**Ação, versão B:** secador a uns 30 cm, por poucos segundos, até o LED amarelo acender (passa de 40 °C). Não encoste o secador.
**Narração (`F4.m4a`):**
> A temperatura e a umidade vêm do DHT22. Acima de quarenta graus, o abrigo entra em atenção.

**Animação:** um contador de temperatura sobe junto com o OLED, e o cartão do código mostra `law TEMP_ATENCAO = 40.0`. Na versão B, a barra de estado vira **ATENÇÃO**, amarela.

---

### F5 ★ · Presença · ~10 s
**Plano:** médio, PIR e OLED no quadro (o OLED precisa estar na página "água e presença"; espere ela voltar).
**Ação:** passe a mão devagar na frente do PIR. O OLED mostra "PIR: movimento".
**Narração (`F5.m4a`):**
> O sensor de presença detecta movimento. Com o abrigo desarmado, ele só aparece no display; armado, vira alarme de intruso.

**Animação:** ondas saindo do PIR e o cone de detecção desenhado sobre a mão.

---

### F6 · Digital e intruso (se o AS608 estiver ligado) · ~25 s
**Plano:** geral.
**Ação:**
1. Encoste o dedo cadastrado no leitor. Ouve-se um bipe e o abrigo fica armado.
2. Espere os 30 s do tempo de saída (a edição corta a espera).
3. Passe a mão no PIR. O LED amarelo acende ("use a digital").
4. Espere 15 s **sem** a digital. Dispara o ALARME por intruso.
5. Encoste o dedo de novo para desarmar.

**Narração (`F6.m4a`):**
> O leitor de digital arma o abrigo. Depois do tempo de saída, uma presença abre quinze segundos para a digital; sem ela, é alarme de intruso. Só a digital desarma.

**Animação:** uma linha do tempo com as faixas "saída 30 s" e "entrada 15 s" correndo; os balões do Telegram 🔒 e 🔓 entram no canto.

---

### F7 · Fumaça (se o MQ-2 estiver ligado) · ~25 s
**Plano:** geral, com o MQ-2, os LEDs e o OLED no quadro.
**Ação:**
1. Aproxime o algodão com álcool do MQ-2, a 1 ou 2 cm, sem encostar.
2. Espere o ALARME: LED vermelho, buzzer, OLED em "FUMACA/GAS" e o relé estalando, se estiver ligado.
3. Tire o algodão e aperte o **botão**. O buzzer cala; o LED vermelho continua.

**Narração (`F7.m4a`):**
> O sensor de gás aprende o nível do ar limpo ao ligar. Quando a leitura passa dessa base, dispara o alarme: sirene, luz vermelha, exaustor e aviso no Telegram. O botão cala a sirene, mas o alarme continua até o ar limpar.

**Animação:**
- Partículas subindo do algodão.
- Uma barra da leitura cruzando a linha "base + margem".
- Barra de estado em **ALARME**, vermelha, piscando.
- Cartão com `checkpoint (media_fumaca >= base_fumaca + MARGEM_FUMACA)`.
- Balão do Telegram com o alerta e, ao apertar o botão, "🔇 silenciado por 60 s".

---

### F8 · Chuva e deslizamento (se chuva e solo estiverem ligados) · ~20 s
**Plano:** geral, com os dois sensores no quadro.
**Ação:**
1. Pingue água na placa de chuva. O LED amarelo acende ("chovendo").
2. Mergulhe o sensor de solo no copo d'água até a marca. Dispara o ALARME de deslizamento.

**Narração (`F8.m4a`):**
> Chuva sozinha é atenção. Chuva com o solo encharcado é o que antecede um deslizamento, e aí o abrigo dispara o alarme.

**Animação:** gotas caindo, barras de % de chuva e de solo subindo, e o cartão com a regra `chovendo && solo_pct >= SOLO_ALARME`.

---

### F9 ★ · O celular (gravação de tela, não câmera) · ~20 s
**Como:** no iPhone, Central de Controle → Gravação de Tela.
**Ação:**
1. Abra a conversa do bot e role devagar pelos alertas que chegaram durante as tomadas.
2. Mande `/status` e espere a resposta (a edição corta a espera).
3. Toque no link do painel da mensagem "AEGIS ligado" e deixe o painel carregar.

**Narração (`F9.m4a`):**
> Na rede de casa, o dono acompanha tudo pelo celular: o bot do Telegram avisa cada mudança, e o painel web é servido pelo próprio ESP32, sem nuvem.

**Animação:** a gravação do celular entra dentro de uma moldura de celular, ao lado do vídeo da placa, com uma etiqueta "servido pelo ESP32".

---

### F10 ★ · Encerramento · ~8 s
**Plano:** geral, de volta ao NORMAL (LED verde).
**Ação:** nada; só a placa funcionando.
**Narração (`F10.m4a`):**
> Do simulador para a placa, o mesmo código, sem nenhuma alteração. Esse é o AEGIS.

**Animação:** as etiquetas saem, o logo do AEGIS entra e a tela escurece.

---

## Onde salvar
Tudo em `video/fisico/` (fora do Git), com os nomes das tomadas:

```
video/fisico/F2.mov  F2.m4a
video/fisico/F3.mov  F3.m4a
...
video/fisico/F9.mov  F9.m4a     (F9.mov = gravação de tela do iPhone)
```

Se gravar no iPhone, mande por AirDrop (vai para Downloads) e me avise; eu renomeio e organizo.

## Checklist
| Tomada | Obrigatória | Vídeo | Narração |
|---|---|---|---|
| F1 você na câmera | não | `F1.mov` (fala ao vivo) | — |
| F2 placa ligando | ★ | `F2.mov` | `F2.m4a` |
| F3 display | ★ | `F3.mov` | `F3.m4a` |
| F4 temperatura | ★ | `F4.mov` | `F4.m4a` |
| F5 presença | ★ | `F5.mov` | `F5.m4a` |
| F6 digital | se AS608 | `F6.mov` | `F6.m4a` |
| F7 fumaça | se MQ-2 | `F7.mov` | `F7.m4a` |
| F8 chuva e solo | se ligados | `F8.mov` | `F8.m4a` |
| F9 celular | ★ | `F9.mov` (tela) | `F9.m4a` |
| F10 encerramento | ★ | `F10.mov` | `F10.m4a` |
