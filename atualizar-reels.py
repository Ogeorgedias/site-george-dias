"""Monta a faixa de Reels do site a partir de reels.json.

Cada item de reels.json é um Reel que o cliente publicou e o George repostou (aba Repostagens do
Instagram @ogeorgedias): {"code", "conta", "data", "texto"}. A capa fica em assets/reels/<code>.jpg
(360x640). Este script reescreve o trecho entre <!--REELS-INICIO--> e <!--REELS-FIM--> do pagina.html,
em ordem de data (mais novo primeiro), e avisa se faltar alguma capa.

Uso: python3 atualizar-reels.py   (depois: python3 gerar-site.py)
     python3 atualizar-reels.py --novos novos.json
         novos.json = lista [{"h": "/conta/reel/CODE/", "src": "<url da capa>", "alt": "<legenda>"}] tirada da aba
         Repostagens. Baixa as capas, acrescenta só os que ainda não estão em reels.json (a data sai do próprio
         código do Reel) e remonta o trecho da página. Imprime NOVOS: <n> e a lista do que entrou.
"""
import datetime
import html
import io
import json
import sys
import urllib.request
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


ALFABETO = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"


def data_do_codigo(code):
    """O código do Reel guarda o momento da publicação (id do Instagram: 41 bits de milissegundos)."""
    n = 0
    for c in code:
        n = n * 64 + ALFABETO.index(c)
    return datetime.datetime.fromtimestamp(((n >> 23) + 1314220021721) / 1000).strftime("%Y-%m-%d")


def acrescentar(arquivo):
    from PIL import Image, ImageCms, ImageFilter, ImageOps
    srgb = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    reels = json.loads((PASTA / "reels.json").read_text(encoding="utf-8"))
    conhecidos = {r["code"] for r in reels}
    entraram = []
    for x in json.loads(Path(arquivo).read_text(encoding="utf-8")):
        partes = x["h"].strip("/").split("/")
        if len(partes) != 3 or partes[1] != "reel" or partes[2] in conhecidos:
            continue
        conta, _, code = partes
        req = urllib.request.Request(x["src"], headers={"User-Agent": "Mozilla/5.0"})
        im = Image.open(io.BytesIO(urllib.request.urlopen(req, timeout=30).read())).convert("RGB")
        im = ImageOps.fit(im, (360, 640), Image.LANCZOS, centering=(0.5, 0.4)).filter(ImageFilter.UnsharpMask(0.5, 30, 2))
        im.save(PASTA / "assets" / "reels" / f"{code}.jpg", quality=78, optimize=True, progressive=True, icc_profile=srgb)
        r = {"code": code, "conta": conta, "data": data_do_codigo(code), "texto": " ".join(x.get("alt", "").split())[:120]}
        reels.append(r)
        conhecidos.add(code)
        entraram.append(r)
    reels.sort(key=lambda r: r["data"], reverse=True)
    (PASTA / "reels.json").write_text(json.dumps(reels, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"NOVOS: {len(entraram)}")
    for r in entraram:
        print(f"- {CONTAS.get(r['conta'], r['conta'])} · {r['data']} · {r['code']}")


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--novos":
        acrescentar(sys.argv[2])
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
