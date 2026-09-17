from manim import *
from manim_slides import Slide
import numpy as np

from aegis.theme import *
from aegis import data as d

CENTRO = LEFT * 3.7 + DOWN * 0.55


class Mercado(Slide):
    def construct(self):
        frame = hud_frame("Análise de Mercado", "06 / 10")
        self.play(FadeIn(frame), run_time=0.6)

        camadas = [
            (2.45, d.TAM, KHAKI_D, 0.0),
            (1.62, d.SAM, OLIVE, 0.10),
            (0.85, d.SOM, GREEN, 0.22),
        ]
        siglas = ["TAM", "SAM", "SOM"]

        for i, (raio, (valor, descricao, fonte), cor, fill) in enumerate(camadas):
            circulo = Circle(radius=raio, stroke_color=cor, stroke_width=3,
                             fill_color=cor, fill_opacity=fill).move_to(CENTRO)

            sigla = tracked(siglas[i], FONT_DISPLAY, cor if i else KHAKI,
                            0.34, buff=0.06)
            num = tracked(valor, FONT_DISPLAY, GREEN if i == 2 else CREAM,
                          0.62, buff=0.1)
            desc = body(descricao, 0.32, CREAM)
            src = body(fonte, 0.24, KHAKI_D)
            bloco = VGroup(sigla, num, desc, src).arrange(DOWN, buff=0.16,
                                                          aligned_edge=LEFT)
            bloco.move_to(RIGHT * 2.9 + UP * (1.75 - i * 1.85), aligned_edge=LEFT)
            bloco.align_to(np.array([1.2, 0, 0]), LEFT)

            self.play(Create(circulo), run_time=0.7)
            self.play(FadeIn(bloco, shift=RIGHT * 0.25), run_time=0.6)
            self.next_slide()

        # ---------- o mercado que já existe e paga ----------
        self.play(
            *[FadeOut(m) for m in self.mobjects if m is not frame],
            run_time=0.7,
        )

        apoios = [
            (d.MERCADO_SEGURANCA, "Segurança eletrônica no Brasil",
             d.MERCADO_SEGURANCA_FONTE),
            (d.MERCADO_SMART_HOME, "Automação residencial no Brasil",
             d.MERCADO_SMART_HOME_FONTE),
            (d.MUNICIPIOS_COM_DESASTRE, "dos municípios tiveram desastre",
             d.MUNICIPIOS_COM_DESASTRE_FONTE),
        ]

        cartoes = VGroup()
        for valor, rotulo, fonte in apoios:
            p = panel(4.1, 3.0)
            num = tracked(valor, FONT_DISPLAY, GREEN, 0.7, buff=0.1)
            rot = body(rotulo, 0.3, CREAM)
            src = body(fonte, 0.2, KHAKI_D, line_spacing=0.8)
            src.set_width(min(src.width, 3.5))
            stack = VGroup(num, rot, src).arrange(DOWN, buff=0.3)
            stack.move_to(p.box.get_center())
            cartoes.add(VGroup(p, stack))

        cartoes.arrange(RIGHT, buff=0.34).move_to(DOWN * 0.4)

        for c in cartoes:
            self.play(FadeIn(c, shift=UP * 0.25), run_time=0.55)
        self.next_slide()
