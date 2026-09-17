from manim import *
from manim_slides import Slide

from aegis.theme import *
from aegis import data as d


class ModeloDeNegocio(Slide):
    def construct(self):
        frame = hud_frame("Modelo de Negócio", "07 / 10")
        self.play(FadeIn(frame), run_time=0.6)

        grade = canvas_grid(d.CANVAS, cell_w=4.05, cell_h=1.78)
        grade.move_to(DOWN * 0.45)

        # destaque na proposta de valor
        grade[0][0].box.set_stroke(GREEN)

        for inicio in (0, 3, 6):
            linha = VGroup(*grade[inicio:inicio + 3])
            self.play(
                LaggedStart(*[FadeIn(c, shift=UP * 0.2) for c in linha],
                            lag_ratio=0.18),
                run_time=0.9,
            )
            self.next_slide()
