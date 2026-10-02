"""
Generador del reporte HTML de ofertas (ofertas.html)
"""
import html
import os

from formatter import MarkdownFormatter
from parser import extract_category


def _category_label(category):
    """Convierte el slug de categoría en etiqueta visible (ej: ropa-escalada -> Ropa Escalada)"""
    return category.replace('-', ' ').replace('_', ' ').title()


def _category_slug(category):
    """Convierte el slug de categoría en id válido para anclas"""
    return category.lower().replace(' ', '-').replace('_', '-')


def _product_card(product, fmt):
    """Genera la tarjeta HTML de un producto con su última oferta e historial"""
    e = html.escape
    offers = sorted(product.get('offers'), key=lambda o: o.get('first_seen', ''))
    latest = max(offers, key=lambda o: o.get('first_seen', ''))
    name = e(product.get('name') or 'Producto desconocido')
    url = product.get('url') or latest.get('source_url') or '#'

    parts = ['<article class="card">']
    if product.get('image_url'):
        parts.append(
            f'<div class="imgbox"><img src="{e(product["image_url"])}" '
            f'alt="{name}" loading="lazy"></div>'
        )
    parts.append(f'<h3>{name}</h3>')

    price_html = f'<strong>{fmt.format_price(latest.get("current_price"))}</strong>'
    if latest.get('old_price') is not None:
        price_html += f' <s>{fmt.format_price(latest.get("old_price"))}</s>'
    if latest.get('discount') is not None:
        price_html += f' <span class="badge">{fmt.format_discount(latest.get("discount"))}</span>'
    parts.append(f'<p class="price">{price_html}</p>')
    parts.append(f'<a href="{e(url)}">Ver producto</a>')

    parts.append(f'<details><summary>Historial ({len(offers)})</summary><ul>')
    for offer in offers:
        line = (
            f'{fmt.format_price(offer.get("current_price"))} '
            f'({fmt.format_price(offer.get("old_price"))}, '
            f'{fmt.format_discount(offer.get("discount"))})'
        )
        date = e(str(offer.get('first_seen', '')))
        link = e(offer.get('source_url') or '#')
        parts.append(f'<li>{line} — {date} — <a href="{link}">Ver</a></li>')
    parts.append('</ul></details></article>')
    return ''.join(parts)


def generate(state, output_file='ofertas.html') -> bool:
    """
    Genera el reporte HTML de ofertas a partir del estado

    Args:
        state (dict): Estado con productos y ofertas
        output_file (str): Ruta al archivo HTML de salida

    Returns:
        bool: True si se generó correctamente
    """
    fmt = MarkdownFormatter()
    e = html.escape

    products = [p for p in state.get('products', {}).values() if p.get('offers')]
    total_offers = sum(len(p['offers']) for p in products)

    # Agrupar por categoría
    groups = {}
    for product in products:
        # ponytail: fallback desde la URL para states viejos sin 'category'
        key = product.get('category') or extract_category(product.get('url') or '') or 'Sin categoría'
        groups.setdefault(key, []).append(product)

    nav_items = []
    sections = []
    for key in sorted(groups, key=_category_label):
        items = groups[key]
        slug = _category_slug(key)
        label = e(_category_label(key))
        nav_items.append(f'<a href="#cat-{e(slug)}">{label} ({len(items)})</a>')
        cards = ''.join(_product_card(p, fmt) for p in items)
        sections.append(
            f'<section id="cat-{e(slug)}"><h2>{label} ({len(items)})</h2>'
            f'<div class="grid">{cards}</div></section>'
        )

    last_updated = e(str(state.get('last_updated') or ''))
    content = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ofertas Blackisard</title>
<style>
* {{ box-sizing: border-box; }}
body {{ font-family: system-ui, sans-serif; margin: 0; background: #fafafa; color: #222; }}
header {{ padding: 1.5rem 1rem; background: #fff; border-bottom: 1px solid #e5e5e5; }}
header h1 {{ margin: 0 0 .25rem; }}
header p {{ margin: 0; color: #555; font-size: .9rem; }}
nav {{ display: flex; flex-wrap: wrap; gap: .5rem; padding: 1rem; }}
nav a {{ text-decoration: none; color: #0b57d0; background: #eef3fd; padding: .25rem .6rem; border-radius: 999px; font-size: .9rem; }}
main {{ padding: 0 1rem 2rem; }}
section {{ margin-top: 1.5rem; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 1rem; }}
.card {{ background: #fff; border: 1px solid #e5e5e5; border-radius: 8px; padding: .75rem; display: flex; flex-direction: column; gap: .4rem; }}
.imgbox {{ height: 160px; display: flex; align-items: center; justify-content: center; background: #f5f5f5; border-radius: 6px; }}
.imgbox img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
.card h3 {{ font-size: .95rem; margin: 0; }}
.price {{ margin: 0; display: flex; flex-wrap: wrap; align-items: center; gap: .4rem; }}
.price s {{ color: #777; }}
.badge {{ background: #e8501e; color: #fff; padding: .1rem .45rem; border-radius: 4px; font-size: .8rem; font-weight: 600; }}
.card > a {{ margin-top: auto; color: #0b57d0; text-decoration: none; font-size: .9rem; }}
details {{ font-size: .85rem; }}
details ul {{ margin: .3rem 0 0; padding-left: 1.1rem; }}
details li {{ margin-bottom: .25rem; }}
@media (max-width: 480px) {{ .grid {{ grid-template-columns: 1fr 1fr; }} }}
</style>
</head>
<body>
<header>
<h1>Ofertas Blackisard</h1>
<p>{len(products)} productos · {total_offers} ofertas · Actualizado: {last_updated}</p>
</header>
<nav>{''.join(nav_items)}</nav>
<main>{''.join(sections)}</main>
</body>
</html>
"""

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except (IOError, OSError) as ex:
        print(f"Error al crear reporte HTML: {ex}")
        return False


if __name__ == "__main__":
    import json
    import sys
    from config import STATE_FILE, HTML_OUTPUT_FILE

    if '--test' not in sys.argv:
        # Uso normal: generar ofertas.html desde state.json
        if not os.path.exists(STATE_FILE):
            print(f"No existe {STATE_FILE}. Ejecuta primero el scraper.")
            sys.exit(1)
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            state = json.load(f)
        sys.exit(0 if generate(state, HTML_OUTPUT_FILE) else 1)

    # Self-check
    print("Test del generador HTML")
    print("=" * 50)

    sample_state = {
        'last_updated': '2026-10-02T12:00:00',
        'products': {
            'id_11085': {
                'name': 'Producto Con Imagen',
                'url': 'https://blackisard.com/escalada-en-roca/ropa-escalada/11085-5183-foo.html',
                'category': 'ropa-escalada',
                'image_url': 'https://blackisard.com/26689-home_default/foo.jpg',
                'offers': [
                    {
                        'current_price': 35.90, 'old_price': 59.90, 'discount': 40.07,
                        'first_seen': '2026-10-01',
                        'source_url': 'https://blackisard.com/escalada-en-roca/ropa-escalada/11085-5183-foo.html'
                    },
                    {
                        'current_price': 29.90, 'old_price': 59.90, 'discount': 50.08,
                        'first_seen': '2026-10-02',
                        'source_url': 'https://blackisard.com/escalada-en-roca/ropa-escalada/11085-5183-foo.html'
                    }
                ]
            },
            'id_11249': {
                'name': 'Producto Sin Imagen',
                'url': 'https://blackisard.com/bulder/pies-de-gato-boulder/11249-x.html',
                'category': 'pies-de-gato-boulder',
                'image_url': None,
                'offers': [
                    {
                        'current_price': 77.00, 'old_price': 100.00, 'discount': 23.00,
                        'first_seen': '2026-10-01',
                        'source_url': 'https://blackisard.com/bulder/pies-de-gato-boulder/11249-x.html'
                    }
                ]
            }
        }
    }

    output = 'test_ofertas.html'
    assert generate(sample_state, output), "generate() devolvió False"

    with open(output, 'r', encoding='utf-8') as f:
        content = f.read()

    assert 'https://blackisard.com/26689-home_default/foo.jpg' in content, "Falta la URL de imagen"
    assert 'Ropa Escalada' in content, "Falta la etiqueta de categoría Ropa Escalada"
    assert 'Pies De Gato Boulder' in content, "Falta la etiqueta de categoría Pies De Gato Boulder"
    assert '35.90 €' in content or '29.90 €' in content, "Falta un precio"
    assert '-50.08%' in content or '-40.07%' in content, "Falta la insignia de descuento"

    os.remove(output)
    print("OK")
