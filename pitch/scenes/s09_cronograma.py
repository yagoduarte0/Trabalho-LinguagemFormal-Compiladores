from manim import *
from manim_slides import Slide

from aegis.theme import *
from aegis import data as d


class Cronograma(Slide):
    def construct(self):
        frame = hud_frame("Cronograma", "09 / 10")
        self.play(FadeIn(frame), run_time=0.6)

        linha_do_tempo = timeline(d.ROADMAP, width=11.2)
        linha_do_tempo.move_to(DOWN * 0.35)

        self.play(Create(linha_do_tempo.line), run_time=0.9)

        for ponto, rotulo in zip(linha_do_tempo.dots, linha_do_tempo.labels):
            self.play(GrowFromCenter(ponto), FadeIn(rotulo, shift=UP * 0.15),
                      run_time=0.45)
        self.next_slide()

        meta = body("Do protótipo ao lançamento comercial em 12 meses.",
                    0.42, GREEN)
        meta.move_to(DOWN * 2.9)
        self.play(FadeIn(meta, shift=UP * 0.2), run_time=0.6)
        self.next_slide()
