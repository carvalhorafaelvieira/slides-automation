"""
Medição de texto e paginação em slides.

O template usa fonte Arial Black bold a 96pt no corpo do conteúdo, o que
cabe pouquíssimo texto por linha e ~4 linhas por slide. Para decidir onde
cortar cada slide com precisão (sem chutar uma média de caractere-por-linha,
que erraria bastante numa fonte bold tão grande), medimos a largura real do
texto renderizado com PIL usando a própria fonte do template.

Regra de corte: nunca no meio de uma palavra; evita cortar no meio de uma
frase quando possível (só desce para cláusula/palavra quando a frase sozinha
não cabe fisicamente em um slide vazio).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from PIL import ImageFont

EMU_PER_INCH = 914400
PT_PER_INCH = 72

# Distância entre linhas ~1.2x o tamanho da fonte é a métrica padrão da
# maioria das fontes; o template herda lnSpc=90% do master (spcPct é relativo
# a essa distância "single line").
SINGLE_LINE_FACTOR = 1.2
LINE_SPACING_PCT = 0.90

# Margens internas padrão do OOXML quando o bodyPr não as sobrescreve
# (é o caso dos dois placeholders do template).
DEFAULT_L_INS_EMU = 91440
DEFAULT_R_INS_EMU = 91440
DEFAULT_T_INS_EMU = 45720
DEFAULT_B_INS_EMU = 45720

# Três variantes usadas no template: Arial Black (texto padrão, 96pt) e
# Arial normal/negrito (diálogos padre↔assembleia, ver deck_plan.py).
FONT_VARIANT_CANDIDATES = {
    "black": [
        r"C:\Windows\Fonts\ariblk.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Arial_Black.ttf",
    ],
    "regular": [
        r"C:\Windows\Fonts\arial.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf",
    ],
    "bold": [
        r"C:\Windows\Fonts\arialbd.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Arial_Bold.ttf",
    ],
}

# Largura média aproximada por caractere (fração do tamanho da fonte),
# usada só se nenhuma fonte real for encontrada no sistema (ex: ambiente
# não-Windows sem essas fontes instaladas).
_FALLBACK_CHAR_WIDTH_EM = {"black": 0.62, "regular": 0.50, "bold": 0.56}

_SENTENCE_SPLIT_RE = re.compile(r'(?<=[.!?])\s+(?=[A-ZÀ-ÚÀ-Ü0-9"“(])')
_CLAUSE_SPLIT_RE = re.compile(r'(?<=[,;:—])\s+')

_font_cache: dict[tuple[str, int], "ImageFont.FreeTypeFont"] = {}


def resolve_font_path(explicit_path: Optional[str] = None, variant: str = "black") -> Optional[str]:
    if explicit_path:
        return explicit_path
    for candidate in FONT_VARIANT_CANDIDATES[variant]:
        if Path(candidate).exists():
            return candidate
    return None


class _FallbackFont:
    """Usado quando a fonte real não está disponível no sistema."""

    def __init__(self, size_pt: float, variant: str = "black"):
        self._size_pt = size_pt
        self._char_width_em = _FALLBACK_CHAR_WIDTH_EM[variant]

    def getlength(self, text: str) -> float:
        return len(text) * self._size_pt * self._char_width_em


def _load_font(font_path: Optional[str], size_pt: float, variant: str = "black"):
    resolved = resolve_font_path(font_path, variant=variant)
    if resolved is None:
        return _FallbackFont(size_pt, variant=variant)
    key = (resolved, round(size_pt))
    font = _font_cache.get(key)
    if font is None:
        # Tratamos "pt" como "px" (equivalente a renderizar a 72 DPI): como
        # medimos a caixa disponível na mesma unidade, o fator de conversão
        # se cancela e o resultado é exato independente do DPI escolhido.
        font = ImageFont.truetype(resolved, round(size_pt))
        _font_cache[key] = font
    return font


def _emu_to_pt(emu: int) -> float:
    return emu / EMU_PER_INCH * PT_PER_INCH


def max_lines_for_box(box_height_emu: int, font_size_pt: float) -> int:
    usable_height_pt = _emu_to_pt(box_height_emu - DEFAULT_T_INS_EMU - DEFAULT_B_INS_EMU)
    line_height_pt = font_size_pt * SINGLE_LINE_FACTOR * LINE_SPACING_PCT
    return max(1, int(usable_height_pt // line_height_pt))


def _max_width_pt(box_width_emu: int) -> float:
    return _emu_to_pt(box_width_emu - DEFAULT_L_INS_EMU - DEFAULT_R_INS_EMU)


def wrap_to_lines(text: str, font, max_width_pt: float) -> list[str]:
    words = text.split()
    if not words:
        return []
    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if font.getlength(candidate) <= max_width_pt:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def count_lines(text: str, font, max_width_pt: float) -> int:
    return len(wrap_to_lines(text, font, max_width_pt))


def count_paragraph_lines(paragraphs: list[str], font, max_width_pt: float) -> int:
    """Conta linhas totais quando cada item de `paragraphs` começa numa
    linha nova (quebra de parágrafo), em vez de ser re-fluído junto."""
    return sum(count_lines(p, font, max_width_pt) for p in paragraphs)


def _split_sentences(text: str) -> list[str]:
    parts = _SENTENCE_SPLIT_RE.split(text.strip())
    return [p.strip() for p in parts if p.strip()]


def _split_clauses(text: str) -> list[str]:
    parts = _CLAUSE_SPLIT_RE.split(text.strip())
    return [p.strip() for p in parts if p.strip()]


def _regroup_words_to_fit(text: str, font, max_width_pt: float, max_lines: int) -> list[str]:
    """Último recurso: agrupa palavras em blocos que cabem em max_lines,
    nunca cortando no meio de uma palavra."""
    wrapped = wrap_to_lines(text, font, max_width_pt)
    return [
        " ".join(wrapped[i:i + max_lines])
        for i in range(0, len(wrapped), max_lines)
    ] or [text]


def _atomize(text: str, font, max_width_pt: float, max_lines: int) -> list[str]:
    """Quebra o texto em unidades que cabem sozinhas em um slide (<=
    max_lines), preferindo frase > cláusula > palavra."""
    atoms: list[str] = []
    for sentence in _split_sentences(text):
        if count_lines(sentence, font, max_width_pt) <= max_lines:
            atoms.append(sentence)
            continue
        for clause in _split_clauses(sentence):
            if count_lines(clause, font, max_width_pt) <= max_lines:
                atoms.append(clause)
            else:
                atoms.extend(_regroup_words_to_fit(clause, font, max_width_pt, max_lines))
    return atoms


def _pack_atoms(atoms: list[str], font, max_width_pt: float, max_lines: int, joiner: str) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    for atom in atoms:
        candidate = current + [atom]
        if count_lines(joiner.join(candidate), font, max_width_pt) <= max_lines:
            current = candidate
        else:
            if current:
                chunks.append(joiner.join(current))
            current = [atom]
    if current:
        chunks.append(joiner.join(current))
    return chunks


def split_into_slide_chunks(
    text: str,
    *,
    is_prose: bool,
    box_width_emu: int,
    box_height_emu: int,
    font_size_pt: float = 96,
    font_path: Optional[str] = None,
    font_variant: str = "black",
) -> list[list[str]]:
    """
    Divide `text` em uma lista de slides. Cada slide é uma lista de
    parágrafos (1 item para prosa, que junta tudo com espaço e deixa o
    PowerPoint re-quebrar linha em runtime; N itens para letra de música,
    que preserva as quebras de linha originais como parágrafos).

    `font_variant` deve bater com a fonte que vai ser aplicada de fato no
    slide (ver render.py) para a medição de linha ficar precisa.
    """
    if not text or not text.strip():
        return []

    font = _load_font(font_path, font_size_pt, variant=font_variant)
    max_width_pt = _max_width_pt(box_width_emu)
    max_lines = max_lines_for_box(box_height_emu, font_size_pt)

    if is_prose:
        atoms = _atomize(text, font, max_width_pt, max_lines)
        chunks = _pack_atoms(atoms, font, max_width_pt, max_lines, joiner=" ")
        return [[chunk] for chunk in chunks]

    # Letra de música: cada linha original é a unidade preferencial.
    raw_lines = [line.strip() for line in text.splitlines() if line.strip()]
    atoms = []
    for line in raw_lines:
        if count_lines(line, font, max_width_pt) <= max_lines:
            atoms.append(line)
        else:
            atoms.extend(_regroup_words_to_fit(line, font, max_width_pt, max_lines))

    chunks: list[list[str]] = []
    current: list[str] = []
    for atom in atoms:
        candidate = current + [atom]
        if count_paragraph_lines(candidate, font, max_width_pt) <= max_lines:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = [atom]
    if current:
        chunks.append(current)
    return chunks
