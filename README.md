# Slides Automation — Missa Dominical

Gera automaticamente os slides (PowerPoint) usados na missa de domingo,
com as leituras, respostas da assembleia, salmo responsorial, músicas e
a oração eucarística escolhida pelo padre.

## Status atual (MVP em construção)

- [x] Modelo de dados (`content_model/sunday_mass.py`)
- [x] Respostas fixas da missa (`static_data/fixed_responses.py`)
- [x] Primeira versão do scraper da Canção Nova (`scraper/cancaonova.py`)
      — **ainda não testada com internet real, ver seção "Primeiro teste" abaixo**
- [ ] Gerador de PowerPoint (`pptx_builder/`) — próximo passo
- [ ] Sugestão automática de músicas por evangelho
- [ ] Interface web para editar músicas / escolher oração eucarística
- [ ] (Futuro) Exportador para Google Slides + agente de ajuste ao vivo

## Setup

```bash
cd slides_automation
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Primeiro teste (importante!)

Este scraper foi escrito com base na estrutura da página observada
manualmente (o ambiente onde escrevi o código não tem acesso à
internet). Rode o teste abaixo e me avise o resultado:

```bash
python -m scraper.cancaonova 2026-08-23
```

Resultado esperado: um JSON no terminal com a 1ª leitura, o salmo
(com a resposta "Ó Senhor, vossa bondade é para sempre..."), 2ª
leitura, aclamação e Evangelho.

**Se der erro ou vier campo vazio/errado:**
1. Copie a mensagem de erro, ou
2. Salve o HTML da página (`view-source:` no navegador, ou
   `requests.get(url).text` num script) e me envie um trecho —
   principalmente ao redor da seção que falhou (ex: o salmo).

Isso é normal na primeira iteração de um scraper: sites mudam de
estrutura com frequência e eu não tenho como testar contra a internet
real daqui. Vamos ajustar junto até ficar estável.

## Estrutura do projeto

```
slides_automation/
├── content_model/       # Modelo de dados (SundayMass, Reading, Psalm, Song, ...)
├── scraper/              # Scraping das leituras/salmo (Canção Nova é a fonte principal)
├── static_data/          # Respostas fixas da missa (não mudam semana a semana)
├── tests/                 # (a preencher)
└── requirements.txt
```

## Próximos passos, em ordem

1. **Validar o scraper localmente** (seção acima) — sem isso, tudo o
   resto fica bloqueado.
2. Escrever `pptx_builder/` — pega um `SundayMass` (JSON) e gera o
   `.pptx` com um layout definido por você (posso sugerir um padrão
   simples de igreja: fundo neutro, texto grande e legível de longe).
3. Adicionar um jeito fácil de editar músicas e a oração eucarística
   antes de gerar o arquivo final (a interface completa fica para
   depois — podemos começar com um JSON editável ou um formulário
   simples em linha de comando).
4. Sugestão de músicas por evangelho (regras simples no início, ex:
   por palavra-chave do evangelho → banco de músicas litúrgicas).
