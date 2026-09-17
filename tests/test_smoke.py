"""
Teste de fumaça: garante que o pipeline scraper->JSON->pptx continua
gerando um arquivo .pptx valido. Nao valida o conteudo visual do slide,
so que a geracao nao quebra - e o suficiente para travar o pipeline de
deploy se alguem quebrar o render.py sem perceber.
"""
from pathlib import Path

from content_model.sunday_mass import SundayMass
from pptx_builder.render import build_pptx

FIXTURE = Path(__file__).parent / "fixtures" / "sample_mass.json"
TEMPLATE = Path(__file__).parent.parent / "TEMPLATE.pptx"


def test_build_pptx_smoke(tmp_path):
    mass = SundayMass.from_json(FIXTURE)
    output = tmp_path / "output.pptx"

    build_pptx(mass, template_path=str(TEMPLATE), output_path=str(output))

    assert output.exists()
    assert output.stat().st_size > 0
