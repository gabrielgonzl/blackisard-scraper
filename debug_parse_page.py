#!/usr/bin/env python3
"""
Debug específico para el parse_page
"""
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin

def debug_parse_page():
    """Debug del parse_page para ver exactamente qué pasa"""
    url = "https://blackisard.com/escalada-en-roca"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print("🔍 Obteniendo primera página para debug...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"📄 Página obtenida: {response.status_code}")
        print(f"📏 Tamaño HTML: {len(response.content)} caracteres")
        
        # Seguir exactamente la lógica de parse_page
        print(f"\n🔍 PASO 1: Buscar div.col...")
        product_elements = soup.find_all('div', class_='col')
        print(f"   Encontrados {len(product_elements)} elementos div.col")
        
        # Filtrar solo los elementos que realmente contienen productos
        valid_product_elements = []
        print(f"\n🔍 PASO 2: Filtrando productos válidos...")
        
        for i, element in enumerate(product_elements):
            # Verificar que tiene enlace a producto y nombre
            has_link = element.find('a', href=re.compile(r'/escalada-en-roca/.*\.html'))
            has_name = element.find(class_='product-title') or element.find('h3')
            has_price = element.find(string=re.compile(r'\d+[,.]?\d*\s*€'))
            
            print(f"   [{i+1}] Elemento div.col:")
            print(f"       - Enlace a producto: {'✅' if has_link else '❌'}")
            print(f"       - Nombre del producto: {'✅' if has_name else '❌'}")
            print(f"       - Precio: {'✅' if has_price else '❌'}")
            
            if has_link and has_name and has_price:
                valid_product_elements.append(element)
                print(f"       🟢 VÁLIDO - Añadido a productos")
            else:
                print(f"       🔴 INVÁLIDO - No cumple criterios")
        
        print(f"\n📊 RESULTADO: {len(valid_product_elements)} productos válidos encontrados")
        
        # Mostrar ejemplos de productos válidos
        if valid_product_elements:
            print(f"\n🔍 PASO 3: Analizando primer producto válido...")
            first = valid_product_elements[0]
            
            print(f"📦 Estructura completa del primer producto:")
            print(first.prettify()[:800])
            
            # Intentar extraer datos como parse_product_card
            print(f"\n🔍 PASO 4: Extrayendo datos...")
            
            # Buscar enlace
            link_element = first.find('a', href=re.compile(r'/escalada-en-roca/.*\.html'))
            if link_element:
                product_url = urljoin("https://blackisard.com", link_element['href'])
                print(f"🔗 URL: {product_url}")
            
            # Buscar nombre
            name_element = first.find(class_='product-title') or first.find('h3')
            if name_element:
                product_name = name_element.get_text().strip()
                print(f"🏷️  Nombre: {product_name}")
            
            # Buscar precios
            current_price_element = None
            old_price_element = None
            current_price_text = ""
            old_price_text = ""
            
            # Buscar en el elemento actual
            current_price_element = first.find(class_='product-price') or \
                                   first.find(class_='current-price') or \
                                   first.find(class_='price')
            
            old_price_element = first.find(class_='regular-price') or \
                               first.find(class_='old-price') or \
                               first.find(class_='crossed-out') or \
                               first.find('del')
            
            # Si no se encuentran, buscar en el contenedor padre
            if not current_price_element:
                parent = first.parent
                for _ in range(3):
                    if parent:
                        current_price_element = parent.find(class_='product-price') or \
                                               parent.find(class_='current-price') or \
                                               parent.find(class_='price')
                        if current_price_element:
                            break
                        parent = parent.parent
            
            # Extraer textos de precio
            if current_price_element:
                current_price_text = current_price_element.get_text().strip()
                print(f"💰 Precio actual (elemento): {current_price_text}")
            
            if old_price_element:
                old_price_text = old_price_element.get_text().strip()
                print(f"💰 Precio anterior (elemento): {old_price_text}")
            
            # CORRECCIÓN ADICIONAL: Buscar precios por texto directo
            if not current_price_text or not old_price_text:
                print(f"\n🔍 PASO 5: Búsqueda por texto directo...")
                
                # Buscar contenedor con precios
                search_element = first
                for level in range(5):
                    if search_element:
                        print(f"   Nivel {level}: {search_element.name} {search_element.get('class', [])}")
                        
                        # Buscar cualquier elemento con precios
                        price_texts = search_element.find_all(string=re.compile(r'\d+[,.]?\d*\s*€'))
                        if price_texts:
                            print(f"      💰 Encontrados {len(price_texts)} precios: {price_texts}")
                            
                            # El texto completo suele estar en el mismo elemento o padre
                            full_text = search_element.get_text()
                            print(f"      📄 Texto completo (primeros 200 chars): {full_text[:200]}...")
                            
                            # Extraer ambos precios del texto completo
                            price_matches = re.findall(r'(\d{1,3}[,.]?\d{0,2})\s*€', full_text)
                            print(f"      💰 Precios extraídos con regex: {price_matches}")
                            
                            if len(price_matches) >= 2:
                                current_price_text = f"{price_matches[0]} €"
                                old_price_text = f"{price_matches[1]} €"
                                print(f"      ✅ Precios finales: {current_price_text} / {old_price_text}")
                                break
                        
                        search_element = search_element.parent
                    else:
                        break
        else:
            print(f"\n❌ NO SE ENCONTRARON PRODUCTOS VÁLIDOS")
            print(f"🔍 Analizando algunos elementos div.col...")
            
            for i, element in enumerate(product_elements[:3]):
                print(f"\n--- ELEMENTO {i+1} ---")
                print(f"Clases: {element.get('class', [])}")
                print(f"Tamaño: {len(element.get_text())} caracteres")
                print(f"Texto: {element.get_text()[:100]}...")
                print(f"Estructura: {element.prettify()[:300]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_parse_page()