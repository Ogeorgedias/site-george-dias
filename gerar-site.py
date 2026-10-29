"""Monta o site para publicar: pagina.html + logos da marca + grade de clientes → docs/.

Uso: python3 gerar-site.py
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
    for c in json.loads(CLIENTES.read_text(encoding="utf-8")):
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
    pagina = (PASTA / "pagina.html").read_text(encoding="utf-8")
    trocas = {
        "<!--MARCA-ALTERNATIVA-BRANCO-->": svg("marca-alternativa-branco.svg"),
        "<!--MARCA-ALTERNATIVA-AZUL-->": svg("marca-alternativa-cor-azul.svg"),
        "<!--CLIENTES-->": grade_clientes(),
    }
    for marcador, conteudo in trocas.items():
        assert marcador in pagina, marcador
        pagina = pagina.replace(marcador, conteudo)

    if SAIDA.exists():
        shutil.rmtree(SAIDA)
    shutil.copytree(PASTA / "assets", SAIDA / "assets",
                    ignore=shutil.ignore_patterns("marca-alternativa-*.svg", ".DS_Store"))
    (SAIDA / "index.html").write_text(pagina, encoding="utf-8")
    (SAIDA / "CNAME").write_text(DOMINIO + "\n")
    tamanho_total = sum(f.stat().st_size for f in SAIDA.rglob("*") if f.is_file())
    print(f"Site gerado em {SAIDA.relative_to(PASTA)}/ ({tamanho_total // 1024} KB)")


if __name__ == "__main__":
    main()
