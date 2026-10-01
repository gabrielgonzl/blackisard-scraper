"""
Parser optimizado para extraer datos de productos de Blackisard
Versión mejorada para paralelización y velocidad
"""
import re
import hashlib
import logging
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple, Set
from functools import lru_cache

logger = logging.getLogger(__name__)

# Cache para selectores (evitar recálculo)
SELECTOR_CACHE = {}

@lru_cache(maxsize=100)
def get_product_selector_cache():
    """Cache para selectores de productos"""
    if 'product_miniature' not in SELECTOR_CACHE:
        SELECTOR_CACHE['product_miniature'] = 'article.product-miniature'
    return SELECTOR_CACHE['product_miniature']

def parse_price_optimized(price_text: str) -> Optional[float]:
    """
    Parsea un precio en formato europeo a float - VERSIÓN OPTIMIZADA
    
    Args:
        price_text (str): Texto del precio (ej: "59,90 €")
    
    Returns:
        float or None: Precio como número o None si no se puede parsear
    """
    if not price_text:
        return None
    
    # Optimización: uso de regex precompilado para patrones comunes
    price_match = re.search(r'(\d{1,4}[.,]?\d{0,2})\s*€', price_text)
    
    if not price_match:
        return None
    
    # Limpiar formato europeo
    price_str = price_match.group(1).replace(',', '.')
    
    try:
        return float(price_str)
    except ValueError:
        return None

def calculate_discount_optimized(current_price: float, old_price: float) -> Optional[float]:
    """
    Calcula el porcentaje de descuento - VERSIÓN OPTIMIZADA
    
    Args:
        current_price (float): Precio actual
        old_price (float): Precio anterior
    
    Returns:
        float or None: Porcentaje de descuento o None si no se puede calcular
    """
    if old_price <= 0 or current_price >= old_price:
        return None
    
    discount = ((old_price - current_price) / old_price) * 100
    return round(discount, 1)

def extract_product_id_optimized(url: str) -> Optional[str]:
    """
    Extrae el ID del producto de la URL - VERSIÓN OPTIMIZADA
    
    Args:
        url (str): URL del producto
    
    Returns:
        str or None: ID del producto o None si no se puede extraer
    """
    if not url:
        return None
    
    # Buscar ID en URL con regex optimizado
    match = re.search(r'/(\d{4,6})[_-]', url)
    return match.group(1) if match else None

def generate_product_id_optimized(product_data: Dict) -> str:
    """
    Genera ID único del producto - VERSIÓN OPTIMIZADA
    
    Args:
        product_data (Dict): Datos del producto
    
    Returns:
        str: Hash único del producto
    """
    # Optimización: usar solo campos esenciales para el hash
    key_fields = ['name', 'product_id', 'url']
    key_string = '|'.join(str(product_data.get(field, '')) for field in key_fields)
    
    return hashlib.md5(key_string.encode()).hexdigest()[:12]

def generate_offer_fingerprint_optimized(product_data: Dict) -> str:
    """
    Genera fingerprint único de la oferta - VERSIÓN OPTIMIZADO
    
    Args:
        product_data (Dict): Datos del producto
    
    Returns:
        str: Fingerprint de la oferta
    """
    # Solo usar campos que cambian en ofertas
    offer_fields = ['product_id', 'current_price', 'old_price']
    offer_string = '|'.join(str(product_data.get(field, '')) for field in offer_fields)
    
    return hashlib.md5(offer_string.encode()).hexdigest()[:12]

@lru_cache(maxsize=200)
def find_products_in_page_cache(soup_html: str) -> List[Dict]:
    """
    Cache para búsqueda de productos en página HTML
    
    Args:
        soup_html (str): HTML de la página como string
    
    Returns:
        List[Dict]: Lista de productos encontrados
    """
    # Parsear HTML desde cache
    soup = BeautifulSoup(soup_html, 'html.parser')
    
    # Buscar productos con selectores optimizados
    product_elements = soup.find_all('article', class_='product-miniature')
    
    products = []
    for element in product_elements:
        product_data = parse_product_card_optimized(element)
        if product_data:
            products.append(product_data)
    
    return products

def parse_product_card_optimized(product_element, base_url="https://blackisard.com"):
    """
    Extrae información de un elemento de producto - VERSIÓN OPTIMIZADA
    
    Args:
        product_element: Elemento BeautifulSoup que contiene el producto
        base_url (str): URL base para construir URLs relativas
    
    Returns:
        dict: Datos del producto o None si no se puede extraer
    """
    try:
        # Extraer URL del producto (más directo)
        link_element = product_element.find('a', href=True)
        if not link_element:
            return None
        
        product_url = urljoin(base_url, link_element['href'])
        
        # Extraer nombre de forma optimizada
        name_element = product_element.find(class_='product-title')
        if not name_element:
            name_element = product_element.find('h3')
        
        if not name_element:
            return None
        
        product_name = name_element.get_text().strip()
        
        # Búsqueda optimizada de precios
        current_price, old_price = find_prices_optimized(product_element, product_url)
        
        # Extraer ID del producto de forma optimizada
        product_id = extract_product_id_optimized(product_url)
        
        # Verificar stock - LÓGICA CORREGIDA
        in_stock = False
        
        # Buscar elementos de stock
        stock_element = product_element.find(class_='stock-label-lbl')
        if stock_element:
            stock_text = stock_element.get_text().strip().lower()
            # "en stock" = True, "fuera de stock" = False
            in_stock = 'en stock' in stock_text
        
        # Si no encuentra el elemento específico, buscar por texto
        if not stock_element:
            product_text = product_element.get_text().lower()
            if 'en stock' in product_text and 'fuera de stock' not in product_text:
                in_stock = True
            elif 'fuera de stock' in product_text:
                in_stock = False
        
        # Construir datos del producto con campos optimizados
        product_data = {
            'product_id': product_id,
            'name': product_name,
            'url': product_url,
            'canonical_url': product_url,
            'current_price': current_price,
            'old_price': old_price,
            'in_stock': in_stock,
            'raw_current_price_text': f"{current_price}€" if current_price else None,
            'raw_old_price_text': f"{old_price}€" if old_price else None
        }
        
        # Calcular descuento solo si tenemos ambos precios
        if current_price is not None and old_price is not None:
            product_data['discount'] = calculate_discount_optimized(current_price, old_price)
        else:
            product_data['discount'] = None
        
        # Generar IDs optimizados
        product_data['product_id_hash'] = generate_product_id_optimized(product_data)
        product_data['offer_fingerprint'] = generate_offer_fingerprint_optimized(product_data)
        
        return product_data
        
    except Exception as e:
        logger.debug(f"Error parseando producto: {e}")
        return None

def find_prices_optimized(product_element, product_url: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Encuentra precios de forma optimizada - LÓGICA CORREGIDA
    
    Args:
        product_element: Elemento del producto
        product_url (str): URL del producto para debug
    
    Returns:
        Tuple[Optional[float], Optional[float]]: (precio_actual, precio_anterior)
    """
    current_price = None
    old_price = None
    
    # CORRECCIÓN: Usar la lógica exacta del parser original que funciona
    
    # Paso 1: Extraer texto completo del producto
    full_text = product_element.get_text()
    
    # Paso 2: Buscar precios con regex (como en el original)
    price_matches = re.findall(r'(\d{1,4}[.,]?\d{0,2})\s*€', full_text)
    
    if len(price_matches) >= 2:
        # Dos precios: actual + anterior
        current_price = parse_price_optimized(f"{price_matches[0]} €")
        old_price = parse_price_optimized(f"{price_matches[1]} €")
    elif len(price_matches) == 1:
        # Solo precio actual
        current_price = parse_price_optimized(f"{price_matches[0]} €")
    
    # Paso 3: Validar que los precios son razonables
    if current_price and (current_price < 1.0 or current_price > 10000):
        logger.warning(f"Precio actual sospechoso: {current_price}€ para {product_url}")
        current_price = None
    
    if old_price and (old_price < 1.0 or old_price > 10000):
        logger.warning(f"Precio anterior sospechoso: {old_price}€ para {product_url}")
        old_price = None
    
    # Paso 4: Si no encontramos precios, intentar método alternativo
    if not current_price:
        # Buscar elementos con clase específica
        price_elem = product_element.find(string=re.compile(r'€', re.IGNORECASE))
        if price_elem:
            # Extraer precios del contexto
            parent_text = price_elem.parent.get_text() if price_elem.parent else ""
            parent_matches = re.findall(r'(\d{1,4}[.,]?\d{0,2})\s*€', parent_text)
            if len(parent_matches) >= 1:
                current_price = parse_price_optimized(f"{parent_matches[0]} €")
                if len(parent_matches) >= 2:
                    old_price = parse_price_optimized(f"{parent_matches[1]} €")
    
    # Debug de precios encontrados
    if current_price or old_price:
        logger.debug(f"💰 Precios encontrados para {product_url}: actual={current_price}, anterior={old_price}")
    
    return current_price, old_price

def parse_page_optimized(soup, base_url="https://blackisard.com"):
    """
    Parsea una página de productos - VERSIÓN OPTIMIZADA
    
    Args:
        soup: BeautifulSoup object de la página
        base_url (str): URL base
    
    Returns:
        tuple: (productos, next_page_url)
    """
    products = []
    
    # Usar cache si es una página que ya vimos
    soup_html = str(soup)[:1000]  # Tomar primeros chars para cache key
    cached_products = find_products_in_page_cache(soup_html)
    
    if cached_products:
        products = cached_products
        logger.debug(f"📦 Usando cache: {len(products)} productos")
    else:
        # Fallback al método original si no hay cache
        products = parse_page_fallback(soup, base_url)
    
    # Buscar siguiente página
    next_page_url = None
    next_link = soup.find('link', rel='next')
    if next_link:
        next_page_url = urljoin(base_url, next_link.get('href', ''))
    
    return products, next_page_url

def parse_page_fallback(soup, base_url="https://blackisard.com"):
    """
    Fallback para parse_page si el cache no funciona
    """
    products = []
    
    # Método principal: article.product-miniature
    product_elements = soup.find_all('article', class_='product-miniature')
    
    for element in product_elements:
        product_data = parse_product_card_optimized(element, base_url)
        if product_data:
            products.append(product_data)
    
    return products

# Alias para compatibilidad
def parse_page(soup, base_url="https://blackisard.com"):
    """Alias para compatibilidad con scraper original"""
    return parse_page_optimized(soup, base_url)

def parse_price(price_text):
    """Alias para compatibilidad con scraper original"""
    return parse_price_optimized(price_text)

def calculate_discount(current_price, old_price):
    """Alias para compatibilidad con scraper original"""
    return calculate_discount_optimized(current_price, old_price)

def generate_product_id(product_data):
    """Alias para compatibilidad con scraper original"""
    return generate_product_id_optimized(product_data)

def generate_offer_fingerprint(product_data):
    """Alias para compatibilidad con scraper original"""
    return generate_offer_fingerprint_optimized(product_data)

# Funciones de compatibilidad que no se usan en la versión optimizada
def extract_from_json_ld(soup):
    """Función de compatibilidad - no implementada en versión optimizada"""
    return []

def parse_stock_status(element):
    """Función de compatibilidad"""
    return True

def extract_product_id_from_url(url):
    """Alias para compatibilidad"""
    return extract_product_id_optimized(url)