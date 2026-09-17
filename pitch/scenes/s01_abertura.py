from manim import *
from manim_slides import Slide
import numpy as np

from aegis.theme import *

C = UP * 0.7
R_IN = 0.95
R_OUT = 1.72
R_BEZEL = 1.80
SWEEP_SPEED = 1.6


class Abertura(Slide):
    def construct(self):
        angle_t = ValueTracker(0)
        angle_t.add_updater(lambda m, dt: m.increment_value(dt * SWEEP_SPEED))
        self.add(angle_t)

        glow = Circle(radius=R_BEZEL, stroke_color=GREEN, stroke_width=12,
                      stroke_opacity=0.10).move_to(C)
        bezel = Circle(radius=R_BEZEL, stroke_color=KHAKI, stroke_width=3).move_to(C)

        ticks = VGroup()
        for i in range(36):
            theta = i * 10 * DEGREES
            long = i % 9 == 0
            u = np.array([np.cos(theta), np.sin(theta), 0])
            ticks.add(Line(C + u * (R_BEZEL + 0.04),
                           C + u * (R_BEZEL + (0.20 if long else 0.10)),
                           stroke_width=3.5 if long else 2,
                           color=KHAKI if long else KHAKI_D))

        grid = VGroup(
            Circle(radius=1.12, stroke_color=GREEN_D, stroke_width=1.5,
                   stroke_opacity=0.55).move_to(C),
            Circle(radius=1.45, stroke_color=GREEN_D, stroke_width=1.5,
                   stroke_opacity=0.55).move_to(C),
            Circle(radius=R_IN, stroke_color=KHAKI_D, stroke_width=2).move_to(C),
        )
        for i in range(4):
            theta = i * 90 * DEGREES
            u = np.array([np.cos(theta), np.sin(theta), 0])
            grid.add(Line(C + u * (R_IN + 0.04), C + u * (R_OUT - 0.04),
                          stroke_width=1.5, color=GREEN_D, stroke_opacity=0.7))

        trail = VGroup()
        n_seg = 24
        for i in range(n_seg):
            trail.add(AnnularSector(
                inner_radius=R_IN, outer_radius=R_OUT,
                angle=-4.2 * DEGREES, start_angle=-i * 4.2 * DEGREES,
                color=GREEN, fill_opacity=0.45 * (1 - i / n_seg) ** 1.25,
                stroke_width=0,
            ))
        edge = Line(RIGHT * R_IN, RIGHT * R_OUT, stroke_width=3, color=GREEN)
        sweep = VGroup(trail, edge).shift(C)
        sweep.add_updater(lambda m, dt: m.rotate(dt * SWEEP_SPEED, about_point=C))

        blips = VGroup()
        for r, deg, size in [(1.26, 42, 0.055), (1.56, 148, 0.07),
                             (1.12, 236, 0.05), (1.44, 312, 0.065)]:
            theta = deg * DEGREES
            pos = C + np.array([np.cos(theta), np.sin(theta), 0]) * r
            dot = Dot(point=pos, radius=size, color=GREEN)

            def make_updater(th):
                def upd(m):
                    d = (angle_t.get_value() - th) % TAU
                    m.set_opacity(max(0.0, 1.0 - d / 2.4) ** 1.6)
                return upd

            dot.add_updater(make_updater(theta))
            dot.set_opacity(0)
            blips.add(dot)

        monogram = stencil_a().scale(0.88).move_to(C)
        core_pos = (monogram[2].get_center() + monogram[3].get_center()) / 2
        core_side = monogram[2].height * 0.8
        core = Square(side_length=core_side, color=GREEN, fill_color=GREEN,
                      fill_opacity=1, stroke_width=0).move_to(core_pos)
        core_glow = Square(side_length=core_side, color=GREEN, stroke_width=9,
                           stroke_opacity=0.35).move_to(core_pos)

        word = tracked("AEGIS", FONT_DISPLAY, CREAM, 1.35, buff=0.17)
        word.move_to(C + DOWN * 2.55)

        tag = tracked("SISTEMA DE MONITORAMENTO", FONT_DISPLAY, "#8AA24C", 0.36,
                      buff=0.09, word_buff=0.26)
        tag.move_to(word.get_center() + DOWN * 0.62)

        rule_l = Line(LEFT * 0.9, ORIGIN, stroke_width=2, color=GREEN_D)
        rule_r = rule_l.copy()
        rule_l.next_to(tag, LEFT, buff=0.26)
        rule_r.next_to(tag, RIGHT, buff=0.26)

        box = SurroundingRectangle(
            VGroup(bezel, ticks, word, tag, rule_l, rule_r), buff=0.45
        )
        brackets = VGroup(
            corner_bracket(box.get_corner(UL), 1, -1),
            corner_bracket(box.get_corner(UR), -1, -1),
            corner_bracket(box.get_corner(DR), -1, 1),
            corner_bracket(box.get_corner(DL), 1, 1),
        )

        self.play(
            LaggedStart(*[FadeIn(b, scale=0.85) for b in brackets], lag_ratio=0.12),
            run_time=0.9,
        )
        self.play(Create(bezel), FadeIn(glow), run_time=0.9)
        self.play(LaggedStart(*[FadeIn(t) for t in ticks], lag_ratio=0.02),
                  run_time=1.0)
        self.play(Create(grid), run_time=0.8)

        self.add(sweep, blips)
        self.play(FadeIn(sweep), run_time=0.5)
        self.play(DrawBorderThenFill(monogram), run_time=1.5)
        self.play(FadeIn(core, scale=0.4), FadeIn(core_glow), run_time=0.5)

        pulses = []
        for _ in range(2):
            ring = Circle(radius=R_IN, stroke_color=GREEN, stroke_width=3,
                          stroke_opacity=0.75).move_to(C)
            self.add(ring)
            pulses.append(
                ring.animate(run_time=1.4, rate_func=rate_functions.ease_out_sine)
                .scale(1.9).set_stroke(opacity=0)
            )
        self.play(LaggedStart(*pulses, lag_ratio=0.45))

        self.play(
            LaggedStart(*[FadeIn(g, shift=UP * 0.25) for g in word[0]],
                        lag_ratio=0.1),
            run_time=1.1,
        )
        self.play(FadeIn(tag), Create(rule_l), Create(rule_r), run_time=0.8)

        # radar girando em loop enquanto o apresentador fala
        self.next_slide(loop=True)
        self.wait(TAU / SWEEP_SPEED)
        self.next_slide()
