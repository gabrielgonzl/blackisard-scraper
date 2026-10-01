"""
Scraper optimizado para Blackisard - Versión paralela
Detecta ofertas de escalada en roca con descuento ≥ umbral
Optimizado para velocidad con paralelización
"""
import time
import logging
import argparse
import os
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Set
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache

import requests
from bs4 import BeautifulSoup

from config import *
from parser import parse_page, calculate_discount, generate_product_id
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
        logging.StreamHandler(),
        logging.FileHandler('scraper.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

class OptimizedBlackisardScraper:
    """
    Scraper optimizado con paralelización y técnicas avanzadas
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Cache para páginas ya procesadas
        self.page_cache = {}
        self.processed_urls = set()
        
        # Configuración de paralelización
        self.max_workers = 5  # Número máximo de threads
        self.batch_size = 10  # Páginas por batch
        
        # Early exit settings
        self.min_products_per_page = 3  # Mínimo productos válidos por página
        self.empty_pages_count = 0
        self.max_empty_pages = 3  # Parar después de 3 páginas vacías
        
        logger.info(f"🚀 Scraper optimizado iniciado")
        logger.info(f"   - Paralelización: {self.max_workers} threads")
        logger.info(f"   - Batch size: {self.batch_size}")
        logger.info(f"   - Early exit: {self.max_empty_pages} páginas vacías máximo")
    
    @lru_cache(maxsize=100)
    def fetch_page_cached(self, url: str) -> Optional[BeautifulSoup]:
        """
        Obtiene una página con cache para evitar requests duplicados
        
        Args:
            url (str): URL a obtener
            
        Returns:
            BeautifulSoup or None: Contenido parseado o None si falla
        """
        if url in self.page_cache:
            logger.debug(f"📦 Usando cache para: {url}")
            return self.page_cache[url]
        
        logger.info(f"🌐 Obteniendo página: {url}")
        
        try:
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
            
            # Cache para uso futuro
            self.page_cache[url] = soup
            return soup
            
        except Exception as e:
            logger.error(f"Error al obtener {url}: {e}")
            return None
    
    def discover_pages_optimized(self) -> List[str]:
        """
        Descubre páginas de productos de forma optimizada
        
        Returns:
            List[str]: Lista de URLs de páginas a procesar
        """
        base_url = "https://blackisard.com/escalada-en-roca"
        pages = []
        current_url = base_url
        page_count = 0
        
        logger.info(f"🔍 Descubriendo páginas de productos...")
        
        while current_url and page_count < 100:  # Límite de seguridad
            page_count += 1
            
            # Usar cache si ya visitamos esta página
            soup = self.fetch_page_cached(current_url)
            if not soup:
                logger.warning(f"No se pudo obtener página {page_count}: {current_url}")
                break
            
            pages.append(current_url)
            logger.debug(f"📄 Página {page_count}: {current_url}")
            
            # Buscar siguiente página
            next_link = soup.find('link', rel='next')
            if next_link:
                next_url = urljoin(base_url, next_link.get('href', ''))
                if next_url != current_url:
                    current_url = next_url
                else:
                    logger.debug("🚫 No hay más páginas")
                    break
            else:
                logger.debug("🚫 No hay más páginas")
                break
        
        logger.info(f"📊 Descubiertas {len(pages)} páginas")
        return pages
    
    def process_page_batch(self, page_urls: List[str]) -> Tuple[List[Dict], List[str]]:
        """
        Procesa un batch de páginas en paralelo
        
        Args:
            page_urls (List[str]): URLs de páginas a procesar
            
        Returns:
            Tuple[List[Dict], List[str]]: (productos, URLs de páginas siguientes)
        """
        all_products = []
        next_pages = []
        
        logger.info(f"🔄 Procesando batch de {len(page_urls)} páginas...")
        
        # Procesar páginas en paralelo
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Enviar trabajos
            future_to_url = {
                executor.submit(self.process_single_page_optimized, url): url 
                for url in page_urls
            }
            
            # Recoger resultados
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    products, next_page = future.result()
                    all_products.extend(products)
                    if next_page:
                        next_pages.append(next_page)
                except Exception as e:
                    logger.error(f"Error procesando {url}: {e}")
        
        logger.info(f"✅ Batch completado: {len(all_products)} productos")
        return all_products, next_pages
    
    def process_single_page_optimized(self, url: str) -> Tuple[List[Dict], Optional[str]]:
        """
        Procesa una sola página con optimización
        
        Args:
            url (str): URL de la página
            
        Returns:
            Tuple[List[Dict], Optional[str]]: (productos, siguiente página)
        """
        soup = self.fetch_page_cached(url)
        if not soup:
            return [], None
        
        # Parsear productos
        products, next_page = parse_page(soup)
        
        # Filtrar solo productos con descuento mínimo (early filtering)
        filtered_products = [
            p for p in products 
            if p.get('discount', 0) >= DISCOUNT_THRESHOLD
        ]
        
        logger.debug(f"📄 {url}: {len(products)} productos, {len(filtered_products)} con descuento ≥{DISCOUNT_THRESHOLD}%")
        
        # Verificar early exit conditions
        if len(products) < self.min_products_per_page:
            self.empty_pages_count += 1
            logger.debug(f"📉 Página con pocos productos: {len(products)} (contador: {self.empty_pages_count})")
        
        return filtered_products, next_page
    
    def run_optimized(self, custom_config: Optional[Dict] = None):
        """
        Ejecuta el scraper optimizado
        
        Args:
            custom_config (Optional[Dict]): Configuración personalizada
        """
        start_time = time.time()
        all_products = []
        
        # Aplicar configuración personalizada
        if custom_config:
            logger.info("🔧 Aplicando configuración personalizada...")
            for key, value in custom_config.items():
                logger.info(f"   - {key}: {value}")
        
        try:
            # Descubrir páginas
            page_urls = self.discover_pages_optimized()
            
            if not page_urls:
                logger.warning("🚫 No se encontraron páginas")
                return
            
            # Procesar páginas en batches para mejor paralelización
            total_batches = (len(page_urls) + self.batch_size - 1) // self.batch_size
            
            for batch_num in range(total_batches):
                start_idx = batch_num * self.batch_size
                end_idx = min(start_idx + self.batch_size, len(page_urls))
                batch_urls = page_urls[start_idx:end_idx]
                
                logger.info(f"🚀 Procesando batch {batch_num + 1}/{total_batches}")
                
                # Early exit si ya no encontramos productos en suficientes páginas
                if self.empty_pages_count >= self.max_empty_pages:
                    logger.info(f"🛑 Early exit: {self.empty_pages_count} páginas vacías consecutivas")
                    logger.info(f"📊 Total productos hasta ahora: {len(all_products)}")
                    break
                
                # Procesar batch
                batch_products, _ = self.process_page_batch(batch_urls)
                all_products.extend(batch_products)
                
                # Log progreso
                elapsed = time.time() - start_time
                logger.info(f"📊 Progreso: {len(all_products)} ofertas ≥{DISCOUNT_THRESHOLD}% en {elapsed:.1f}s")
            
            # Eliminar duplicados y filtrar por umbral
            unique_products = self.remove_duplicates(all_products)
            final_offers = [p for p in unique_products if p.get('discount', 0) >= DISCOUNT_THRESHOLD]
            
            # Generar reportes
            self.generate_reports(final_offers, start_time)
            
            return final_offers
            
        except Exception as e:
            logger.error(f"Error durante la ejecución: {e}")
            raise
    
    def remove_duplicates(self, products: List[Dict]) -> List[Dict]:
        """
        Elimina productos duplicados basándose en la URL y fingerprint
        
        Args:
            products (List[Dict]): Lista de productos
            
        Returns:
            List[Dict]: Lista sin duplicados
        """
        seen_urls = set()
        seen_fingerprints = set()
        unique_products = []
        
        for product in products:
            url = product.get('url', '')
            fingerprint = product.get('offer_fingerprint', '')
            
            # Evitar duplicados por URL
            if url and url in seen_urls:
                continue
            
            # Evitar duplicados por fingerprint de oferta
            if fingerprint and fingerprint in seen_fingerprints:
                continue
            
            if url:
                seen_urls.add(url)
            if fingerprint:
                seen_fingerprints.add(fingerprint)
            
            unique_products.append(product)
        
        duplicates_removed = len(products) - len(unique_products)
        if duplicates_removed > 0:
            logger.info(f"🗑️ Eliminados {duplicates_removed} duplicados")
        
        return unique_products
    
    def generate_reports(self, products: List[Dict], start_time: float):
        """
        Genera reportes finales
        
        Args:
            products (List[Dict]): Lista de productos finales
            start_time (float): Tiempo de inicio
        """
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info("")
        logger.info("="*60)
        logger.info("🎯 RESUMEN DE EJECUCIÓN")
        logger.info("="*60)
        logger.info(f"📊 Productos analizados: {len(products)}")
        logger.info(f"📦 Productos en stock: {sum(1 for p in products if p.get('in_stock', True))}")
        logger.info(f"💰 Ofertas ≥ {DISCOUNT_THRESHOLD}%: {len(products)}")
        logger.info(f"⏱️ Duración: {duration:.2f}s")
        logger.info(f"🚀 Velocidad: {len(products)/duration:.1f} ofertas/s")
        logger.info("="*60)
        
        if products:
            logger.info(f"🎉 ¡Se encontraron {len(products)} ofertas!")
            for i, product in enumerate(products[:5], 1):
                name = product.get('name', 'Sin nombre')[:50]
                price = product.get('current_price', 'N/A')
                discount = product.get('discount', 0)
                logger.info(f"   [{i}] {name} - {price}€ ({discount:.1f}% desc.)")
            
            if len(products) > 5:
                logger.info(f"   ... y {len(products) - 5} más")
        else:
            logger.info(f"😔 No hay nuevas ofertas.")
        
        # Generar archivos
        try:
            # Guardar estado
            state_manager = StateManager()
            state_manager.save_products(products)
            
            # Generar reporte
            formatter = MarkdownFormatter()
            formatter.generate_report(products)
            
            logger.info("")
            logger.info("="*60)
            logger.info("💾 Guardado en: state.json y ofertas.md")
            logger.info("="*60)
            logger.info(f"🚀 Scraper completado en {duration:.2f} segundos")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Error generando reportes: {e}")

def main():
    """Función principal"""
    parser = argparse.ArgumentParser(description='Blackisard Scraper Optimizado')
    parser.add_argument('--debug', action='store_true', help='Activar modo debug')
    parser.add_argument('--threshold', type=float, default=DISCOUNT_THRESHOLD, 
                       help=f'Descuento mínimo (default: {DISCOUNT_THRESHOLD}%)')
    parser.add_argument('--timeout', type=int, default=REQUEST_TIMEOUT,
                       help=f'Timeout de requests (default: {REQUEST_TIMEOUT}s)')
    parser.add_argument('--output', default=OUTPUT_FILE,
                       help=f'Archivo de salida (default: {OUTPUT_FILE})')
    parser.add_argument('--workers', type=int, default=5,
                       help='Número de workers paralelos (default: 5)')
    
    args = parser.parse_args()
    
    # Aplicar argumentos
    if args.debug:
        os.environ['DEBUG_MODE'] = 'True'
    if args.threshold != DISCOUNT_THRESHOLD:
        os.environ['DISCOUNT_THRESHOLD'] = str(args.threshold)
    if args.timeout != REQUEST_TIMEOUT:
        os.environ['REQUEST_TIMEOUT'] = str(args.timeout)
    
    # Configurar scraper
    config_dict = {
        'discount_threshold': args.threshold,
        'request_timeout': args.timeout,
        'output_file': args.output,
        'workers': args.workers
    }
    
    # Ejecutar scraper
    scraper = OptimizedBlackisardScraper()
    scraper.max_workers = args.workers
    
    logger.info("="*60)
    logger.info("BLACKISARD SCRAPER OPTIMIZADO")
    logger.info("="*60)
    logger.info(f"Categoría: Escalada en roca")
    logger.info(f"Descuento mínimo: {args.threshold}%")
    logger.info(f"Estado: state.json")
    logger.info(f"Salida: {args.output}")
    logger.info(f"Workers paralelos: {args.workers}")
    logger.info("="*60)
    logger.info("")
    
    scraper.run_optimized(config_dict)

if __name__ == "__main__":
    main()