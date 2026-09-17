"""
Monta a sequência completa de slides da missa (SlideSpec), combinando o
conteúdo dinâmico do SundayMass (leituras, salmo, evangelho, músicas) com
as partes fixas de static_data/fixed_responses.py (saudação, ato
penitencial, Glória, Credo, diálogo eucarístico, Santo, Pai Nosso, etc.).

Este módulo não sabe nada sobre python-pptx — só produz uma lista de
SlideSpec. Quem escreve o .pptx de fato é o render.py.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from content_model.sunday_mass import SundayMass, Song
from static_data.fixed_responses import (
    GREETING_RESPONSE,
    PENITENTIAL_ACT_KYRIE,
    GLORIA,
    CREED_TITLE,
    CREED_NICENE,
    PRAYERS_OF_THE_FAITHFUL_RESPONSE,
    EUCHARISTIC_DIALOGUE,
    SANCTUS,
    MYSTERY_OF_FAITH_OPTIONS,
    OUR_FATHER_TITLE,
    SIGN_OF_PEACE,
    LAMB_OF_GOD,
    DISMISSAL_RESPONSE,
)
from pptx_builder.text_fit import split_into_slide_chunks


@dataclass
class SlideSpec:
    layout: str  # "title" (PASCOM_Título) ou "content" (PASCOM_Título e Conteúdo)
    title: Optional[str] = None
    body: Optional[list[str]] = None  # parágrafos; None para slide-título puro
    # "leader" (padre/leitor, Arial normal) ou "assembly" (resposta da
    # assembleia, prefixo "R:" + Arial negrito) — None mantém o estilo
    # padrão do template (Arial Black) usado no resto do deck.
    role: Optional[str] = None


# Fonte usada em cada role, pra render.py aplicar e pro text_fit medir com
# precisão (ver ROLE_FONT_VARIANT em render.py, que precisa bater com isto).
_ROLE_FONT_VARIANT = {"leader": "regular", "assembly": "bold"}


def _title_slide(text: str) -> SlideSpec:
    return SlideSpec(layout="title", title=text)


def _content_slides(
    part_title: str,
    text: str,
    *,
    is_prose: bool,
    box_width_emu: int,
    box_height_emu: int,
    font_size_pt: float,
    role: Optional[str] = None,
) -> list[SlideSpec]:
    chunks = split_into_slide_chunks(
        text,
        is_prose=is_prose,
        box_width_emu=box_width_emu,
        box_height_emu=box_height_emu,
        font_size_pt=font_size_pt,
        font_variant=_ROLE_FONT_VARIANT.get(role, "black"),
    )
    return [SlideSpec(layout="content", title=part_title, body=chunk, role=role) for chunk in chunks]


def _song_slides(
    song: Song, *, box_width_emu: int, box_height_emu: int, font_size_pt: float
) -> list[SlideSpec]:
    part_title = f"Música: {song.moment}"
    announcement = f"{song.title} — {song.author}" if song.author else song.title
    slides = (
        _content_slides(
            part_title,
            announcement,
            is_prose=True,
            box_width_emu=box_width_emu,
            box_height_emu=box_height_emu,
            font_size_pt=font_size_pt,
        )
        if announcement.strip()
        else []
    )
    if song.lyrics.strip():
        chunks = split_into_slide_chunks(
            song.lyrics,
            is_prose=False,
            box_width_emu=box_width_emu,
            box_height_emu=box_height_emu,
            font_size_pt=font_size_pt,
        )
        slides.extend(SlideSpec(layout="content", title=part_title, body=chunk) for chunk in chunks)
    return slides


def _songs_for_moment(songs: list[Song], moment: str) -> list[Song]:
    return [s for s in songs if s.moment.strip().lower() == moment.strip().lower()]


def build_full_deck(
    mass: SundayMass,
    *,
    box_width_emu: int,
    box_height_emu: int,
    font_size_pt: float = 96,
) -> list[SlideSpec]:
    slides: list[SlideSpec] = []

    def content(part_title: str, text: str, is_prose: bool = True, role: Optional[str] = None) -> None:
        slides.extend(
            _content_slides(
                part_title,
                text,
                is_prose=is_prose,
                box_width_emu=box_width_emu,
                box_height_emu=box_height_emu,
                font_size_pt=font_size_pt,
                role=role,
            )
        )

    def line(part_title: str, text: str) -> None:
        # "Fala curta" ainda passa pelo chunking normal — o texto pode vir
        # do scraper (ex: fala do leitor) e não temos garantia de que
        # sempre caiba num único slide de 4 linhas.
        if text and text.strip():
            content(part_title, text)

    def leader(part_title: str, text: str) -> None:
        """Fala do padre/leitor — Arial normal, sem prefixo."""
        if text and text.strip():
            content(part_title, text, role="leader")

    def assembly(part_title: str, text: str) -> None:
        """Resposta da assembleia — prefixo 'R:' + Arial negrito."""
        if text and text.strip():
            content(part_title, f"R: {text}", role="assembly")

    def dialogue(part_title: str, leader_text: str, assembly_text: str) -> None:
        leader(part_title, leader_text)
        assembly(part_title, assembly_text)

    def songs(moment: str) -> None:
        for song in _songs_for_moment(mass.songs, moment):
            slides.extend(
                _song_slides(
                    song,
                    box_width_emu=box_width_emu,
                    box_height_emu=box_height_emu,
                    font_size_pt=font_size_pt,
                )
            )

    # 1. Título da missa
    slides.append(_title_slide(mass.liturgical_day))

    # 2. Música de Entrada
    songs("Entrada")

    # 3. Saudação Inicial
    line("Saudação Inicial", GREETING_RESPONSE)

    # 4. Ato Penitencial
    for leader_text, assembly_text in PENITENTIAL_ACT_KYRIE:
        dialogue("Ato Penitencial", leader_text, assembly_text)

    # Glória — omitido no Advento/Quaresma (cor litúrgica Roxo)
    if mass.liturgical_color.strip().lower() != "roxo":
        content("Glória", GLORIA)

    # 5. Liturgia da Palavra
    slides.append(_title_slide("Liturgia da Palavra"))

    # Leitura/Evangelho projetam só a referência (quem lê usa o Lecionário/
    # Missal impresso) — sem o corpo do texto e sem os diálogos de resposta
    # ("Palavra do Senhor." / "R: Graças a Deus." etc.).
    if mass.first_reading:
        content("1ª Leitura", mass.first_reading.reference)

    if mass.psalm:
        p = mass.psalm
        assembly("Salmo Responsorial", p.response)

    if mass.second_reading:
        content("2ª Leitura", mass.second_reading.reference)

    if mass.gospel_acclamation:
        ga = mass.gospel_acclamation
        line("Aclamação ao Evangelho", ga.text)
        if ga.verse:
            content("Aclamação ao Evangelho", ga.verse)
        line("Aclamação ao Evangelho", ga.text)

    if mass.gospel:
        content("Evangelho", mass.gospel.reference)

    # Homilia — sem slide, é falada livremente pelo padre.

    # 6. Credo
    slides.append(_title_slide(CREED_TITLE))
    content(CREED_TITLE, CREED_NICENE)

    # 7. Preces da Assembleia (as intenções em si não são modeladas — só a resposta fixa)
    line("Preces da Assembleia", PRAYERS_OF_THE_FAITHFUL_RESPONSE)

    # 8. Música de Ofertório
    songs("Ofertório")

    # 9. Liturgia Eucarística
    slides.append(_title_slide("Liturgia Eucarística"))

    for leader_text, assembly_text in EUCHARISTIC_DIALOGUE:
        dialogue("Diálogo Eucarístico", leader_text, assembly_text)

    content("Santo", SANCTUS)

    # Oração Eucarística — sem slide, é reservada ao padre;
    # mass.eucharistic_prayer fica só como metadado (qual prece ele escolheu).

    # Mistério da Fé — as 3 opções em slides separados; quem opera o telão
    # escolhe qual mostrar conforme o que o padre disser (ver nota no plano
    # sobre um agente futuro que decida isso automaticamente).
    for i, option in enumerate(MYSTERY_OF_FAITH_OPTIONS, start=1):
        content(f"Mistério da Fé — Opção {i}", option)

    # 10. Pai Nosso — só o título (rezado de cor, sem projetar o texto)
    slides.append(_title_slide(OUR_FATHER_TITLE))

    line("Saudação da Paz", SIGN_OF_PEACE)

    content("Cordeiro de Deus", LAMB_OF_GOD)

    # 11. Músicas de Comunhão e Ação de Graças
    songs("Comunhão")
    songs("Ação de Graças")

    # 12. Rito Final
    line("Rito Final", DISMISSAL_RESPONSE)

    songs("Final")

    return slides
