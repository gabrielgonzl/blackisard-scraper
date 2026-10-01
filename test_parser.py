"""
Tests unitarios para el parser de Blackisard
"""
import pytest
import sys
import os

# Añadir el directorio actual al path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parser import parse_price, calculate_discount, generate_product_id, generate_offer_fingerprint, parse_stock_status

class TestPriceParser:
    """Tests para el parseador de precios"""
    
    def test_parse_european_prices_with_comma(self):
        """Test parseo de precios europeos con coma"""
        assert parse_price("59,90 €") == 59.90
        assert parse_price("1.299,95 €") == 1299.95
        assert parse_price("15,72 €") == 15.72
        assert parse_price("77,00 €") == 77.00
    
    def test_parse_european_prices_with_dot(self):
        """Test parseo de precios europeos con punto"""
        assert parse_price("59.90 €") == 59.90
        assert parse_price("1.299.95 €") == 1299.95
        assert parse_price("77.00 €") == 77.00
    
    def test_parse_prices_with_spaces(self):
        """Test parseo de precios con espacios no separables"""
        assert parse_price("59,90\xa0€") == 59.90  # Non-breaking space
        assert parse_price("1 299,95 €") == 1299.95
    
    def test_parse_prices_mixed_format(self):
        """Test parseo de precios en formatos mixtos"""
        assert parse_price("€59,90") == 59.90
        assert parse_price("Precio: 1.299,95€") == 1299.95
    
    def test_parse_invalid_prices(self):
        """Test parseo de precios inválidos"""
        assert parse_price("") is None
        assert parse_price("gratis") is None
        assert parse_price("N/A") is None
        assert parse_price("consultar precio") is None
    
    def test_parse_none_price(self):
        """Test parseo de precios None"""
        assert parse_price(None) is None

class TestDiscountCalculator:
    """Tests para el calculador de descuentos"""
    
    def test_calculate_standard_discount(self):
        """Test cálculo de descuento estándar"""
        assert calculate_discount(35.90, 59.90) == 40.07
        assert calculate_discount(50.00, 100.00) == 50.00
        assert calculate_discount(51.16, 77.00) == 33.56  # Actual result with rounding
    
    def test_calculate_no_discount(self):
        """Test cálculo cuando no hay descuento"""
        assert calculate_discount(59.90, 59.90) == 0.00
        assert calculate_discount(100.00, 100.00) == 0.00
    
    def test_calculate_discount_same_prices(self):
        """Test cálculo con precios iguales"""
        assert calculate_discount(50.00, 50.00) == 0.00
    
    def test_calculate_discount_invalid_prices(self):
        """Test cálculo con precios inválidos"""
        assert calculate_discount(None, 59.90) is None
        assert calculate_discount(35.90, None) is None
        assert calculate_discount(35.90, 0) is None
        assert calculate_discount(-10, 50) is None

class TestProductIDGenerator:
    """Tests para el generador de IDs de producto"""
    
    def test_generate_id_with_real_product_id(self):
        """Test generación de ID con product_id real"""
        product_data = {
            'product_id': '11085',
            'name': 'Producto Test',
            'url': 'https://example.com/product'
        }
        
        product_id = generate_product_id(product_data)
        assert product_id == 'id_11085'
    
    def test_generate_id_with_sku(self):
        """Test generación de ID con SKU"""
        product_data = {
            'sku': 'ABC123',
            'name': 'Producto Test',
            'url': 'https://example.com/product'
        }
        
        product_id = generate_product_id(product_data)
        assert product_id == 'sku_ABC123'
    
    def test_generate_id_with_url(self):
        """Test generación de ID con URL"""
        product_data = {
            'canonical_url': 'https://example.com/escalada-en-roca/producto-test.html',
            'name': 'Producto Test'
        }
        
        product_id = generate_product_id(product_data)
        assert product_id.startswith('url_')
        assert len(product_id) > 5  # url_ + hash
    
    def test_generate_id_fallback(self):
        """Test generación de ID con fallback a nombre"""
        product_data = {
            'name': 'Producto Test Único'
        }
        
        product_id = generate_product_id(product_data)
        assert product_id.startswith('name_')
        assert len(product_id) > 6  # name_ + hash
    
    def test_generate_id_empty_data(self):
        """Test generación de ID con datos vacíos"""
        product_data = {}
        
        product_id = generate_product_id(product_data)
        assert product_id.startswith('name_')

class TestOfferFingerprint:
    """Tests para la huella digital de ofertas"""
    
    def test_generate_fingerprint(self):
        """Test generación de fingerprint estándar"""
        product_data = {
            'current_price': 35.90,
            'old_price': 59.90
        }
        
        fingerprint = generate_offer_fingerprint(product_data)
        assert isinstance(fingerprint, str)
        assert len(fingerprint) == 16
        assert all(c in '0123456789abcdef' for c in fingerprint)  # hex
    
    def test_fingerprint_same_prices(self):
        """Test que precios iguales generan el mismo fingerprint"""
        product_data1 = {
            'current_price': 35.90,
            'old_price': 59.90
        }
        product_data2 = {
            'current_price': 35.90,
            'old_price': 59.90
        }
        
        fingerprint1 = generate_offer_fingerprint(product_data1)
        fingerprint2 = generate_offer_fingerprint(product_data2)
        
        assert fingerprint1 == fingerprint2
    
    def test_fingerprint_different_prices(self):
        """Test que precios diferentes generan fingerprints diferentes"""
        product_data1 = {
            'current_price': 35.90,
            'old_price': 59.90
        }
        product_data2 = {
            'current_price': 29.90,
            'old_price': 59.90
        }
        
        fingerprint1 = generate_offer_fingerprint(product_data1)
        fingerprint2 = generate_offer_fingerprint(product_data2)
        
        assert fingerprint1 != fingerprint2
    
    def test_fingerprint_missing_prices(self):
        """Test generación con precios faltantes"""
        product_data1 = {
            'current_price': None,
            'old_price': 59.90
        }
        product_data2 = {
            'current_price': 35.90,
            'old_price': None
        }
        
        assert generate_offer_fingerprint(product_data1) is None
        assert generate_offer_fingerprint(product_data2) is None

class TestStockStatus:
    """Tests para la detección de stock"""
    
    def test_in_stock_indicators(self):
        """Test detección de productos en stock"""
        from bs4 import BeautifulSoup
        
        # Producto en stock
        html_in_stock = '<div class="stock-label-lbl-in-stock">En stock</div>'
        soup = BeautifulSoup(html_in_stock, 'html.parser')
        
        assert parse_stock_status(soup) == True
    
    def test_unavailable_indicators(self):
        """Test detección de productos no disponibles"""
        from bs4 import BeautifulSoup
        
        # Producto agotado
        html_out_of_stock = '<div>Producto agotado</div>'
        soup = BeautifulSoup(html_out_of_stock, 'html.parser')
        
        assert parse_stock_status(soup) == False
        
        # Producto sin stock
        html_no_stock = '<div>Sin stock</div>'
        soup = BeautifulSoup(html_no_stock, 'html.parser')
        
        assert parse_stock_status(soup) == False
    
    def test_no_stock_indicators(self):
        """Test cuando no hay indicadores de stock"""
        from bs4 import BeautifulSoup
        
        # Sin indicadores de stock
        html_no_indicators = '<div>Producto genérico</div>'
        soup = BeautifulSoup(html_no_indicators, 'html.parser')
        
        # Por defecto, asumir disponible
        assert parse_stock_status(soup) == True

class TestIntegration:
    """Tests de integración"""
    
    def test_price_rounding(self):
        """Test redondeo de precios"""
        assert parse_price("59,99 €") == 59.99
        
        # El calculador de descuento debe redondear a 2 decimales
        discount = calculate_discount(35.99, 59.99)
        assert discount == 40.01  # Actual result with rounding
    
    def test_currency_symbols(self):
        """Test diferentes símbolos de moneda"""
        assert parse_price("59,90€") == 59.90
        assert parse_price("59,90 €") == 59.90
        assert parse_price("€59,90") == 59.90
        assert parse_price("59,90 $") == 59.90  # Símbolo diferente

if __name__ == "__main__":
    # Ejecutar tests si se llama directamente
    pytest.main([__file__, "-v"])