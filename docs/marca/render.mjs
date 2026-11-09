// Renderiza docs/marca/logo.html em PNG (2x): logo-bot.png e logo-completa.png.
// Uso (na raiz do repositório): node docs/marca/render.mjs
import { createRequire } from "node:module";
import { homedir } from "node:os";
import { readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const aqui = dirname(fileURLToPath(import.meta.url));
const npx = join(homedir(), ".npm/_npx");
const pasta = readdirSync(npx).map(d => join(npx, d, "node_modules/puppeteer-core"))
  .find(p => { try { readdirSync(p); return true; } catch { return false; } });
const puppeteer = createRequire(import.meta.url)(pasta);
const cdir = join(homedir(), ".cache/hyperframes/chrome/chrome-headless-shell");
const versao = readdirSync(cdir)[0];
const chrome = join(cdir, versao, readdirSync(join(cdir, versao))[0], "chrome-headless-shell");

const nav = await puppeteer.launch({ executablePath: chrome });
const pag = await nav.newPage();
for (const [v, w, h] of [["bot", 640, 640], ["completa", 1600, 900]]) {
  await pag.setViewport({ width: w, height: h, deviceScaleFactor: 2 });
  await pag.goto(pathToFileURL(join(aqui, "logo.html")).href + "?v=" + v, { waitUntil: "networkidle0" });
  await pag.evaluate(() => document.fonts.ready);
  const ok = await pag.evaluate(() => document.fonts.check('40px "League Gothic"'));
  if (!ok) throw new Error("League Gothic não carregou (precisa de internet)");
  await pag.screenshot({ path: join(aqui, `logo-${v}.png`), clip: { x: 0, y: 0, width: w, height: h } });
  console.log(join(aqui, `logo-${v}.png`));
}
await nav.close();
