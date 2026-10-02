"""
Gestión de estado persistente para el scraper de Blackisard
"""
import json
import os
from datetime import datetime
from typing import Dict, Optional, List

class StateManager:
    """Gestiona el estado persistente de ofertas detectadas"""
    
    def __init__(self, state_file: str = "state.json"):
        """
        Inicializa el gestor de estado
        
        Args:
            state_file (str): Ruta al archivo de estado
        """
        self.state_file = state_file
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """
        Carga el estado desde el archivo
        
        Returns:
            dict: Estado cargado o estado vacío
        """
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                # Verificar estructura mínima
                if 'products' not in state:
                    state = {'products': {}}
                
                return state
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: No se pudo cargar el estado: {e}")
                print("Iniciando con estado vacío...")
        
        # Estado inicial vacío
        return {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'products': {}
        }
    
    def _save_state(self) -> bool:
        """
        Guarda el estado de forma atómica
        
        Returns:
            bool: True si se guardó correctamente
        """
        try:
            # Actualizar timestamp
            self.state['last_updated'] = datetime.now().isoformat()
            
            # Escribir en archivo temporal primero
            temp_file = self.state_file + '.tmp'
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
            
            # Renombrar de forma atómica
            os.replace(temp_file, self.state_file)
            return True
            
        except (IOError, OSError) as e:
            print(f"Error al guardar estado: {e}")
            # Intentar limpiar archivo temporal
            temp_file = self.state_file + '.tmp'
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass
            return False
    
    def get_known_offers(self, product_id: str) -> List[Dict]:
        """
        Obtiene las ofertas conocidas para un producto
        
        Args:
            product_id (str): ID del producto
        
        Returns:
            list: Lista de ofertas conocidas
        """
        if product_id not in self.state['products']:
            return []
        
        return self.state['products'][product_id].get('offers', [])
    
    def offer_exists(self, product_id: str, fingerprint: str) -> bool:
        """
        Verifica si una oferta ya existe
        
        Args:
            product_id (str): ID del producto
            fingerprint (str): Huella digital de la oferta
        
        Returns:
            bool: True si la oferta existe
        """
        if product_id not in self.state['products']:
            return False
        
        offers = self.state['products'][product_id].get('offers', [])
        return any(offer.get('fingerprint') == fingerprint for offer in offers)
    
    def add_offer(self, product_data: Dict, first_seen: Optional[str] = None) -> bool:
        """
        Añade una nueva oferta al estado
        
        Args:
            product_data (dict): Datos del producto con la oferta
            first_seen (str, optional): Fecha de primera vista
        
        Returns:
            bool: True si se añadió, False si ya existía
        """
        product_id = product_data.get('product_id_hash')
        if not product_id:
            return False
        
        fingerprint = product_data.get('offer_fingerprint')
        if not fingerprint:
            return False
        
        # Verificar si la oferta ya existe
        if self.offer_exists(product_id, fingerprint):
            return False
        
        # Si no existe el producto, crearlo
        if product_id not in self.state['products']:
            self.state['products'][product_id] = {
                'name': product_data.get('name', 'Producto desconocido'),
                'url': product_data.get('canonical_url', product_data.get('url', '')),
                'product_id': product_data.get('product_id'),
                'sku': product_data.get('sku'),
                'image_url': product_data.get('image_url'),
                'category': product_data.get('category'),
                'offers': []
            }
        
        # Añadir la oferta
        offer = {
            'fingerprint': fingerprint,
            'current_price': product_data.get('current_price'),
            'old_price': product_data.get('old_price'),
            'discount': product_data.get('discount'),
            'first_seen': first_seen or datetime.now().strftime('%Y-%m-%d'),
            'source_url': product_data.get('url'),
            'raw_current_price_text': product_data.get('raw_current_price_text'),
            'raw_old_price_text': product_data.get('raw_old_price_text')
        }
        
        self.state['products'][product_id]['offers'].append(offer)
        return True
    
    def update_product(self, product_id: str, product_data: Dict) -> bool:
        """
        Actualiza información básica de un producto
        
        Args:
            product_id (str): ID del producto
            product_data (dict): Datos del producto
        
        Returns:
            bool: True si se actualizó
        """
        if product_id in self.state['products']:
            # Actualizar información si ha cambiado
            if product_data.get('name') and product_data['name'] != self.state['products'][product_id]['name']:
                self.state['products'][product_id]['name'] = product_data['name']
            
            if product_data.get('canonical_url') and product_data['canonical_url'] != self.state['products'][product_id]['url']:
                self.state['products'][product_id]['url'] = product_data['canonical_url']
            
            if product_data.get('sku') and product_data['sku'] != self.state['products'][product_id].get('sku'):
                self.state['products'][product_id]['sku'] = product_data['sku']
            
            if product_data.get('image_url') and not self.state['products'][product_id].get('image_url'):
                self.state['products'][product_id]['image_url'] = product_data['image_url']
            if product_data.get('category') and not self.state['products'][product_id].get('category'):
                self.state['products'][product_id]['category'] = product_data['category']
            
            return True
        
        return False
    
    def get_statistics(self) -> Dict:
        """
        Obtiene estadísticas del estado
        
        Returns:
            dict: Estadísticas del estado
        """
        total_products = len(self.state['products'])
        total_offers = sum(len(product.get('offers', [])) for product in self.state['products'].values())
        
        # Calcular descuentos promedio
        all_discounts = []
        for product in self.state['products'].values():
            for offer in product.get('offers', []):
                if offer.get('discount'):
                    all_discounts.append(offer['discount'])
        
        avg_discount = sum(all_discounts) / len(all_discounts) if all_discounts else 0
        
        return {
            'total_products': total_products,
            'total_offers': total_offers,
            'average_discount': round(avg_discount, 2),
            'last_updated': self.state.get('last_updated'),
            'version': self.state.get('version', 'unknown')
        }
    
    def export_to_dict(self) -> Dict:
        """
        Exporta todo el estado como diccionario
        
        Returns:
            dict: Estado completo
        """
        import copy
        return copy.deepcopy(self.state)
    
    def clear(self) -> bool:
        """
        Limpia todo el estado
        
        Returns:
            bool: True si se limpió
        """
        self.state = {
            'version': '1.0',
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'products': {}
        }
        return self._save_state()
    
    def merge_state(self, other_state: Dict) -> bool:
        """
        Fusiona otro estado con el actual
        
        Args:
            other_state (dict): Estado a fusionar
        
        Returns:
            bool: True si se fusionó correctamente
        """
        if 'products' not in other_state:
            return False
        
        merged = False
        for product_id, product_data in other_state['products'].items():
            if product_id not in self.state['products']:
                # Producto nuevo
                self.state['products'][product_id] = product_data
                merged = True
            else:
                # Producto existente, fusionar ofertas
                existing_offers = self.state['products'][product_id].get('offers', [])
                existing_fingerprints = {offer.get('fingerprint') for offer in existing_offers}
                
                for offer in product_data.get('offers', []):
                    fingerprint = offer.get('fingerprint')
                    if fingerprint and fingerprint not in existing_fingerprints:
                        existing_offers.append(offer)
                        merged = True
        
        if merged:
            return self._save_state()
        
        return True
    
    def save(self) -> bool:
        """
        Guarda el estado actual
        
        Returns:
            bool: True si se guardó correctamente
        """
        return self._save_state()

if __name__ == "__main__":
    # Test básico del StateManager
    print("Test del StateManager")
    print("=" * 50)
    
    # Crear instancia de test
    state_manager = StateManager("test_state.json")
    
    # Test de añadir ofertas
    test_product = {
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
    added = state_manager.add_offer(test_product)
    print(f"Primera oferta añadida: {added}")
    
    # Segunda oferta igual (no debe añadirse)
    added = state_manager.add_offer(test_product)
    print(f"Segunda oferta igual añadida: {added}")
    
    # Tercera oferta con precio diferente
    test_product_2 = test_product.copy()
    test_product_2['current_price'] = 29.90
    test_product_2['discount'] = 50.08
    test_product_2['offer_fingerprint'] = 'test_fingerprint_2'
    
    added = state_manager.add_offer(test_product_2)
    print(f"Tercera oferta con precio diferente añadida: {added}")
    
    # Mostrar estadísticas
    stats = state_manager.get_statistics()
    print(f"\nEstadísticas: {stats}")
    
    # Limpiar archivo de test
    if os.path.exists("test_state.json"):
        os.remove("test_state.json")