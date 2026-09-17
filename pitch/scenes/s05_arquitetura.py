from manim import *
from manim_slides import Slide
import numpy as np

from aegis.theme import *

# palavras de controle em verde, chamadas de hardware em cáqui
KW = {
    "law": GREEN, "supply": GREEN, "checkpoint": GREEN, "fallback": GREEN,
    "if": GREEN, "else": GREEN,
    "broadcast": KHAKI, "log_entry": KHAKI, "radio": KHAKI, "gpio": KHAKI,
}

# As duas listas são alinhadas por índice; a posição vazia no fim do Python é
# onde a chave de fechamento do AEGIS desaparece, porque Python usa indentação.
# Este Python é a saída real do compilador, não uma tradução escrita à mão.
AEGIS_SRC = [
    "law ALARME = 5",
    "supply perigo = gpio.read(radio(27))",
    "",
    "checkpoint (perigo) {",
    "  broadcast(radio(ALARME))",
    "} fallback {",
    '  log_entry("area limpa")',
    "}",
]

PYTHON_SRC = [
    "ALARME = 5  # constante",
    "perigo = gpio.read(radio(27))",
    "",
    "if perigo:",
    "    broadcast(radio(ALARME))",
    "else:",
    '    log_entry("area limpa")',
    "",
]

ETAPAS = [
    ("Sensores", "5 módulos"),
    ("ESP32", "coleta e envia"),
    ("Linguagem\nAEGIS", "regras legíveis"),
    ("Compilador", "léxico, sintático, AST"),
    ("Python", "executa e alerta"),
]


def code_block(linhas, scale=0.30, line_h=0.44, indent_w=0.3):
    """Cada linha é posicionada à mão: o Text do Manim descarta espaços à esquerda."""
    bloco = VGroup()
    for i, ln in enumerate(linhas):
        if ln.strip() == "":
            continue
        indent = (len(ln) - len(ln.lstrip())) // 2
        m = Text(ln.strip(), font=FONT_MONO, color=CREAM, t2c=KW).scale(scale)
        m.move_to([indent * indent_w, -i * line_h, 0], aligned_edge=LEFT)
        bloco.add(m)
    return bloco


class ComoFunciona(Slide):
    def construct(self):
        frame = hud_frame("Como Funciona", "05 / 10")
        self.play(FadeIn(frame), run_time=0.6)

        # ---------- o caminho do dado ----------
        caixas = VGroup()
        for titulo, sub in ETAPAS:
            p = panel(2.25, 1.6)
            t = tracked(titulo.upper().replace("\n", " "), FONT_DISPLAY,
                        CREAM, 0.28, buff=0.05)
            s = body(sub, 0.22, KHAKI_D)
            stack = VGroup(t, s).arrange(DOWN, buff=0.18)
            stack.move_to(p.box.get_center())
            caixas.add(VGroup(p, stack))

        caixas.arrange(RIGHT, buff=0.58).move_to(UP * 1.75)
        caixas[2][0].box.set_stroke(GREEN)
        caixas[3][0].box.set_stroke(GREEN)

        setas = VGroup(*[
            Arrow(caixas[i].get_right(), caixas[i + 1].get_left(),
                  buff=0.1, stroke_width=3, color=KHAKI_D,
                  max_tip_length_to_length_ratio=0.3)
            for i in range(len(caixas) - 1)
        ])

        for i, caixa in enumerate(caixas):
            self.play(FadeIn(caixa, shift=RIGHT * 0.25), run_time=0.4)
            if i < len(setas):
                self.play(GrowArrow(setas[i]), run_time=0.25)
        self.next_slide()

        nota = body("O diferencial está no meio do caminho: as regras de automação\n"
                    "são escritas na linguagem AEGIS, que o compilador traduz para Python.",
                    0.36, KHAKI, line_spacing=1.0)
        nota.move_to(DOWN * 0.15)
        self.play(FadeIn(nota, shift=UP * 0.2), run_time=0.7)
        self.next_slide()

        # ---------- a mesma regra, duas linguagens ----------
        self.play(FadeOut(nota), run_time=0.4)

        aegis_lbl = tracked("LINGUAGEM AEGIS", FONT_DISPLAY, GREEN, 0.3, buff=0.06)
        py_lbl = tracked("PYTHON GERADO", FONT_DISPLAY, KHAKI, 0.3, buff=0.06)

        aegis_code = code_block(AEGIS_SRC)
        py_code = code_block(PYTHON_SRC)

        # alinhados pelo topo (e não pelo centro) para cada linha do AEGIS
        # ficar no mesmo nível da linha de Python que ela gera
        for bloco, x_esq in ((aegis_code, -6.2), (py_code, 0.75)):
            bloco.align_to(np.array([0, -0.25, 0]), UP)
            bloco.align_to(np.array([x_esq, 0, 0]), LEFT)

        aegis_lbl.next_to(aegis_code, UP, buff=0.34).align_to(aegis_code, LEFT)
        py_lbl.next_to(py_code, UP, buff=0.34).align_to(py_code, LEFT)

        self.play(FadeIn(aegis_lbl), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(ln, shift=RIGHT * 0.2) for ln in aegis_code],
                              lag_ratio=0.15), run_time=1.4)
        self.next_slide()

        seta_c = Arrow(aegis_code.get_right() + RIGHT * 0.15,
                       py_code.get_left() + LEFT * 0.15,
                       buff=0.1, stroke_width=3, color=GREEN,
                       max_tip_length_to_length_ratio=0.25)
        compilador = body("compilador", 0.26, GREEN)
        compilador.next_to(seta_c, UP, buff=0.14)

        self.play(GrowArrow(seta_c), FadeIn(compilador), FadeIn(py_lbl),
                  run_time=0.7)

        for origem, destino in zip(aegis_code, py_code):
            self.play(TransformMatchingShapes(origem.copy(), destino),
                      run_time=0.55)
        self.next_slide()
