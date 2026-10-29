"""Monta o site para publicar: pagina.html + logos da marca + grade de clientes → docs/.

Uso: python3 gerar-site.py              (site que vai para o ar, em docs/)
     python3 gerar-site.py --rascunho  (mesma página em rascunho/, com as legendas dos espaços de foto,
                                        só para ver no computador antes de publicar)
O site está no ar em www.georgedias.com.br (DNS trocado em 28/10/2026), por isso o CNAME sai sempre.
A lista de clientes vem de ../propostas/clientes.json (a mesma das propostas) e os logos de assets/clientes/.
A pasta docs/ é o que o GitHub Pages publica.
"""
import html
import json
import re
import shutil
import sys
import unicodedata
from pathlib import Path

from PIL import Image

PASTA = Path(__file__).parent
SAIDA = PASTA / "docs"
CLIENTES = PASTA.parent / "propostas" / "clientes.json"
DOMINIO = "www.georgedias.com.br"
# Os logos ficam em ordem alfabética pelo nome que aparece no logo (sem "Tintas", "Academia"...),
# para nenhum cliente parecer mais importante que outro (pedido do George em 28/10/2026)
PREFIXOS = ("Academia ", "Colégio ", "Construtora ", "Tintas ")


def nome_no_logo(c):
    nome = c if isinstance(c, str) else c["nome"]
    for prefixo in PREFIXOS:
        if nome.startswith(prefixo):
            return nome[len(prefixo):]
    return nome


def slug(texto):
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return "-".join("".join(c if c.isalnum() else " " for c in t).split())


def proporcao(arq):
    if arq.suffix == ".svg":
        s = arq.read_text()
        m = re.search(r'viewBox="[\d.\-]+[ ,]+[\d.\-]+[ ,]+([\d.]+)[ ,]+([\d.]+)"', s) or \
            re.search(r'width="([\d.]+)[a-z]*"\s+height="([\d.]+)', s)
        return float(m.group(1)) / float(m.group(2))
    w, h = Image.open(arq).size
    return w / h


def tamanho(arq, area=5200, larg_max=180, alt_max=64):
    """Mesma área visual para todos os logos, dentro do cartão (em px)."""
    r = proporcao(arq)
    larg, alt = (area * r) ** .5, (area / r) ** .5
    fator = min(1, larg_max / larg, alt_max / alt)
    return round(larg * fator), round(alt * fator)


def grade_clientes():
    itens = []
    for c in sorted(json.loads(CLIENTES.read_text(encoding="utf-8")), key=lambda c: slug(nome_no_logo(c))):
        nome = c if isinstance(c, str) else c["nome"]
        fundo = "" if isinstance(c, str) else f' style="background:{c["fundo"]}"'
        arq = next((PASTA / "assets" / "clientes" / f"{slug(nome)}.{ext}" for ext in ("svg", "png", "jpg")
                    if (PASTA / "assets" / "clientes" / f"{slug(nome)}.{ext}").exists()), None)
        if arq:
            w, h = tamanho(arq)
            miolo = f'<img src="assets/clientes/{arq.name}" alt="{html.escape(nome)}" width="{w}" height="{h}" loading="lazy">'
        else:
            miolo = f"<span>{html.escape(nome)}</span>"
        itens.append(f'      <div class="logo"{fundo}>{miolo}</div>')
    return "\n".join(itens)


def svg(nome):
    s = (PASTA / "assets" / nome).read_text(encoding="utf-8").strip()
    return re.sub(r"<title>.*?</title>", "", s, flags=re.S)


def main():
    rascunho = "--rascunho" in sys.argv
    saida = PASTA / "rascunho" if rascunho else SAIDA
    pagina = (PASTA / "pagina.html").read_text(encoding="utf-8")
    if rascunho:
        pagina = pagina.replace("<body>", '<body class="rascunho">', 1)
    trocas = {
        "<!--MARCA-ALTERNATIVA-BRANCO-->": svg("marca-alternativa-branco.svg"),
        "<!--MARCA-ALTERNATIVA-AZUL-->": svg("marca-alternativa-cor-azul.svg"),
        "<!--CLIENTES-->": grade_clientes(),
    }
    for marcador, conteudo in trocas.items():
        assert marcador in pagina, marcador
        pagina = pagina.replace(marcador, conteudo)

    if saida.exists():
        shutil.rmtree(saida)
    # A marca azul vai só dentro da página; a branca também sai como arquivo, porque o app da equipe usa
    shutil.copytree(PASTA / "assets", saida / "assets",
                    ignore=shutil.ignore_patterns("marca-alternativa-cor-azul.svg", ".DS_Store"))
    (saida / "index.html").write_text(pagina, encoding="utf-8")
    if not rascunho:
        (saida / "CNAME").write_text(DOMINIO + "\n")
    tamanho_total = sum(f.stat().st_size for f in saida.rglob("*") if f.is_file())
    print(f"Site gerado em {saida.relative_to(PASTA)}/ ({tamanho_total // 1024} KB)")


if __name__ == "__main__":
    main()
