#!/usr/bin/env python3
"""
Test específico para verificar la corrección de precios en la página principal
"""
import requests
from bs4 import BeautifulSoup
import re

def test_price_correction():
    """Test específico para el problema de precios en página principal"""
    url = "https://blackisard.com/escalada-en-roca"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print("🔍 TEST: Verificando corrección de precios en página principal")
        print("="*60)
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"📄 Página principal: {url}")
        
        # Buscar todos los productos
        products = soup.find_all('article', class_='product-miniature')
        print(f"✅ Encontrados {len(products)} productos")
        
        # Analizar los primeros 5 productos para ver el patrón
        for i, product in enumerate(products[:5]):
            print(f"\n{'='*50}")
            print(f"🔍 PRODUCTO {i+1}")
            print(f"{'='*50}")
            
            # Extraer nombre
            name_elem = product.find(class_='product-title')
            name = name_elem.get_text().strip() if name_elem else "Sin nombre"
            print(f"🏷️  Nombre: {name}")
            
            # Extraer URL para referencia
            link_elem = product.find('a', href=True)
            url_product = link_elem.get('href') if link_elem else "Sin URL"
            print(f"🔗 URL: {url_product}")
            
            # Aplicar la lógica corregida
            current_price, old_price = extract_prices_correctly_test(product, url_product)
            
            print(f"\n💰 PRECIOS EXTRAÍDOS:")
            print(f"   Precio actual: {current_price}€")
            print(f"   Precio anterior: {old_price}€")
            
            if current_price and old_price:
                discount = ((old_price - current_price) / old_price) * 100
                print(f"   Descuento calculado: {discount:.1f}%")
                
                # Verificar si hay descuento sospechoso
                if discount > 90:
                    print(f"   ⚠️  DESCUENTO SOSPECHOSO: {discount:.1f}%")
                else:
                    print(f"   ✅ Descuento razonable")
            
            # Mostrar el texto de precios para debugging
            product_text = product.get_text()
            price_sections = re.findall(r'([^€]*\d+[.,]?\d*\s*€[^€]*%[^€]*)', product_text)
            if price_sections:
                print(f"\n📋 Sección de precios:")
                for section in price_sections[:2]:  # Solo primeras 2
                    print(f"   {section.strip()[:100]}...")
            
            # Buscar elementos con precios
            price_elements = product.find_all(string=re.compile(r'€'))
            print(f"\n💶 Elementos con '€': {len(price_elements)}")
            for j, elem in enumerate(price_elements[:3]):
                print(f"   [{j}] {elem.strip()}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

def extract_prices_correctly_test(product_element, product_url: str):
    """
    Versión de test de extract_prices_correctly
    """
    current_price = None
    old_price = None
    
    # MÉTODO 1: Buscar elementos específicos de precio
    price_text = None
    
    # Buscar texto que contenga patrón: "precio_actual € precio_anterior € descuento%"
    price_section = product_element.find(string=re.compile(r'.*€.*€.*%'))
    if price_section:
        price_text = price_section.strip()
        print(f"   🔍 Sección con precios y descuento: {price_text}")
    else:
        # Fallback: buscar cualquier texto con precios
        price_elements = product_element.find_all(string=re.compile(r'€'))
        if price_elements:
            # Tomar el primer elemento que tenga precio
            for elem in price_elements:
                parent_text = elem.parent.get_text() if elem.parent else ""
                if '€' in parent_text and len(re.findall(r'€', parent_text)) >= 2:
                    price_text = parent_text
                    print(f"   🔍 Texto del padre con 2+ precios: {parent_text[:150]}...")
                    break
    
    if price_text:
        # Extraer precios del texto
        price_matches = re.findall(r'(\d{1,4}[.,]?\d{0,2})\s*€', price_text)
        print(f"   💰 Precios encontrados: {price_matches}")
        
        if len(price_matches) >= 2:
            # En Blackisard, el primer precio es el ACTUAL (con descuento)
            # y el segundo es el ANTERIOR (precio original)
            current_price = float(price_matches[0].replace(',', '.'))
            old_price = float(price_matches[1].replace(',', '.'))
            print(f"   ✅ Asignados: actual={current_price}€, anterior={old_price}€")
        elif len(price_matches) == 1:
            current_price = float(price_matches[0].replace(',', '.'))
            print(f"   ⚠️ Solo un precio: actual={current_price}€")
    
    # VALIDACIÓN: Verificar que los precios son razonables
    if current_price and (current_price < 0.5 or current_price > 10000):
        print(f"   ⚠️ Precio actual sospechoso: {current_price}€")
        current_price = None
    
    if old_price and (old_price < 0.5 or old_price > 10000):
        print(f"   ⚠️ Precio anterior sospechoso: {old_price}€")
        old_price = None
    
    # VALIDACIÓN ESPECÍFICA: Verificar descuento sospechoso
    if current_price and old_price:
        calculated_discount = ((old_price - current_price) / old_price) * 100
        if calculated_discount > 90:
            print(f"   ❌ DESCUENTO SOSPECHOSO: {calculated_discount:.1f}% - Probablemente precios mezclados")
            print(f"       Reintentando con solo primer precio...")
            # Tomar solo el primer precio y limpiar anterior
            old_price = None
            print(f"   ✅ Corregido: solo actual={current_price}€")
    
    return current_price, old_price

if __name__ == "__main__":
    test_price_correction()