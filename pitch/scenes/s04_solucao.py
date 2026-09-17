from manim import *
from manim_slides import Slide
import numpy as np

from aegis.theme import *
from aegis import data as d

HUB = DOWN * 0.75
R_NODE = 2.3


def icon_presenca(color):
    dome = Arc(radius=0.2, start_angle=0, angle=PI, stroke_color=color,
               stroke_width=3)
    base = Line(LEFT * 0.2, RIGHT * 0.2, stroke_color=color, stroke_width=3)
    waves = VGroup(*[
        Arc(radius=r, start_angle=PI / 5, angle=3 * PI / 5,
            stroke_color=color, stroke_width=2, stroke_opacity=0.8)
        for r in (0.3, 0.4)
    ])
    return VGroup(dome, base, waves)


def icon_agua(color):
    tank = Rectangle(width=0.42, height=0.44, stroke_color=color, stroke_width=3)
    nivel = Line(LEFT * 0.21, RIGHT * 0.21, stroke_color=color, stroke_width=3)
    nivel.shift(DOWN * 0.06)
    onda = Arc(radius=0.1, start_angle=PI, angle=-PI, stroke_color=color,
               stroke_width=2).shift(DOWN * 0.06 + LEFT * 0.1)
    return VGroup(tank, nivel, onda)


def icon_fumaca(color):
    waves = VGroup(*[
        ParametricFunction(
            lambda t, s=shift: np.array([s + 0.05 * np.sin(t * TAU), t * 0.5 - 0.25, 0]),
            t_range=[0, 1], stroke_color=color, stroke_width=2.5,
        )
        for shift in (-0.14, 0, 0.14)
    ])
    return waves


def icon_ar(color):
    linhas = VGroup(*[
        Line(LEFT * w, RIGHT * w, stroke_color=color, stroke_width=2.5)
        .shift(UP * y)
        for w, y in ((0.22, 0.13), (0.28, 0.0), (0.18, -0.13))
    ])
    return linhas


def icon_temp(color):
    tubo = RoundedRectangle(corner_radius=0.07, width=0.14, height=0.42,
                            stroke_color=color, stroke_width=3)
    tubo.shift(UP * 0.08)
    bulbo = Circle(radius=0.11, stroke_color=color, stroke_width=3,
                   fill_color=color, fill_opacity=1).shift(DOWN * 0.2)
    return VGroup(tubo, bulbo)


ICONES = [icon_presenca, icon_agua, icon_fumaca, icon_ar, icon_temp]


class Solucao(Slide):
    def construct(self):
        frame = hud_frame("A Solução", "04 / 10")
        self.play(FadeIn(frame), run_time=0.6)

        chamada = body("Uma automação que monitora o que importa\n"
                       "quando tudo o mais falha.", 0.44, CREAM, line_spacing=1.0)
        chamada.move_to(UP * 2.42)
        self.play(FadeIn(chamada, shift=UP * 0.2), run_time=0.7)

        # ---------- o controlador no centro ----------
        anel = Circle(radius=0.92, stroke_color=KHAKI_D, stroke_width=2).move_to(HUB)
        nucleo = RoundedRectangle(corner_radius=0.1, width=1.25, height=0.72,
                                  stroke_color=KHAKI, stroke_width=3,
                                  fill_color=OLIVE, fill_opacity=0.12).move_to(HUB)
        esp = tracked("ESP32", FONT_DISPLAY, CREAM, 0.42, buff=0.08).move_to(HUB)

        self.play(Create(anel), FadeIn(nucleo), FadeIn(esp), run_time=1.0)

        # ---------- os cinco módulos em volta ----------
        nodes = VGroup()
        linhas = VGroup()
        for i, (nome, modelo, _) in enumerate(d.MODULOS):
            ang = PI / 2 + i * TAU / 5
            u = np.array([np.cos(ang), np.sin(ang), 0])
            pos = HUB + u * R_NODE

            ico = ICONES[i](GREEN)
            nome_m = tracked(nome.upper(), FONT_DISPLAY, CREAM, 0.32, buff=0.06)
            modelo_m = body(modelo, 0.24, KHAKI_D)
            node = VGroup(ico, nome_m, modelo_m).arrange(DOWN, buff=0.15)
            node.move_to(pos)
            nodes.add(node)

            linhas.add(Line(HUB + u * 0.95, pos - u * 0.62,
                            stroke_color=KHAKI_D, stroke_width=1.5))

        for node, linha in zip(nodes, linhas):
            self.play(Create(linha), FadeIn(node, scale=0.85), run_time=0.45)
        self.next_slide()

        # ---------- os dados chegando ao controlador ----------
        self.next_slide(loop=True)
        pulsos = []
        for linha in linhas:
            p = Dot(linha.get_end(), radius=0.055, color=GREEN)
            caminho = Line(linha.get_end(), linha.get_start())
            pulsos.append(Succession(
                FadeIn(p, run_time=0.2),
                MoveAlongPath(p, caminho, run_time=1.6, rate_func=linear),
                FadeOut(p, run_time=0.2),
            ))
        self.play(LaggedStart(*pulsos, lag_ratio=0.12))
        self.next_slide()

        # ---------- o diferencial ----------
        self.play(
            FadeOut(nodes), FadeOut(linhas), FadeOut(anel),
            FadeOut(nucleo), FadeOut(esp), FadeOut(chamada),
            run_time=0.8,
        )

        comum = panel(5.5, 2.7)
        comum_t = tracked("AUTOMAÇÃO COMUM", FONT_DISPLAY, KHAKI_D, 0.36, buff=0.07)
        comum_t.next_to(comum.box.get_top(), DOWN, buff=0.3)
        comum_l = bullets([
            "Foco em conforto",
            "Depende da nuvem",
            "Sem internet, não funciona",
        ], scale=0.36, buff=0.36, marker_color=KHAKI_D, text_color=KHAKI)
        comum_l.next_to(comum_t, DOWN, buff=0.38)
        bloco_comum = VGroup(comum, comum_t, comum_l)

        aegis = panel(5.5, 2.7)
        aegis.box.set_stroke(GREEN)
        aegis_t = tracked("AEGIS", FONT_DISPLAY, GREEN, 0.36, buff=0.07)
        aegis_t.next_to(aegis.box.get_top(), DOWN, buff=0.3)
        aegis_l = bullets([
            "Foco em resiliência",
            "Processa tudo localmente",
            "Funciona sem internet",
        ], scale=0.36, buff=0.36)
        aegis_l.next_to(aegis_t, DOWN, buff=0.38)
        bloco_aegis = VGroup(aegis, aegis_t, aegis_l)

        dupla = VGroup(bloco_comum, bloco_aegis).arrange(RIGHT, buff=0.6)
        dupla.move_to(DOWN * 0.4)

        self.play(FadeIn(bloco_comum, shift=RIGHT * 0.3), run_time=0.7)
        self.next_slide()
        self.play(FadeIn(bloco_aegis, shift=LEFT * 0.3), run_time=0.7)
        self.next_slide()
