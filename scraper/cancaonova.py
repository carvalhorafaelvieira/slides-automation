"""
Scraper da Canção Nova (liturgia.cancaonova.com).

Validado contra o HTML real do site (ver `find_url_for_date` e
`parse_mass_page`). Cada parte da liturgia (1ª Leitura, Salmo, 2ª
Leitura, Evangelho) fica numa aba (`div.tab-pane`) com a referência
bíblica em `div.referencia`; extraímos o conteúdo a partir dessa
estrutura em vez de heurísticas de texto solto.

A navegação por data usa um POST para /wp-admin/admin-ajax.php — o
widget de calendário do site é 100% client-side (JS faz esse POST ao
clicar em "mês anterior/seguinte"); os parâmetros `sMes`/`sAno` na URL
da própria página de calendário são ignorados pelo servidor.
"""
from __future__ import annotations

import re
from datetime import date
from typing import Optional

import requests
from bs4 import BeautifulSoup

from content_model.sunday_mass import (
    SundayMass, Reading, Psalm, GospelAcclamation, Gospel,
)

BASE_URL = "https://liturgia.cancaonova.com"
ADMIN_AJAX_URL = f"{BASE_URL}/wp-admin/admin-ajax.php"

HEADERS = {
    # Alguns sites bloqueiam requests sem um User-Agent de navegador.
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}


def find_url_for_date(target_date: date) -> str:
    """
    Encontra a URL da página de liturgia para uma data específica.

    O widget de calendário do site NÃO navega por GET (`?sMes=&sAno=` na
    própria página sempre mostra o mês atual do servidor, independente
    dos parâmetros) — a troca de mês é feita via JS por um POST em
    /wp-admin/admin-ajax.php (action=widget-ajax), que devolve o HTML do
    calendário daquele mês com um link por dia. Reproduzimos esse POST
    diretamente para conseguir navegar para qualquer mês/ano.
    """
    payload = {
        "action": "widget-ajax",
        "sMes": f"{target_date.month:02d}",
        "sAno": str(target_date.year),
        "title": "",
        "type": "liturgia",
        "ajax": "true",
    }
    resp = requests.post(ADMIN_AJAX_URL, headers=HEADERS, data=payload, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # Procura por um link cujo href contenha os parâmetros de data exatos.
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if f"sDia={target_date.day}&" in href and f"sMes={target_date.month:02d}" in href and f"sAno={target_date.year}" in href:
            if href.startswith("http"):
                return href
            return BASE_URL + href

    raise ValueError(
        f"Não encontrei link para {target_date.isoformat()} no calendário "
        f"(POST para {ADMIN_AJAX_URL} com sMes={target_date.month:02d}, sAno={target_date.year})."
    )


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _strip_leading_dash(text: str) -> str:
    # As falas de líder/assembleia vêm marcadas no site com um "-" ou "—"
    # inicial (indicação de quem fala), que não deve ir para o slide.
    return re.sub(r"^[-–—]\s*", "", text).strip()


# Em algumas páginas (observado em snapshots mais antigos do site),
# <div class="referencia"> vem só com a citação limpa (ex: "Is 22,19-23"),
# mas em outras vem com o rótulo da seção embutido (ex:
# "Primeira Leitura (Pr 8,22-31)" ou "Responsório Sl 8,4-5... (R. 2a)").
# Removemos esses rótulos para sempre obter só a citação bíblica.
_REFERENCE_LABEL_PREFIXES = [
    "Primeira Leitura", "1ª Leitura", "1a Leitura",
    "Segunda Leitura", "2ª Leitura", "2a Leitura",
    "Terceira Leitura", "3ª Leitura", "3a Leitura",
    "Responsório", "Salmo Responsorial",
    "Evangelho",
]


def _clean_reference(raw: str) -> str:
    text = _clean(raw)
    for prefix in _REFERENCE_LABEL_PREFIXES:
        m = re.match(rf"^{re.escape(prefix)}\s*", text, re.IGNORECASE)
        if m:
            text = text[m.end():].strip()
            if text.startswith("(") and text.endswith(")") and text.count("(") == text.count(")"):
                text = text[1:-1].strip()
            break
    return text


def _tab_reference_map(soup: BeautifulSoup) -> dict[str, tuple[str, str]]:
    """
    A página organiza cada parte da liturgia (1ª Leitura, Salmo, 2ª Leitura,
    Evangelho) numa aba, com a referência bíblica exata em
    <div class="referencia">. Mapeamos id-da-aba -> (rótulo, referência).
    """
    mapping: dict[str, tuple[str, str]] = {}
    tab_list = soup.find("ul", class_="menu-leituras")
    if tab_list is None:
        return mapping
    for a in tab_list.find_all("a", href=True):
        pane_id = a["href"].lstrip("#")
        label_el = a.find("label")
        ref_el = a.find("div", class_="referencia")
        label = _clean(label_el.get_text()) if label_el else ""
        reference = _clean_reference(ref_el.get_text()) if ref_el else ""
        mapping[pane_id] = (label, reference)
    return mapping


def _pane_paragraphs(soup: BeautifulSoup, pane_id: str) -> list[str]:
    """Texto de cada <p> direto dentro da aba, pulando o player de áudio."""
    pane = soup.find(id=pane_id)
    if pane is None:
        return []
    texts = []
    for p in pane.find_all("p", recursive=False):
        if p.find("div", class_="embeds-audio"):
            continue
        text = p.get_text(" ", strip=True)
        if text:
            texts.append(text)
    return texts


def _parse_reading_pane(soup: BeautifulSoup, pane_id: str, reference: str) -> Optional[Reading]:
    paragraphs = _pane_paragraphs(soup, pane_id)
    if len(paragraphs) < 2:
        return None

    # paragraphs[0] é o cabeçalho ("Primeira Leitura (Is 22,19-23)") — descartado,
    # já temos a referência vinda da aba.
    source_label = paragraphs[1]

    leader_idx = None
    assembly_idx = None
    for i, text in enumerate(paragraphs):
        if leader_idx is None and re.search(r"Palavra do Senhor", text, re.IGNORECASE):
            leader_idx = i
        if re.search(r"Gra[cç]as a Deus", text, re.IGNORECASE):
            assembly_idx = i

    body_end = leader_idx if leader_idx is not None else len(paragraphs)
    body_paragraphs = paragraphs[2:body_end]
    text = _clean(" ".join(body_paragraphs))

    leader_line = (
        _strip_leading_dash(paragraphs[leader_idx]) if leader_idx is not None else "Palavra do Senhor."
    )
    assembly_response = (
        _strip_leading_dash(paragraphs[assembly_idx]) if assembly_idx is not None else "Graças a Deus."
    )

    return Reading(
        reference=reference,
        source_label=source_label,
        text=text,
        leader_line=leader_line,
        assembly_response=assembly_response,
    )


def _parse_psalm_pane(soup: BeautifulSoup, pane_id: str, reference: str) -> Optional[Psalm]:
    paragraphs = _pane_paragraphs(soup, pane_id)
    if len(paragraphs) < 2:
        return None

    # paragraphs[0] é o cabeçalho ("Responsório Sl ..."), descartado.
    body = paragraphs[1:]
    response = _strip_leading_dash(body[0])

    verses = body[1:]
    # A resposta normalmente se repete logo em seguida (1x normal, 1x em
    # negrito, como refrão) antes das estrofes — removemos a duplicata.
    if verses and _clean(_strip_leading_dash(verses[0])) == _clean(response):
        verses = verses[1:]

    verses = [_strip_leading_dash(v) for v in verses]

    return Psalm(reference=reference, response=response, verses=verses)


def _parse_gospel_pane(
    soup: BeautifulSoup, pane_id: str, reference: str
) -> tuple[Optional[Gospel], Optional[GospelAcclamation]]:
    paragraphs = _pane_paragraphs(soup, pane_id)
    if len(paragraphs) < 4:
        return None, None

    # paragraphs[0] é o cabeçalho ("Evangelho (Mt 16,13-20)").
    # paragraphs[1] é a aclamação ("Aleluia, Aleluia, Aleluia." ou, na
    # Quaresma, outra fórmula sem "Aleluia").
    # paragraphs[2] é o versículo que antecede o Evangelho.
    acclamation_text = _strip_leading_dash(paragraphs[1])
    acclamation_verse = _strip_leading_dash(paragraphs[2])

    source_idx = None
    for i, text in enumerate(paragraphs):
        if re.search(r"Proclama[cç][ãa]o do Evangelho", text, re.IGNORECASE):
            source_idx = i
            break
    source_label = paragraphs[source_idx] if source_idx is not None else ""

    before_idx = None
    search_start = (source_idx + 1) if source_idx is not None else 3
    for i in range(search_start, len(paragraphs)):
        if re.search(r"Gl[oó]ria a v[oó]s|Louvor a v[oó]s", paragraphs[i], re.IGNORECASE):
            before_idx = i
            break
    assembly_before = _strip_leading_dash(paragraphs[before_idx]) if before_idx is not None else "Glória a vós, Senhor."

    leader_idx = None
    search_start = (before_idx + 1) if before_idx is not None else search_start
    for i in range(search_start, len(paragraphs)):
        if re.search(r"Palavra da Salva[cç][ãa]o", paragraphs[i], re.IGNORECASE):
            leader_idx = i
            break

    body_start = (before_idx + 1) if before_idx is not None else search_start
    body_end = leader_idx if leader_idx is not None else len(paragraphs)
    text = _clean(" ".join(paragraphs[body_start:body_end]))

    leader_after = _strip_leading_dash(paragraphs[leader_idx]) if leader_idx is not None else "Palavra da Salvação."
    assembly_after = ""
    if leader_idx is not None and leader_idx + 1 < len(paragraphs):
        assembly_after = _strip_leading_dash(paragraphs[leader_idx + 1])
    if not assembly_after:
        assembly_after = "Glória a vós, Senhor."

    gospel = Gospel(
        reference=reference,
        source_label=source_label,
        text=text,
        assembly_before=assembly_before,
        leader_after=leader_after,
        assembly_after=assembly_after,
    )
    acclamation = GospelAcclamation(text=acclamation_text, verse=acclamation_verse)
    return gospel, acclamation


def parse_mass_page(html: str, source_url: str) -> SundayMass:
    soup = BeautifulSoup(html, "html.parser")

    # Dia litúrgico: <h1 class="entry-title"> dentro do cabeçalho de conteúdo
    # (o <h1> genérico da página é só o logo "Canção Nova - Liturgia Diária").
    h1 = soup.find("h1", class_="entry-title")
    liturgical_day = _clean(h1.get_text()) if h1 else ""

    # Cor litúrgica: <span class="cor-liturgica">Cor Litúrgica: Verde</span>
    liturgical_color = ""
    color_el = soup.find(class_="cor-liturgica")
    if color_el:
        m = re.search(r"Cor Litúrgica:\s*(\w+)", color_el.get_text())
        if m:
            liturgical_color = m.group(1)

    tabs = _tab_reference_map(soup)

    first_reading = None
    second_reading = None
    psalm = None
    gospel = None
    gospel_acclamation = None

    for pane_id, (label, reference) in tabs.items():
        label_lower = label.lower()
        if "salmo" in label_lower:
            psalm = _parse_psalm_pane(soup, pane_id, reference)
        elif "evangelho" in label_lower:
            gospel, gospel_acclamation = _parse_gospel_pane(soup, pane_id, reference)
        elif label_lower.startswith("1"):
            first_reading = _parse_reading_pane(soup, pane_id, reference)
        elif label_lower.startswith("2"):
            second_reading = _parse_reading_pane(soup, pane_id, reference)

    mass = SundayMass(
        date="",  # preenchido pelo chamador
        liturgical_day=liturgical_day,
        liturgical_color=liturgical_color,
        source_url=source_url,
        first_reading=first_reading,
        psalm=psalm,
        second_reading=second_reading,
        gospel_acclamation=gospel_acclamation,
        gospel=gospel,
    )
    return mass


def fetch_mass_for_date(target_date: date) -> SundayMass:
    url = find_url_for_date(target_date)
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    mass = parse_mass_page(resp.text, source_url=url)
    mass.date = target_date.isoformat()
    return mass


if __name__ == "__main__":
    import sys
    import json
    from dataclasses import asdict

    # No Windows, stdout costuma abrir no codepage do console (ex: cp1252)
    # em vez de UTF-8, corrompendo acentos ao redirecionar a saída para um
    # arquivo. Forçamos UTF-8 para a saída ser sempre confiável.
    sys.stdout.reconfigure(encoding="utf-8")

    target = date(2026, 8, 23)
    if len(sys.argv) > 1:
        target = date.fromisoformat(sys.argv[1])

    mass = fetch_mass_for_date(target)
    print(json.dumps(asdict(mass), ensure_ascii=False, indent=2))
