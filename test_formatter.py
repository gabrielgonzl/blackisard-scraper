"""
Tests para el MarkdownFormatter
"""
import pytest
import tempfile
import os
from datetime import datetime

# Importar módulos a testear
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from formatter import MarkdownFormatter

class TestMarkdownFormatter:
    """Tests para MarkdownFormatter"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.md')
        self.temp_file.close()
        self.output_file = self.temp_file.name
        self.formatter = MarkdownFormatter(self.output_file)
    
    def teardown_method(self):
        """Cleanup después de cada test"""
        if os.path.exists(self.output_file):
            os.unlink(self.output_file)
    
    def test_format_price(self):
        """Test formateo de precios"""
        assert self.formatter.format_price(59.90) == "59.90 €"
        assert self.formatter.format_price(1299.95) == "1299.95 €"
        assert self.formatter.format_price(35.72) == "35.72 €"
        assert self.formatter.format_price(None) == "N/A"
        assert self.formatter.format_price(0) == "0.00 €"
    
    def test_format_discount(self):
        """Test formateo de descuentos"""
        assert self.formatter.format_discount(40.07) == "-40.07%"
        assert self.formatter.format_discount(50.00) == "-50.00%"
        assert self.formatter.format_discount(33.55) == "-33.55%"
        assert self.formatter.format_discount(None) == "N/A"
        assert self.formatter.format_discount(0) == "-0.00%"
    
    def test_generate_offer_block(self):
        """Test generación de bloques de ofertas"""
        product_name = "Producto Test"
        product_url = "https://example.com/product"
        offer = {
            'current_price': 35.90,
            'old_price': 59.90,
            'discount': 40.07,
            'first_seen': '2026-10-01'
        }
        date = '2026-10-01'
        
        block = self.formatter.generate_offer_block(product_name, product_url, offer, date)
        
        # Verificar que contiene los elementos esperados
        assert "### Producto Test" in block
        assert "**35.90 €**" in block
        assert "~~59.90 €~~" in block
        assert "**-40.07%**" in block
        assert "✅ En stock" in block
        assert "Primera vista: 2026-10-01" in block
        assert "[Ver producto](https://example.com/product)" in block
    
    def test_append_offers_new_file(self):
        """Test añadir ofertas a archivo nuevo"""
        # Eliminar archivo temporal si existe
        if os.path.exists(self.output_file):
            os.unlink(self.output_file)
        
        new_offers = [
            {
                'name': 'Producto X',
                'url': 'https://example.com/product-x',
                'current_price': 35.90,
                'old_price': 59.90,
                'discount': 40.07,
                'first_seen': '2026-10-01'
            },
            {
                'name': 'Producto Y',
                'url': 'https://example.com/product-y',
                'current_price': 42.90,
                'old_price': 79.90,
                'discount': 46.31,
                'first_seen': '2026-10-01'
            }
        ]
        
        # Añadir ofertas
        result = self.formatter.append_offers(new_offers)
        assert result == True
        
        # Verificar que se creó el archivo
        assert os.path.exists(self.output_file)
        
        # Verificar contenido
        with open(self.output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar cabecera
        assert "# Ofertas Blackisard" in content
        
        # Verificar fecha
        current_date = datetime.now().strftime('%Y-%m-%d')
        assert f"## {current_date}" in content
        
        # Verificar productos
        assert "Producto X" in content
        assert "Producto Y" in content
        assert "35.90 €" in content
        assert "42.90 €" in content
    
    def test_append_offers_existing_file(self):
        """Test añadir ofertas a archivo existente"""
        # Crear archivo existente
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write("# Ofertas Blackisard\n\n")
            f.write("## 2026-09-30\n\n")
            f.write("### Producto Antiguo\n")
            f.write("- Precio: **25.00 €**\n")
        
        new_offers = [
            {
                'name': 'Producto Nuevo',
                'url': 'https://example.com/product-new',
                'current_price': 35.90,
                'old_price': 59.90,
                'discount': 40.07,
                'first_seen': '2026-10-01'
            }
        ]
        
        # Añadir ofertas
        result = self.formatter.append_offers(new_offers)
        assert result == True
        
        # Verificar contenido
        with open(self.output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Debe mantener el contenido existente
        assert "Producto Antiguo" in content
        assert "25.00 €" in content
        
        # Y añadir el nuevo
        assert "Producto Nuevo" in content
        assert "35.90 €" in content
    
    def test_append_empty_offers(self):
        """Test añadir ofertas vacías"""
        result = self.formatter.append_offers([])
        assert result == True
        
        # No debe crear archivo si no hay ofertas (verificar que sigue sin existir)
        # El archivo temporal puede existir ya, pero el método no debe escribir
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r', encoding='utf-8') as f:
                content = f.read()
            # Si el archivo existe, debe estar vacío o tener solo contenido previo
            assert 'Producto' not in content
    
    def test_create_report(self):
        """Test creación de reporte completo"""
        new_offers = [
            {
                'name': 'Producto X',
                'url': 'https://example.com/product-x',
                'current_price': 35.90,
                'old_price': 59.90,
                'discount': 40.07,
                'first_seen': '2026-10-01'
            }
        ]
        
        scan_info = {
            'products': [{'name': 'Producto X', 'url': 'https://example.com/product-x'}],
            'total_pages': 5,
            'total_products': 100,
            'in_stock': 85,
            'valid_offers': 10,
            'state_manager': None
        }
        
        # Crear reporte
        result = self.formatter.create_report(new_offers, scan_info)
        assert result == True
        
        # Verificar que se creó el archivo
        assert os.path.exists(self.output_file)
        
        # Verificar contenido
        with open(self.output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar secciones
        assert "# Ofertas Blackisard" in content
        assert "## Resumen de ejecución" in content
        assert "5" in content  # páginas
        assert "100" in content  # productos
        assert "85" in content  # en stock
        assert "10" in content  # ofertas válidas
        assert "Producto X" in content
        assert "## Historial de ofertas" in content
    
    def test_create_report_no_new_offers(self):
        """Test creación de reporte sin nuevas ofertas"""
        scan_info = {
            'products': [],
            'total_pages': 5,
            'total_products': 100,
            'in_stock': 85,
            'valid_offers': 10,
            'state_manager': None
        }
        
        # Crear reporte
        result = self.formatter.create_report([], scan_info)
        assert result == True
        
        # Verificar contenido
        with open(self.output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "No se encontraron nuevas ofertas" in content
    
    def test_create_report_with_state_manager(self):
        """Test creación de reporte con StateManager"""
        from state import StateManager
        
        # Crear StateManager de prueba
        state_manager = StateManager()
        state_manager.state['products'] = {
            'test_product_1': {
                'name': 'Producto Histórico',
                'url': 'https://example.com/product',
                'offers': [
                    {
                        'fingerprint': 'fingerprint_1',
                        'current_price': 35.90,
                        'old_price': 59.90,
                        'discount': 40.07,
                        'first_seen': '2026-09-30',
                        'source_url': 'https://example.com/product'
                    },
                    {
                        'fingerprint': 'fingerprint_2',
                        'current_price': 29.90,
                        'old_price': 59.90,
                        'discount': 50.08,
                        'first_seen': '2026-10-01',
                        'source_url': 'https://example.com/product'
                    }
                ]
            }
        }
        
        scan_info = {
            'products': [],
            'total_pages': 1,
            'total_products': 10,
            'in_stock': 8,
            'valid_offers': 2,
            'state_manager': state_manager
        }
        
        # Crear reporte
        result = self.formatter.create_report([], scan_info)
        assert result == True
        
        # Verificar contenido
        with open(self.output_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "Producto Histórico" in content
        assert "**35.90 €**" in content
        assert "**29.90 €**" in content
        assert "-40.07%" in content
        assert "-50.08%" in content
        assert "2026-09-30" in content
        assert "2026-10-01" in content

if __name__ == "__main__":
    # Ejecutar tests si se llama directamente
    pytest.main([__file__, "-v"])