#!/usr/bin/env python3
"""
Debug detallado para encontrar la estructura exacta de productos
"""
import requests
from bs4 import BeautifulSoup
import re

def find_product_structure():
    """Encuentra la estructura exacta de los productos"""
    url = "https://blackisard.com/escalada-en-roca"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("🔍 Buscando la estructura real de productos...")
        
        # Buscar todos los enlaces a productos
        product_links = soup.find_all('a', href=re.compile(r'/escalada-en-roca/.*\.html'))
        print(f"\n📦 Encontrados {len(product_links)} enlaces a productos")
        
        # Analizar cada producto individualmente
        for i, link in enumerate(product_links[:5]):  # Solo primeros 5
            print(f"\n{'='*60}")
            print(f"PRODUCTO {i+1}:")
            print(f"{'='*60}")
            
            href = link.get('href')
            print(f"🔗 URL: {href}")
            
            # Buscar el contenedor del producto
            product_container = link.find_parent(['div', 'article', 'section', 'li'])
            if not product_container:
                # Buscar padres más arriba
                parent = link.parent
                for _ in range(5):  # Subir hasta 5 niveles
                    if parent and parent.name in ['div', 'article', 'section', 'li']:
                        product_container = parent
                        break
                    parent = parent.parent if parent else None
            
            if product_container:
                print(f"📦 Contenedor: {product_container.name}")
                print(f"🎨 Clases del contenedor: {product_container.get('class', [])}")
                
                # Buscar nombre del producto
                name_elem = product_container.find(['h3', 'h2', 'h4', 'h1']) or \
                          product_container.find(class_=re.compile(r'name|title|product.*name')) or \
                          product_container.find('a', href=href)
                
                if name_elem:
                    name = name_elem.get_text().strip()
                    print(f"🏷️  Nombre: {name}")
                else:
                    print(f"🏷️  Nombre: NO ENCONTRADO")
                
                # Buscar precios
                price_elems = product_container.find_all(['span', 'div'], string=re.compile(r'\d+[,.]?\d*\s*€'))
                print(f"💰 Elementos de precio: {len(price_elems)}")
                for j, price_elem in enumerate(price_elems):
                    price_text = price_elem.get_text().strip()
                    print(f"    [{j}] {price_text}")
                
                # Buscar descuentos
                discount_elems = product_container.find_all(string=re.compile(r'-?\d+[,.]?\d*\s*%'))
                print(f"🏷️  Elementos de descuento: {len(discount_elems)}")
                for j, discount_elem in enumerate(discount_elems):
                    discount_text = discount_elem.strip()
                    print(f"    [{j}] {discount_text}")
                
                # Mostrar estructura HTML
                print(f"\n📋 Estructura HTML:")
                print(product_container.prettify()[:500] + "...")
        
        # Buscar patrones comunes en los productos
        print(f"\n🔍 Analizando patrones comunes...")
        
        # Buscar contenedores que tengan tanto precio como enlace
        all_divs = soup.find_all('div')
        product_containers = []
        
        for div in all_divs:
            if div.find('a', href=re.compile(r'/escalada-en-roca/.*\.html')) and \
               div.find(text=re.compile(r'\d+[,.]?\d*\s*€')):
                product_containers.append(div)
        
        print(f"🎯 Posibles contenedores de productos: {len(product_containers)}")
        
        if product_containers:
            first = product_containers[0]
            print(f"📦 Primer contenedor:")
            print(f"   Nombre: {first.name}")
            print(f"   Clases: {first.get('class', [])}")
            print(f"   ID: {first.get('id', 'None')}")
            
            # Verificar si tiene estructura consistente
            prices = first.find_all(text=re.compile(r'\d+[,.]?\d*\s*€'))
            links = first.find_all('a', href=re.compile(r'/escalada-en-roca/.*\.html'))
            print(f"   Precios: {len(prices)}, Enlaces: {len(links)}")
    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    find_product_structure()