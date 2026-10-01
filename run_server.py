#!/usr/bin/env python3
"""
Script de ejemplo para ejecutar el scraper en servidor
Incluye configuraciones específicas para diferentes plataformas
"""
import os
import sys
from datetime import datetime

# Configuración para servidor
SERVER_CONFIG = {
    'discount_threshold': float(os.getenv('DISCOUNT_THRESHOLD', '40')),
    'request_timeout': int(os.getenv('REQUEST_TIMEOUT', '30')),
    'output_file': os.getenv('OUTPUT_FILE', 'ofertas.md'),
    'state_file': os.getenv('STATE_FILE', 'state.json'),
    'debug_mode': os.getenv('DEBUG_MODE', 'false').lower() == 'true',
    'log_level': os.getenv('LOG_LEVEL', 'INFO'),
    'platform': os.getenv('PLATFORM', 'generic')  # github, railway, heroku, etc.
}

def log_server_info():
    """Log información del servidor y configuración"""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                    BLACKISARD SCRAPER                        ║
║                    SERVidor Deployment                       ║
╚══════════════════════════════════════════════════════════════╝

Plataforma: {SERVER_CONFIG['platform']}
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Threshold descuento: {SERVER_CONFIG['discount_threshold']}%
Timeout: {SERVER_CONFIG['request_timeout']}s
Debug: {SERVER_CONFIG['debug_mode']}
Output: {SERVER_CONFIG['output_file']}
Estado: {SERVER_CONFIG['state_file']}

""")

def run_scraper():
    """Ejecuta el scraper con configuración del servidor"""
    try:
        # Importar el scraper principal
        from scraper import BlackisardScraper
        
        # Aplicar configuración del servidor
        print("🚀 Iniciando scraper con configuración del servidor...")
        
        # Crear y ejecutar scraper (el método run() ahora acepta custom_config)
        scraper = BlackisardScraper()
        
        # Configuración limpia para el scraper
        config_dict = {
            'discount_threshold': SERVER_CONFIG['discount_threshold'],
            'request_timeout': SERVER_CONFIG['request_timeout'],
            'output_file': SERVER_CONFIG['output_file'],
            'state_file': SERVER_CONFIG['state_file'],
            'debug_mode': SERVER_CONFIG['debug_mode'],
            'log_level': SERVER_CONFIG['log_level']
        }
        
        result = scraper.run(config_dict)
        
        # Log resultado
        print(f"""
╔══════════════════════════════════════════════════════════════╗
║                      RESULTADO                               ║
╚══════════════════════════════════════════════════════════════╝

✅ Éxito: {result.get('success', False)}
📊 Nuevas ofertas: {result.get('new_offers', 0)}
📦 Productos analizados: {result.get('total_products', 0)}
⏱️  Duración: {result.get('duration', 0):.2f}s
❌ Errores: {result.get('errors', 0)}

""")
        
        return result
        
    except Exception as e:
        print(f"❌ Error al ejecutar scraper: {e}")
        print(f"Tipo: {type(e).__name__}")
        
        if SERVER_CONFIG['debug_mode']:
            import traceback
            traceback.print_exc()
        
        return {'success': False, 'error': str(e)}

def save_result_marker():
    """Guarda un marcador del resultado para monitoreo"""
    marker_file = "scraper_result.json"
    
    result_data = {
        'timestamp': datetime.now().isoformat(),
        'platform': SERVER_CONFIG['platform'],
        'success': True,  # Si llegamos aquí, el script se ejecutó
        'config': SERVER_CONFIG
    }
    
    try:
        import json
        with open(marker_file, 'w') as f:
            json.dump(result_data, f, indent=2)
        print(f"📄 Marcador guardado en: {marker_file}")
    except Exception as e:
        print(f"⚠️  No se pudo guardar el marcador: {e}")

if __name__ == "__main__":
    log_server_info()
    
    try:
        result = run_scraper()
        save_result_marker()
        
        # Exit code para CI/CD
        if result.get('success', False):
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Scraper interrumpido por el usuario")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        sys.exit(1)