// Página do painel web do abrigo, servida pelo próprio ESP32 na rede local
// (módulo "web" dos runtimes). Fica num arquivo separado só para facilitar a
// edição: o gerador embute este texto no Python gerado como uma string.
//
// Restrições, porque o texto vai parar dentro de um template do gerador e de
// uma string Python: sem crases, sem "${" e sem barras invertidas. A página
// não carrega nada de fora (funciona sem internet) e pede /dados a cada 2 s.
var PAINEL_HTML = `<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AEGIS - Abrigo</title>
<style>
:root{--fundo:#0A0D0A;--cartao:#131813;--linha:#2A322A;--caqui:#C8B88A;--radar:#A8D04A;--creme:#EDE4CC;--ambar:#E8A33C;--alerta:#E5533D;--apagado:#7D8574}
*{box-sizing:border-box;margin:0}
body{background:var(--fundo);color:var(--creme);font:15px/1.4 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;padding:16px;max-width:760px;margin:0 auto}
header{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}
h1{font:30px Impact,"Arial Narrow",sans-serif;letter-spacing:4px;color:var(--caqui)}
.sub{color:var(--apagado);font-size:11px;letter-spacing:1px;text-transform:uppercase}
#con{font-size:12px;color:var(--apagado);white-space:nowrap}
#con:before{content:"";display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--alerta);margin-right:6px}
#con.on:before{background:var(--radar)}
#estado{border-radius:12px;padding:18px;margin-bottom:12px;border:1px solid var(--linha);background:var(--cartao)}
#nome{display:block;font:38px Impact,"Arial Narrow",sans-serif;letter-spacing:3px;color:var(--radar)}
#motivo{font-size:18px}
#estado.s1{border-color:var(--ambar)}#estado.s1 #nome{color:var(--ambar)}
#estado.s2{border-color:var(--alerta);animation:pisca 1s steps(2) infinite}#estado.s2 #nome{color:var(--alerta)}
@keyframes pisca{50%{background:#3A1410}}
.grade{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px}
.c{background:var(--cartao);border:1px solid var(--linha);border-radius:12px;padding:12px}
.c small{color:var(--apagado);font-size:11px;text-transform:uppercase;letter-spacing:1px}
.c div{font-size:24px;font-weight:600;margin-top:2px;font-variant-numeric:tabular-nums}
.barra{height:6px;background:var(--linha);border-radius:3px;margin-top:8px;overflow:hidden}
.barra i{display:block;height:100%;width:0;background:var(--radar);transition:width .4s}
.barra i.alto{background:var(--alerta)}
.tags{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0}
.tag{border:1px solid var(--linha);border-radius:999px;padding:4px 12px;font-size:13px;color:var(--apagado)}
.tag.on{color:var(--fundo);background:var(--caqui);border-color:var(--caqui)}
.tag.alerta{color:#fff;background:var(--alerta);border-color:var(--alerta)}
button{width:100%;padding:15px;border-radius:12px;border:0;background:var(--alerta);color:#fff;font:600 16px system-ui,sans-serif;cursor:pointer}
button:disabled{background:var(--linha);color:var(--apagado);cursor:default}
footer{margin-top:14px;color:var(--apagado);font-size:12px;text-align:center}
</style></head><body>
<header><div><h1>AEGIS</h1><div class="sub">painel do abrigo &middot; rede local</div></div><span id="con">conectando</span></header>
<section id="estado"><span id="nome">...</span><span id="motivo">aguardando o abrigo</span></section>
<div class="grade">
<div class="c"><small>Temperatura</small><div id="temp">--</div></div>
<div class="c"><small>Umidade do ar</small><div id="umid">--</div></div>
<div class="c"><small>Fuma&ccedil;a / g&aacute;s</small><div id="fumaca">--</div><div class="barra"><i id="b_fumaca"></i></div></div>
<div class="c"><small>Qualidade do ar</small><div id="ar">--</div><div class="barra"><i id="b_ar"></i></div></div>
<div class="c"><small>N&iacute;vel da &aacute;gua</small><div id="agua">--</div></div>
<div class="c"><small>Chuva</small><div id="chuva">--</div><div class="barra"><i id="b_chuva"></i></div></div>
<div class="c"><small>Solo</small><div id="solo">--</div><div class="barra"><i id="b_solo"></i></div></div>
<div class="c"><small>Presen&ccedil;a</small><div id="pir">--</div></div>
</div>
<div class="tags" id="tags"></div>
<button id="mudo" disabled>Silenciar sirene</button>
<footer id="rodape">&nbsp;</footer>
<script>
function el(i){return document.getElementById(i)}
function barra(id,v,lim){var p=lim>0?Math.max(0,Math.min(100,100*v/lim)):0;var e=el(id);e.style.width=p+"%";e.className=p>=100?"alto":""}
function tag(t,c){return '<span class="tag '+c+'">'+t+'</span>'}
function duracao(s){var h=Math.floor(s/3600),m=Math.floor(s%3600/60);return h?h+" h "+m+" min":m?m+" min":s+" s"}
var visto=0,ligado=0;
function mostrar(d){
visto=Date.now();ligado=d.ligado_s;
el("con").className="on";el("con").textContent="ao vivo";
el("estado").className="s"+d.estado;el("nome").textContent=d.nome;el("motivo").textContent=d.motivo;
el("temp").innerHTML=d.temp<0?"--":d.temp.toFixed(1)+" &deg;C";
el("umid").textContent=d.umid<0?"--":Math.round(d.umid)+" %";
el("fumaca").textContent=d.aquecido?Math.round(100*Math.max(0,d.fumaca)/d.fumaca_lim)+" %":"aquecendo";
el("ar").textContent=d.aquecido?Math.round(100*Math.max(0,d.ar)/d.ar_lim)+" %":"aquecendo";
barra("b_fumaca",d.fumaca,d.fumaca_lim);barra("b_ar",d.ar,d.ar_lim);
el("agua").textContent=d.agua_cm<0?"sem eco":Math.round(d.agua_cm)+" cm";
el("chuva").textContent=d.chuva+" %";el("solo").textContent=d.solo+" %";
barra("b_chuva",d.chuva,100);barra("b_solo",d.solo,100);
el("pir").textContent=d.pir?"movimento":"livre";
var t=tag(d.armado?"armado":"desarmado",d.armado?"on":"");
if(d.entrada)t+=tag("entrada: use a digital","alerta");
if(d.rele)t+=tag("exaustor ligado","on");
if(d.mudo)t+=tag("sirene silenciada","on");
t+=tag("Telegram",d.bot?"on":"")+tag("MQTT",d.mqtt?"on":"");
el("tags").innerHTML=t;
var b=el("mudo");b.disabled=!(d.estado==2&&!d.mudo);b.textContent=d.mudo?"Sirene silenciada":"Silenciar sirene";
}
function atualizar(){fetch("/dados",{cache:"no-store"}).then(function(r){return r.json()}).then(mostrar).catch(function(){el("con").className="";el("con").textContent="sem contato"})}
el("mudo").onclick=function(){this.disabled=true;fetch("/silenciar",{method:"POST"}).then(atualizar)};
setInterval(atualizar,2000);atualizar();
setInterval(function(){if(visto)el("rodape").textContent="abrigo ligado há "+duracao(ligado)+" · atualizado há "+Math.round((Date.now()-visto)/1000)+" s"},1000);
</script></body></html>`;

if (typeof module !== "undefined") {
  module.exports = { PAINEL_HTML };
}
