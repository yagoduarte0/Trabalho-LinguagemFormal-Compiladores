from manim import *
from manim_slides import Slide

from aegis.theme import *
from aegis import data as d


class SumarioExecutivo(Slide):
    def construct(self):
        frame = hud_frame("Sumário Executivo", "02 / 10")
        self.play(FadeIn(frame), run_time=0.6)

        cards = [
            ("O que é",
             "Automação residencial de\n"
             "sobrevivência. Sensores e uma\n"
             "linguagem própria monitoram\n"
             "água, ar, fumaça, temperatura\n"
             "e presença — sem depender\n"
             "de internet."),
            ("Para quem",
             f"{d.DOMICILIOS_AREA_RISCO} de domicílios em áreas\n"
             "de risco de desastre no Brasil,\n"
             "mais entusiastas de preparo\n"
             "e donos de sítios e casas\n"
             "de campo."),
            ("Como ganha",
             f"Kit de {d.brl(d.PRECO_KIT, 0)} na venda e\n"
             f"assinatura de {d.brl(d.ASSINATURA)} por mês.\n"
             f"Margem de {d.MARGEM_KIT_PCT}% por kit e\n"
             f"ponto de equilíbrio em\n"
             f"{d.BREAK_EVEN_KITS} kits por mês."),
        ]

        group = VGroup()
        for title, text in cards:
            p = panel(4.1, 3.4)
            ttl = tracked(title.upper(), FONT_DISPLAY, GREEN, 0.34, buff=0.07)
            ttl.next_to(p.box.get_top(), DOWN, buff=0.3)
            txt = body(text, 0.33, CREAM, line_spacing=1.0)
            txt.next_to(ttl, DOWN, buff=0.34)
            group.add(VGroup(p, ttl, txt))

        group.arrange(RIGHT, buff=0.34).move_to(DOWN * 0.35)

        for card in group:
            self.play(FadeIn(card, shift=UP * 0.3), run_time=0.7)
            self.next_slide()
