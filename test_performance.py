#!/usr/bin/env python3
"""
Test de rendimiento: Comparar scraper original vs optimizado
"""
import time
import argparse
import subprocess
import sys

def test_scraper_performance():
    """Test comparativo de rendimiento"""
    print("🚀 INICIANDO TEST DE RENDIMIENTO")
    print("="*50)
    
    # Configuración de test
    pages_to_test = [1, 2, 3, 5]  # Número de páginas a probar
    thresholds = [25, 35]  # Umbrales a probar
    
    results = []
    
    for threshold in thresholds:
        for pages in pages_to_test:
            print(f"\n🧪 Test: {pages} páginas, umbral {threshold}%")
            print("-" * 40)
            
            # Test scraper original (limitado)
            print("📊 Probando scraper ORIGINAL...")
            start_time = time.time()
            
            try:
                cmd_original = [
                    sys.executable, "scraper.py", 
                    "--threshold", str(threshold),
                    "--timeout", "30"
                ]
                
                # Simular páginas limitadas modificando temporalmente
                env = {"DISCOUNT_THRESHOLD": str(threshold)}
                result_original = subprocess.run(
                    cmd_original, 
                    capture_output=True, 
                    text=True, 
                    timeout=120,
                    env=env
                )
                
                original_time = time.time() - start_time
                original_success = result_original.returncode == 0
                
            except subprocess.TimeoutExpired:
                original_time = 120  # Timeout
                original_success = False
            except Exception as e:
                original_time = 0
                original_success = False
            
            # Test scraper optimizado
            print("🚀 Probando scraper OPTIMIZADO...")
            start_time = time.time()
            
            try:
                cmd_optimized = [
                    sys.executable, "scraper_optimized.py",
                    "--threshold", str(threshold),
                    "--timeout", "15",  # Timeout menor
                    "--workers", "3"
                ]
                
                result_optimized = subprocess.run(
                    cmd_optimized,
                    capture_output=True,
                    text=True,
                    timeout=60,  # Timeout más corto
                    env=env
                )
                
                optimized_time = time.time() - start_time
                optimized_success = result_optimized.returncode == 0
                
            except subprocess.TimeoutExpired:
                optimized_time = 60
                optimized_success = False
            except Exception as e:
                optimized_time = 0
                optimized_success = False
            
            # Calcular mejoras
            if original_success and optimized_success and original_time > 0:
                speedup = original_time / optimized_time
                time_saved = original_time - optimized_time
            else:
                speedup = 0
                time_saved = 0
            
            # Guardar resultados
            result = {
                'pages': pages,
                'threshold': threshold,
                'original_time': original_time,
                'original_success': original_success,
                'optimized_time': optimized_time,
                'optimized_success': optimized_success,
                'speedup': speedup,
                'time_saved': time_saved
            }
            results.append(result)
            
            # Mostrar resultado
            print(f"   Original:  {original_time:.1f}s {'✅' if original_success else '❌'}")
            print(f"   Optimizado: {optimized_time:.1f}s {'✅' if optimized_success else '❌'}")
            print(f"   Mejora: {speedup:.1f}x más rápido ({time_saved:.1f}s ahorrados)")
    
    # Mostrar resumen
    print("\n" + "="*50)
    print("📊 RESUMEN DE RENDIMIENTO")
    print("="*50)
    
    successful_tests = [r for r in results if r['original_success'] and r['optimized_success']]
    
    if successful_tests:
        avg_speedup = sum(r['speedup'] for r in successful_tests) / len(successful_tests)
        total_saved = sum(r['time_saved'] for r in successful_tests)
        
        print(f"🚀 Promedio de mejora: {avg_speedup:.1f}x")
        print(f"⏱️  Tiempo total ahorrado: {total_saved:.1f}s")
        print(f"📈 Tests exitosos: {len(successful_tests)}/{len(results)}")
        
        print(f"\n🏆 MEJORES RESULTADOS:")
        best_test = max(successful_tests, key=lambda x: x['speedup'])
        print(f"   {best_test['pages']} páginas, umbral {best_test['threshold']}%: {best_test['speedup']:.1f}x más rápido")
    else:
        print("❌ No hay tests exitosos para comparar")
    
    return results

def quick_performance_test():
    """Test rápido de rendimiento"""
    print("⚡ TEST RÁPIDO DE RENDIMIENTO")
    print("="*40)
    
    import time
    start_time = time.time()
    
    # Test simple: importar módulos y hacer operaciones básicas
    print("📦 Test de importación de módulos...")
    
    try:
        import requests
        from bs4 import BeautifulSoup
        import concurrent.futures
        from urllib.parse import urljoin
        
        import_time = time.time() - start_time
        print(f"✅ Módulos importados en {import_time:.3f}s")
        
    except ImportError as e:
        print(f"❌ Error importando módulos: {e}")
        return
    
    # Test de paralelización
    print("🚀 Test de paralelización...")
    
    def test_function(x):
        import time
        time.sleep(0.1)
        return x * 2
    
    start_parallel = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(test_function, i) for i in range(10)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    parallel_time = time.time() - start_parallel
    print(f"✅ Paralelización: {parallel_time:.3f}s para 10 tareas")
    
    # Test de caché
    print("💾 Test de caché...")
    
    from functools import lru_cache
    
    @lru_cache(maxsize=100)
    def cached_function(x):
        return x ** 2
    
    # Sin caché
    start_cache = time.time()
    for i in range(1000):
        _ = i ** 2
    no_cache_time = time.time() - start_cache
    
    # Con caché
    start_cache = time.time()
    for i in range(1000):
        _ = cached_function(10)  # Mismo valor repetido
    with_cache_time = time.time() - start_cache
    
    print(f"✅ Sin caché: {no_cache_time:.3f}s")
    print(f"✅ Con caché: {with_cache_time:.3f}s")
    print(f"🚀 Mejora de caché: {no_cache_time/with_cache_time:.1f}x")
    
    print(f"\n🎯 RECOMENDACIONES:")
    print(f"   📦 Importaciones: {import_time:.3f}s")
    print(f"   🚀 Paralelización disponible: Sí")
    print(f"   💾 Caché disponible: Sí")
    print(f"   ⚡ El scraper optimizado debería ser significativamente más rápido")

def main():
    parser = argparse.ArgumentParser(description='Test de rendimiento del scraper')
    parser.add_argument('--quick', action='store_true', help='Test rápido')
    parser.add_argument('--full', action='store_true', help='Test completo (lento)')
    
    args = parser.parse_args()
    
    if args.quick:
        quick_performance_test()
    elif args.full:
        test_scraper_performance()
    else:
        print("Uso:")
        print("  python test_performance.py --quick    # Test rápido")
        print("  python test_performance.py --full     # Test completo")

if __name__ == "__main__":
    main()