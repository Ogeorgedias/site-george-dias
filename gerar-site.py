"""Monta o site para publicar: pagina.html + logos da marca + grade de clientes → docs/.

Uso: python3 gerar-site.py              (site que vai para o ar, em docs/)
     python3 gerar-site.py --rascunho  (mesma página em rascunho/, com as legendas dos espaços de foto,
                                        só para ver no computador antes de publicar)
O site está no ar em www.georgedias.com.br (DNS trocado em 28/10/2026), por isso o CNAME sai sempre.
A lista de clientes vem de ../propostas/clientes.json (a mesma das propostas) e os logos de assets/clientes/.
A pasta docs/ é o que o GitHub Pages publica.
Páginas de serviço (13/11/2026): o texto de cada uma fica em servicos.json e o modelo em servico.html;
saem em docs/<slug>/, com o estilo, o topo e o rodapé da pagina.html, os vídeos da grade de Trabalhos e o sitemap.
"""
import html
import json
import re
import shutil
import sys
import unicodedata
from datetime import date
from pathlib import Path

from PIL import Image

PASTA = Path(__file__).parent
SAIDA = PASTA / "docs"
CLIENTES = PASTA.parent / "propostas" / "clientes.json"
DOMINIO = "www.georgedias.com.br"
SERVICOS = PASTA / "servicos.json"
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



# ---------- Páginas de serviço (13/11/2026): uma por serviço, para o site aparecer em mais buscas ----------

PREGUICA = ' loading="lazy"'  # imagem que só carrega quando chega perto da tela


def esc(t):
    return html.escape(t, quote=True)


def links_servicos(servicos, recuo, atual=None):
    return "\n".join(f'{recuo}<a href="/{s["slug"]}/">{esc(s["nome"])}</a>' for s in servicos if s["slug"] != atual)


def trecho(pagina, inicio, fim):
    """Pedaço da pagina.html (topo, rodapé, estilo) para repetir nas páginas de serviço."""
    i = pagina.index(inicio)
    return pagina[i:pagina.index(fim, i) + len(fim)]


def para_subpagina(t):
    # As páginas de serviço ficam em /<slug>/: links e imagens precisam partir da raiz do site
    t = t.replace('href="#inicio"', 'href="/"').replace('href="#', 'href="/#')
    return t.replace('src="assets/', 'src="/assets/').replace("url(assets/", "url(/assets/")


def img_tag(f, extra=""):
    w, h = Image.open(PASTA / f["src"]).size
    pos = f' style="object-position: {f["posicao"]}"' if f.get("posicao") else ""
    return f'<img src="/{f["src"]}" alt="{esc(f["alt"])}" width="{w}" height="{h}"{extra}{pos}>'


def ordem_na_grade(pagina, ids):
    """Mesma ordem da grade de Trabalhos da principal (data de publicação, mais novo primeiro)."""
    return sorted(ids, key=lambda v: pagina.index(f'data-video="{v}"'))


def cartoes_videos(pagina, ids):
    itens = []
    for vid in ids:
        m = re.search(r'<article>(<button class="foto video" type="button" data-video="' + re.escape(vid) + r'".*?)</article>',
                      pagina, re.S)
        assert m, f"o vídeo {vid} de servicos.json não está na grade de Trabalhos da pagina.html"
        itens.append("      <article>" + para_subpagina(m.group(1)) + "</article>")
    return '    <div class="grade">\n' + "\n".join(itens) + "\n    </div>"


def cartoes_reels(pagina, inicio, quantos):
    """Reels mais novos da faixa de Reels da principal (atualizada toda semana pelo atualizar-reels.py)."""
    arts = re.findall(r'<article(?: class="escondido")?>(<button class="foto reel".*?)</article>', pagina, re.S)
    return "\n".join("      <article>" + para_subpagina(a) + "</article>" for a in arts[inicio:inicio + quantos])


JANELA_REEL = """<div class="modal-reel" hidden role="dialog" aria-modal="true" aria-label="Reel no Instagram"><button class="fechar" type="button" aria-label="Fechar">×</button></div>
<script>
  // Reels: tocam numa janela por cima (player do Instagram)
  (function () {
    var modal = document.querySelector('.modal-reel');
    function fechar() { var f = modal.querySelector('iframe'); if (f) f.remove(); modal.hidden = true; }
    document.addEventListener('click', function (e) {
      var r = e.target.closest('[data-reel]'); if (!r) return;
      var f = document.createElement('iframe');
      f.src = 'https://www.instagram.com/reel/' + r.dataset.reel + '/embed/';
      f.title = r.getAttribute('aria-label');
      f.allow = 'autoplay; encrypted-media; fullscreen';
      modal.appendChild(f); modal.hidden = false;
      modal.querySelector('.fechar').focus();
    });
    modal.addEventListener('click', function (e) { if (e.target === modal || e.target.closest('.fechar')) fechar(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !modal.hidden) fechar(); });
  })();
</script>
"""


def botao_link(link):
    return f'    <div class="link-extra"><a class="botao contorno" href="{link["href"]}">{esc(link["texto"])}</a></div>\n'


def pagina_servico(s, servicos, modelo, pagina_bruta, pagina_pronta, marca_azul, marca_branca):
    url = f"https://{DOMINIO}/{s['slug']}/"
    dados = {"@context": "https://schema.org", "@graph": [
        {"@type": "Service", "name": s["nome"], "serviceType": s["nome"], "description": s["descricao"], "url": url,
         "provider": {"@type": "ProfessionalService", "@id": f"https://{DOMINIO}/#empresa",
                      "name": "George Dias Audiovisual", "url": f"https://{DOMINIO}/"},
         "areaServed": [{"@type": "City", "name": "Cuiabá"}, {"@type": "State", "name": "Mato Grosso"},
                        {"@type": "Country", "name": "Brasil"}]},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Início", "item": f"https://{DOMINIO}/"},
            {"@type": "ListItem", "position": 2, "name": s["nome"], "item": url}]}]}
    itens = []
    for n, it in enumerate(s["itens"], 1):
        titulo = f'<a href="{it["link"]}">{esc(it["titulo"])}</a>' if it.get("link") else esc(it["titulo"])
        itens.append(f'      <article><span class="num">{n:02d}</span><h3>{titulo}</h3><p>{esc(it["texto"])}</p></article>')
    # Topo: um vídeo do tipo (pedido do George em 13/11/2026), dois Reels (produção de conteúdo) ou uma foto
    if s.get("destaque"):
        capa = cartoes_videos(pagina_pronta, [s["destaque"]]).replace(PREGUICA, "")
        classe_topo = " com-video"
    elif s.get("reels"):
        capa = '    <div class="grade-reels">\n' + cartoes_reels(pagina_pronta, 0, 2).replace(PREGUICA, "") + "\n    </div>"
        classe_topo = " com-reels"
    else:
        capa = f'    <div class="foto capa">{img_tag(s["capa"])}</div>'
        classe_topo = ""
    # Logo abaixo do topo: os outros trabalhos do mesmo tipo
    miolo = ""
    if s.get("videos"):
        miolo = cartoes_videos(pagina_pronta, ordem_na_grade(pagina_pronta, [v for v in s["videos"] if v != s.get("destaque")]))
    elif s.get("reels"):
        miolo = '    <div class="grade-reels">\n' + cartoes_reels(pagina_pronta, 2, 8) + "\n    </div>"
    trabalhos = ""
    if miolo:
        trabalhos = ('<section class="trabalhos" id="trabalhos">\n  <div class="largura">\n    <span class="rotulo">Trabalhos</span>\n'
                     f'    <h2>{esc(s["titulo_trabalhos"])}</h2>\n{miolo}\n'
                     + (botao_link(s["link_trabalhos"]) if s.get("link_trabalhos") else "")
                     + "  </div>\n</section>\n")
    if s.get("reels"):
        trabalhos += JANELA_REEL
    fotos = ""
    if s.get("fotos"):
        # Galeria de fotos (cobertura fotográfica na cobertura de eventos; os retratos na página de retratos)
        fotos = (f'<section class="fotos-evento">\n  <div class="largura">\n    <span class="rotulo">{esc(s.get("rotulo_fotos", "Fotografia"))}</span>\n'
                 f'    <h2>{esc(s["titulo_fotos"])}</h2>\n    <div class="galeria-fotos">\n'
                 + "\n".join(f'      <div class="foto">{img_tag(f, extra=PREGUICA)}</div>' for f in s["fotos"])
                 + "\n    </div>\n" + (botao_link(s["link_extra"]) if s.get("link_extra") else "")
                 + "  </div>\n</section>\n")
    trocas = {
        "<!--TITULO-->": esc(s["titulo"]),
        "<!--DESCRICAO-->": esc(s["descricao"]),
        "<!--URL-->": url,
        "<!--JSONLD-->": '<script type="application/ld+json">\n' + json.dumps(dados, ensure_ascii=False, indent=1) + "\n</script>",
        "<!--ESTILO-->": para_subpagina(trecho(pagina_bruta, "<style>", "</style>")),
        "<!--TOPO-->": para_subpagina(trecho(pagina_bruta, '<header class="topo">', "</header>")).replace(
            "<!--MARCA-ALTERNATIVA-AZUL-->", marca_azul),
        "<!--RODAPE-->": para_subpagina(trecho(pagina_bruta, '<footer class="rodape">', "</footer>")).replace(
            "<!--MARCA-ALTERNATIVA-BRANCO-->", marca_branca).replace(
            "<!--SERVICOS-RODAPE-->", links_servicos(servicos, " " * 8)),
        "<!--ROTULO-->": esc(s["rotulo"]),
        "<!--H1-->": esc(s["h1"]),
        "<!--INTRO-->": "\n".join(f"        <p>{esc(p)}</p>" for p in s["intro"]),
        "<!--CAPA-->": capa,
        "<!--CLASSE-TOPO-->": classe_topo,
        "<!--ITENS-->": "\n".join(itens),
        "<!--TRABALHOS-->": trabalhos,
        "<!--FOTOS-->": fotos,
        "<!--OUTROS-->": "\n".join(f'      <li><a href="/{o["slug"]}/">{esc(o["nome"])}</a></li>'
                                   for o in servicos if o["slug"] != s["slug"]),
    }
    t = modelo
    for marcador, conteudo in trocas.items():
        assert marcador in t, marcador
        t = t.replace(marcador, conteudo)
    return t


def main():
    rascunho = "--rascunho" in sys.argv
    saida = PASTA / "rascunho" if rascunho else SAIDA
    pagina = (PASTA / "pagina.html").read_text(encoding="utf-8")
    pagina_bruta = pagina
    servicos = json.loads(SERVICOS.read_text(encoding="utf-8"))
    if rascunho:
        pagina = pagina.replace("<body>", '<body class="rascunho">', 1)
    trocas = {
        "<!--MARCA-ALTERNATIVA-AZUL-->": svg("marca-alternativa-cor-azul.svg"),
        "<!--CLIENTES-->": grade_clientes(),
        "<!--SERVICOS-RODAPE-->": links_servicos(servicos, " " * 8),
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
    # Endereço curto e com prévia bonita no WhatsApp para o formulário de orçamento (Apps Script)
    (saida / "orcamento").mkdir()
    shutil.copy(PASTA / "orcamento.html", saida / "orcamento" / "index.html")
    # Para o Google: ícone na raiz (é onde ele procura primeiro), robots.txt e sitemap (13/11/2026)
    shutil.copy(PASTA / "assets" / "icone" / "favicon.ico", saida / "favicon.ico")
    (saida / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: https://{DOMINIO}/sitemap.xml\n", encoding="utf-8")
    modelo = (PASTA / "servico.html").read_text(encoding="utf-8")
    for sv in servicos:
        (saida / sv["slug"]).mkdir()
        (saida / sv["slug"] / "index.html").write_text(
            pagina_servico(sv, servicos, modelo, pagina_bruta, pagina,
                           svg("marca-alternativa-cor-azul.svg"), svg("marca-alternativa-branco.svg")), encoding="utf-8")
    # Página de endereço que não existe, com as corujas da marca (13/11/2026)
    t404 = (PASTA / "nao-encontrada.html").read_text(encoding="utf-8")
    for marcador, conteudo in {
        "<!--ESTILO-->": para_subpagina(trecho(pagina_bruta, "<style>", "</style>")),
        "<!--TOPO-->": para_subpagina(trecho(pagina_bruta, '<header class="topo">', "</header>")).replace(
            "<!--MARCA-ALTERNATIVA-AZUL-->", svg("marca-alternativa-cor-azul.svg")),
        "<!--RODAPE-->": para_subpagina(trecho(pagina_bruta, '<footer class="rodape">', "</footer>")).replace(
            "<!--MARCA-ALTERNATIVA-BRANCO-->", svg("marca-alternativa-branco.svg")).replace(
            "<!--SERVICOS-RODAPE-->", links_servicos(servicos, " " * 8)),
    }.items():
        assert marcador in t404, marcador
        t404 = t404.replace(marcador, conteudo)
    (saida / "404.html").write_text(t404, encoding="utf-8")
    hoje = date.today().isoformat()
    enderecos = [f"https://{DOMINIO}/"] + [f"https://{DOMINIO}/{sv['slug']}/" for sv in servicos]
    (saida / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>{u}</loc><lastmod>{hoje}</lastmod></url>\n" for u in enderecos)
        + '</urlset>\n', encoding="utf-8")
    if not rascunho:
        (saida / "CNAME").write_text(DOMINIO + "\n")
    tamanho_total = sum(f.stat().st_size for f in saida.rglob("*") if f.is_file())
    print(f"Site gerado em {saida.relative_to(PASTA)}/ ({tamanho_total // 1024} KB)")


if __name__ == "__main__":
    main()
