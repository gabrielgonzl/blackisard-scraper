"""
Scraper principal para ofertas de Blackisard
Detecta ofertas de escalada en roca con descuento >= 40%
"""
import time
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from config import *
from parser import parse_page, parse_price, calculate_discount
from state import StateManager
from formatter import MarkdownFormatter

# Configurar logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scraper.log', encoding='utf-8')
    ] if not DEBUG_MODE else [
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BlackisardScraper:
    """Scraper principal de Blackisard"""
    
    def __init__(self):
        """Inicializa el scraper"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.state_manager = StateManager(STATE_FILE)
        self.formatter = MarkdownFormatter(OUTPUT_FILE)
        
        # Estadísticas
        self.stats = {
            'total_pages': 0,
            'total_products': 0,
            'in_stock': 0,
            'valid_offers': 0,
            'new_offers': 0,
            'errors': 0,
            'skipped_no_prices': 0,
            'skipped_no_stock': 0,
            'skipped_low_discount': 0
        }
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Obtiene y parsea una página
        
        Args:
            url (str): URL a obtener
        
        Returns:
            BeautifulSoup or None: Contenido parseado o None si falla
        """
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Obteniendo página: {url}")
                response = self.session.get(
                    url,
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True
                )
                
                response.raise_for_status()
                
                # Verificar encoding
                if response.encoding.lower() not in ['utf-8', 'utf8']:
                    response.encoding = 'utf-8'
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Verificar que no es una página de error
                if soup.find('title') and '404' in soup.find('title').get_text():
                    logger.warning(f"Página 404: {url}")
                    return None
                
                return soup
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Error al obtener {url} (intento {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    logger.info(f"Reintentando en {retry_delay} segundos...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Backoff exponencial
                else:
                    logger.error(f"No se pudo obtener {url} después de {max_retries} intentos")
                    self.stats['errors'] += 1
                    return None
            except Exception as e:
                logger.error(f"Error inesperado al obtener {url}: {e}")
                self.stats['errors'] += 1
                return None
    
    def discover_pages(self, start_url: str) -> List[str]:
        """
        Descubre todas las páginas de productos automáticamente
        
        Args:
            start_url (str): URL inicial de la categoría
        
        Returns:
            list: Lista de URLs de páginas
        """
        pages = [start_url]
        current_url = start_url
        visited_urls = set()
        
        logger.info("Descubriendo páginas de productos...")
        
        while current_url and current_url not in visited_urls:
            visited_urls.add(current_url)
            
            soup = self.fetch_page(current_url)
            if not soup:
                break
            
            # Buscar enlace a la siguiente página
            next_link = soup.find('link', rel='next')
            if next_link:
                next_url = next_link.get('href')
                if next_url:
                    # Construir URL completa si es relativa
                    if next_url.startswith('/'):
                        next_url = urljoin(BASE_URL, next_url)
                    elif not next_url.startswith('http'):
                        next_url = urljoin(BASE_URL, next_url)
                    
                    # Verificar que no hemos vuelto atrás
                    if next_url not in visited_urls:
                        pages.append(next_url)
                        current_url = next_url
                        continue
            
            # No hay más páginas
            break
        
        logger.info(f"Descubiertas {len(pages)} páginas")
        return pages
    
    def is_valid_offer(self, product_data: Dict) -> bool:
        """
        Verifica si una oferta cumple los criterios
        
        Args:
            product_data (dict): Datos del producto
        
        Returns:
            bool: True si es una oferta válida
        """
        # Verificar que tiene precios
        if product_data.get('current_price') is None or product_data.get('old_price') is None:
            self.stats['skipped_no_prices'] += 1
            return False
        
        # Verificar stock
        if not product_data.get('in_stock', True):
            self.stats['skipped_no_stock'] += 1
            return False
        
        # Verificar descuento mínimo
        discount = product_data.get('discount')
        if discount is None or discount < DISCOUNT_THRESHOLD:
            self.stats['skipped_low_discount'] += 1
            return False
        
        return True
    
    def scrape_category(self, category_url: str) -> List[Dict]:
        """
        Escanea una categoría completa
        
        Args:
            category_url (str): URL de la categoría
        
        Returns:
            list: Lista de productos con ofertas válidas
        """
        # Descubrir páginas
        pages = self.discover_pages(category_url)
        self.stats['total_pages'] = len(pages)
        
        valid_offers = []
        
        # Escanear cada página
        for page_url in pages:
            logger.info(f"Escaneando página {len(valid_offers) + 1}/{len(pages)}: {page_url}")
            
            soup = self.fetch_page(page_url)
            if not soup:
                continue
            
            # Parsear productos
            products, next_page = parse_page(soup, BASE_URL)
            
            self.stats['total_products'] += len(products)
            
            # Procesar cada producto
            for product in products:
                try:
                    # Verificar si es una oferta válida
                    if self.is_valid_offer(product):
                        valid_offers.append(product)
                        self.stats['valid_offers'] += 1
                    
                    # Contar productos en stock
                    if product.get('in_stock'):
                        self.stats['in_stock'] += 1
                    
                    # Actualizar información del producto en el estado
                    product_id = product.get('product_id_hash')
                    if product_id:
                        self.state_manager.update_product(product_id, product)
                
                except Exception as e:
                    logger.error(f"Error procesando producto {product.get('name', 'Unknown')}: {e}")
                    self.stats['errors'] += 1
                    continue
            
            # Pausa entre páginas
            time.sleep(1)
        
        return valid_offers
    
    def detect_new_offers(self, products: List[Dict]) -> List[Dict]:
        """
        Detecta ofertas nuevas vs conocidas
        
        Args:
            products (list): Lista de productos con ofertas
        
        Returns:
            list: Lista de ofertas nuevas
        """
        new_offers = []
        
        for product in products:
            product_id = product.get('product_id_hash')
            fingerprint = product.get('offer_fingerprint')
            
            if not product_id or not fingerprint:
                continue
            
            # Verificar si la oferta ya existe
            if not self.state_manager.offer_exists(product_id, fingerprint):
                # Es una oferta nueva
                if self.state_manager.add_offer(product):
                    new_offers.append(product)
                    self.stats['new_offers'] += 1
                    logger.info(f"Nueva oferta detectada: {product.get('name')} - {product.get('current_price')}€ ({product.get('discount')}%)")
            else:
                logger.debug(f"Oferta conocida: {product.get('name')} - {product.get('current_price')}€")
        
        return new_offers
    
    def run(self) -> Dict:
        """
        Ejecuta el scraper completo
        
        Returns:
            dict: Resultado de la ejecución
        """
        logger.info("=" * 60)
        logger.info("BLACKISARD SCRAPER")
        logger.info("=" * 60)
        logger.info(f"Categoría: Escalada en roca")
        logger.info(f"Descuento mínimo: {DISCOUNT_THRESHOLD}%")
        logger.info(f"Estado: {STATE_FILE}")
        logger.info(f"Salida: {OUTPUT_FILE}")
        logger.info("=" * 60)
        
        start_time = datetime.now()
        
        try:
            # Escanear categoría
            all_products = self.scrape_category(CATEGORY_URL)
            
            # Detectar ofertas nuevas
            new_offers = self.detect_new_offers(all_products)
            
            # Guardar estado
            logger.info("Guardando estado...")
            if not self.state_manager.save():
                logger.error("Error al guardar estado")
            
            # Generar reporte
            logger.info("Generando reporte...")
            scan_info = {
                'products': all_products,
                'total_pages': self.stats['total_pages'],
                'total_products': self.stats['total_products'],
                'in_stock': self.stats['in_stock'],
                'valid_offers': self.stats['valid_offers'],
                'state_manager': self.state_manager
            }
            
            if not self.formatter.create_report(new_offers, scan_info):
                logger.error("Error al generar reporte")
            
            # Mostrar resumen
            self.print_summary(new_offers)
            
            # Calcular tiempo total
            end_time = datetime.now()
            duration = end_time - start_time
            
            logger.info("=" * 60)
            logger.info(f"Scraper completado en {duration.total_seconds():.2f} segundos")
            logger.info("=" * 60)
            
            return {
                'success': True,
                'new_offers': len(new_offers),
                'total_products': self.stats['total_products'],
                'total_pages': self.stats['total_pages'],
                'duration': duration.total_seconds(),
                'errors': self.stats['errors']
            }
        
        except KeyboardInterrupt:
            logger.info("Scraper interrumpido por el usuario")
            return {'success': False, 'error': 'Interrumpido por el usuario'}
        except Exception as e:
            logger.error(f"Error durante la ejecución: {e}")
            return {'success': False, 'error': str(e)}
    
    def print_summary(self, new_offers: List[Dict]):
        """Imprime el resumen de la ejecución"""
        logger.info("")
        logger.info("RESUMEN DE EJECUCIÓN")
        logger.info("=" * 60)
        logger.info(f"Productos analizados: {self.stats['total_products']}")
        logger.info(f"Productos en stock: {self.stats['in_stock']}")
        logger.info(f"Ofertas >= {DISCOUNT_THRESHOLD}%: {self.stats['valid_offers']}")
        logger.info(f"Nuevas ofertas detectadas: {self.stats['new_offers']}")
        logger.info("")
        
        if new_offers:
            logger.info("NUEVAS OFERTAS:")
            logger.info("-" * 60)
            for i, offer in enumerate(new_offers[:10], 1):  # Mostrar solo las primeras 10
                name = offer.get('name', 'Producto desconocido')
                current_price = offer.get('current_price')
                old_price = offer.get('old_price')
                discount = offer.get('discount')
                
                logger.info(f"[{i:2d}] {name[:40]:40} {current_price:.2f}€  (-{discount:.2f}%)")
            
            if len(new_offers) > 10:
                logger.info(f"... y {len(new_offers) - 10} más")
        else:
            logger.info("No hay nuevas ofertas.")
        
        logger.info("")
        logger.info(f"Guardado en: {STATE_FILE} y {OUTPUT_FILE}")

def main():
    """Función principal"""
    from config import (
        DISCOUNT_THRESHOLD as BASE_DISCOUNT_THRESHOLD, 
        REQUEST_TIMEOUT as BASE_REQUEST_TIMEOUT,
        OUTPUT_FILE as BASE_OUTPUT_FILE,
        STATE_FILE as BASE_STATE_FILE
    )
    
    parser = argparse.ArgumentParser(
        description="Scraper de ofertas de Blackisard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  python scraper.py              # Ejecutar scraper con configuración por defecto
  python scraper.py --debug      # Ejecutar con modo debug
  python scraper.py --threshold 35  # Cambiar umbral de descuento a 35%
        """
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Activar modo debug con logs detallados'
    )
    
    parser.add_argument(
        '--threshold',
        type=float,
        default=BASE_DISCOUNT_THRESHOLD,
        help=f'Umbral de descuento mínimo (default: {BASE_DISCOUNT_THRESHOLD}%)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=BASE_REQUEST_TIMEOUT,
        help=f'Timeout de peticiones (default: {BASE_REQUEST_TIMEOUT}s)'
    )
    
    parser.add_argument(
        '--output',
        default=BASE_OUTPUT_FILE,
        help=f'Archivo de salida (default: {BASE_OUTPUT_FILE})'
    )
    
    parser.add_argument(
        '--state',
        default=BASE_STATE_FILE,
        help=f'Archivo de estado (default: {BASE_STATE_FILE})'
    )
    
    args = parser.parse_args()
    
    # Configuración personalizada para el scraper
    custom_config = {
        'discount_threshold': args.threshold,
        'request_timeout': args.timeout,
        'output_file': args.output,
        'state_file': args.state,
        'debug_mode': args.debug,
        'log_level': 'DEBUG' if args.debug else 'INFO'
    }
    
    # Actualizar variables globales para el módulo config
    global DISCOUNT_THRESHOLD, REQUEST_TIMEOUT, OUTPUT_FILE, STATE_FILE, LOG_LEVEL, DEBUG_MODE
    DISCOUNT_THRESHOLD = args.threshold
    REQUEST_TIMEOUT = args.timeout
    OUTPUT_FILE = args.output
    STATE_FILE = args.state
    LOG_LEVEL = 'DEBUG' if args.debug else 'INFO'
    DEBUG_MODE = args.debug
    
    # Actualizar configuración del módulo config
    import config
    config.DISCOUNT_THRESHOLD = args.threshold
    config.REQUEST_TIMEOUT = args.timeout
    config.OUTPUT_FILE = args.output
    config.STATE_FILE = args.state
    config.LOG_LEVEL = 'DEBUG' if args.debug else 'INFO'
    config.DEBUG_MODE = args.debug
    
    # Crear y ejecutar scraper
    scraper = BlackisardScraper()
    result = scraper.run(custom_config)
    
    # Exit code
    if result['success']:
        print(f"\n✅ Scraper ejecutado exitosamente")
        print(f"   Nuevas ofertas: {result['new_offers']}")
        print(f"   Productos analizados: {result['total_products']}")
        print(f"   Duración: {result['duration']:.2f}s")
        exit(0)
    else:
        print(f"\n❌ Error durante la ejecución: {result.get('error', 'Unknown error')}")
        exit(1)

if __name__ == "__main__":
    main()