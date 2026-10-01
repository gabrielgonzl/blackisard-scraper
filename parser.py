"""
Parser para extraer datos de productos de Blackisard
"""
import re
import hashlib
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

def parse_price(price_text):
    """
    Parsea un precio en formato europeo a float
    
    Args:
        price_text (str): Texto del precio (ej: "59,90 €")
    
    Returns:
        float or None: Precio como número o None si no se puede parsear
    """
    if not price_text:
        return None
    
    # Eliminar espacios no separables y normalizar
    price_text = price_text.replace('\xa0', ' ').strip()
    
    # Extraer todos los números/dígitos
    price_match = re.search(r'(\d+(?:[., ]\d{3})*|\d+)(?:[,.](\d{2}))?', price_text)
    
    if not price_match:
        return None
    
    # Separar parte entera y decimal
    int_part = price_match.group(1)
    decimal_part = price_match.group(2)
    
    # Limpiar separadores de miles de la parte entera
    for sep in ['.', ',', ' ']:
        if sep != ',' and sep in int_part:
            int_part = int_part.replace(sep, '')
    
    # Construir número
    if decimal_part:
        number_str = int_part + '.' + decimal_part
    else:
        number_str = int_part
    
    try:
        return float(number_str)
    except ValueError:
        return None

def calculate_discount(current_price, old_price):
    """
    Calcula el porcentaje de descuento
    
    Args:
        current_price (float): Precio actual
        old_price (float): Precio anterior
    
    Returns:
        float or None: Porcentaje de descuento redondeado a 2 decimales
    """
    if current_price is None or old_price is None or old_price <= 0 or current_price < 0:
        return None
    
    discount = ((old_price - current_price) / old_price) * 100
    return round(discount, 2)

def generate_product_id(product_data):
    """
    Genera un identificador estable para un producto
    
    Args:
        product_data (dict): Datos del producto
    
    Returns:
        str: ID único del producto
    """
    # Priorizar IDs reales
    if product_data.get('product_id'):
        return f"id_{product_data['product_id']}"
    
    if product_data.get('sku'):
        return f"sku_{product_data['sku']}"
    
    # Usar URL canónica
    if product_data.get('canonical_url'):
        url_hash = hashlib.md5(product_data['canonical_url'].encode()).hexdigest()[:12]
        return f"url_{url_hash}"
    
    # Fallback: hash de nombre + URL base
    base_str = f"{product_data.get('name', '')}"
    if product_data.get('url'):
        parsed_url = urlparse(product_data['url'])
        base_str += parsed_url.path
    else:
        base_str += product_data.get('name', '')
    
    name_hash = hashlib.md5(base_str.encode()).hexdigest()[:12]
    return f"name_{name_hash}"

def generate_offer_fingerprint(product_data):
    """
    Genera una huella digital única para una oferta
    
    Args:
        product_data (dict): Datos del producto
    
    Returns:
        str: Fingerprint único para la oferta
    """
    current_price = product_data.get('current_price')
    old_price = product_data.get('old_price')
    
    if current_price is None or old_price is None:
        return None
    
    # Crear fingerprint basado en producto + precios
    price_data = f"{current_price:.2f}_{old_price:.2f}"
    return hashlib.md5(price_data.encode()).hexdigest()[:16]

def extract_product_id_from_url(url):
    """
    Extrae el ID del producto de la URL si está presente
    
    Args:
        url (str): URL del producto
    
    Returns:
        str or None: ID del producto si se encuentra
    """
    # URLs de productos suelen tener el formato /producto/id-producto
    # o similar con el ID numérico
    patterns = [
        r'/(\d{3,6})-',  # Ej: /11085-producto-name
        r'\/(\d{4,6})(?:\/|$)',  # ID al final del path
        r'id_product[=:](\d+)',  # Parámetro id_product
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def parse_stock_status(product_element):
    """
    Determina si un producto está en stock
    
    Args:
        product_element: Elemento BeautifulSoup del producto
    
    Returns:
        bool: True si está en stock, False en caso contrario
    """
    # Buscar indicadores de stock
    stock_indicators = [
        'stock-label-lbl-in-stock',
        'in-stock',
        'available'
    ]
    
    # También buscar texto que indique disponibilidad
    stock_text = product_element.get_text().lower()
    unavailable_indicators = [
        'agotado',
        'out of stock',
        'no disponible',
        'sin stock'
    ]
    
    # Verificar indicadores de no disponibilidad primero
    for indicator in unavailable_indicators:
        if indicator in stock_text:
            return False
    
    # Verificar indicadores de disponibilidad
    for indicator in stock_indicators:
        if product_element.find(class_=re.compile(indicator, re.I)):
            return True
    
    # Si no se encuentra ningún indicador, asumir disponible
    # (es lo más común en ecommerce)
    return True

def parse_product_card(product_element, base_url="https://blackisard.com"):
    """
    Extrae información de un elemento de producto
    
    Args:
        product_element: Elemento BeautifulSoup que contiene el producto
        base_url (str): URL base para construir URLs relativas
    
    Returns:
        dict: Datos del producto o None si no se puede extraer
    """
    try:
        # Extraer URL del producto
        link_element = product_element.find('a', href=True)
        if not link_element:
            return None
        
        product_url = urljoin(base_url, link_element['href'])
        
        # Extraer nombre
        name_element = product_element.find(class_='product-title') or \
                      product_element.find('h3') or \
                      product_element.find(class_=re.compile('title|name'))
        
        if not name_element:
            return None
        
        product_name = name_element.get_text().strip()
        
        # CORRECCIÓN: Los precios pueden estar en contenedores padre
        # Buscar precios en el elemento y en contenedores padre
        current_price_element = None
        old_price_element = None
        current_price_text = ""
        old_price_text = ""
        
        # Primero buscar en el elemento actual
        current_price_element = product_element.find(class_='product-price') or \
                               product_element.find(class_='current-price') or \
                               product_element.find(class_='price')
        
        old_price_element = product_element.find(class_='regular-price') or \
                           product_element.find(class_='old-price') or \
                           product_element.find(class_='crossed-out') or \
                           product_element.find('del')
        
        # Si no se encuentran, buscar en el contenedor padre
        if not current_price_element:
            parent = product_element.parent
            for _ in range(3):  # Buscar hasta 3 niveles arriba
                if parent:
                    current_price_element = parent.find(class_='product-price') or \
                                           parent.find(class_='current-price') or \
                                           parent.find(class_='price')
                    if current_price_element:
                        break
                    parent = parent.parent
        
        if not old_price_element:
            parent = product_element.parent
            for _ in range(3):  # Buscar hasta 3 niveles arriba
                if parent:
                    old_price_element = parent.find(class_='regular-price') or \
                                       parent.find(class_='old-price') or \
                                       parent.find(class_='crossed-out') or \
                                       parent.find('del')
                    if old_price_element:
                        break
                    parent = parent.parent
        
        # Extraer textos de precio
        if current_price_element:
            current_price_text = current_price_element.get_text().strip()
        
        if old_price_element:
            old_price_text = old_price_element.get_text().strip()
        
        # CORRECCIÓN ADICIONAL: Buscar precios por texto directo
        # Ya que vimos "51,16 € 77,00 € -33,56%" en el HTML
        if not current_price_text or not old_price_text:
            # Buscar contenedor con precios
            search_element = product_element
            for _ in range(5):  # Buscar en hasta 5 niveles
                if search_element:
                    # Buscar cualquier elemento con precios
                    price_texts = search_element.find_all(string=re.compile(r'\d+[,.]?\d*\s*€'))
                    if price_texts:
                        # El texto completo suele estar en el mismo elemento o padre
                        parent = search_element.parent
                        if parent:
                            full_text = parent.get_text()
                            # Extraer ambos precios del texto completo
                            price_matches = re.findall(r'(\d{1,3}[,.]?\d{0,2})\s*€', full_text)
                            if len(price_matches) >= 2:
                                current_price_text = f"{price_matches[0]} €"
                                old_price_text = f"{price_matches[1]} €"
                                break
                    
                    search_element = search_element.parent
                else:
                    break
        
        # Parsear precios
        current_price = parse_price(current_price_text) if current_price_text else None
        old_price = parse_price(old_price_text) if old_price_text else None
        
        # Verificar stock
        in_stock = parse_stock_status(product_element)
        
        # Extraer ID del producto
        product_id = extract_product_id_from_url(product_url)
        
        # Extraer SKU o referencia si está disponible
        sku_element = product_element.find(class_=re.compile('sku|ref|reference'))
        sku = sku_element.get_text().strip() if sku_element else None
        
        # Construir datos del producto
        product_data = {
            'product_id': product_id,
            'name': product_name,
            'url': product_url,
            'canonical_url': product_url,
            'current_price': current_price,
            'old_price': old_price,
            'in_stock': in_stock,
            'sku': sku,
            'raw_current_price_text': current_price_text,
            'raw_old_price_text': old_price_text
        }
        
        # Calcular descuento si ambos precios están disponibles
        if current_price is not None and old_price is not None:
            product_data['discount'] = calculate_discount(current_price, old_price)
        else:
            product_data['discount'] = None
        
        # Generar IDs
        product_data['product_id_hash'] = generate_product_id(product_data)
        product_data['offer_fingerprint'] = generate_offer_fingerprint(product_data)
        
        return product_data
        
    except Exception as e:
        # En caso de error, log y continuar
        return None

def extract_from_json_ld(soup):
    """
    Extrae productos de datos JSON-LD si están disponibles
    
    Args:
        soup: BeautifulSoup object
    
    Returns:
        list: Lista de productos extraídos de JSON-LD
    """
    products = []
    
    # Buscar scripts JSON-LD
    json_scripts = soup.find_all('script', type='application/ld+json')
    
    for script in json_scripts:
        try:
            import json
            data = json.loads(script.string)
            
            # Buscar ItemList con productos
            if isinstance(data, dict) and data.get('@type') == 'ItemList':
                for item in data.get('itemListElement', []):
                    product_info = item.get('item', {})
                    
                    # Extraer datos del producto
                    name = product_info.get('name', '')
                    url = product_info.get('url', '')
                    product_id = None
                    
                    # Intentar extraer ID de la URL
                    if url:
                        product_id = extract_product_id_from_url(url)
                    
                    if name and url:
                        product_data = {
                            'product_id': product_id,
                            'name': name,
                            'url': url,
                            'canonical_url': url,
                            'source': 'json-ld'
                        }
                        products.append(product_data)
        
        except (json.JSONDecodeError, Exception):
            # Si falla el parsing JSON, continuar
            continue
    
    return products

def parse_page(soup, base_url="https://blackisard.com"):
    """
    Parsea una página de productos
    
    Args:
        soup: BeautifulSoup object de la página
        base_url (str): URL base
    
    Returns:
        tuple: (productos, next_page_url)
    """
    products = []
    
    print(f"🔍 DEBUG: Iniciando parseo de página...")
    
    # CORRECCIÓN FINAL: Usar la estructura real encontrada
    # article.product-miniature es el contenedor correcto
    product_elements = soup.find_all('article', class_='product-miniature')
    
    print(f"🔍 DEBUG: {len(product_elements)} artículos product-miniature encontrados")
    
    # Extraer datos de cada producto
    for i, element in enumerate(product_elements):
        product_data = parse_product_card(element, base_url)
        if product_data:
            products.append(product_data)
            print(f"   [{i+1}] ✅ {product_data.get('name', 'Sin nombre')[:50]}...")
            print(f"        💰 {product_data.get('current_price')}€ ({product_data.get('discount', 0):.1f}% desc.)")
        else:
            print(f"   [{i+1}] ❌ Fallo al extraer datos")
    
    # Si no se encuentran productos en product-miniature, usar fallback anterior
    if not product_elements:
        print("⚠️  No se encontraron productos en article.product-miniature, usando método anterior...")
        
        # Paso 1: Encontrar todos los enlaces a productos
        product_links = soup.find_all('a', href=re.compile(r'/escalada-en-roca/.*\.html'))
        print(f"🔍 DEBUG: {len(product_links)} enlaces a productos encontrados")
        
        # Agrupar enlaces únicos
        unique_urls = set()
        for link in product_links:
            url = link.get('href', '')
            unique_urls.add(url)
        
        print(f"🔍 DEBUG: {len(unique_urls)} URLs únicas de productos")
        
        # Para cada URL única, encontrar el mejor contenedor
        processed_urls = set()
        for link in product_links:
            url = link.get('href', '')
            
            if url in processed_urls:
                continue
            processed_urls.add(url)
            
            print(f"🔍 DEBUG: Procesando {url[:50]}...")
            
            # Buscar el enlace por URL
            found_link = soup.find('a', href=url)
            if not found_link:
                continue
            
            # Buscar article.product-miniature padre
            product_container = found_link.find_parent('article', class_='product-miniature')
            
            # Extraer datos del producto
            if product_container:
                product_data = parse_product_card(product_container, base_url)
                if product_data:
                    products.append(product_data)
                    print(f"   ✅ {product_data.get('name', 'Sin nombre')[:30]}...")
                else:
                    print(f"   ❌ Fallo al extraer datos")
            else:
                print(f"   ❌ No se encontró contenedor de producto")
    
    print(f"🔍 DEBUG: {len(products)} productos extraídos exitosamente")
    
    # También intentar extraer de JSON-LD
    json_ld_products = extract_from_json_ld(soup)
    print(f"🔍 DEBUG: {len(json_ld_products)} productos de JSON-LD")
    
    for product_data in json_ld_products:
        # Completar con IDs y fingerprints
        product_data['product_id_hash'] = generate_product_id(product_data)
        products.append(product_data)
    
    # Encontrar URL de la siguiente página
    next_page_url = None
    
    # Buscar enlace rel="next"
    next_link = soup.find('link', rel='next')
    if next_link:
        next_page_url = urljoin(base_url, next_link.get('href', ''))
        print(f"🔍 DEBUG: Siguiente página encontrada: {next_page_url}")
    else:
        print(f"🔍 DEBUG: No hay siguiente página")
    
    return products, next_page_url

if __name__ == "__main__":
    # Test básico del parser
    print("Test del parser")
    print("=" * 50)
    
    # Test de parseo de precios
    test_prices = [
        "59,90 €",
        "1.299,95 €",
        "59.90 €",
        "15,72 €",
        "77,00 €"
    ]
    
    for price_text in test_prices:
        parsed = parse_price(price_text)
        print(f"{price_text:15} -> {parsed}")
    
    print("\n" + "=" * 50)
    
    # Test de cálculo de descuento
    test_discounts = [
        (59.90, 35.90),
        (100.00, 50.00),
        (77.00, 51.16)
    ]
    
    for current, old in test_discounts:
        discount = calculate_discount(current, old)
        print(f"{old:.2f}€ -> {current:.2f}€ = -{discount:.2f}%")