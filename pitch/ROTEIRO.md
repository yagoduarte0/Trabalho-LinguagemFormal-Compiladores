# Roteiro do pitch — AEGIS (10 minutos)

A fala de cada cena do `pitch.html`. **[→]** marca onde apertar a seta para a
direita. Com a demonstração do painel e do Telegram (1 min, logo depois da
cena 05), os tempos somam 10 min. Se atrasar, encurte as cenas 07 e 09.

Não precisa decorar palavra por palavra. Decore a **primeira frase** de cada
cena, porque ela puxa o resto, e os **números**, que estão em negrito.

---

## Antes de começar

**O que levar**
- O Mac carregado, com `pitch/pitch.html` aberto no Chrome em tela cheia
  (`Cmd+Ctrl+F`). Ele funciona sem internet, porque os vídeos estão dentro do
  arquivo. Leve uma cópia num pendrive.
- Como plano B, o vídeo `video/saida/aegis-completo.mp4`.
- Se quiser mostrar a placa, leve-a já montada e ligue pelo USB antes de
  começar. Ela roda offline, com os LEDs, o display e o alarme funcionando.
  **Não grave firmware ao vivo**, porque a alimentação pelo USB é o ponto
  fraco da placa.
- O abrigo rodando no Mac para a demonstração do painel e do Telegram (ver
  "Demonstração do painel e do Telegram", logo abaixo). Precisa de internet
  no Mac, porque o bot usa a internet.
- O celular com o Telegram aberto no chat do AegisBot, ou o Telegram para Mac
  aberto, para a banca ver a mensagem no projetor.

## Demonstração do painel e do Telegram

A placa real roda sem Wi‑Fi, porque o USB não aguenta o rádio. Por isso o
painel e o bot são mostrados com o **mesmo `abrigo.aeg`** rodando no Mac, com
os sensores simulados. O firmware, o painel e o bot são os mesmos da placa.

**5 minutos antes** (no Terminal):

```sh
cd ~/Faculdade/Trabalho-LinguagemFormal-Compiladores
./firmware/wokwi.sh pc
```

- Chega no Telegram a mensagem "🛡 AEGIS ligado e vigiando".
- Abra `http://localhost:8080` numa janela do Chrome. O painel fica verde,
  em **NORMAL**.
- Deixe o Terminal e o painel lado a lado e volte para o `pitch.html`.

**Na hora** (depois da cena 05, ~1 min). Troque de janela com `Cmd+Tab`:

1. > Agora o sistema funcionando. É o mesmo programa da placa, rodando aqui
   > com os sensores simulados. Este é o painel web que o ESP32 serve na rede
   > de casa.
2. No Terminal, digite `fumaca` e aperte Enter.
   > Vou simular fumaça. Em uns 2 segundos o painel fica vermelho, em
   > alarme, e o celular recebe o alerta no Telegram.

   Mostre o celular ou o Telegram para Mac com o "🚨 ALARME: FUMACA/GAS".
3. Clique em **Silenciar sirene** no painel.
   > Pelo painel dá para calar a sirene, mas não desarmar: desarmar só com a
   > digital, de propósito.
4. Digite `normal` e aperte Enter. O painel volta ao verde e chega "✅ NORMAL"
   no Telegram.
5. `Cmd+Tab` de volta ao pitch e **[→]**.

Outros eventos que dá para digitar: `chuva`, `deslizamento` (chuva com solo
encharcado), `agua`, `calor`, `ar`, `dedo` (arma ou desarma) e `estranho`
(digital desconhecida). Para encerrar, use `Ctrl+C`.

**Se não tiver internet:** o painel funciona igual, só o Telegram não chega.
Se a rede da faculdade bloquear, ligue o Mac no roteador do celular.

**Versão no Wokwi** (o ESP32 virtual na tela, com LEDs e display): é mais
bonita, mas tem mais peças que podem falhar ao vivo. O passo a passo está em
`docs/demo-wokwi.md` (`./firmware/wokwi.sh demo`, painel em
`http://localhost:8180`).

**Teste no projetor:** abra o `pitch.html`, passe pelas 10 cenas e veja se as
animações rodam. A abertura fica em loop (o radar girando) até você apertar a
seta.

---

## 01 · Abertura (0:30)

> Boa tarde. Eu sou o Yago e vou apresentar o **AEGIS**, um sistema de
> monitoramento para abrigos e casas em área de risco. O nome vem do escudo
> da mitologia grega, e a ideia é essa: proteger quando tudo o mais falha.

**[→]**

## 02 · Sumário executivo (0:45)

> Em uma frase: o AEGIS é **automação residencial de sobrevivência**.
> Sensores ligados a um ESP32 vigiam água, ar, fumaça, temperatura e presença,
> e tudo funciona **sem internet**.
>
> É para os **2,47 milhões de domicílios** em área de risco no Brasil, e
> também para quem mora em sítio ou casa de campo.
>
> O negócio é um kit de **R$ 549** mais uma assinatura de **R$ 29,90** por
> mês. Com margem de **64%** por kit, o ponto de equilíbrio chega com
> **12 kits por mês**.

**[→]**

## 03 · O problema (1:00)

> A automação residencial de hoje resolve **conforto**: acender a luz pelo
> celular, ligar a TV por voz, ajustar o ar sozinho.

**[→]**

> Mas e quando a crise chega? Na enchente, no deslizamento ou no incêndio,
> o conforto não ajuda.

**[→]**

> Ninguém automatizou as perguntas que importam nessa hora: como está o
> nível da caixa d'água? O ar está bom? Começou um incêndio? Tem alguém lá
> fora?

**[→]**

> E não é um problema pequeno: **8,27 milhões de brasileiros** vivem em área
> de risco, segundo o IBGE com o Cemaden. Em 2024 foram mais de **1.600
> desastres** registrados, e o número de desastres cresceu **250%** em
> relação aos anos 90.

**[→]**

## 04 · A solução (1:00)

> A solução é um controlador, o ESP32, que custa uns 60 reais, cercado de
> sensores: presença, nível da água, fumaça, qualidade do ar e temperatura.

**[→]**

> Cada sensor manda a leitura para o controlador, que decide sozinho, ali
> mesmo, se está tudo normal, se é caso de atenção ou se é alarme.

**[→]**

> A diferença para a automação comum é essa. A comum depende da nuvem: sem
> internet, não funciona. O AEGIS processa **tudo localmente**. Se a internet
> cair, ele continua avisando com sirene, luz e display. Quando tem rede, ele
> também manda alerta no Telegram e mostra um painel web.
>
> No protótipo que eu montei, fui além desses cinco: coloquei sensor de
> **chuva** e de **umidade do solo**, que juntos detectam risco de
> **deslizamento**.

**[→] [→]**

## 05 · Como funciona (2:00) — a parte do compilador

Esta é a cena da disciplina. Vá devagar aqui.

> O caminho do dado é este: o sensor lê, o ESP32 coleta, e no meio está o
> que este projeto tem de diferente: uma **linguagem de programação própria**,
> a linguagem AEGIS, e um **compilador** que eu escrevi para ela.

**[→]**

> Por que uma linguagem? Porque as regras de um abrigo precisam ser fáceis
> de ler e de mudar. Quem configura o sistema escreve as regras em AEGIS, e
> o compilador traduz para Python.

**[→]**

> Olhem uma regra em AEGIS. `law` é uma constante. `supply` lê o pino 27 do
> sensor. `checkpoint` é o "se": se tem perigo, `broadcast` liga o alarme no
> pino 5; `fallback` é o "senão", e registra "área limpa".

**[→]**

> E isto é o que o compilador gera, a saída **real**, não um exemplo feito à
> mão. Cada linha do AEGIS vira uma linha de Python. As chaves somem, porque
> o Python usa indentação.
>
> O compilador tem as **três fases** clássicas. A **análise léxica** quebra o
> texto em tokens: são 29 palavras reservadas e 25 símbolos. A **análise
> sintática** é um parser descendente recursivo que confere a gramática e
> monta a árvore sintática, a AST. A **geração de código** percorre essa
> árvore e escreve o Python. Se tem erro, ele aponta a linha e a coluna e
> continua procurando os próximos erros.
>
> E para chegar na placa: o mesmo programa compila para dois alvos. Para o
> **PC**, com sensores simulados, para testar. Para o **ESP32**, onde o
> compilador junta as funções que falam com o hardware de verdade. O Python
> gerado é pré-compilado no computador e gravado na placa pelo USB, com um
> comando só. A placa roda MicroPython, que é Python para microcontrolador.
>
> O programa do abrigo tem **810 linhas** de AEGIS, e o mesmo arquivo rodou
> no simulador, no PC e na placa real **sem nenhuma alteração**.

**Demonstração (1:00):** painel e Telegram, conforme a seção
"Demonstração do painel e do Telegram", lá em cima. Depois volte ao pitch.

**[→]**

## 06 · Mercado (1:00)

> O mercado total é a segurança eletrônica no Brasil: **R$ 14 bilhões**, e
> cresceu 16% em 2024. A automação residencial no Brasil movimenta **US$ 2,96
> bilhões** e cresce quase 28% ao ano.
>
> O nosso mercado atendível são os **2,47 milhões** de domicílios em área de
> risco: **R$ 1,36 bilhão**. E a meta do primeiro ano é conservadora:
> **300 kits**, uns **R$ 210 mil**.

**[→]**

> E o problema só cresce: **88% dos municípios** brasileiros tiveram algum
> desastre climático em 2024. Em 2013 eram 29%.

**[→]**

## 07 · Modelo de negócio (0:45)

> No modelo de negócio, a proposta de valor é uma automação que **protege**,
> e não só dá conforto, e que funciona sem internet.
>
> Os clientes são famílias em área de risco, entusiastas de preparo e donos
> de sítio. A venda é direta, online e em marketplace. As parcerias são com
> distribuidores de eletrônica, lojas de material de construção e a **Defesa
> Civil** municipal.
>
> A receita vem de duas fontes: o kit, na venda, e a assinatura mensal, que dá
> suporte e atualizações.

**[→]**

## 08 · Plano financeiro (1:15)

> Montar um protótipo custa **R$ 235,92** em peças de varejo.

**[→]**

> Comprando em escala, de 100 unidades, o hardware cai para uns **R$ 153**.
> O investimento inicial é de **R$ 24.900**, que cobre protótipos, estoque de
> 50 kits, desenvolvimento, marca e marketing de lançamento.

**[→]**

> Por kit: o custo com montagem fica em **R$ 198** e o preço é **R$ 549**.
> Isso dá **64%** de margem, uns **R$ 350** por kit. A assinatura de R$ 29,90
> deixa **R$ 25,90** de margem por mês.

**[→]**

> O custo fixo é de **R$ 3.900** por mês. Com **12 kits por mês**, a margem
> dos kits já paga o custo fixo: esse é o ponto de equilíbrio.

**[→]**

> E a assinatura acumula. Depois de 12 meses nesse ritmo, só ela já rende uns
> **R$ 3.700 por mês**, quase todo o custo fixo coberto pela receita
> recorrente.

**[→]**

## 09 · Cronograma (0:45)

> O plano leva 12 meses do protótipo ao lançamento. Nos meses 1 e 2, o MVP,
> que é o que eu trouxe hoje: a linguagem, o compilador e o protótipo
> funcionando.

**[→]**

> Nos meses 3 e 4, um piloto em **10 casas** de área de risco. Do 5 ao 8, o
> primeiro lote de **100 kits**. Do 9 ao 12, o lançamento em venda direta e
> marketplace. E no ano 2, a expansão para Defesa Civil e condomínios.

**[→]**

## 10 · Encerramento (0:30)

> O AEGIS é **automação que protege quando tudo o mais falha**. Com
> **R$ 24.900** de investimento, chegamos ao ponto de equilíbrio com
> **12 kits por mês**.

**[→]**

> Obrigado. Fico à disposição para perguntas.

---

## Como funciona a compilação para a placa (para você entender)

O caminho completo, do arquivo que você escreve até a placa:

```
abrigo.aeg ──► aegisc ──► abrigo.py ──► mpy-cross ──► abrigo.mpy ──► mpremote ──► ESP32
(AEGIS)       (léxico,    (Python +     (no Mac)      (bytecode)     (pelo USB)    (MicroPython
              sintático,  runtime                                                  roda o main.py)
              gerador)    do ESP32)
```

1. **Você escreve** as regras em `firmware/abrigo.aeg` (810 linhas).
2. **O compilador** (`compilador/aegisc.js`, em Node) passa pelas três fases:
   - léxico (`lexer.js`): texto → lista de tokens;
   - sintático (`parser.js`): tokens → AST, a árvore do programa;
   - gerador (`gerador.js`): AST → Python.
3. **O alvo**: com `--alvo esp32`, o gerador cola no topo do arquivo um
   *runtime*, que são as funções que falam com o hardware de verdade
   (`machine.Pin` para os pinos, `dht` para o DHT22, o display, o WiFi). Com
   `--alvo simulado`, cola um runtime com sensores falsos para rodar no PC.
   **O programa é o mesmo, só o runtime muda.** Sai o `abrigo.py`, com umas
   1.260 linhas.
4. **A pré-compilação**: o `mpy-cross` transforma o `abrigo.py` em bytecode
   (`abrigo.mpy`) ainda no Mac. Compilar 1.260 linhas dentro do ESP32 gastava
   a memória de que o WiFi e o display precisam, e a placa travava.
5. **A gravação**: o `mpremote` copia para a placa, pelo USB, o `boot.py`, o
   `main.py`, o `abrigo.mpy` e o `config.json` (WiFi e token do bot, fora do
   Git). O `main.py` só faz `import abrigo` e `abrigo.main()`.
6. A placa já tem o **MicroPython** gravado uma vez com o `esptool`. Ele é o
   interpretador que roda o bytecode.

Os passos 2 a 5 são **um comando só**:

```sh
./firmware/wokwi.sh placa
```

Para mostrar só a compilação, sem placa (leva menos de um segundo):

```sh
node compilador/aegisc.js firmware/abrigo.aeg --alvo esp32 -o /tmp/abrigo.py
```

---

## Se perguntarem

**"Por que não escrever direto em Python?"**
> Porque a linguagem fala a língua do problema: `survivor` é uma tarefa que
> vigia um sensor, `checkpoint` é uma condição, `broadcast` liga um alarme.
> E o compilador me deixa trocar o alvo sem mexer no programa: o mesmo
> arquivo roda no PC, no simulador e na placa.

**"Por que gerar Python e não C?"**
> Porque o ESP32 roda MicroPython, e o Python gerado dá para ler e conferir
> linha a linha com o AEGIS. O compilador guarda de qual linha do AEGIS veio
> cada linha de Python, e a interface do compilador mostra essa origem.

**"Que tipo de parser é?"**
> Descendente recursivo, LL(1): uma função para cada regra da gramática, que
> está publicada em EBNF no código. Quando acha um erro, ele se recupera em
> modo pânico: pula até o próximo ponto seguro e continua, para mostrar todos
> os erros de uma vez.

**"Tem análise semântica?"**
> Ainda não. Os tipos (`ration`, `vital`, `status`) ficam registrados na
> árvore, mas não são verificados. É a próxima fase natural.

**"Como os sensores rodam ao mesmo tempo?"**
> Cada sensor tem um `survivor`, que vira uma função. O laço principal chama
> todos a cada **500 ms**, um depois do outro, e depois decide o estado e
> aciona as saídas. Como nenhum deles bloqueia, na prática todos são
> vigiados ao mesmo tempo.

**"Como você testou?"**
> **84 testes** no compilador, cobrindo as três fases, e **42 cenários** do
> firmware rodando no PC, como fumaça, chuva com solo encharcado
> (deslizamento), digital desconhecida e comandos do Telegram. Depois, no simulador Wokwi, e por fim na placa real.

**"O WiFi e o Telegram funcionam na placa?"**
> No simulador e no PC, sim: painel e bot funcionando. Na placa, alimentada
> só pelo USB do computador, o pico de corrente do rádio do WiFi derruba a
> tensão e ela reinicia. O mesmo vale para os sensores de gás e o relé. A
> solução é uma fonte própria, que está nos próximos passos. Sem rede, o
> abrigo continua funcionando com sirene, LEDs e display, e esse é justamente
> o ponto do projeto.

**"Esses números de mercado vêm de onde?"**
> Estão em `pitch/aegis/data.py`, cada um com a fonte ao lado: IBGE e
> Cemaden para a população em risco, S2iD para o aumento de desastres, CNM
> para os municípios, ABESE para segurança eletrônica e Grand View Research
> para automação residencial.
