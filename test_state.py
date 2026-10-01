"""
Tests para el StateManager
"""
import pytest
import tempfile
import os
import json
from datetime import datetime

# Importar módulos a testear
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from state import StateManager

class TestStateManager:
    """Tests para StateManager"""
    
    def setup_method(self):
        """Setup para cada test"""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json')
        self.temp_file.close()
        self.state_file = self.temp_file.name
        self.state_manager = StateManager(self.state_file)
    
    def teardown_method(self):
        """Cleanup después de cada test"""
        if os.path.exists(self.state_file):
            os.unlink(self.state_file)
        # Limpiar también archivo temporal si existe
        temp_file = self.state_file + '.tmp'
        if os.path.exists(temp_file):
            os.unlink(temp_file)
    
    def test_initial_state(self):
        """Test estado inicial"""
        assert 'products' in self.state_manager.state
        assert len(self.state_manager.state['products']) == 0
        assert 'version' in self.state_manager.state
        assert 'created_at' in self.state_manager.state
        assert 'last_updated' in self.state_manager.state
    
    def test_load_existing_state(self):
        """Test cargar estado existente"""
        # Crear estado de prueba
        test_state = {
            'version': '1.0',
            'created_at': '2026-01-01T00:00:00',
            'last_updated': '2026-01-01T00:00:00',
            'products': {
                'test_product_1': {
                    'name': 'Producto Test',
                    'url': 'https://example.com/product',
                    'offers': []
                }
            }
        }
        
        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(test_state, f)
        
        # Crear nueva instancia
        new_manager = StateManager(self.state_file)
        
        assert len(new_manager.state['products']) == 1
        assert 'test_product_1' in new_manager.state['products']
        assert new_manager.state['products']['test_product_1']['name'] == 'Producto Test'
    
    def test_add_offer_new_product(self):
        """Test añadir oferta a producto nuevo"""
        product_data = {
            'product_id_hash': 'test_product_1',
            'name': 'Producto Test',
            'url': 'https://example.com/product',
            'canonical_url': 'https://example.com/product',
            'current_price': 35.90,
            'old_price': 59.90,
            'discount': 40.07,
            'offer_fingerprint': 'test_fingerprint_1'
        }
        
        # Primera oferta
        added = self.state_manager.add_offer(product_data, '2026-10-01')
        
        assert added == True
        assert len(self.state_manager.state['products']) == 1
        assert 'test_product_1' in self.state_manager.state['products']
        assert len(self.state_manager.state['products']['test_product_1']['offers']) == 1
        
        offer = self.state_manager.state['products']['test_product_1']['offers'][0]
        assert offer['fingerprint'] == 'test_fingerprint_1'
        assert offer['current_price'] == 35.90
        assert offer['old_price'] == 59.90
        assert offer['discount'] == 40.07
        assert offer['first_seen'] == '2026-10-01'
    
    def test_add_duplicate_offer(self):
        """Test no añadir oferta duplicada"""
        product_data = {
            'product_id_hash': 'test_product_1',
            'name': 'Producto Test',
            'url': 'https://example.com/product',
            'canonical_url': 'https://example.com/product',
            'current_price': 35.90,
            'old_price': 59.90,
            'discount': 40.07,
            'offer_fingerprint': 'test_fingerprint_1'
        }
        
        # Primera oferta
        added1 = self.state_manager.add_offer(product_data, '2026-10-01')
        assert added1 == True
        
        # Segunda oferta igual
        added2 = self.state_manager.add_offer(product_data, '2026-10-02')
        assert added2 == False
        
        # Solo debe haber una oferta
        assert len(self.state_manager.state['products']['test_product_1']['offers']) == 1
    
    def test_add_different_offer_same_product(self):
        """Test añadir oferta diferente del mismo producto"""
        product_data1 = {
            'product_id_hash': 'test_product_1',
            'name': 'Producto Test',
            'url': 'https://example.com/product',
            'canonical_url': 'https://example.com/product',
            'current_price': 35.90,
            'old_price': 59.90,
            'discount': 40.07,
            'offer_fingerprint': 'fingerprint_1'
        }
        
        product_data2 = {
            'product_id_hash': 'test_product_1',
            'name': 'Producto Test',
            'url': 'https://example.com/product',
            'canonical_url': 'https://example.com/product',
            'current_price': 29.90,
            'old_price': 59.90,
            'discount': 50.08,
            'offer_fingerprint': 'fingerprint_2'
        }
        
        # Primera oferta
        added1 = self.state_manager.add_offer(product_data1, '2026-10-01')
        assert added1 == True
        
        # Segunda oferta diferente
        added2 = self.state_manager.add_offer(product_data2, '2026-10-02')
        assert added2 == True
        
        # Debe haber dos ofertas
        assert len(self.state_manager.state['products']['test_product_1']['offers']) == 2
    
    def test_offer_exists(self):
        """Test verificación de existencia de ofertas"""
        product_data = {
            'product_id_hash': 'test_product_1',
            'name': 'Producto Test',
            'url': 'https://example.com/product',
            'canonical_url': 'https://example.com/product',
            'current_price': 35.90,
            'old_price': 59.90,
            'discount': 40.07,
            'offer_fingerprint': 'test_fingerprint_1'
        }
        
        # Verificar que no existe antes de añadir
        exists = self.state_manager.offer_exists('test_product_1', 'test_fingerprint_1')
        assert exists == False
        
        # Añadir oferta
        self.state_manager.add_offer(product_data)
        
        # Verificar que ahora existe
        exists = self.state_manager.offer_exists('test_product_1', 'test_fingerprint_1')
        assert exists == True
        
        # Verificar fingerprint inexistente
        exists = self.state_manager.offer_exists('test_product_1', 'nonexistent')
        assert exists == False
        
        # Verificar producto inexistente
        exists = self.state_manager.offer_exists('nonexistent_product', 'test_fingerprint_1')
        assert exists == False
    
    def test_get_known_offers(self):
        """Test obtener ofertas conocidas"""
        product_data1 = {
            'product_id_hash': 'test_product_1',
            'name': 'Producto Test',
            'url': 'https://example.com/product',
            'canonical_url': 'https://example.com/product',
            'current_price': 35.90,
            'old_price': 59.90,
            'discount': 40.07,
            'offer_fingerprint': 'fingerprint_1'
        }
        
        product_data2 = {
            'product_id_hash': 'test_product_1',
            'name': 'Producto Test',
            'url': 'https://example.com/product',
            'canonical_url': 'https://example.com/product',
            'current_price': 29.90,
            'old_price': 59.90,
            'discount': 50.08,
            'offer_fingerprint': 'fingerprint_2'
        }
        
        # Añadir ofertas
        self.state_manager.add_offer(product_data1, '2026-10-01')
        self.state_manager.add_offer(product_data2, '2026-10-02')
        
        # Obtener ofertas
        offers = self.state_manager.get_known_offers('test_product_1')
        
        assert len(offers) == 2
        assert offers[0]['fingerprint'] == 'fingerprint_1'
        assert offers[0]['first_seen'] == '2026-10-01'
        assert offers[1]['fingerprint'] == 'fingerprint_2'
        assert offers[1]['first_seen'] == '2026-10-02'
        
        # Producto inexistente
        offers = self.state_manager.get_known_offers('nonexistent')
        assert len(offers) == 0
    
    def test_update_product(self):
        """Test actualizar información de producto"""
        # Añadir producto inicial
        self.state_manager.state['products']['test_product_1'] = {
            'name': 'Producto Original',
            'url': 'https://example.com/old',
            'offers': []
        }
        
        # Datos actualizados
        updated_data = {
            'name': 'Producto Actualizado',
            'canonical_url': 'https://example.com/new',
            'sku': 'SKU123'
        }
        
        # Actualizar
        updated = self.state_manager.update_product('test_product_1', updated_data)
        assert updated == True
        
        # Verificar cambios
        product = self.state_manager.state['products']['test_product_1']
        assert product['name'] == 'Producto Actualizado'
        assert product['url'] == 'https://example.com/new'
        assert product['sku'] == 'SKU123'
        
        # Producto inexistente
        updated = self.state_manager.update_product('nonexistent', updated_data)
        assert updated == False
    
    def test_get_statistics(self):
        """Test obtener estadísticas"""
        # Añadir productos y ofertas
        product_data1 = {
            'product_id_hash': 'test_product_1',
            'name': 'Producto Test 1',
            'url': 'https://example.com/product1',
            'canonical_url': 'https://example.com/product1',
            'current_price': 35.90,
            'old_price': 59.90,
            'discount': 40.07,
            'offer_fingerprint': 'fingerprint_1'
        }
        
        product_data2 = {
            'product_id_hash': 'test_product_2',
            'name': 'Producto Test 2',
            'url': 'https://example.com/product2',
            'canonical_url': 'https://example.com/product2',
            'current_price': 50.00,
            'old_price': 100.00,
            'discount': 50.00,
            'offer_fingerprint': 'fingerprint_2'
        }
        
        self.state_manager.add_offer(product_data1)
        self.state_manager.add_offer(product_data2)
        
        # Obtener estadísticas
        stats = self.state_manager.get_statistics()
        
        assert stats['total_products'] == 2
        assert stats['total_offers'] == 2
        assert abs(stats['average_discount'] - 45.035) < 0.01  # Allow small rounding differences
        assert stats['version'] == '1.0'
        assert 'last_updated' in stats
    
    def test_save_state(self):
        """Test guardar estado"""
        # Añadir datos
        product_data = {
            'product_id_hash': 'test_product_1',
            'name': 'Producto Test',
            'url': 'https://example.com/product',
            'canonical_url': 'https://example.com/product',
            'current_price': 35.90,
            'old_price': 59.90,
            'discount': 40.07,
            'offer_fingerprint': 'test_fingerprint_1'
        }
        
        self.state_manager.add_offer(product_data)
        
        # Guardar
        saved = self.state_manager.save()
        assert saved == True
        
        # Verificar que se guardó en disco
        with open(self.state_file, 'r', encoding='utf-8') as f:
            saved_state = json.load(f)
        
        assert 'products' in saved_state
        assert 'test_product_1' in saved_state['products']
    
    def test_clear_state(self):
        """Test limpiar estado"""
        # Añadir datos
        product_data = {
            'product_id_hash': 'test_product_1',
            'name': 'Producto Test',
            'url': 'https://example.com/product',
            'canonical_url': 'https://example.com/product',
            'current_price': 35.90,
            'old_price': 59.90,
            'discount': 40.07,
            'offer_fingerprint': 'test_fingerprint_1'
        }
        
        self.state_manager.add_offer(product_data)
        
        # Limpiar
        cleared = self.state_manager.clear()
        assert cleared == True
        
        # Verificar que se limpió
        assert len(self.state_manager.state['products']) == 0
        
        # Guardar y verificar en disco
        self.state_manager.save()
        with open(self.state_file, 'r', encoding='utf-8') as f:
            saved_state = json.load(f)
        
        assert len(saved_state['products']) == 0
    
    def test_export_state(self):
        """Test exportar estado"""
        # Añadir datos
        product_data = {
            'product_id_hash': 'test_product_1',
            'name': 'Producto Test',
            'url': 'https://example.com/product',
            'canonical_url': 'https://example.com/product',
            'current_price': 35.90,
            'old_price': 59.90,
            'discount': 40.07,
            'offer_fingerprint': 'test_fingerprint_1'
        }
        
        self.state_manager.add_offer(product_data)
        
        # Exportar
        exported = self.state_manager.export_to_dict()
        
        assert 'products' in exported
        assert 'test_product_1' in exported['products']
        
        # Verificar que es una copia
        assert exported is not self.state_manager.state
        assert exported['products'] is not self.state_manager.state['products']

if __name__ == "__main__":
    # Ejecutar tests si se llama directamente
    pytest.main([__file__, "-v"])