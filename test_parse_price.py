#!/usr/bin/env python3
"""
Test directo para verificar parse_price
"""
import requests
from bs4 import BeautifulSoup
import re

def test_parse_price():
    """Test directo de parse_price"""
    url = "https://blackisard.com/escalada-en-roca"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print("🧪 TEST DIRECTO: Verificando parse_price")
        print("="*50)
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Tomar el primer producto
        product = soup.find('article', class_='product-miniature')
        
        if not product:
            print("❌ No se encontró producto")
            return
        
        print("✅ Producto encontrado")
        
        # Buscar elementos con €
        price_elements = product.find_all(string=re.compile(r'€'))
        print(f"💶 Elementos con '€' encontrados: {len(price_elements)}")
        
        for i, elem in enumerate(price_elements):
            price_text = elem.strip()
            print(f"   [{i}] Texto original: '{price_text}'")
            
            # Test parse_price manualmente
            parsed_price = parse_price_test(price_text)
            print(f"       Parsed price: {parsed_price}")
        
        # Test del texto completo del producto
        print(f"\n🔍 Texto completo del producto (primeros 200 chars):")
        product_text = product.get_text()[:200]
        print(f"   {product_text}...")
        
        # Buscar todos los precios en el texto
        all_prices = re.findall(r'(\d{1,4}[.,]?\d{0,2})\s*€', product_text)
        print(f"\n💰 Todos los precios en texto: {all_prices}")
        
        # Test parse_price con cada precio
        for i, price_str in enumerate(all_prices):
            full_price_text = f"{price_str} €"
            parsed = parse_price_test(full_price_text)
            print(f"   [{i}] '{price_str}' -> {parsed}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def parse_price_test(price_text):
    """Test de parse_price simplificado"""
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

if __name__ == "__main__":
    test_parse_price()