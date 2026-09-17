from manim import *
from manim_slides import Slide

from aegis.theme import *
from aegis import data as d


class PlanoFinanceiro(Slide):
    def construct(self):
        frame = hud_frame("Plano Financeiro", "08 / 10")
        self.play(FadeIn(frame), run_time=0.6)

        # ---------- quanto custa montar ----------
        linhas = [[nome, d.brl(valor)] for nome, valor in d.ORCAMENTO_RESUMO]
        linhas.append(["TOTAL DO PROTÓTIPO", d.brl(d.CUSTO_PROTOTIPO)])

        tabela = data_table(linhas, headers=["Item", "Custo"], scale=0.5,
                            highlight_last=True)
        tabela.move_to(LEFT * 3.1 + DOWN * 0.4)

        notas = VGroup(
            body(f"Em escala (100 un.), o hardware cai para\n{d.brl(d.CUSTO_HARDWARE_ESCALA)} por kit.",
                 0.32, CREAM, line_spacing=1.0),
            body(d.NOTA_ESCALA, 0.22, KHAKI_D),
            body(f"Investimento inicial: {d.brl(d.TOTAL_INVESTIMENTO, 0)}",
                 0.36, GREEN),
        ).arrange(DOWN, buff=0.45, aligned_edge=LEFT)
        notas.move_to(RIGHT * 3.4 + DOWN * 0.4)

        self.play(FadeIn(tabela), run_time=0.9)
        self.next_slide()
        self.play(FadeIn(notas, shift=RIGHT * 0.25), run_time=0.7)
        self.next_slide()

        # ---------- a conta por kit ----------
        self.play(FadeOut(tabela), FadeOut(notas), run_time=0.6)

        tiles = VGroup(
            stat_tile(d.brl(d.CUSTO_UNITARIO, 0), "custo unitário\nem escala",
                      value_color=KHAKI),
            stat_tile(d.brl(d.PRECO_KIT, 0), "preço de venda\ndo kit"),
            stat_tile(f"{d.MARGEM_KIT_PCT}%", f"margem bruta\n{d.brl(d.MARGEM_KIT)} por kit"),
        ).arrange(RIGHT, buff=0.45).move_to(UP * 1.35)

        for t in tiles:
            self.play(FadeIn(t, shift=UP * 0.25), run_time=0.5)

        assinatura = body(
            f"Mais {d.brl(d.ASSINATURA)} por mês de assinatura, "
            f"com {d.brl(d.MARGEM_ASSINATURA)} de margem recorrente.",
            0.36, CREAM)
        assinatura.move_to(DOWN * 1.0)
        self.play(FadeIn(assinatura), run_time=0.6)
        self.next_slide()

        # ---------- ponto de equilíbrio ----------
        self.play(FadeOut(tiles), FadeOut(assinatura), run_time=0.6)

        grafico = break_even_chart(d.TOTAL_FIXO_MENSAL, d.MARGEM_KIT, x_max=30)
        grafico.move_to(DOWN * 0.55)

        eixo_x = body("kits vendidos por mês", 0.26, KHAKI_D)
        eixo_x.next_to(grafico.axes, DOWN, buff=0.25)
        eixo_y = body("R$ / mês", 0.26, KHAKI_D)
        eixo_y.next_to(grafico.axes, LEFT, buff=0.25).rotate(PI / 2)

        rot_fixo = body(f"custo fixo: {d.brl(d.TOTAL_FIXO_MENSAL, 0)}/mês",
                        0.28, AMBER)
        rot_fixo.next_to(grafico.fixed_line, UP, buff=0.22).shift(LEFT * 2.2)

        rot_margem = body("margem acumulada dos kits", 0.28, GREEN)
        rot_margem.next_to(grafico.margin_line.get_end(), UP, buff=0.15)
        rot_margem.shift(LEFT * 1.3)

        self.play(Create(grafico.axes), FadeIn(eixo_x), FadeIn(eixo_y),
                  run_time=0.9)
        self.play(Create(grafico.fixed_line), FadeIn(rot_fixo), run_time=0.8)
        self.play(Create(grafico.margin_line), FadeIn(rot_margem), run_time=1.0)

        equilibrio = tracked(f"{d.BREAK_EVEN_KITS} KITS POR MÊS", FONT_DISPLAY,
                             CREAM, 0.44, buff=0.08)
        equilibrio.next_to(grafico.be_dot, DOWN + RIGHT, buff=0.45)

        self.play(Create(grafico.be_drop), FadeIn(grafico.be_dot), run_time=0.6)
        self.play(FadeIn(equilibrio, scale=0.9), run_time=0.6)
        self.next_slide()

        # ---------- o efeito da recorrência ----------
        recorrencia = body(
            f"Depois de 12 meses nesse ritmo, a assinatura sozinha já gera\n"
            f"{d.brl(d.RECORRENTE_12M, 0)} por mês — quase todo o custo fixo coberto\n"
            f"pela receita recorrente.",
            0.38, GREEN, line_spacing=1.0)
        recorrencia.move_to(DOWN * 0.3)

        self.play(
            FadeOut(grafico), FadeOut(eixo_x), FadeOut(eixo_y),
            FadeOut(rot_fixo), FadeOut(rot_margem), FadeOut(equilibrio),
            run_time=0.7,
        )
        self.play(FadeIn(recorrencia, shift=UP * 0.2), run_time=0.8)
        self.next_slide()
