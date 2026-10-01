#!/usr/bin/env python3
"""
Debug script para verificar la estructura HTML de Blackisard
"""
import requests
from bs4 import BeautifulSoup
import re

def debug_blackisard():
    """Debug la estructura de la página de Blackisard"""
    url = "https://blackisard.com/escalada-en-roca"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    }
    
    try:
        print(f"🔍 Obteniendo página: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"\n📄 Título de la página:")
        title = soup.find('title')
        print(f"  {title.get_text() if title else 'No encontrado'}")
        
        print(f"\n🔎 Buscando elementos de productos...")
        
        # Buscar diferentes selectores posibles
        selectors_to_try = [
            'js-product-miniature',
            'product-miniature',
            'product-card',
            'product',
            'item-product',
            '.product',
            '[class*="product"]',
            '[class*="item"]',
            'article',
            '.col',
            '.row > div'
        ]
        
        for selector in selectors_to_try:
            elements = soup.select(selector)
            print(f"  {selector}: {len(elements)} elementos")
            if elements:
                print(f"    Ejemplo: {elements[0].get_text()[:100]}...")
        
        print(f"\n🔗 Buscando enlaces de productos...")
        product_links = soup.find_all('a', href=re.compile(r'/escalada-en-roca/.*\.html'))
        print(f"  Enlaces a productos: {len(product_links)}")
        
        if product_links:
            print(f"  Primer enlace: {product_links[0].get('href')}")
            print(f"  Texto: {product_links[0].get_text().strip()}")
        
        print(f"\n💰 Buscando precios...")
        price_elements = soup.find_all(['span', 'div'], class_=re.compile(r'price|€'))
        print(f"  Elementos con 'price' o '€': {len(price_elements)}")
        
        if price_elements:
            for i, elem in enumerate(price_elements[:5]):
                text = elem.get_text().strip()
                if '€' in text or re.search(r'\d+[,.]?\d*', text):
                    print(f"    [{i}] {text}")
        
        print(f"\n📦 Buscando estructura general...")
        # Buscar el contenedor principal de productos
        main_content = soup.find('main') or soup.find('div', id='main') or soup.find('div', class_=re.compile(r'main|content'))
        if main_content:
            print(f"  Contenido principal encontrado")
            
            # Buscar grids de productos
            product_grids = main_content.find_all(['div', 'section'], class_=re.compile(r'grid|list|collection'))
            print(f"  Grids de productos: {len(product_grids)}")
            
            # Mostrar estructura HTML del primer grid
            if product_grids:
                first_grid = product_grids[0]
                print(f"\n📋 Estructura del primer grid:")
                print(first_grid.prettify()[:1000] + "...")
        
        print(f"\n🎯 Verificando si hay productos con descuentos...")
        # Buscar texto que indique descuentos
        discount_indicators = soup.find_all(text=re.compile(r'%\s*descuento|-\s*\d+|descuento|rebaja|oferta', re.I))
        print(f"  Indicadores de descuento: {len(discount_indicators)}")
        
        if discount_indicators:
            for indicator in discount_indicators[:3]:
                parent = indicator.parent
                if parent:
                    print(f"    Contexto: {parent.get_text()[:100]}...")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_blackisard()