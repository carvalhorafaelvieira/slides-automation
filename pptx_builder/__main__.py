"""
CLI: gera o .pptx da missa a partir de um SundayMass salvo em JSON
(tipicamente a saída do scraper, já editada manualmente pra incluir as
músicas da semana).

Uso:
    python -m pptx_builder caminho/para/mass.json [-o saida.pptx] [--template TEMPLATE.pptx]

Se -o não for informado, o nome do arquivo de saída é derivado da data da
missa (ex: "missa_2026-08-23.pptx") — rodar de novo pro mesmo domingo
sobrescreve o arquivo; datas diferentes geram arquivos novos.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from content_model.sunday_mass import SundayMass
from pptx_builder.render import build_pptx

DEFAULT_TEMPLATE = "TEMPLATE.pptx"


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera o .pptx da missa dominical.")
    parser.add_argument("mass_json", help="Caminho do SundayMass em JSON.")
    parser.add_argument("-o", "--output", help="Caminho do .pptx de saída.")
    parser.add_argument(
        "--template", default=DEFAULT_TEMPLATE, help=f"Template .pptx (padrão: {DEFAULT_TEMPLATE})"
    )
    args = parser.parse_args()

    mass = SundayMass.from_json(args.mass_json)
    output_path = args.output or f"missa_{mass.date}.pptx"

    build_pptx(mass, template_path=args.template, output_path=output_path)
    print(output_path)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
