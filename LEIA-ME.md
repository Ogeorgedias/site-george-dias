# Site George Dias Audiovisual

Site de www.georgedias.com.br, feito com o Claude. No ar desde 28/10/2026, hospedado no GitHub Pages (repositório Ogeorgedias/site-george-dias).

- Edite `pagina.html` e rode `python3 gerar-site.py`. O site pronto sai em `docs/`, que o GitHub Pages publica.
- A grade de clientes vem de `../propostas/clientes.json` e de `assets/clientes/`.
- Publicar: `git add -A && git commit && git push`. O GitHub leva cerca de 1 minuto para atualizar.
- DNS no Registro.br: a raiz aponta para os 4 endereços do GitHub Pages (185.199.108.153 a 185.199.111.153), e o `www` é CNAME para `ogeorgedias.github.io`. Os registros MX (e-mail do Google) e o TXT do Google não podem ser mexidos.
