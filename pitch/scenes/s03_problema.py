from manim import *
from manim_slides import Slide

from aegis.theme import *
from aegis import data as d

HOUSE_POS = LEFT * 3.6 + DOWN * 0.3


def icon_lamp(color):
    bulb = Circle(radius=0.17, stroke_color=color, stroke_width=3)
    neck = Rectangle(width=0.16, height=0.11, stroke_color=color, stroke_width=3)
    neck.next_to(bulb, DOWN, buff=0.01)
    rays = VGroup(*[
        Line(UP * 0.26, UP * 0.36, stroke_color=color, stroke_width=2.5)
        .rotate(a, about_point=ORIGIN)
        for a in (-0.7, 0, 0.7)
    ])
    return VGroup(bulb, neck, rays)


def icon_tv(color):
    screen = RoundedRectangle(corner_radius=0.05, width=0.52, height=0.36,
                              stroke_color=color, stroke_width=3)
    stand = Line(LEFT * 0.12, RIGHT * 0.12, stroke_color=color, stroke_width=3)
    stand.next_to(screen, DOWN, buff=0.07)
    return VGroup(screen, stand)


def icon_sound(color):
    box = Polygon([-0.17, -0.10, 0], [-0.04, -0.10, 0], [0.07, -0.21, 0],
                  [0.07, 0.21, 0], [-0.04, 0.10, 0], [-0.17, 0.10, 0],
                  stroke_color=color, stroke_width=3)
    waves = VGroup(*[
        Arc(radius=r, start_angle=-PI / 4, angle=PI / 2,
            stroke_color=color, stroke_width=2.5).shift(RIGHT * 0.08)
        for r in (0.16, 0.26)
    ])
    return VGroup(box, waves)


def icon_ac(color):
    shell = RoundedRectangle(corner_radius=0.06, width=0.54, height=0.24,
                             stroke_color=color, stroke_width=3)
    flow = VGroup(*[
        Line(DOWN * 0.18, DOWN * 0.3, stroke_color=color, stroke_width=2.5)
        .shift(RIGHT * x)
        for x in (-0.15, 0, 0.15)
    ])
    return VGroup(shell, flow)


class Problema(Slide):
    def construct(self):
        frame = hud_frame("O Problema", "03 / 10")
        self.play(FadeIn(frame), run_time=0.6)

        # ---------- a casa inteligente de hoje ----------
        house = Polygon(
            [-1.5, -1.35, 0], [1.5, -1.35, 0], [1.5, 0.35, 0],
            [0, 1.5, 0], [-1.5, 0.35, 0],
            stroke_color=KHAKI, stroke_width=4,
        ).move_to(HOUSE_POS)

        icons = VGroup(
            VGroup(icon_lamp(GREEN), body("LUZ", 0.26, KHAKI)).arrange(DOWN, buff=0.16),
            VGroup(icon_tv(GREEN), body("TV", 0.26, KHAKI)).arrange(DOWN, buff=0.16),
            VGroup(icon_sound(GREEN), body("SOM", 0.26, KHAKI)).arrange(DOWN, buff=0.16),
            VGroup(icon_ac(GREEN), body("AR", 0.26, KHAKI)).arrange(DOWN, buff=0.16),
        )
        icons.arrange_in_grid(rows=2, cols=2, buff=(0.75, 0.42))
        icons.move_to(house.get_center() + DOWN * 0.18)

        self.play(Create(house), run_time=1.0)
        self.play(LaggedStart(*[FadeIn(i, scale=0.8) for i in icons],
                              lag_ratio=0.18), run_time=1.4)

        titulo = body("A automação residencial de hoje\nresolve conforto.",
                      0.52, CREAM, line_spacing=1.0)
        lista = bullets([
            "Acender a luz pelo celular",
            "Ligar a TV por comando de voz",
            "Ajustar a temperatura sozinha",
        ], scale=0.38)
        bloco = VGroup(titulo, lista).arrange(DOWN, buff=0.6, aligned_edge=LEFT)
        bloco.move_to(RIGHT * 2.9 + DOWN * 0.3)

        self.play(FadeIn(titulo, shift=UP * 0.2), run_time=0.7)
        self.play(LaggedStart(*[FadeIn(b, shift=RIGHT * 0.3) for b in lista],
                              lag_ratio=0.25), run_time=1.2)
        self.next_slide()

        # ---------- a crise ----------
        alerta = body("E quando a crise chega?", 0.62, AMBER)
        alerta.move_to(bloco.get_center())

        self.play(FadeOut(bloco), run_time=0.5)
        self.play(FadeIn(alerta, scale=0.9), run_time=0.6)

        scan = Line(house.get_left() + UP * 1.6, house.get_right() + UP * 1.6,
                    stroke_color=RED, stroke_width=3, stroke_opacity=0.9)
        self.add(scan)
        self.play(scan.animate.shift(DOWN * 3.2).set_stroke(opacity=0),
                  house.animate.set_stroke(RED),
                  run_time=1.2)
        self.remove(scan)

        self.play(
            LaggedStart(*[
                i.animate.set_color(KHAKI_D).set_opacity(0.22) for i in icons
            ], lag_ratio=0.3),
            run_time=2.0,
        )
        self.next_slide()

        # ---------- as perguntas que ninguém automatizou ----------
        self.play(FadeOut(alerta), run_time=0.4)

        perguntas = VGroup(*[
            body(q, 0.46, CREAM) for q in [
                "E o nível da caixa d'água?",
                "E a qualidade do ar?",
                "E o princípio de incêndio?",
                "E quem está lá fora?",
            ]
        ]).arrange(DOWN, buff=0.52, aligned_edge=LEFT)
        perguntas.move_to(RIGHT * 2.9 + DOWN * 0.3)

        for q in perguntas:
            self.play(FadeIn(q, shift=RIGHT * 0.25), run_time=0.5)
        self.next_slide()

        # ---------- o tamanho do problema ----------
        self.play(
            FadeOut(perguntas), FadeOut(icons), FadeOut(house),
            run_time=0.8,
        )

        numero = tracked(d.PESSOAS_AREA_RISCO, FONT_DISPLAY, GREEN, 1.7, buff=0.16)
        legenda = body("de brasileiros vivem em áreas\nde risco de desastre no Brasil",
                       0.52, CREAM, line_spacing=1.0)
        fonte = body(d.PESSOAS_AREA_RISCO_FONTE, 0.26, KHAKI_D)

        stat = VGroup(numero, legenda, fonte).arrange(DOWN, buff=0.45)
        stat.move_to(DOWN * 0.3)

        self.play(FadeIn(numero, scale=0.85), run_time=0.9)
        self.play(FadeIn(legenda, shift=UP * 0.2), run_time=0.7)
        self.play(FadeIn(fonte), run_time=0.5)
        self.next_slide()
