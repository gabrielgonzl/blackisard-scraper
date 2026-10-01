#!/usr/bin/env python3
"""
Debug específico del nuevo parse_page
"""
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

def debug_new_parse():
    """Debug del nuevo método de parseo"""
    url = "https://blackisard.com/escalada-en-roca"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"🔍 PASO 1: Encontrar enlaces a productos...")
        
        # Paso 1: Encontrar todos los enlaces a productos
        product_links = soup.find_all('a', href=re.compile(r'/escalada-en-roca/.*\.html'))
        print(f"   ✅ {len(product_links)} enlaces a productos encontrados")
        
        # Paso 2: Agrupar enlaces únicos (evitar duplicados)
        unique_urls = set()
        for link in product_links:
            url_text = link.get('href', '')
            unique_urls.add(url_text)
        
        print(f"   ✅ {len(unique_urls)} URLs únicas de productos")
        
        # Mostrar las primeras URLs
        print(f"   📋 Primeras 5 URLs:")
        for i, url_text in enumerate(list(unique_urls)[:5]):
            print(f"      [{i+1}] {url_text}")
        
        # Paso 3: Procesar la primera URL como ejemplo
        processed_urls = set()
        first_link = None
        first_url = None
        
        for link in product_links:
            url_text = link.get('href', '')
            if url_text not in processed_urls:
                first_link = link
                first_url = url_text
                break
        
        if first_link:
            processed_urls.add(first_url)
            
            print(f"\n🔍 PASO 2: Analizando primer producto...")
            print(f"   URL: {first_url}")
            
            # Buscar el enlace por URL
            found_link = soup.find('a', href=first_url)
            if not found_link:
                print(f"   ❌ No se pudo encontrar el enlace")
                return
            
            print(f"   ✅ Enlace encontrado en el DOM")
            
            # Encontrar el contenedor de producto más apropiado
            print(f"\n🔍 PASO 3: Buscando contenedor de producto...")
            
            # Opción 1: Buscar thumbnail-container padre
            print(f"   🔍 Opción 1: Buscando thumbnail-container...")
            thumbnail = found_link.find_parent(class_='thumbnail-container')
            if thumbnail:
                print(f"      ✅ Thumbnail-container encontrado")
                
                # Buscar el div.col asociado (padre del thumbnail)
                col_parent = thumbnail.parent
                if col_parent and col_parent.name == 'div':
                    print(f"      ✅ div.col padre encontrado: {col_parent.get('class', [])}")
                else:
                    print(f"      ❌ No se encontró div.col como padre")
            else:
                print(f"      ❌ No hay thumbnail-container")
            
            # Opción 2: Si no hay thumbnail-container, usar el div.col más cercano
            print(f"\n   🔍 Opción 2: Buscando div.col más cercano...")
            div_col = found_link.find_parent('div', class_='col')
            if div_col:
                print(f"      ✅ div.col encontrado: {div_col.get('class', [])}")
                print(f"      📄 Contenido del div.col (primeros 200 chars): {div_col.get_text()[:200]}...")
                
                # Verificar si este div.col tiene precios
                prices = div_col.find_all(string=re.compile(r'\d+[,.]?\d*\s*€'))
                print(f"      💰 Precios en div.col: {len(prices)}")
                if prices:
                    for i, price in enumerate(prices[:3]):
                        print(f"         [{i+1}] {price.strip()}")
            else:
                print(f"      ❌ No hay div.col como contenedor")
            
            # Opción 3: Usar el contenedor más apropiado disponible
            print(f"\n   🔍 Opción 3: Buscando contenedor padre con precios...")
            parent = found_link.parent
            found_container = None
            
            for level in range(4):  # Buscar hasta 4 niveles arriba
                if parent:
                    has_price = parent.find(string=re.compile(r'\d+[,.]?\d*\s*€'))
                    price_count = len(has_price) if has_price else 0
                    print(f"      Nivel {level}: {parent.name} {parent.get('class', [])} - Precios: {price_count}")
                    
                    if has_price:
                        found_container = parent
                        print(f"      ✅ Contenedor con precios encontrado")
                        break
                    parent = parent.parent
                else:
                    break
            
            if found_container:
                print(f"   ✅ Contenedor final seleccionado")
                print(f"      📦 Tipo: {found_container.name}")
                print(f"      🎨 Clases: {found_container.get('class', [])}")
                print(f"      📄 Texto (primeros 300 chars): {found_container.get_text()[:300]}...")
                
                # Probar extracción de datos
                print(f"\n🔍 PASO 4: Probando extracción de datos...")
                
                # Buscar nombre
                name_elem = found_container.find(class_='product-title') or found_container.find('h3')
                if name_elem:
                    name = name_elem.get_text().strip()
                    print(f"   ✅ Nombre encontrado: {name}")
                else:
                    print(f"   ❌ No se encontró nombre")
                
                # Buscar precios
                print(f"\n   💰 Buscando precios en contenedor final...")
                
                # Método 1: Buscar por clases
                current_price_elem = found_container.find(class_='product-price') or \
                                   found_container.find(class_='current-price') or \
                                   found_container.find(class_='price')
                
                if current_price_elem:
                    current_text = current_price_elem.get_text().strip()
                    print(f"   ✅ Precio por clase encontrado: {current_text}")
                else:
                    print(f"   ❌ No hay precio por clase")
                
                # Método 2: Buscar texto directo
                full_text = found_container.get_text()
                price_matches = re.findall(r'(\d{1,3}[,.]?\d{0,2})\s*€', full_text)
                print(f"   💰 Precios con regex: {price_matches}")
                
                if len(price_matches) >= 2:
                    current_price = f"{price_matches[0]} €"
                    old_price = f"{price_matches[1]} €"
                    print(f"   ✅ Precios extraídos: {current_price} / {old_price}")
                else:
                    print(f"   ❌ No se pudieron extraer 2 precios")
                    
            else:
                print(f"   ❌ No se encontró contenedor con precios")
        else:
            print(f"❌ No se pudieron procesar productos")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_new_parse()