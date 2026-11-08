// Ajudantes das cenas: o instante em que a narração diz uma palavra.
//
//   AEGIS.w("02", "scavenge")       -> início da 1ª vez que "scavenge" é dita
//   AEGIS.w("05b", "base de ar", 1) -> início da expressão (palavras seguidas)
//   AEGIS.fim("02", "supply")       -> fim da palavra
//
// A comparação ignora maiúsculas, acentos e pontuação, e cada palavra da
// busca só precisa ser o começo da palavra dita ("sobreviv" acha
// "sobrevivência"). Os tempos vêm de assets/tempos.js e já estão no relógio
// da cena (0 = começo da cena).
(function () {
  const normalizar = (s) =>
    s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase().replace(/[^a-z0-9]/g, "");

  function achar(bloco, busca, n) {
    const cena = window.AEGIS_TEMPOS[bloco];
    if (!cena) throw new Error("AEGIS: bloco desconhecido " + bloco);
    const alvo = busca.split(/\s+/).map(normalizar);
    const ps = cena.palavras;
    let achadas = 0;
    for (let i = 0; i + alvo.length <= ps.length; i++) {
      const casa = alvo.every((a, k) => normalizar(ps[i + k].t).startsWith(a));
      if (casa && ++achadas === n) return [ps[i], ps[i + alvo.length - 1]];
    }
    throw new Error(`AEGIS: "${busca}" (${n}ª vez) não aparece na narração ${bloco}`);
  }

  window.AEGIS = {
    w: (bloco, busca, n = 1) => achar(bloco, busca, n)[0].s,
    fim: (bloco, busca, n = 1) => achar(bloco, busca, n)[1].e,
    dur: (bloco) => window.AEGIS_TEMPOS[bloco].duracao,
  };
})();
