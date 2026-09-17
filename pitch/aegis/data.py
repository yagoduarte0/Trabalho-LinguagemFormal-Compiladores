"""Números do pitch AEGIS. Edite aqui — nenhuma cena tem número escrito no meio da animação.

Toda estatística de mercado traz a fonte junto, para responder à banca.
"""


def brl(valor, casas=2):
    """Formata no padrão brasileiro: 3900 -> 'R$ 3.900,00'."""
    s = f"{valor:,.{casas}f}"
    return "R$ " + s.replace(",", "X").replace(".", ",").replace("X", ".")

# ---------------------------------------------------------------------------
# PESQUISA DE MERCADO
# ---------------------------------------------------------------------------

PESSOAS_AREA_RISCO = "8,27 MI"
PESSOAS_AREA_RISCO_FONTE = "IBGE + Cemaden, População em Áreas de Risco no Brasil (Censo 2010)"

DOMICILIOS_AREA_RISCO = "2,47 MI"
DOMICILIOS_AREA_RISCO_NUM = 2_471_349

DESASTRES_2024 = "1.600+"
DESASTRES_2024_FONTE = "Cemaden, ocorrências registradas em 2024"

ALTA_DESASTRES = "+250%"
ALTA_DESASTRES_FONTE = "S2iD/MIDR — 2020-2023 (16.306) vs. década de 1990 (6.523)"

MUNICIPIOS_COM_DESASTRE = "88%"
MUNICIPIOS_COM_DESASTRE_FONTE = "CNM — municípios com desastre climático em 2024 (era 29% em 2013)"

MERCADO_SEGURANCA = "R$ 14 BI"
MERCADO_SEGURANCA_FONTE = "ABESE, Panorama 2024/2025 — setor cresceu 16,1% em 2024"

MERCADO_SMART_HOME = "US$ 2,96 BI"
MERCADO_SMART_HOME_FONTE = "Grand View Research — Brasil 2024, CAGR 27,6% até 2030"

# Os três números que abrem a apresentação
ABERTURA_STATS = [
    (PESSOAS_AREA_RISCO, "de brasileiros vivem\nem áreas de risco"),
    (DESASTRES_2024, "desastres registrados\nsó em 2024"),
    (ALTA_DESASTRES, "de aumento frente\nà década de 1990"),
]

# ---------------------------------------------------------------------------
# TAM / SAM / SOM
# ---------------------------------------------------------------------------

TAM = ("R$ 14 BI", "Segurança eletrônica no Brasil", "ABESE 2024")
SAM = ("R$ 1,36 BI", "2,47 mi de domicílios em área de risco", "IBGE/Cemaden")
SOM = ("R$ 210 MIL", "300 kits no primeiro ano", "meta conservadora")

# ---------------------------------------------------------------------------
# ORÇAMENTO DO PROTÓTIPO (preços de varejo, Eletrogate/Mercado Livre, set/2026)
# ---------------------------------------------------------------------------

BOM = [
    ("ESP32 DevKit V1", "Controlador WiFi", 59.90),
    ("PIR HC-SR501", "Presença", 11.90),
    ("HC-SR04", "Nível de água", 9.90),
    ("MQ-2", "Fumaça e gás", 14.72),
    ("MQ-135", "Qualidade do ar", 16.90),
    ("DHT22", "Temperatura e umidade", 45.00),
    ("Protoboard 830", "Montagem", 11.90),
    ("Kit jumpers", "Montagem", 8.90),
    ("Fonte 5V 2A", "Alimentação", 17.00),
    ("Buzzer + LEDs", "Alertas", 21.40),
    ("Case", "Gabinete", 18.40),
]

CUSTO_PROTOTIPO = round(sum(item[2] for item in BOM), 2)   # R$ 235,92
FAIXA_PROTOTIPO = "R$ 220 a R$ 260"

DESCONTO_ESCALA = 0.35
CUSTO_HARDWARE_ESCALA = round(CUSTO_PROTOTIPO * (1 - DESCONTO_ESCALA), 2)  # ~R$ 153
NOTA_ESCALA = "Estimativa por desconto de volume típico do setor (100 un.), não cotação fechada"

# ---------------------------------------------------------------------------
# MODELO FINANCEIRO
# ---------------------------------------------------------------------------

CUSTO_MONTAGEM = 45.00
CUSTO_UNITARIO = round(CUSTO_HARDWARE_ESCALA + CUSTO_MONTAGEM, 2)   # ~R$ 198
PRECO_KIT = 549.00
MARGEM_KIT = round(PRECO_KIT - CUSTO_UNITARIO, 2)                   # ~R$ 351
MARGEM_KIT_PCT = round(MARGEM_KIT / PRECO_KIT * 100)                # ~64%

ASSINATURA = 29.90
CUSTO_SERVIR = 4.00
MARGEM_ASSINATURA = round(ASSINATURA - CUSTO_SERVIR, 2)             # R$ 25,90

INVESTIMENTO_INICIAL = [
    ("Protótipos e testes", 3_000),
    ("Estoque inicial (50 kits)", 9_900),
    ("Desenvolvimento e ferramentas", 4_000),
    ("Marca, registro e contabilidade", 3_000),
    ("Marketing de lançamento", 5_000),
]
TOTAL_INVESTIMENTO = sum(v for _, v in INVESTIMENTO_INICIAL)        # R$ 24.900

CUSTOS_FIXOS = [
    ("Infraestrutura e nuvem", 600),
    ("Marketing", 2_000),
    ("Administrativo e contábil", 900),
    ("Ferramentas e licenças", 400),
]
TOTAL_FIXO_MENSAL = sum(v for _, v in CUSTOS_FIXOS)                 # R$ 3.900

import math
BREAK_EVEN_KITS = math.ceil(TOTAL_FIXO_MENSAL / MARGEM_KIT)         # 12 kits/mês

# Depois de 12 meses vendendo no ritmo do ponto de equilíbrio,
# a assinatura sozinha já cobre quase todo o custo fixo.
BASE_ASSINANTES_12M = BREAK_EVEN_KITS * 12
RECORRENTE_12M = round(BASE_ASSINANTES_12M * MARGEM_ASSINATURA)

# ---------------------------------------------------------------------------
# BUSINESS MODEL CANVAS
# ---------------------------------------------------------------------------

CANVAS = [
    ("Proposta de valor", [
        "Automação que protege,",
        "não só a que dá conforto.",
        "Funciona sem internet.",
    ]),
    ("Clientes", [
        "Famílias em áreas de risco",
        "Entusiastas de preparo",
        "Sítios e casas de campo",
    ]),
    ("Canais", [
        "Venda direta online",
        "Marketplaces",
        "Parcerias com integradores",
    ]),
    ("Parcerias", [
        "Distribuidores de eletrônica",
        "Defesa Civil municipal",
        "Lojas de material de construção",
    ]),
    ("Atividades", [
        "Montagem dos kits",
        "Desenvolvimento da linguagem",
        "Suporte e atualizações",
    ]),
    ("Recursos", [
        "Linguagem AEGIS própria",
        "Firmware ESP32",
        "Plataforma de monitoramento",
    ]),
    ("Relacionamento", [
        "Instalação assistida",
        "Comunidade de usuários",
        "Suporte por assinatura",
    ]),
    ("Custos", [
        f"Hardware: R$ {CUSTO_UNITARIO:.0f}/kit",
        f"Fixos: R$ {TOTAL_FIXO_MENSAL:,}/mês".replace(",", "."),
        "Marketing e suporte",
    ]),
    ("Receitas", [
        f"Kit: R$ {PRECO_KIT:.0f} (venda única)",
        f"Assinatura: R$ {ASSINATURA:.2f}/mês".replace(".", ","),
        "Instalação sob demanda",
    ]),
]

# Orçamento agrupado para caber numa tabela legível no slide
ORCAMENTO_RESUMO = [
    ("Controlador ESP32", 59.90),
    ("5 sensores", 98.42),
    ("Montagem e alimentação", 59.20),
    ("Gabinete", 18.40),
]

# ---------------------------------------------------------------------------
# CRONOGRAMA DO PRODUTO
# ---------------------------------------------------------------------------

ROADMAP = [
    ("MVP", "Mês 1-2\nProtótipo + linguagem"),
    ("Piloto", "Mês 3-4\n10 casas em área de risco"),
    ("Produção", "Mês 5-8\nPrimeiro lote de 100"),
    ("Lançamento", "Mês 9-12\nVenda direta e marketplaces"),
    ("Expansão", "Ano 2\nDefesa Civil e condomínios"),
]

# ---------------------------------------------------------------------------
# OS 5 MÓDULOS MONITORADOS
# ---------------------------------------------------------------------------

MODULOS = [
    ("Presença", "PIR HC-SR501", "Detecta movimento no perímetro"),
    ("Água", "HC-SR04", "Mede o nível da reserva"),
    ("Fumaça", "MQ-2", "Identifica princípio de incêndio"),
    ("Ar", "MQ-135", "Monitora qualidade do ar"),
    ("Temperatura", "DHT22", "Temperatura e umidade"),
]
