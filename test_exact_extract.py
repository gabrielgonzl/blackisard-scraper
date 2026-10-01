#!/usr/bin/env python3
"""
Test final: Replicar exactamente extract_prices_correctly
"""
import requests
from bs4 import BeautifulSoup
import re

def test_extract_prices_exact():
    """Test que replica exactamente extract_prices_correctly"""
    url = "https://blackisard.com/escalada-en-roca"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print("🔍 TEST FINAL: Replicando extract_prices_correctly")
        print("="*60)
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Tomar el primer producto
        product_element = soup.find('article', class_='product-miniature')
        product_url = "test_url"
        
        if not product_element:
            print("❌ No se encontró producto")
            return
        
        print("✅ Producto encontrado")
        
        # REPLICAR EXACTAMENTE extract_prices_correctly
        print(f"\n🔄 REPLICANDO LÓGICA:")
        
        current_price = None
        old_price = None
        
        # MÉTODO SIMPLIFICADO: Buscar todos los elementos con €
        price_elements = product_element.find_all(string=re.compile(r'€'))
        print(f"   💶 Elementos con '€' encontrados: {len(price_elements)}")
        
        if len(price_elements) >= 2:
            print(f"   ✅ 2+ elementos con € encontrados")
            
            # Extraer texto de ambos elementos
            current_price_text = price_elements[0].strip()
            old_price_text = price_elements[1].strip()
            
            print(f"   📝 Texto precio actual: '{current_price_text}'")
            print(f"   📝 Texto precio anterior: '{old_price_text}'")
            
            # Parsear precios
            current_price = parse_price_test(current_price_text)
            old_price = parse_price_test(old_price_text)
            
            print(f"   💰 Precio actual parsed: {current_price}")
            print(f"   💰 Precio anterior parsed: {old_price}")
        
        elif len(price_elements) == 1:
            print(f"   ⚠️ Solo 1 elemento con €")
            current_price = parse_price_test(price_elements[0].strip())
            print(f"   💰 Precio único parsed: {current_price}")
        
        # VALIDACIÓN
        print(f"\n🔍 VALIDACIÓN:")
        if current_price and (current_price < 0.5 or current_price > 5000):
            print(f"   ⚠️ Precio actual sospechoso: {current_price}€")
            current_price = None
        
        if old_price and (old_price < 0.5 or old_price > 5000):
            print(f"   ⚠️ Precio anterior sospechoso: {old_price}€")
            old_price = None
        
        # VALIDACIÓN ESPECÍFICA
        if current_price and old_price:
            calculated_discount = calculate_discount_test(current_price, old_price)
            print(f"   📊 Descuento calculado: {calculated_discount}%")
            
            if calculated_discount and (calculated_discount > 80 or calculated_discount < -20):
                print(f"   ⚠️ Descuento sospechoso: {calculated_discount}%")
                old_price = None
                print(f"   ✅ Corregido: solo precio actual {current_price}€")
        
        # RESULTADO FINAL
        print(f"\n🎯 RESULTADO FINAL:")
        print(f"   Precio actual: {current_price}€")
        print(f"   Precio anterior: {old_price}€")
        
        if current_price and old_price:
            discount = ((old_price - current_price) / old_price) * 100
            print(f"   Descuento final: {discount:.1f}%")
            
            # Verificar si es correcto
            if abs(current_price - 51.16) < 0.1 and abs(old_price - 77.0) < 0.1:
                print(f"   ✅ PRECIOS CORRECTOS!")
            else:
                print(f"   ❌ Precios incorrectos")
        elif current_price:
            print(f"   ✅ Solo precio actual: {current_price}€")
        else:
            print(f"   ❌ No se pudieron extraer precios")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def parse_price_test(price_text):
    """Test de parse_price exacto"""
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

def calculate_discount_test(current_price, old_price):
    """Test de calculate_discount exacto"""
    if old_price <= 0 or current_price >= old_price:
        return None
    
    discount = ((old_price - current_price) / old_price) * 100
    return round(discount, 1)

if __name__ == "__main__":
    test_extract_prices_exact()