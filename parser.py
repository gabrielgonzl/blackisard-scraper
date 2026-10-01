"""
Parser para extraer datos de productos de Blackisard
"""
import re
import hashlib
import logging
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

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
    Extrae información de un elemento de producto - VERSIÓN CORREGIDA
    
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
        
        # CORRECCIÓN FINAL: Usar el método probado del debug
        # Basado en el análisis que mostró que funciona correctamente
        current_price, old_price = extract_prices_correctly(product_element, product_url)
        
        # Verificar stock - MÉTODO CORREGIDO
        in_stock = extract_stock_correctly(product_element)
        
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
            'raw_current_price_text': f"{current_price}€" if current_price else None,
            'raw_old_price_text': f"{old_price}€" if old_price else None
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
        logger.debug(f"Error parseando producto: {e}")
        return None

def extract_prices_correctly(product_element, product_url: str):
    """
    Extrae precios correctamente - LÓGICA SIMPLIFICADA Y PROBADA
    
    Args:
        product_element: Elemento del producto
        product_url (str): URL del producto
    
    Returns:
        Tuple[Optional[float], Optional[float]]: (precio_actual, precio_anterior)
    """
    current_price = None
    old_price = None
    
    # MÉTODO SIMPLIFICADO: Buscar todos los elementos con €
    price_elements = product_element.find_all(string=re.compile(r'€'))
    
    if len(price_elements) >= 2:
        # En Blackisard, el primer precio es el ACTUAL (con descuento)
        # y el segundo es el ANTERIOR (precio original)
        
        # Extraer texto de ambos elementos
        current_price_text = price_elements[0].strip()
        old_price_text = price_elements[1].strip()
        
        # Parsear precios
        current_price = parse_price(current_price_text)
        old_price = parse_price(old_price_text)
        
        logger.debug(f"💰 Precios extraídos: actual={current_price}€, anterior={old_price}€")
    
    elif len(price_elements) == 1:
        # Solo un precio (producto sin descuento)
        current_price = parse_price(price_elements[0].strip())
        logger.debug(f"💰 Precio único: actual={current_price}€")
    
    # VALIDACIÓN: Verificar que los precios son razonables
    if current_price and (current_price < 0.5 or current_price > 5000):
        logger.warning(f"Precio actual sospechoso: {current_price}€ para {product_url}")
        current_price = None
    
    if old_price and (old_price < 0.5 or old_price > 5000):
        logger.warning(f"Precio anterior sospechoso: {old_price}€ para {product_url}")
        old_price = None
    
    # VALIDACIÓN ESPECÍFICA: Verificar que el descuento tenga sentido
    if current_price and old_price:
        calculated_discount = calculate_discount(current_price, old_price)
        
        # Si el descuento es sospechoso (>80% o <0% para productos en oferta)
        if calculated_discount and (calculated_discount > 80 or calculated_discount < -20):
            logger.warning(f"Descuento sospechoso: {calculated_discount}% para {product_url}")
            logger.warning(f"Precios: actual={current_price}€, anterior={old_price}€")
            
            # En caso de descuento muy alto, asumir que son precios de productos diferentes
            # Tomar solo el primer precio como precio actual
            old_price = None
            logger.info(f"Corregido: solo precio actual {current_price}€ (sin precio anterior)")
    
    return current_price, old_price
    
    return current_price, old_price

def extract_stock_correctly(product_element):
    """
    Extrae el estado de stock correctamente basándose en el debug
    
    Args:
        product_element: Elemento del producto
    
    Returns:
        bool: True si está en stock, False si no
    """
    # MÉTODO 1: Buscar elemento específico de stock
    stock_element = product_element.find(class_='stock-label-lbl')
    
    if stock_element:
        stock_text = stock_element.get_text().strip().lower()
        # "En stock" = True, "Fuera de stock" = False
        if 'en stock' in stock_text and 'fuera de stock' not in stock_text:
            return True
        elif 'fuera de stock' in stock_text:
            return False
    
    # MÉTODO 2: Buscar por texto si no encuentra el elemento específico
    product_text = product_element.get_text().lower()
    
    # Indicadores de que SÍ está en stock
    if any(indicator in product_text for indicator in ['en stock', 'disponible']) and \
       'fuera de stock' not in product_text:
        return True
    
    # Indicadores de que NO está en stock
    if any(indicator in product_text for indicator in ['fuera de stock', 'out of stock', 'agotado']):
        return False
    
    # Si no se encuentra información específica, asumir que está en stock
    # para no perder productos válidos
    return True

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
    
    logger.debug("🔍 DEBUG: Iniciando parseo de página...")
    
    # CORRECCIÓN FINAL: Usar la estructura real encontrada
    # article.product-miniature es el contenedor correcto
    product_elements = soup.find_all('article', class_='product-miniature')
    
    logger.debug(f"🔍 DEBUG: {len(product_elements)} artículos product-miniature encontrados")
    
    # Extraer datos de cada producto
    for i, element in enumerate(product_elements):
        product_data = parse_product_card(element, base_url)
        if product_data:
            products.append(product_data)
            logger.debug(f"   [{i+1}] ✅ {product_data.get('name', 'Sin nombre')[:50]}...")
            logger.debug(f"        💰 {product_data.get('current_price')}€ ({product_data.get('discount', 0):.1f}% desc.)")
        else:
            logger.debug(f"   [{i+1}] ❌ Fallo al extraer datos")
    
    # Si no se encuentran productos en product-miniature, usar fallback anterior
    if not product_elements:
        logger.warning("⚠️  No se encontraron productos en article.product-miniature, usando método anterior...")
        
        # Paso 1: Encontrar todos los enlaces a productos
        product_links = soup.find_all('a', href=re.compile(r'/escalada-en-roca/.*\.html'))
        logger.debug(f"🔍 DEBUG: {len(product_links)} enlaces a productos encontrados")
        
        # Agrupar enlaces únicos
        unique_urls = set()
        for link in product_links:
            url = link.get('href', '')
            unique_urls.add(url)
        
        logger.debug(f"🔍 DEBUG: {len(unique_urls)} URLs únicas de productos")
        
        # Para cada URL única, encontrar el mejor contenedor
        processed_urls = set()
        for link in product_links:
            url = link.get('href', '')
            
            if url in processed_urls:
                continue
            processed_urls.add(url)
            
            logger.debug(f"🔍 DEBUG: Procesando {url[:50]}...")
            
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
                    logger.debug(f"   ✅ {product_data.get('name', 'Sin nombre')[:30]}...")
                else:
                    logger.debug(f"   ❌ Fallo al extraer datos")
            else:
                logger.debug(f"   ❌ No se encontró contenedor de producto")
    
    logger.debug(f"🔍 DEBUG: {len(products)} productos extraídos exitosamente")
    
    # También intentar extraer de JSON-LD
    json_ld_products = extract_from_json_ld(soup)
    logger.debug(f"🔍 DEBUG: {len(json_ld_products)} productos de JSON-LD")
    
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
        logger.debug(f"🔍 DEBUG: Siguiente página encontrada: {next_page_url}")
    else:
        logger.debug(f"🔍 DEBUG: No hay siguiente página")
    
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