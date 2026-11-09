# Vídeo de demonstração do AEGIS — roteiro

Duração-alvo: **6 minutos**. O Yago grava a narração e as cenas; a edição junta tudo.

Cada bloco abaixo tem três partes:

- **Narração**: o texto para ler. Grave **um arquivo de áudio por bloco** (ex.: `04b.m4a`).
- **Cena**: o que gravar na tela, no celular ou na câmera. Também **um arquivo por cena** (ex.: `04b.mov`).
- **Duração**: tempo aproximado da narração. A cena pode ser mais longa; a edição corta.

A narração manda no ritmo: a edição encaixa a cena embaixo do áudio. Então grave as cenas com
calma e com folga (2 a 3 s parado antes e depois de cada ação).

---

## Antes de gravar

### Narração

- Lugar silencioso, sem ventilador nem ar-condicionado. Celular a um palmo da boca, um pouco de lado.
- App **Gravador** (iPhone) ou **Gravador de voz** (Android). Um arquivo por bloco, com o nome do
  bloco (`01.m4a`, `02.m4a`, `04b.m4a`...).
- Ritmo de conversa, sem pressa. Se errar, **pare, respire e repita a frase inteira**, sem apagar.
  A edição corta o erro.
- Deixe 1 s de silêncio no começo e no fim de cada arquivo.
- Os números estão escritos por extenso para facilitar a leitura.

### Tela do Mac

- Ative o **Não perturbe** (Central de Controle) para nenhuma notificação aparecer.
- Grave com **Cmd + Shift + 5** → *Gravar a tela inteira* (ou *Gravar parte selecionada*,
  mantendo a proporção 16:9). Para parar, clique no ícone de parar na barra de menus.
- Feche abas e janelas que não fazem parte da cena. Aumente a fonte do VS Code e do Terminal
  (**Cmd +** duas ou três vezes) para o texto ser legível no vídeo.
- Mova o mouse devagar. Quando for mostrar algo, pare o mouse em cima e espere 2 s.
- Salve como `NN.mov`, com o número da cena.

### Celular

- **Telegram:** grave a tela do celular (iPhone: Central de Controle → *Gravação de Tela*).
- **Placa real:** filme na **horizontal**, em 1080p, com a câmera apoiada (pilha de livros ou
  suporte) e boa luz. Nada de zoom digital: aproxime o celular.

### Onde salvar

Tudo dentro de `video/` na raiz do repositório. Essa pasta fica **fora do Git**.

```
video/
  narracao/   01.m4a  02.m4a  03a.m4a ...
  cenas/      01.mov  02.mov  03a.mov ... (e os vídeos do celular)
  saida/      (o vídeo final, gerado na edição)
```

### Deixe pronto antes de começar

```sh
cd ~/Faculdade/Trabalho-LinguagemFormal-Compiladores
node compilador/testes.js          # tem que dar 84/84
python3 firmware/cenarios.py       # tem que dar 42/42
```

- **Wokwi:** VS Code com `firmware/diagram.json` aberto, a aba do diagrama visível, a simulação
  rodando e o firmware enviado (`./firmware/wokwi.sh enviar`). Gire os potenciômetros de **chuva e
  solo até o fim** (seco), para começar em NORMAL.
- **Navegador:** `http://localhost:8180` (painel do Wokwi) e `compilador/index.html` (interface do
  compilador), cada um numa aba.
- **Celular:** conversa com o **@Aegis_IoT_bot** aberta.

---

## 1. Abertura — o problema (≈ 35 s)

**Narração (`01.m4a`):**

> Mais de oito milhões de brasileiros vivem em áreas de risco de desastre, e só em dois mil e vinte
> e quatro o país registrou mais de mil e seiscentos desastres. A automação residencial que existe
> hoje cuida do conforto e depende da internet, justamente o que falha numa emergência. Eu sou o
> Yago, e este é o AEGIS: um sistema de proteção para abrigos residenciais que funciona sem
> internet e que é programado numa linguagem que eu criei, com um compilador próprio.

**Cena (`01.mov`):** abra `pitch/pitch.html` no navegador, em tela cheia, e deixe passar a cena de
abertura e a do problema (dados de risco). Se preferir, grave a tela de abertura do OLED no Wokwi
(o escudo do AEGIS e "protecao offline").

---

## 2. A linguagem AEGIS (≈ 50 s)

**Narração (`02.m4a`):**

> A linguagem também se chama AEGIS, e usa um vocabulário de sobrevivência. Um programa começa com
> scavenge, que traz os módulos do hardware. Constantes são law, e variáveis são supply. Cada
> sensor ganha um survivor, uma sentinela que lê o valor e classifica o risco. As decisões são
> checkpoint e fallback, os laços são watch e patrol, e as funções são mission. O programa
> principal fica no chronicle. Este é o firmware completo do abrigo: cerca de oitocentas linhas,
> escritas inteiramente em AEGIS.

**Cena (`02.mov`):** VS Code com `firmware/abrigo.aeg`. Role devagar, parando 2 a 3 s em cada
trecho, na ordem da narração:

1. o topo, com os `scavenge`;
2. as `law` dos pinos (`law PINO_PIR = 27`...);
3. o `survivor sentinela_fumaca`;
4. a `mission avaliar()`, com a sequência de `checkpoint`;
5. o `chronicle` no fim do arquivo, com o `watch`.

---

## 3. O compilador (≈ 80 s)

### 3a. Léxico e sintático

**Narração (`03a.m4a`):**

> O compilador foi escrito em JavaScript, sem nenhuma dependência, e tem três fases. A análise
> léxica usa expressões regulares e a regra do maximal munch para quebrar o código em tokens. São
> vinte e nove palavras reservadas e vinte e cinco símbolos, e cada token guarda a sua linha e a
> sua coluna. A análise sintática é descendente recursiva, sobre uma gramática LL(1): cada regra
> vira uma função, e o resultado é uma árvore sintática abstrata com vinte e seis tipos de nó.

**Cena (`03a.mov`):** navegador com `compilador/index.html`. No seletor de exemplos, escolha
**"Sentinela de perímetro (exemplo de referência)"**, compile e mostre:

1. a aba **Tokens** (a tabela com tipo, lexema, linha e coluna) — role um pouco;
2. a aba **AST** (a árvore) — role um pouco.

### 3b. Erros

**Narração (`03b.m4a`):**

> Se o código tiver erros, o compilador não para no primeiro. Ele se recupera em modo pânico e
> mostra todos de uma vez, cada um com a linha e a coluna.

**Cena (`03b.mov`):** no mesmo `index.html`, escolha o exemplo **"Erros propositais (sintático)"**
no seletor de exemplos, compile e mostre a lista de erros, cada um com linha e coluna. (Se quiser,
mostre também o **"Erros propositais (léxico)"**.)

### 3c. Geração de código e testes

**Narração (`03c.m4a`):**

> Por fim, o gerador percorre a árvore e escreve Python. São dois alvos: um simulado, que roda no
> computador, e outro em MicroPython, para o ESP32. O programa traduzido é igual nos dois; só muda a
> camada que fala com o hardware. Tudo isso é verificado por oitenta e quatro testes automatizados.

**Cena (`03c.mov`):**

1. volte ao exemplo da sentinela de perímetro e abra a aba **Python** do `index.html`; pare o mouse
   numa linha e espere aparecer a dica "gerada da linha N do fonte";
2. no Terminal: `node compilador/testes.js` — deixe aparecer o `84/84 testes passaram.`

---

## 4. Do código à placa (≈ 25 s)

**Narração (`04.m4a`):**

> Para gravar o abrigo, um único comando compila o AEGIS para MicroPython, pré-compila o resultado
> e envia para a placa. Este é o Wokwi, um simulador de ESP32, montado com as mesmas ligações do
> protótipo real.

**Cena (`04.mov`):** Terminal ao lado do VS Code:

```sh
./firmware/wokwi.sh enviar
```

Em seguida mostre o diagrama do Wokwi e o terminal da simulação imprimindo `[boot] WiFi conectado`,
`painel web: http://...` e `bot do Telegram ativo`. O OLED mostra o escudo e depois o IP.

---

## 5. Demonstração no Wokwi (≈ 2 min)

### 5a. Os sensores

**Narração (`05a.m4a`):**

> O ESP32 lê sete sensores: presença, nível da água, fumaça, qualidade do ar, temperatura, chuva e
> umidade do solo. A cada meio segundo, o pior risco decide o estado do abrigo: normal, atenção ou
> alarme.

**Cena (`05a.mov`):** diagrama do Wokwi em NORMAL (LED verde). Passe o mouse devagar por cada
sensor; espere o OLED trocar entre as três páginas de leituras.

### 5b. Fumaça

**Narração (`05b.m4a`):**

> Vou simular fumaça. A leitura sobe acima da base de ar limpo que o firmware aprendeu ao ligar, e o
> abrigo entra em alarme: LED vermelho, sirene de dois tons e o exaustor ligado pelo relé.

**Cena (`05b.mov`):** gire o potenciômetro do **MQ-2 (fumaça)** até o máximo. Mostre o LED
vermelho, o relé, o OLED piscando "ALARME / FUMACA/GAS" e o terminal com `estado: ALARME`.

### 5c. Painel web

**Narração (`05c.m4a`):**

> Com WiFi, o próprio ESP32 serve este painel na rede de casa, sem nuvem nenhuma. Ele mostra o
> estado e todas as leituras, e se atualiza sozinho.

**Cena (`05c.mov`):** navegador em `http://localhost:8180` com o painel vermelho em ALARME. Para
ficar com cara de celular, abra o modo responsivo (Safari: *Desenvolvedor → Entrar no Modo de
Design Responsivo*; Chrome: F12 → ícone do celular) ou só estreite a janela.

### 5d. Telegram

**Narração (`05d.m4a`):**

> E o dono recebe o alerta no celular, pelo Telegram. Pelo bot, eu posso pedir o status ou
> silenciar a sirene. O alarme continua; só o som é calado. Por segurança, nenhum canal remoto
> desarma o abrigo: para isso, é preciso a digital.

**Cena (`05d-celular.mp4`, gravação da tela do celular):**

1. a mensagem `🚨 ALARME: FUMACA/GAS` chegando;
2. mande `/status` e espere a resposta (no Wokwi leva até uns 20 s; a edição corta a espera);
3. mande `/silenciar` e espere o `🔇 Sirene silenciada pelo Telegram...`.

Depois volte o potenciômetro do MQ-2 para o mínimo: chega `✅ NORMAL`.

### 5e. Deslizamento

**Narração (`05e.m4a`):**

> Chuva com o solo encharcado é o que antecede um deslizamento de terra. Os dois sensores juntos
> disparam esse alarme, e ele só desliga quando o solo seca, mesmo que a chuva já tenha parado.

**Cena (`05e.mov`):** gire o potenciômetro da **chuva** para o mínimo (ATENÇÃO "chovendo",
LED amarelo), depois o do **solo** para o mínimo (ALARME "DESLIZAMENTO"). Volte a chuva para o
máximo e mostre que o alarme continua. Por fim, volte o solo: NORMAL.

### 5f. Digital

**Narração (`05f.m4a`):**

> A digital arma e desarma a vigilância. Armado, qualquer presença abre um tempo para a pessoa se
> identificar; sem a digital, vira alarme de intruso. No simulador, o Touch ID do Mac faz o papel
> do leitor biométrico.

**Cena (`05f.mov`):** no Terminal, `./firmware/wokwi.sh dedo` e encoste o dedo no Touch ID. Mostre
o OLED com o cadeado e "saia 30s", e o Telegram com `🔒 Abrigo armado pela digital 1`. Rode
`./firmware/wokwi.sh dedo` de novo para desarmar.

---

## 6. O protótipo real (≈ 45 s)

**Narração (`06.m4a`):**

> E este é o protótipo físico. O mesmo programa, sem nenhuma alteração, roda no ESP32 de verdade.
> O display mostra o estado e as leituras, os sensores de presença e de temperatura respondem, e o
> painel abre no celular pelo endereço da placa.

**Cena (`06.mp4`, câmera do celular, horizontal):**

1. plano aberto da protoboard com o ESP32 ligado;
2. close no OLED trocando as páginas;
3. passe a mão na frente do PIR (o OLED mostra "PIR: movimento");
4. segure o DHT22 entre os dedos alguns segundos (a temperatura sobe);
5. o celular, na rede de casa, abrindo `http://<ip do OLED>/`.

Antes: grave a placa com `./firmware/wokwi.sh placa` (WiFi de casa no `firmware/config.json`).
**Se a placa não colaborar a tempo**, grave a montagem desligada e o OLED ligado só pelo USB; a
narração continua valendo (troque a última frase por "e a mesma montagem está sendo finalizada").

---

## 7. Testes e encerramento (≈ 40 s)

**Narração (`07.m4a`):**

> A lógica do firmware é verificada por quarenta e um cenários que rodam no computador, incluindo o
> servidor do painel e o bot. Com o AEGIS, as regras de emergência de uma casa ficam legíveis como
> um diário de operação, e o mesmo código roda no simulador e na placa. Como próximos passos, ficam
> uma fase de análise semântica, para verificar os tipos, e a montagem completa do hardware.
> Obrigado.

**Cena (`07.mov`):** Terminal com `python3 firmware/cenarios.py`, deixando a lista de `OK` rolar
até `41/41 cenarios passaram.`. Para fechar, a tela de abertura do OLED ou a cena final do
`pitch/pitch.html`.

---

## Checklist de arquivos para a edição

| Bloco | Narração | Cena |
|---|---|---|
| 1 | `01.m4a` | `01.mov` |
| 2 | `02.m4a` | `02.mov` |
| 3 | `03a.m4a` `03b.m4a` `03c.m4a` | `03a.mov` `03b.mov` `03c.mov` |
| 4 | `04.m4a` | `04.mov` |
| 5 | `05a.m4a` ... `05f.m4a` | `05a.mov` `05b.mov` `05c.mov` `05d-celular.mp4` `05e.mov` `05f.mov` |
| 6 | `06.m4a` | `06.mp4` |
| 7 | `07.m4a` | `07.mov` |

## Para a edição

- Saída: `video/saida/aegis-demonstracao.mp4`, 1920×1080, 30 fps, H.264 + AAC.
- Ordem e encaixe: a narração de cada bloco por cima da cena com o mesmo número; corte esperas
  (como a resposta do bot) e acelere rolagens longas.
- Áudio: tirar ruído de fundo, normalizar a voz (em torno de −16 LUFS), cortar erros e respirações
  longas; trilha instrumental baixa é opcional.
- Títulos curtos no canto inferior em cada bloco, na identidade do AEGIS: fundo `#0A0D0A`, cáqui
  `#C8B88A`, verde radar `#A8D04A`, creme `#EDE4CC`, fonte display Impact. Ex.: "A linguagem",
  "Análise léxica", "Painel web", "Bot do Telegram", "Protótipo real".
- Legendas queimadas no vídeo, a partir do texto deste roteiro (o professor pode assistir sem som).
- Ferramenta: `ffmpeg` (não está instalado no Mac: `brew install ffmpeg`).
