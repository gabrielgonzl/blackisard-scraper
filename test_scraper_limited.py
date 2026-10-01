#!/usr/bin/env python3
"""
Test del scraper completo pero solo 2 páginas
"""
import sys
sys.path.append('.')

from parser import parse_page
from scraper import BlackisardScraper
from config import DISCOUNT_THRESHOLD

def test_scraper_limited():
    """Test del scraper limitado a 2 páginas"""
    try:
        # Crear scraper en modo debug
        scraper = BlackisardScraper()
        
        # Ejecutar solo 2 páginas (bypass del bucle normal)
        print("🧪 Iniciando test limitado...")
        
        # Procesar solo la primera página
        base_url = "https://blackisard.com/escalada-en-roca"
        soup = scraper.fetch_page(base_url)
        
        if soup:
            print(f"✅ Página obtenida exitosamente")
            products, next_page = parse_page(soup)
            print(f"📊 RESULTADOS:")
            print(f"   Productos encontrados: {len(products)}")
            print(f"   Siguiente página: {next_page}")
            
            # Filtrar ofertas con descuento >= 40%
            offers = [p for p in products if p.get('discount', 0) >= DISCOUNT_THRESHOLD]
            print(f"   Ofertas >= {DISCOUNT_THRESHOLD}%: {len(offers)}")
            
            if offers:
                print(f"\n🎯 OFERTAS ENCONTRADAS:")
                for i, offer in enumerate(offers[:5]):
                    print(f"   [{i+1}] {offer.get('name', 'Sin nombre')[:40]}...")
                    print(f"       💰 {offer.get('current_price')}€ (antes: {offer.get('old_price')}€)")
                    print(f"       📉 Descuento: {offer.get('discount', 0):.1f}%")
                    print(f"       🔗 {offer.get('url', 'Sin URL')}")
                    print()
            else:
                print(f"\n❌ No hay ofertas con descuento >= {DISCOUNT_THRESHOLD}%")
                print(f"🔍 Mostrando todos los productos con descuento:")
                for i, product in enumerate(products[:5]):
                    discount = product.get('discount', 0)
                    print(f"   [{i+1}] {product.get('name', 'Sin nombre')[:40]}... - {discount:.1f}% desc.")
        else:
            print(f"❌ No se pudo obtener la página")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scraper_limited()