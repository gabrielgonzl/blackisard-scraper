#!/usr/bin/env python3
"""
Debug específico para analizar precios y stock reales
"""
import requests
from bs4 import BeautifulSoup
import re

def debug_prices_and_stock():
    """Debug específico de precios y stock"""
    url = "https://blackisard.com/escalada-en-roca"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print("🔍 DEBUG: Analizando estructura real de precios y stock...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Buscar el primer producto
        product_elements = soup.find_all('article', class_='product-miniature')
        
        if not product_elements:
            print("❌ No se encontraron productos")
            return
        
        print(f"✅ Encontrados {len(product_elements)} productos")
        
        # Analizar los primeros 3 productos en detalle
        for i, product in enumerate(product_elements[:3]):
            print(f"\n{'='*60}")
            print(f"🔍 ANÁLISIS DETALLADO PRODUCTO {i+1}")
            print(f"{'='*60}")
            
            # Extraer nombre
            name_elem = product.find(class_='product-title')
            if name_elem:
                name = name_elem.get_text().strip()
                print(f"🏷️  Nombre: {name}")
            
            # Extraer URL
            link_elem = product.find('a', href=True)
            if link_elem:
                url = link_elem.get('href')
                print(f"🔗 URL: {url}")
            
            print(f"\n📋 Estructura HTML del producto:")
            print(product.prettify()[:1500])
            
            print(f"\n💰 ANÁLISIS DE PRECIOS:")
            
            # Método 1: Buscar todos los elementos con texto que contenga precios
            all_text = product.get_text()
            print(f"📄 Todo el texto del producto (primeros 500 chars):")
            print(f"   {all_text[:500]}...")
            
            # Buscar patrones de precio en el texto
            price_patterns = [
                r'(\d{1,4}[.,]?\d{0,2})\s*€',
                r'(\d{1,4}[.,]?\d{0,2})\s*euros?',
                r'(\d{1,4}[.,]?\d{0,2})\s*EUR',
                r'(\d{1,4}[.,]?\d{0,2})\s*eur'
            ]
            
            all_prices = []
            for pattern in price_patterns:
                matches = re.findall(pattern, all_text, re.IGNORECASE)
                all_prices.extend(matches)
            
            print(f"💰 Precios encontrados en texto: {all_prices}")
            
            # Método 2: Buscar elementos específicos de precio
            print(f"\n🔍 Buscando elementos de precio específicos...")
            
            # Buscar elementos con clases relacionadas con precio
            price_selectors = [
                '.product-price',
                '.current-price', 
                '.price',
                '.price-current',
                '.price-amount',
                '[class*="price"]',
                '[class*="cost"]',
                '[class*="amount"]'
            ]
            
            for selector in price_selectors:
                elements = product.select(selector)
                if elements:
                    print(f"   {selector}: {len(elements)} elementos")
                    for j, elem in enumerate(elements[:2]):
                        text = elem.get_text().strip()
                        if text:
                            print(f"      [{j}] {text}")
            
            # Método 3: Buscar elementos span/div que contengan €
            euro_elements = product.find_all(['span', 'div'], string=re.compile(r'€'))
            print(f"\n💶 Elementos con '€': {len(euro_elements)}")
            for j, elem in enumerate(euro_elements[:5]):
                context = elem.parent.get_text() if elem.parent else ""
                print(f"   [{j}] Elemento: {elem.get_text().strip()}")
                print(f"       Contexto: {context[:100]}...")
            
            # Método 4: Buscar elementos con descuento
            print(f"\n🏷️  ANÁLISIS DE STOCK:")
            
            # Buscar elementos de stock
            stock_selectors = [
                '.stock-label-lbl',
                '.stock-status',
                '[class*="stock"]',
                '[class*="availability"]'
            ]
            
            for selector in stock_selectors:
                elements = product.select(selector)
                if elements:
                    print(f"   {selector}: {len(elements)} elementos")
                    for j, elem in enumerate(elements[:2]):
                        text = elem.get_text().strip()
                        if text:
                            print(f"      [{j}] {text}")
            
            # Buscar texto de stock en general
            stock_keywords = ['stock', 'disponible', 'agotado', 'out of stock', 'in stock', 'disponibilidad']
            for keyword in stock_keywords:
                matches = product.find_all(string=re.compile(keyword, re.I))
                if matches:
                    print(f"   📦 '{keyword}' encontrado: {len(matches)} veces")
            
            # Método 5: Verificar si hay JSON-LD con precios
            print(f"\n📄 ANÁLISIS JSON-LD:")
            json_scripts = product.find_all('script', type='application/ld+json')
            if json_scripts:
                print(f"   📄 JSON-LD encontrado: {len(json_scripts)} scripts")
                for j, script in enumerate(json_scripts[:2]):
                    try:
                        import json
                        data = json.loads(script.string)
                        print(f"      [{j}] JSON data keys: {list(data.keys()) if isinstance(data, dict) else 'Lista'}")
                        if isinstance(data, dict) and 'offers' in data:
                            print(f"          Offers: {data['offers']}")
                    except:
                        print(f"      [{j}] Error parsing JSON")
            else:
                print(f"   📄 No se encontró JSON-LD")
            
            print(f"\n" + "="*60)
        
        # Análisis general del problema
        print(f"\n🎯 ANÁLISIS GENERAL:")
        print(f"📊 Total productos analizados: {len(product_elements)}")
        
        # Verificar si hay patrones comunes en errores de precio
        all_prices_collected = []
        for product in product_elements:
            text = product.get_text()
            euro_prices = re.findall(r'(\d{1,4}[.,]?\d{0,2})\s*€', text)
            all_prices_collected.extend(euro_prices)
        
        print(f"💰 Total precios únicos en la página: {len(set(all_prices_collected))}")
        print(f"💰 Precios únicos encontrados: {sorted(set(all_prices_collected))}")
        
        # Verificar si los precios parecen realistas
        if all_prices_collected:
            numeric_prices = []
            for price_str in all_prices_collected:
                try:
                    price = float(price_str.replace(',', '.'))
                    numeric_prices.append(price)
                except:
                    pass
            
            if numeric_prices:
                print(f"📈 Precios numéricos: min={min(numeric_prices):.2f}€, max={max(numeric_prices):.2f}€, promedio={sum(numeric_prices)/len(numeric_prices):.2f}€")
                
                # Detectar posibles precios erróneos
                suspiciously_low = [p for p in numeric_prices if p < 1.0]
                suspiciously_high = [p for p in numeric_prices if p > 10000]
                
                if suspiciously_low:
                    print(f"⚠️  Precios sospechosamente bajos: {suspiciously_low}")
                if suspiciously_high:
                    print(f"⚠️  Precios sospechosamente altos: {suspiciously_high}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_prices_and_stock()