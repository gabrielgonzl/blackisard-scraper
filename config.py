"""
Configuración del scraper de Blackisard
"""
import os

# Configuración de la web
BASE_URL = "https://blackisard.com"
CATEGORY_PATH = "/escalada-en-roca"
CATEGORY_URL = BASE_URL + CATEGORY_PATH

# Configuración del scraper
DISCOUNT_THRESHOLD = 40.0  # Descuento mínimo del 40%
REQUEST_TIMEOUT = 30  # segundos

# User-Agent más realista para evitar bloqueos
import os
PLATFORM = os.getenv('PLATFORM', 'local')
if PLATFORM == 'github-actions':
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
elif PLATFORM == 'railway':
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
else:
    USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# Configuración de archivos
STATE_FILE = "state.json"
OUTPUT_FILE = "ofertas.md"

# Configuración de paginación
PRODUCTS_PER_PAGE = 24  # Estimado basado en la web

# Configuración de logging
LOG_LEVEL = "INFO"
DEBUG_MODE = False