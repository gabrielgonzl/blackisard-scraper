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
USER_AGENT = "Blackisard-Scraper/1.0 (Educational Purposes)"

# Configuración de archivos
STATE_FILE = "state.json"
OUTPUT_FILE = "ofertas.md"

# Configuración de paginación
PRODUCTS_PER_PAGE = 24  # Estimado basado en la web

# Configuración de logging
LOG_LEVEL = "INFO"
DEBUG_MODE = False