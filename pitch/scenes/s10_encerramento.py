from manim import *
from manim_slides import Slide

from aegis.theme import *
from aegis import data as d


class Encerramento(Slide):
    def construct(self):
        selo = radar_mark(1.15).move_to(UP * 1.5)
        marca = tracked("AEGIS", FONT_DISPLAY, CREAM, 1.2, buff=0.16)
        marca.next_to(selo, DOWN, buff=0.55)

        frase = body("Automação que protege quando tudo o mais falha.",
                     0.48, KHAKI)
        frase.next_to(marca, DOWN, buff=0.5)

        self.play(FadeIn(selo, scale=0.85), run_time=0.8)
        self.play(
            LaggedStart(*[FadeIn(g, shift=UP * 0.22) for g in marca[0]],
                        lag_ratio=0.1),
            run_time=0.9,
        )
        self.play(FadeIn(frase), run_time=0.6)
        self.next_slide()

        pedido = VGroup(
            body(f"Investimento inicial de {d.brl(d.TOTAL_INVESTIMENTO, 0)}",
                 0.4, CREAM),
            body(f"para chegar ao ponto de equilíbrio em {d.BREAK_EVEN_KITS} kits por mês.",
                 0.4, CREAM),
        ).arrange(DOWN, buff=0.22)
        pedido.next_to(frase, DOWN, buff=0.75)

        self.play(FadeIn(pedido, shift=UP * 0.2), run_time=0.7)
        self.next_slide()
