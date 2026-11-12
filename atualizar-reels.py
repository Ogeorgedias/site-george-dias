"""Monta a faixa de Reels do site a partir de reels.json.

Cada item de reels.json é um Reel que o cliente publicou e o George repostou (aba Repostagens do
Instagram @ogeorgedias): {"code", "conta", "data", "texto"}. A capa fica em assets/reels/<code>.jpg
(360x640). Este script reescreve o trecho entre <!--REELS-INICIO--> e <!--REELS-FIM--> do pagina.html,
em ordem de data (mais novo primeiro), e avisa se faltar alguma capa.

Uso: python3 atualizar-reels.py   (depois: python3 gerar-site.py)
"""
import html
import json
from pathlib import Path

PASTA = Path(__file__).parent
MESES = "jan fev mar abr mai jun jul ago set out nov dez".split()
CONTAS = {
    "sicrediouroverde": "Sicredi Ouro Verde",
    "sicredivaledocerrado": "Sicredi Vale do Cerrado",
    "sicredisudoeste": "Sicredi Sudoeste",
    "sicredi": "Sicredi",
    "agroamazonia": "Agro Amazônia",
    "sesimt": "SESI Mato Grosso",
    "sesicultura.inovacao": "SESI Cultura e Inovação",
    "sistemafiemt": "Sistema FIEMT",
    "ses.mt": "Secretaria de Saúde MT",
    "energisa": "Energisa",
    "denzacuiaba": "Denza Cuiabá",
    "tintasmaxviniloficial": "Tintas Maxvinil",
    "team_tucare": "Team Tucaré",
    "murilogroth_": "Murilo Groth",
    "fe.fernando.pereira": "Fernando Pereira",
}
VISIVEIS = 4  # quantos aparecem de cara; o resto abre no "Ver mais"


def main():
    reels = json.loads((PASTA / "reels.json").read_text(encoding="utf-8"))
    reels.sort(key=lambda r: r["data"], reverse=True)
    linhas, faltam = [], []
    for n, r in enumerate(reels):
        if not (PASTA / "assets" / "reels" / f"{r['code']}.jpg").exists():
            faltam.append(r["code"])
            continue
        cliente = CONTAS.get(r["conta"], r["conta"])
        a, m, d = r["data"].split("-")
        quando = f"{int(d)} {MESES[int(m) - 1]} {a}"
        classe = "" if n < VISIVEIS else ' class="escondido"'
        linhas.append(
            f'      <article{classe}><button class="foto reel" type="button" data-reel="{r["code"]}" '
            f'aria-label="Assistir o Reel de {html.escape(cliente)}"><img src="assets/reels/{r["code"]}.jpg" alt="" '
            f'width="360" height="640" loading="lazy"><span class="play" aria-hidden="true"></span></button>'
            f'<div class="ficha"><h3>{html.escape(cliente)}</h3><time datetime="{r["data"]}">{quando}</time></div></article>'
        )
    pagina = (PASTA / "pagina.html").read_text(encoding="utf-8")
    ini, fim = "<!--REELS-INICIO-->", "<!--REELS-FIM-->"
    a, b = pagina.index(ini) + len(ini), pagina.index(fim)
    pagina = pagina[:a] + "\n" + "\n".join(linhas) + "\n      " + pagina[b:]
    (PASTA / "pagina.html").write_text(pagina, encoding="utf-8")
    print(f"{len(linhas)} Reels na página" + (f"; sem capa: {', '.join(faltam)}" if faltam else ""))


if __name__ == "__main__":
    main()
