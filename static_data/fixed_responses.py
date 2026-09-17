"""
Respostas e diálogos fixos da missa — não vêm de scraping,
pois são sempre os mesmos independentemente do domingo.

Isso alimenta o pptx_builder para gerar slides de partes fixas da
celebração (saudação inicial, ato penitencial, diálogo eucarístico,
etc.), enquanto o conteúdo dinâmico (leituras, salmo, homilia,
músicas) vem do SundayMass montado pelo scraper + edição manual.

Sinta-se à vontade para editar os textos abaixo caso a paróquia
utilize alguma variação diferente (ex: outra fórmula de saudação).
"""

GREETING_RESPONSE = "Bendito seja Deus que nos reuniu no amor de Cristo."

PENITENTIAL_ACT_KYRIE = [
    ("Senhor, tende piedade de nós.", "Senhor, tende piedade de nós."),
    ("Cristo, tende piedade de nós.", "Cristo, tende piedade de nós."),
    ("Senhor, tende piedade de nós.", "Senhor, tende piedade de nós."),
]

# Texto conforme a 3ª edição típica do Missal Romano (tradução CNBB, em uso
# no Brasil desde o Advento de 2020). Omitido no Advento e na Quaresma —
# quem monta o deck decide isso a partir de mass.liturgical_color.
GLORIA = (
    "Glória a Deus nas alturas, e paz na terra aos homens por Ele amados. "
    "Senhor Deus, Rei dos céus, Deus Pai todo-poderoso, nós vos louvamos, "
    "vos bendizemos, vos adoramos, vos glorificamos, vos damos graças por "
    "vossa imensa glória. "
    "Senhor Jesus Cristo, Filho Unigênito, Senhor Deus, Cordeiro de Deus, "
    "Filho de Deus Pai. "
    "Vós que tirais o pecado do mundo, tende piedade de nós. "
    "Vós que tirais o pecado do mundo, acolhei a nossa súplica. "
    "Vós que estais à direita do Pai, tende piedade de nós. "
    "Só vós sois o Santo, só vós, o Senhor, só vós, o Altíssimo, Jesus "
    "Cristo, com o Espírito Santo, na glória de Deus Pai. Amém."
)

GOSPEL_DIALOGUE = {
    "before": "Glória a vós, Senhor.",
    "after": "Palavra da Salvação.",
    "after_response": "Glória a vós, Senhor.",
}

READING_DIALOGUE = {
    "leader": "Palavra do Senhor.",
    "response": "Graças a Deus.",
}

CREED_TITLE = "Credo"  # Niceno-Constantinopolitano (ou Apostólico, se preferir configurar)

# Credo Niceno-Constantinopolitano, tradução CNBB (3ª edição típica).
# Troque por CREED_APOSTLES abaixo se a paróquia costuma rezar o Apostólico.
CREED_NICENE = (
    "Creio em um só Deus, Pai todo-poderoso, criador do céu e da terra, "
    "do universo visível e invisível. "
    "Creio em um só Senhor, Jesus Cristo, Filho Unigênito de Deus, "
    "nascido do Pai antes de todos os séculos: Deus de Deus, Luz da Luz, "
    "Deus verdadeiro de Deus verdadeiro; gerado, não criado, "
    "consubstancial ao Pai. Por Ele todas as coisas foram criadas. "
    "E por nossa causa, e para nossa salvação, desceu dos céus. "
    "E encarnou pelo Espírito Santo, no seio da Virgem Maria e se fez "
    "homem. Também por nós foi crucificado sob Pôncio Pilatos; padeceu "
    "e foi sepultado. Ressuscitou ao terceiro dia, conforme as "
    "Escrituras; e subiu aos céus, onde está sentado à direita do Pai. "
    "E de novo há de vir, em sua glória, para julgar os vivos e os "
    "mortos; e o seu reino não terá fim. "
    "Creio no Espírito Santo, Senhor que dá a vida, que procede do Pai "
    "e do Filho; e com o Pai e o Filho é adorado e glorificado: Ele que "
    "falou pelos profetas. "
    "Creio na Igreja, una, santa, católica e apostólica. "
    "Professo um só batismo para a remissão dos pecados. E espero a "
    "ressurreição dos mortos e a vida do mundo que há de vir. Amém."
)

CREED_APOSTLES = (
    "Creio em Deus Pai todo-poderoso, criador do céu e da terra. "
    "E em Jesus Cristo, seu único Filho, nosso Senhor, que foi concebido "
    "pelo poder do Espírito Santo; nasceu da Virgem Maria; padeceu sob "
    "Pôncio Pilatos, foi crucificado, morto e sepultado; desceu à "
    "mansão dos mortos; ressuscitou ao terceiro dia; subiu aos céus, "
    "está sentado à direita de Deus Pai todo-poderoso, donde há de vir "
    "a julgar os vivos e os mortos. "
    "Creio no Espírito Santo, na Santa Igreja Católica, na comunhão dos "
    "santos, na remissão dos pecados, na ressurreição da carne, na "
    "vida eterna. Amém."
)

PRAYERS_OF_THE_FAITHFUL_RESPONSE = "Senhor, escutai a nossa prece."  # comum, mas verificar com a paróquia

EUCHARISTIC_DIALOGUE = [
    ("O Senhor esteja convosco.", "Ele está no meio de nós."),
    ("Corações ao alto.", "O nosso coração está em Deus."),
    ("Demos graças ao Senhor, nosso Deus.", "É nosso dever e nossa salvação."),
]

SANCTUS = (
    "Santo, Santo, Santo, Senhor Deus do Universo. "
    "O céu e a terra proclamam a vossa glória. "
    "Hosana nas alturas! "
    "Bendito o que vem em nome do Senhor. "
    "Hosana nas alturas!"
)

MYSTERY_OF_FAITH_OPTIONS = [
    "Anunciamos, Senhor, a vossa morte e proclamamos a vossa ressurreição, enquanto esperamos a vossa vinda.",
    "Todas as vezes que comemos deste pão e bebemos deste cálice, anunciamos, Senhor, a vossa morte, enquanto esperamos a vossa vinda.",
    "Senhor, nós vos louvamos, Senhor, nós vos bendizemos, nós vos rendemos graças, esperando a vossa vinda.",
]

OUR_FATHER_TITLE = "Pai Nosso"

OUR_FATHER_TEXT = (
    "Pai nosso que estais nos céus, santificado seja o vosso nome; "
    "venha a nós o vosso reino; seja feita a vossa vontade, assim na "
    "terra como no céu. "
    "O pão nosso de cada dia nos dai hoje; perdoai-nos as nossas "
    "ofensas, assim como nós perdoamos a quem nos tem ofendido; "
    "e não nos deixeis cair em tentação; mas livrai-nos do mal. Amém."
)

SIGN_OF_PEACE = "A paz do Senhor esteja sempre convosco. E com o vosso espírito."

LAMB_OF_GOD = (
    "Cordeiro de Deus, que tirais o pecado do mundo, tende piedade de nós. "
    "Cordeiro de Deus, que tirais o pecado do mundo, tende piedade de nós. "
    "Cordeiro de Deus, que tirais o pecado do mundo, dai-nos a paz."
)

DISMISSAL_RESPONSE = "Graças a Deus."

# Nomes das 4 orações eucarísticas mais comuns no Missal Romano (1 a 4),
# mais a V (usada às vezes, com variantes a/b/c/d). Ajuste conforme o
# que o padre normalmente usa na paróquia.
EUCHARISTIC_PRAYER_NAMES = {
    1: "Oração Eucarística I (Cânon Romano)",
    2: "Oração Eucarística II",
    3: "Oração Eucarística III",
    4: "Oração Eucarística IV",
    5: "Oração Eucarística V (Reconciliação / Circunstâncias especiais)",
}
