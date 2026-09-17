"""
Modelo de dados que representa todo o conteúdo litúrgico e musical
de uma missa dominical. Este é o "contrato" entre o scraper, a
interface de edição e o gerador de slides (pptx_builder, futuramente
também um exportador para Google Slides).

Mantemos isso como dataclasses simples (fácil de serializar para JSON
e fácil de editar manualmente num arquivo .json enquanto não existe
interface web).
"""
from dataclasses import dataclass, field, asdict
from typing import Optional
import json


@dataclass
class Reading:
    reference: str  # ex: "Is 22,19-23"
    source_label: str  # ex: "Leitura do Livro do Profeta Isaías"
    text: str
    # resposta fixa após a leitura, ex: ("Palavra do Senhor.", "Graças a Deus.")
    leader_line: str = "Palavra do Senhor."
    assembly_response: str = "Graças a Deus."


@dataclass
class Psalm:
    reference: str  # ex: "Sl 137(138),1-2a.2bc-3.6.8bc (R. 8bc)"
    response: str  # a resposta cantada pela assembleia - MUDA toda semana
    verses: list[str] = field(default_factory=list)


@dataclass
class GospelAcclamation:
    text: str = "Aleluia, Aleluia, Aleluia."
    verse: Optional[str] = None  # verso que antecede o Evangelho


@dataclass
class Gospel:
    reference: str  # ex: "Mt 16,13-20"
    source_label: str  # ex: "Proclamação do Evangelho de Jesus Cristo segundo Mateus"
    text: str
    assembly_before: str = "Glória a vós, Senhor."
    leader_after: str = "Palavra da Salvação."
    assembly_after: str = "Glória a vós, Senhor."


@dataclass
class Song:
    moment: str  # ex: "Entrada", "Ofertório", "Comunhão", "Ação de Graças", "Final"
    title: str = ""
    author: str = ""
    lyrics: str = ""  # opcional, se quiser projetar a letra também
    suggested: bool = False  # True se foi sugerida por nós, False se veio do músico


@dataclass
class EucharisticPrayer:
    number: int = 2  # 1 a 5 (a maioria das paróquias usa a II com frequência)
    note: str = ""  # observação do padre, se houver


@dataclass
class SundayMass:
    date: str  # formato "YYYY-MM-DD"
    liturgical_day: str  # ex: "21º Domingo do Tempo Comum"
    liturgical_color: str = ""
    source_url: str = ""

    first_reading: Optional[Reading] = None
    psalm: Optional[Psalm] = None
    second_reading: Optional[Reading] = None
    gospel_acclamation: Optional[GospelAcclamation] = None
    gospel: Optional[Gospel] = None

    songs: list[Song] = field(default_factory=list)
    eucharistic_prayer: EucharisticPrayer = field(default_factory=EucharisticPrayer)

    pope_commentary: Optional[str] = None  # opcional, vindo do Vatican News

    def to_json(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(self), f, ensure_ascii=False, indent=2)

    @staticmethod
    def from_json(path: str) -> "SundayMass":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Reconstrução simples; para um modelo mais robusto,
        # dá para usar pydantic no lugar de dataclasses puras.
        data["first_reading"] = Reading(**data["first_reading"]) if data.get("first_reading") else None
        data["psalm"] = Psalm(**data["psalm"]) if data.get("psalm") else None
        data["second_reading"] = Reading(**data["second_reading"]) if data.get("second_reading") else None
        data["gospel_acclamation"] = GospelAcclamation(**data["gospel_acclamation"]) if data.get("gospel_acclamation") else None
        data["gospel"] = Gospel(**data["gospel"]) if data.get("gospel") else None
        data["songs"] = [Song(**s) for s in data.get("songs", [])]
        data["eucharistic_prayer"] = EucharisticPrayer(**data["eucharistic_prayer"]) if data.get("eucharistic_prayer") else EucharisticPrayer()
        return SundayMass(**data)
