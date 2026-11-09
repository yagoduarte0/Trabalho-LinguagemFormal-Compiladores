#!/usr/bin/env python3
"""Gera a logo do AEGIS (radar + 'A' em estêncil) em SVG e PNG 640x640.

O desenho é o da abertura do pitch (pitch/scenes/s01_abertura.py e
stencil_a em pitch/aegis/theme.py), parado no meio da varredura. O fundo é
quadrado e o desenho fica dentro do círculo, porque o Telegram corta a foto
do bot em círculo.

Uso (na raiz do repositório):
  python3 docs/marca/gerar_logo.py
"""
import math
import subprocess
from pathlib import Path

AQUI = Path(__file__).resolve().parent
CHROME = next((Path.home() / ".cache/hyperframes/chrome/chrome-headless-shell").glob(
    "*/chrome-headless-shell-*/chrome-headless-shell"))

BG, KHAKI, KHAKI_D, GREEN, GREEN_D = "#0A0D0A", "#C8B88A", "#7E7350", "#A8D04A", "#3E5622"
U = 140            # pixels por unidade do Manim
R_IN, R_OUT, R_BEZEL = 0.95 * U, 1.72 * U, 1.80 * U
ANG = -38          # onde a varredura parou (graus, 0 = direita, anti-horário)


def p(x, y):       # Manim (y para cima) -> SVG (y para baixo)
    return f"{x * U:.1f},{-y * U:.1f}"


def polar(r, graus):
    t = math.radians(graus)
    return r * math.cos(t), -r * math.sin(t)


def setor(r0, r1, a0, a1):
    (x0, y0), (x1, y1) = polar(r1, a0), polar(r1, a1)
    (x2, y2), (x3, y3) = polar(r0, a1), polar(r0, a0)
    return (f'M{x0:.1f},{y0:.1f} A{r1:.1f},{r1:.1f} 0 0 0 {x1:.1f},{y1:.1f} '
            f'L{x2:.1f},{y2:.1f} A{r0:.1f},{r0:.1f} 0 0 1 {x3:.1f},{y3:.1f} Z')


partes = [f'<rect x="-320" y="-320" width="640" height="640" fill="{BG}"/>',
          f'<circle r="{R_BEZEL:.1f}" fill="none" stroke="{GREEN}" stroke-width="16" stroke-opacity="0.10"/>']
# grade
for r in (1.12 * U, 1.45 * U):
    partes.append(f'<circle r="{r:.1f}" fill="none" stroke="{GREEN_D}" stroke-width="2.2" stroke-opacity="0.6"/>')
for a in (0, 90, 180, 270):
    (x0, y0), (x1, y1) = polar(R_IN + 6, a), polar(R_OUT - 6, a)
    partes.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" '
                  f'stroke="{GREEN_D}" stroke-width="2.2" stroke-opacity="0.75"/>')
# rastro da varredura (24 fatias atrás da linha, cada vez mais fracas)
for i in range(24):
    op = 0.45 * (1 - i / 24) ** 1.25
    a1 = ANG - i * 4.2
    partes.append(f'<path d="{setor(R_IN, R_OUT, a1 - 4.3, a1)}" fill="{GREEN}" fill-opacity="{op:.3f}"/>')
(x0, y0), (x1, y1) = polar(R_IN, ANG), polar(R_OUT, ANG)
partes.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="{GREEN}" stroke-width="4.5"/>')
partes.append(f'<circle r="{R_IN:.1f}" fill="{BG}" stroke="{KHAKI_D}" stroke-width="3"/>')
# alvos (os que a varredura acabou de passar brilham mais)
for r, a, tam in [(1.26, 42, 0.055), (1.56, 148, 0.07), (1.12, 236, 0.05), (1.44, 312, 0.065)]:
    d = (ANG - a) % 360
    op = max(0.0, 1 - math.radians(d) / 2.4) ** 1.6
    if op > 0.02:
        x, y = polar(r * U, a)
        partes.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{tam * U:.1f}" fill="{GREEN}" fill-opacity="{op:.2f}"/>')
# aro e marcas
partes.append(f'<circle r="{R_BEZEL:.1f}" fill="none" stroke="{KHAKI}" stroke-width="4.5"/>')
for i in range(36):
    longa = i % 9 == 0
    (x0, y0), (x1, y1) = polar(R_BEZEL + 6, i * 10), polar(R_BEZEL + (0.20 if longa else 0.10) * U, i * 10)
    partes.append(f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" '
                  f'stroke="{KHAKI if longa else KHAKI_D}" stroke-width="{5 if longa else 3}"/>')
# monograma 'A' em estêncil (stencil_a, escala 0.88) e o núcleo verde
s = 0.88
pernas = [[(-0.11, 0.70), (0.15, 0.70), (-0.36, -0.70), (-0.62, -0.70)],
          [(0.11, 0.70), (-0.15, 0.70), (0.36, -0.70), (0.62, -0.70)]]
for perna in pernas:
    pts = " ".join(p(x * s, y * s) for x, y in perna)
    partes.append(f'<polygon points="{pts}" fill="{KHAKI}" stroke="{KHAKI}" stroke-width="2" stroke-linejoin="round"/>')
for cx in (-0.21, 0.21):
    w, h = 0.26 * s, 0.17 * s
    partes.append(f'<rect x="{(cx * s - w / 2) * U:.1f}" y="{(0.19 * s - h / 2) * U:.1f}" '
                  f'width="{w * U:.1f}" height="{h * U:.1f}" fill="{KHAKI}"/>')
lado = 0.17 * s * 0.8 * U
nx, ny = -lado / 2, 0.19 * s * U - lado / 2
partes.append(f'<rect x="{nx:.1f}" y="{ny:.1f}" width="{lado:.1f}" height="{lado:.1f}" '
              f'fill="none" stroke="{GREEN}" stroke-width="12" stroke-opacity="0.35"/>')
partes.append(f'<rect x="{nx:.1f}" y="{ny:.1f}" width="{lado:.1f}" height="{lado:.1f}" fill="{GREEN}"/>')

svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="640" height="640" viewBox="-320 -320 640 640">\n  '
       + "\n  ".join(partes) + "\n</svg>\n")
(AQUI / "logo-aegis.svg").write_text(svg)
html = AQUI / ".logo.html"
html.write_text(f'<!doctype html><html><body style="margin:0;background:{BG}">{svg}</body></html>')
subprocess.run([str(CHROME), "--headless", "--hide-scrollbars", "--window-size=640,640",
                "--force-device-scale-factor=1", f"--screenshot={AQUI / 'logo-aegis.png'}",
                html.as_uri()], check=True, capture_output=True)
html.unlink()
print(AQUI / "logo-aegis.png")
