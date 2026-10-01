"""
Tests de integración para el scraper principal
"""
import pytest
import tempfile
import os
import json
from unittest.mock import Mock, patch, MagicMock

# Importar módulos a testear
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper import BlackisardScraper
from config import DISCOUNT_THRESHOLD

class TestBlackisardScraper:
    """Tests de integración para BlackisardScraper"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.temp_dir = tempfile.mkdtemp()
        self.state_file = os.path.join(self.temp_dir, "test_state.json")
        self.output_file = os.path.join(self.temp_dir, "test_ofertas.md")
        
        # Parchear archivos de configuración
        self.original_state_file = "state.json"
        self.original_output_file = "ofertas.md"
        
        import config
        config.STATE_FILE = self.state_file
        config.OUTPUT_FILE = self.output_file
        
        # Crear scraper
        self.scraper = BlackisardScraper()
    
    def teardown_method(self):
        """Cleanup después de cada test"""
        # Restaurar configuración original
        import config
        config.STATE_FILE = self.original_state_file
        config.OUTPUT_FILE = self.original_output_file
        
        # Limpiar archivos temporales
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test inicialización del scraper"""
        assert self.scraper.session is not None
        assert self.scraper.state_manager is not None
        assert self.scraper.formatter is not None
        
        # Verificar headers de sesión
        headers = self.scraper.session.headers
        assert 'User-Agent' in headers
        assert 'Blackisard-Scraper' in headers['User-Agent']
        
        # Verificar estadísticas
        stats = self.scraper.stats
        assert all(key in stats for key in [
            'total_pages', 'total_products', 'in_stock', 
            'valid_offers', 'new_offers', 'errors'
        ])
    
    @patch('requests.Session.get')
    def test_fetch_page_success(self, mock_get):
        """Test obtener página exitosamente"""
        # Mock de respuesta exitosa
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.encoding = 'utf-8'
        mock_response.content = b'<html><body>Test</body></html>'
        mock_get.return_value = mock_response
        
        result = self.scraper.fetch_page("https://example.com/test")
        
        assert result is not None
        assert result.find('body') is not None
        assert result.find('body').get_text() == 'Test'
        
        # Verificar que se llamó con los parámetros correctos
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == "https://example.com/test"
        assert 'timeout' in kwargs
        assert kwargs['timeout'] == 30
    
    @patch('requests.Session.get')
    def test_fetch_page_404_error(self, mock_get):
        """Test manejar error 404"""
        # Mock de respuesta 404
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("404 Client Error")
        mock_response.content = b'<html><head><title>404 - Page not found</title></head></html>'
        mock_get.return_value = mock_response
        
        result = self.scraper.fetch_page("https://example.com/404")
        
        assert result is None
    
    @patch('requests.Session.get')
    def test_fetch_page_retry_on_error(self, mock_get):
        """Test reintentos en caso de error"""
        # Mock de primera respuesta fallida
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("Connection timeout")
        mock_get.return_value = mock_response
        
        result = self.scraper.fetch_page("https://example.com/slow")
        
        assert result is None
        # Debería haber intentado varias veces
        assert mock_get.call_count >= 2
    
    def test_is_valid_offer(self):
        """Test validación de ofertas"""
        # Oferta válida
        valid_offer = {
            'current_price': 35.90,
            'old_price': 59.90,
            'discount': 40.07,
            'in_stock': True
        }
        assert self.scraper.is_valid_offer(valid_offer) == True
        
        # Oferta sin precios
        no_prices = {
            'current_price': None,
            'old_price': 59.90,
            'discount': 40.07,
            'in_stock': True
        }
        assert self.scraper.is_valid_offer(no_prices) == False
        
        # Oferta sin stock
        no_stock = {
            'current_price': 35.90,
            'old_price': 59.90,
            'discount': 40.07,
            'in_stock': False
        }
        assert self.scraper.is_valid_offer(no_stock) == False
        
        # Oferta con descuento insuficiente
        low_discount = {
            'current_price': 70.00,
            'old_price': 100.00,
            'discount': 30.00,
            'in_stock': True
        }
        assert self.scraper.is_valid_offer(low_discount) == False
    
    def test_is_valid_offer_custom_threshold(self):
        """Test validación con umbral personalizado"""
        # Oferta con 35% descuento (no válida con 40%, sí con 30%)
        offer_35_percent = {
            'current_price': 65.00,
            'old_price': 100.00,
            'discount': 35.00,
            'in_stock': True
        }
        
        # Con umbral por defecto (40%)
        assert self.scraper.is_valid_offer(offer_35_percent) == False
        
        # Cambiar umbral a 30%
        import config
        original_threshold = config.DISCOUNT_THRESHOLD
        config.DISCOUNT_THRESHOLD = 30.0
        
        try:
            assert self.scraper.is_valid_offer(offer_35_percent) == True
        finally:
            config.DISCOUNT_THRESHOLD = original_threshold
    
    @patch.object(BlackisardScraper, 'fetch_page')
    @patch.object(BlackisardScraper, 'discover_pages')
    def test_scrape_category(self, mock_discover, mock_fetch):
        """Test escaneo completo de categoría"""
        from bs4 import BeautifulSoup
        
        # Mock de páginas
        mock_discover.return_value = ["https://example.com/page1", "https://example.com/page2"]
        
        # Mock de contenido de página
        page_html = '''
        <html>
        <body>
            <div class="js-product-miniature">
                <a href="/producto-1"></a>
                <h3 class="product-title">Producto 1</h3>
                <span class="product-price">35,90 €</span>
                <span class="regular-price">59,90 €</span>
                <div class="stock-label-lbl-in-stock">En stock</div>
            </div>
        </body>
        </html>
        '''
        
        soup = BeautifulSoup(page_html, 'html.parser')
        mock_fetch.return_value = soup
        
        # Escanear categoría
        result = self.scraper.scrape_category("https://example.com/category")
        
        # Verificar resultados
        assert len(result) == 1
        product = result[0]
        assert product['name'] == 'Producto 1'
        assert product['current_price'] == 35.90
        assert product['old_price'] == 59.90
        assert product['discount'] == 40.07
        assert product['in_stock'] == True
        
        # Verificar estadísticas
        assert self.scraper.stats['total_pages'] == 2
        assert self.scraper.stats['total_products'] == 1
        assert self.scraper.stats['in_stock'] == 1
        assert self.scraper.stats['valid_offers'] == 1
    
    @patch.object(BlackisardScraper, 'fetch_page')
    @patch.object(BlackisardScraper, 'discover_pages')
    def test_detect_new_offers(self, mock_discover, mock_fetch):
        """Test detección de ofertas nuevas"""
        from bs4 import BeautifulSoup
        
        # Mock de página
        mock_discover.return_value = ["https://example.com/page1"]
        page_html = '''
        <html>
        <body>
            <div class="js-product-miniature">
                <a href="/producto-1"></a>
                <h3 class="product-title">Producto 1</h3>
                <span class="product-price">35,90 €</span>
                <span class="regular-price">59,90 €</span>
                <div class="stock-label-lbl-in-stock">En stock</div>
            </div>
        </body>
        </html>
        '''
        
        soup = BeautifulSoup(page_html, 'html.parser')
        mock_fetch.return_value = soup
        
        # Escanear categoría
        all_products = self.scraper.scrape_category("https://example.com/category")
        
        # Detectar ofertas nuevas
        new_offers = self.scraper.detect_new_offers(all_products)
        
        # Primera ejecución: todas las ofertas son nuevas
        assert len(new_offers) == 1
        assert new_offers[0]['name'] == 'Producto 1'
        assert self.scraper.stats['new_offers'] == 1
        
        # Segunda ejecución: no hay ofertas nuevas
        new_offers_2 = self.scraper.detect_new_offers(all_products)
        assert len(new_offers_2) == 0
        assert self.scraper.stats['new_offers'] == 0  # No se incrementa
    
    @patch('scraper.BlackisardScraper.scrape_category')
    @patch('scraper.BlackisardScraper.detect_new_offers')
    @patch('scraper.BlackisardScraper.print_summary')
    def test_run_success(self, mock_print, mock_detect, mock_scrape):
        """Test ejecución exitosa completa"""
        # Mock de datos de prueba
        mock_scrape.return_value = [
            {
                'name': 'Producto Test',
                'current_price': 35.90,
                'old_price': 59.90,
                'discount': 40.07,
                'product_id_hash': 'test_1',
                'offer_fingerprint': 'fp_1'
            }
        ]
        
        mock_detect.return_value = [
            {
                'name': 'Producto Test',
                'current_price': 35.90,
                'old_price': 59.90,
                'discount': 40.07
            }
        ]
        
        # Ejecutar scraper
        result = self.scraper.run()
        
        # Verificar resultado
        assert result['success'] == True
        assert result['new_offers'] == 1
        assert 'duration' in result
        
        # Verificar que se llamó a los métodos
        mock_scrape.assert_called_once()
        mock_detect.assert_called_once()
        
        # Verificar que se guardó el estado
        assert os.path.exists(self.state_file)
    
    @patch('scraper.BlackisardScraper.scrape_category')
    def test_run_keyboard_interrupt(self, mock_scrape):
        """Test manejo de interrupción por teclado"""
        mock_scrape.side_effect = KeyboardInterrupt()
        
        result = self.scraper.run()
        
        assert result['success'] == False
        assert result['error'] == 'Interrumpido por el usuario'
    
    @patch('scraper.BlackisardScraper.scrape_category')
    def test_run_exception(self, mock_scrape):
        """Test manejo de excepciones"""
        mock_scrape.side_effect = Exception("Error de prueba")
        
        result = self.scraper.run()
        
        assert result['success'] == False
        assert 'Error de prueba' in result['error']
    
    def test_print_summary(self):
        """Test impresión de resumen"""
        # Configurar estadísticas de prueba
        self.scraper.stats = {
            'total_products': 100,
            'in_stock': 80,
            'valid_offers': 5,
            'new_offers': 2,
            'errors': 0
        }
        
        new_offers = [
            {
                'name': 'Producto A',
                'current_price': 35.90,
                'discount': 40.07
            },
            {
                'name': 'Producto B',
                'current_price': 42.90,
                'discount': 45.31
            }
        ]
        
        # Ejecutar print_summary (verificar que no falla)
        try:
            self.scraper.print_summary(new_offers)
        except Exception as e:
            pytest.fail(f"print_summary falló: {e}")
    
    def test_discover_pages(self):
        """Test descubrimiento de páginas"""
        from bs4 import BeautifulSoup
        
        # Mock de página 1 con enlace a página 2
        page1_html = '''
        <html>
        <head>
            <link rel="next" href="?page=2">
        </head>
        </html>
        '''
        
        # Mock de página 2 sin enlace a siguiente página
        page2_html = '''
        <html>
        <head>
            <link rel="prev" href="?page=1">
        </head>
        </html>
        '''
        
        # Configurar respuestas de fetch_page
        soup1 = BeautifulSoup(page1_html, 'html.parser')
        soup2 = BeautifulSoup(page2_html, 'html.parser')
        
        call_count = 0
        def fetch_side_effect(url):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return soup1
            elif call_count == 2:
                return soup2
            return None
        
        with patch.object(self.scraper, 'fetch_page', side_effect=fetch_side_effect):
            pages = self.scraper.discover_pages("https://example.com/category")
        
        # Verificar páginas descubiertas
        assert len(pages) == 2
        assert "https://example.com/category" in pages[0]
        assert "page=2" in pages[1]
    
    @patch('scraper.BlackisardScraper.fetch_page')
    def test_discover_pages_error_handling(self, mock_fetch):
        """Test manejo de errores en descubrimiento de páginas"""
        # Mock de fetch_page que falla
        mock_fetch.return_value = None
        
        pages = self.scraper.discover_pages("https://example.com/category")
        
        # Debe devolver solo la URL inicial
        assert len(pages) == 1
        assert pages[0] == "https://example.com/category"

if __name__ == "__main__":
    # Ejecutar tests si se llama directamente
    pytest.main([__file__, "-v"])