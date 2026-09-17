"""Tema visual compartilhado do pitch AEGIS."""

from manim import *
import numpy as np

BG = "#0A0D0A"
KHAKI = "#C8B88A"
KHAKI_D = "#7E7350"
OLIVE = "#55672F"
GREEN = "#A8D04A"
GREEN_D = "#3E5622"
CREAM = "#EDE4CC"
AMBER = "#F0A202"
RED = "#D62828"

FONT_DISPLAY = "Impact"
FONT_BODY = "Bahnschrift"
FONT_MONO = "Consolas"

HALF_X = 6.75
HALF_Y = 3.75

config.background_color = BG


# --------------------------------------------------------------------------
# primitivas
# --------------------------------------------------------------------------

def tracked(text, font=FONT_DISPLAY, color=CREAM, scale=1.0, buff=0.13,
            word_buff=0.34, weight=NORMAL):
    """Texto com espaçamento entre letras, montado palavra a palavra."""
    words = VGroup()
    for w in text.split(" "):
        glyphs = Text(w, font=font, color=color, weight=weight).scale(scale)
        if len(glyphs.submobjects) > 1:
            glyphs.arrange(RIGHT, buff=buff)
        words.add(glyphs)
    if len(words.submobjects) > 1:
        words.arrange(RIGHT, buff=word_buff)
    return words


def body(text, scale=0.42, color=CREAM, line_spacing=0.9):
    return Text(text, font=FONT_BODY, color=color,
                line_spacing=line_spacing).scale(scale)


def corner_bracket(corner, dx, dy, length=0.5, color=KHAKI_D, stroke_width=3):
    h = Line(corner, corner + np.array([dx * length, 0, 0]),
             stroke_width=stroke_width, color=color)
    v = Line(corner, corner + np.array([0, dy * length, 0]),
             stroke_width=stroke_width, color=color)
    return VGroup(h, v)


def stencil_a(color=KHAKI):
    """Monograma 'A' em estêncil, o mesmo da logo."""
    left = Polygon(
        [-0.11, 0.70, 0], [0.15, 0.70, 0], [-0.36, -0.70, 0], [-0.62, -0.70, 0],
        color=color, fill_color=color, fill_opacity=1, stroke_width=2,
    )
    right = Polygon(
        [0.11, 0.70, 0], [-0.15, 0.70, 0], [0.36, -0.70, 0], [0.62, -0.70, 0],
        color=color, fill_color=color, fill_opacity=1, stroke_width=2,
    )
    bar_l = Rectangle(width=0.26, height=0.17, color=color, fill_color=color,
                      fill_opacity=1, stroke_width=2).move_to([-0.21, -0.19, 0])
    bar_r = bar_l.copy().move_to([0.21, -0.19, 0])
    return VGroup(left, right, bar_l, bar_r)


# --------------------------------------------------------------------------
# estrutura de cena
# --------------------------------------------------------------------------

def hud_frame(title=None, index=None):
    """Moldura HUD padrão: 4 cantos, régua superior, rótulo da seção."""
    g = VGroup()
    for (x, y), dx, dy in [((-HALF_X, HALF_Y), 1, -1), ((HALF_X, HALF_Y), -1, -1),
                           ((HALF_X, -HALF_Y), -1, 1), ((-HALF_X, -HALF_Y), 1, 1)]:
        g.add(corner_bracket(np.array([x, y, 0]), dx, dy))

    if title:
        label = tracked(title.upper(), FONT_DISPLAY, KHAKI, 0.44, buff=0.09)
        label.move_to([-HALF_X + 0.62, HALF_Y - 0.52, 0], aligned_edge=LEFT)
        g.add(label)

        rule = Line([-HALF_X + 0.6, HALF_Y - 0.92, 0],
                    [HALF_X - 0.6, HALF_Y - 0.92, 0],
                    stroke_width=1.5, color=KHAKI_D)
        g.add(rule)

    if index:
        idx = tracked(index, FONT_DISPLAY, KHAKI_D, 0.34, buff=0.07)
        idx.move_to([HALF_X - 0.62, HALF_Y - 0.52, 0], aligned_edge=RIGHT)
        g.add(idx)

    return g


def section_card(number, title, subtitle=None):
    """Cartão de transição entre seções."""
    num = tracked(number, FONT_DISPLAY, GREEN_D, 1.6, buff=0.12)
    ttl = tracked(title.upper(), FONT_DISPLAY, CREAM, 1.05, buff=0.16)
    g = VGroup(num, ttl).arrange(DOWN, buff=0.35)
    if subtitle:
        sub = body(subtitle, 0.42, KHAKI)
        g.add(sub)
        sub.next_to(ttl, DOWN, buff=0.4)
    return g


def panel(width, height, label=None, fill_opacity=0.06):
    box = RoundedRectangle(corner_radius=0.12, width=width, height=height,
                           stroke_color=KHAKI_D, stroke_width=2,
                           fill_color=OLIVE, fill_opacity=fill_opacity)
    g = VGroup(box)
    g.box = box
    if label:
        tab = tracked(label.upper(), FONT_DISPLAY, KHAKI, 0.3, buff=0.06)
        tab.next_to(box.get_top(), DOWN, buff=0.22)
        g.add(tab)
        g.tab = tab
    return g


# --------------------------------------------------------------------------
# conteúdo
# --------------------------------------------------------------------------

def bullets(items, scale=0.44, buff=0.42, marker_color=GREEN, text_color=CREAM):
    rows = VGroup()
    for it in items:
        marker = Square(side_length=0.12, color=marker_color,
                        fill_color=marker_color, fill_opacity=1,
                        stroke_width=0).rotate(PI / 4)
        txt = body(it, scale, text_color)
        edge = UP if "\n" in it else ORIGIN
        row = VGroup(marker, txt).arrange(RIGHT, buff=0.3, aligned_edge=edge)
        rows.add(row)
    rows.arrange(DOWN, buff=buff, aligned_edge=LEFT)
    return rows


def stat_tile(value, label, width=3.6, height=2.1, value_color=GREEN):
    p = panel(width, height)
    val = tracked(value, FONT_DISPLAY, value_color, 0.95, buff=0.1)
    lab = body(label, 0.33, KHAKI)
    stack = VGroup(val, lab).arrange(DOWN, buff=0.28)
    stack.move_to(p.box.get_center())
    g = VGroup(p, stack)
    g.value_mob = val
    g.label_mob = lab
    return g


def count_to(scene, tracker, target, run_time=1.4):
    scene.play(tracker.animate.set_value(target), run_time=run_time,
               rate_func=rate_functions.ease_out_cubic)


def data_table(rows, headers=None, scale=0.42, highlight_last=False):
    kwargs = dict(
        element_to_mobject=Text,
        element_to_mobject_config={"font": FONT_BODY, "color": CREAM},
        line_config={"stroke_color": KHAKI_D, "stroke_width": 1.2},
        v_buff=0.32, h_buff=0.75,
        include_outer_lines=False,
    )
    if headers:
        kwargs["col_labels"] = [
            Text(h, font=FONT_DISPLAY, color=KHAKI) for h in headers
        ]
    t = Table(rows, **kwargs).scale(scale)
    if highlight_last:
        for cell in t.get_rows()[-1]:
            cell.set_color(GREEN)
    return t


def timeline(milestones, width=11.0):
    """milestones: lista de (titulo, descricao)."""
    line = Line(LEFT * width / 2, RIGHT * width / 2,
                stroke_color=KHAKI_D, stroke_width=2)
    dots = VGroup()
    labels = VGroup()
    n = len(milestones)
    for i, (title, sub) in enumerate(milestones):
        x = -width / 2 + width * i / max(1, n - 1)
        p = np.array([x, 0, 0])
        dots.add(Dot(p, radius=0.1, color=GREEN))
        ttl = tracked(title.upper(), FONT_DISPLAY, CREAM, 0.4, buff=0.07)
        sb = body(sub, 0.3, KHAKI)
        block = VGroup(ttl, sb).arrange(DOWN, buff=0.14)
        block.next_to(p, UP if i % 2 == 0 else DOWN, buff=0.42)
        labels.add(block)
    g = VGroup(line, dots, labels)
    g.line, g.dots, g.labels = line, dots, labels
    return g


def canvas_grid(blocks, cell_w=4.1, cell_h=1.85, rows=3, cols=3):
    """blocks: lista de (titulo, [itens]) — vira a grade do Business Model Canvas."""
    cells = VGroup()
    for title, items in blocks:
        p = panel(cell_w, cell_h)
        ttl = tracked(title.upper(), FONT_DISPLAY, GREEN, 0.28, buff=0.05)
        ttl.next_to(p.box.get_top(), DOWN, buff=0.16)
        txt = body("\n".join(items), 0.26, CREAM, line_spacing=0.8)
        txt.next_to(ttl, DOWN, buff=0.16)
        cell = VGroup(p, ttl, txt)
        cell.title_mob = ttl
        cells.add(cell)
    cells.arrange_in_grid(rows=rows, cols=cols, buff=0.22)
    return cells


def break_even_chart(fixed, unit_margin, x_max=40, x_length=8.4, y_length=4.0):
    """Receita de margem x custo fixo. Retorna VGroup com atributos nomeados."""
    y_max = max(fixed * 2.2, unit_margin * x_max)
    axes = Axes(
        x_range=[0, x_max, x_max / 4],
        y_range=[0, y_max, y_max / 4],
        x_length=x_length, y_length=y_length,
        axis_config={"color": KHAKI_D, "stroke_width": 2,
                     "include_ticks": True, "include_numbers": False},
        tips=False,
    )
    fixed_line = axes.plot(lambda x: fixed, x_range=[0, x_max],
                           color=AMBER, stroke_width=3)
    margin_line = axes.plot(lambda x: unit_margin * x, x_range=[0, x_max],
                            color=GREEN, stroke_width=3)

    x_be = fixed / unit_margin
    be_point = axes.c2p(x_be, fixed)
    be_dot = Dot(be_point, radius=0.09, color=CREAM)
    be_drop = DashedLine(be_point, axes.c2p(x_be, 0),
                         stroke_width=2, color=KHAKI_D)

    g = VGroup(axes, fixed_line, margin_line, be_drop, be_dot)
    g.axes = axes
    g.fixed_line = fixed_line
    g.margin_line = margin_line
    g.be_dot = be_dot
    g.be_drop = be_drop
    g.x_be = x_be
    return g


def radar_mark(radius=0.55):
    """Selo compacto do AEGIS para marcar canto de cena."""
    ring = Circle(radius=radius, stroke_color=KHAKI_D, stroke_width=2)
    mono = stencil_a(KHAKI).scale(radius / 1.55)
    return VGroup(ring, mono)
