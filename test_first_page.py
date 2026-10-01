#!/usr/bin/env python3
"""
Test simple: Solo la primera página para verificar si encuentra productos
"""
import sys
sys.path.append('.')

from parser import parse_page
import requests
from bs4 import BeautifulSoup

def test_first_page():
    """Test solo la primera página"""
    url = "https://blackisard.com/escalada-en-roca"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"🔍 Obteniendo primera página...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"✅ Página obtenida: {response.status_code}")
        print(f"📏 Tamaño HTML: {len(response.content)} caracteres")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"\n🔍 Llamando a parse_page...")
        products, next_page = parse_page(soup)
        
        print(f"\n📊 RESULTADO:")
        print(f"   Productos encontrados: {len(products)}")
        print(f"   Siguiente página: {next_page}")
        
        if products:
            print(f"\n🎯 PRIMEROS 3 PRODUCTOS:")
            for i, product in enumerate(products[:3]):
                print(f"   [{i+1}] {product.get('name', 'Sin nombre')}")
                print(f"       💰 {product.get('current_price')}€")
                print(f"       🔗 {product.get('url', 'Sin URL')}")
        else:
            print(f"\n❌ NO SE ENCONTRARON PRODUCTOS")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_first_page()