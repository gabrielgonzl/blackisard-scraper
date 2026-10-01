# Blackisard Scraper

Scraper bajo demanda para detectar ofertas en Blackisard (categoría escalada en roca) con descuentos reales del 40% o superiores.

## 🎯 Objetivo

Detectar y registrar exclusivamente productos en stock con descuentos reales ≥ 40%, manteniendo un histórico de ofertas para identificar únicamente las ofertas nuevas en cada ejecución.

## ✨ Características

- ✅ **Ejecución manual**: `python scraper.py`
- ✅ **Detección automática de páginas**: Sin hardcodear número de páginas
- ✅ **Filtros estrictos**: Solo productos en stock con descuento real ≥ 40%
- ✅ **Detección inteligente**: Diferencia ofertas nuevas de ofertas conocidas
- ✅ **Estado persistente**: Archivo `state.json` con historial
- ✅ **Output append-only**: `ofertas.md` nunca se borra, solo se añade
- ✅ **Robusto ante cambios**: Selectores centralizados y adaptables
- ✅ **Logs configurables**: Modo debug opcional
- ✅ **Tests incluidos**: Suite de tests unitarios

## 📋 Requisitos

- Python 3.8+
- Conexión a internet
- Dependencias (ver `requirements.txt`)

## 🚀 Instalación

```bash
# Clonar o descargar el proyecto
cd blackisard-scraper

# Instalar dependencias
pip install -r requirements.txt
```

## 📚 Dependencias

```
requests==2.31.0
beautifulsoup4==4.12.2
lxml==4.9.3
pytest==7.4.3
```

## 🎮 Uso

### Ejecución básica

```bash
python scraper.py
```

### Con modo debug

```bash
python scraper.py --debug
```

### Con umbral personalizado

```bash
python scraper.py --threshold 35  # Detectar descuentos ≥ 35%
```

### Otros parámetros

```bash
python scraper.py --threshold 30 --timeout 60 --output mis_ofertas.md
```

## 📊 Funcionamiento

### 1. Descubrimiento de páginas

El scraper detecta automáticamente todas las páginas de productos:
- Utiliza los enlaces `rel="next"` y `rel="prev"` 
- No hardcodea el número de páginas
- Funciona aunque aumenten/dismuyan las páginas

### 2. Filtrado de ofertas

Una oferta es válida solo si:
- ✅ Producto en stock/disponible
- ✅ Precio actual válido
- ✅ Precio anterior/referencia válido  
- ✅ Descuento calculado ≥ 40%

**Nota**: El descuento se calcula matemáticamente, no se confía en lo que muestra la web:
```python
discount = ((old_price - current_price) / old_price) * 100
```

### 3. Detección de ofertas nuevas

**MUY IMPORTANTE**: No identifica ofertas únicamente por URL o ID.

La lógica es:
```
producto + precio_actual + precio_anterior = oferta concreta
```

Una oferta se considera nueva si esa combinación exacta no existe en el estado.

**Ejemplo de funcionamiento:**

| Ejecución | Producto | Precios | ¿Nueva? | Estado |
|-----------|----------|---------|---------|---------|
| 1 | Producto X | 59,90€ → 35,90€ (-40,07%) | ✅ SÍ | Se registra |
| 2 | Producto X | 59,90€ → 35,90€ (-40,07%) | ❌ NO | Ya existía |
| 3 | Producto X | 59,90€ → 29,90€ (-50,08%) | ✅ SÍ | Precio cambió |

### 4. Archivos generados

#### `state.json` (Estado persistente)
```json
{
  "version": "1.0",
  "created_at": "2026-10-01T10:00:00",
  "last_updated": "2026-10-01T10:30:00",
  "products": {
    "id_11085": {
      "name": "Margalef Pant (Mango)",
      "url": "https://blackisard.com/escalada-en-roca/...",
      "offers": [
        {
          "fingerprint": "abc123...",
          "current_price": 35.90,
          "old_price": 59.90,
          "discount": 40.07,
          "first_seen": "2026-10-01",
          "source_url": "https://blackisard.com/escalada-en-roca/..."
        }
      ]
    }
  }
}
```

#### `ofertas.md` (Append-only)
```markdown
# Ofertas Blackisard

## Resumen de ejecución

**Categoría:** Escalada en roca  
**Páginas encontradas:** 122  
**Productos analizados:** 2427  
**Productos en stock:** 1836  
**Ofertas >= 40%:** 37  
**Nuevas ofertas detectadas:** 4  

**Fecha de ejecución:** 2026-10-01 10:30:00

---

## 2026-10-01

### Margalef Pant (Mango)
- Precio: **35,90 €**
- Precio anterior: ~~59,90 €~~
- Descuento: **-40,07 %**
- Stock: ✅ En stock
- Primera vista: 2026-10-01
- [Ver producto](https://blackisard.com/escalada-en-roca/...)
```

### 5. Salida de consola

```
Blackisard scraper
==================

Categoría: Escalada en roca
Páginas encontradas: 122
Productos analizados: 2427
Productos en stock: 1836
Ofertas >= 40%: 37
Nuevas ofertas detectadas: 4

Nuevas ofertas:

[1] Margalef Pant (Mango)       35,90 €  (-40,07 %)
[2] Orient Express Orange       42,90 €  (-46,01 %)
[3] Pack Pivot Orange           19,90 €  (-52,15 %)
[4] Dragon Cam 00, 0 y 1        74,90 €  (-43,20 %)

Guardado:
- state.json
- ofertas.md
```

## 📁 Estructura del proyecto

```
blackisard-scraper/
├── scraper.py              # Scraper principal
├── parser.py               # Parser HTML y extracción de datos
├── state.py                # Gestión de estado persistente
├── formatter.py            # Generador de archivos markdown
├── config.py               # Configuración global
├── requirements.txt        # Dependencias
├── test_*.py              # Tests unitarios
└── README.md              # Esta documentación
```

### Descripción de módulos

- **`scraper.py`**: Scraper principal con lógica de escaneo y detección de ofertas
- **`parser.py`**: Parseo de HTML, precios europeos, cálculo de descuentos
- **`state.py`**: Gestión del archivo `state.json` con ofertas conocidas
- **`formatter.py`**: Generación del archivo `ofertas.md`
- **`config.py`**: Configuración centralizada

## ⚙️ Configuración

### Umbral de descuento

```python
# En config.py
DISCOUNT_THRESHOLD = 40.0  # Por defecto 40%

# O por línea de comandos
python scraper.py --threshold 35
```

### Timeouts y User-Agent

```python
# En config.py
REQUEST_TIMEOUT = 30  # segundos
USER_AGENT = "Blackisard-Scraper/1.0 (Educational Purposes)"
```

### Archivos de salida

```python
# En config.py
STATE_FILE = "state.json"
OUTPUT_FILE = "ofertas.md"

# O por línea de comandos
python scraper.py --state mi_estado.json --output mis_ofertas.md
```

## 🧪 Testing

### Ejecutar tests

```bash
# Todos los tests
pytest

# Tests específicos
pytest test_parser.py
pytest test_state.py
pytest test_formatter.py
pytest test_scraper.py

# Con información detallada
pytest -v
```

### Cobertura de tests

- ✅ Parseo de precios europeos (`59,90 €`, `1.299,95 €`)
- ✅ Cálculo de descuentos
- ✅ Generación de IDs de productos
- ✅ Detección de ofertas nuevas
- ✅ Gestión de estado persistente
- ✅ Generación de archivos markdown
- ✅ Manejo de errores y reintentos
- ✅ Descubrimiento automático de páginas

## 🔧 Adaptar a cambios de la web

Si Blackisard cambia su HTML, los selectores están centralizados en `parser.py`:

```python
# En parse_product_card()
name_element = product_element.find(class_='product-title') or \
              product_element.find('h3') or \
              product_element.find(class_=re.compile('title|name'))

current_price_element = product_element.find(class_='product-price') or \
                       product_element.find(class_='current-price') or \
                       product_element.find(class_='price')

old_price_element = product_element.find(class_='regular-price') or \
                   product_element.find(class_='old-price')
```

**Para adaptar:**

1. Inspeccionar el HTML de la web
2. Actualizar los selectores CSS en `parser.py`
3. Probar con `python scraper.py --debug`

## ⚠️ Consideraciones importantes

### Control de stock

El scraper verifica múltiples indicadores de stock:
- Clase `stock-label-lbl-in-stock`
- Texto "En stock"
- Detección de texto "agotado", "sin stock"

### Variantes de productos

- Si hay variantes, analiza correctamente la disponibilidad
- No marca como agotado si solo una variante está agotada
- Evita falsos positivos

### Precios

Normaliza correctamente formatos europeos:
- `59,90 €` → `59.90`
- `1.299,95 €` → `1299.95`
- Maneja espacios no separables (`\xa0`)

### Robustez

- **Reintentos**: Hasta 3 intentos por página con backoff exponencial
- **Timeouts**: Configurable (default 30s)
- **Manejo de errores**: Continúa aunque falle alguna página
- **Escritura atómica**: `state.json.tmp` → `state.json` (no se corrompe)

## 🛡️ Buenas prácticas

- Respeta `robots.txt` y términos de uso
- Pausa entre peticiones (1 segundo)
- User-Agent identificable
- No paralelización agresiva
- Logs informativos (no spam)

## ❌ Qué NO incluye

- ❌ Telegram/WhatsApp/Bot notifications
- ❌ Ejecución programada (cron, systemd)
- ❌ Bases de datos (SQLite, PostgreSQL)
- ❌ Selenium/Playwright (solo HTTP + BeautifulSoup)
- ❌ APIs externas

## 🔍 Solución de problemas

### Error: "No se pudo cargar el estado"

```bash
# Verificar que el archivo no esté corrupto
python -c "import json; print(json.load(open('state.json')))"
```

Si hay error, el scraper creará un estado vacío automáticamente.

### Error: "No se pudo obtener página"

```bash
# Ejecutar con debug para más información
python scraper.py --debug
```

### El scraper no detecta productos

```bash
# Verificar que la web funciona
curl https://blackisard.com/escalada-en-roca/

# Ejecutar con debug y revisar los logs
python scraper.py --debug
```

### Modificar umbral de descuento

```bash
# Detectar descuentos del 50% o más
python scraper.py --threshold 50
```

## 📝 Ejemplo de flujo completo

```bash
# Primera ejecución
$ python scraper.py
# Encontrará X ofertas y las registrará

# Segunda ejecución
$ python scraper.py  
# Solo detectará ofertas NUEVAS (si las hay)

# Tercera ejecución con umbral diferente
$ python scraper.py --threshold 30
# Detectará ofertas con 30-39% descuento que no se detectaron antes

# Ver historial
$ cat ofertas.md
```

## 📄 Licencia

Este proyecto es solo para fines educativos y de aprendizaje.

## 🤝 Contribuir

Para adaptar el scraper a otros sitios web o categorías:

1. Cambiar `CATEGORY_URL` en `config.py`
2. Ajustar selectores en `parser.py` si es necesario
3. Probar con `python scraper.py --debug`

---

**Última actualización**: Octubre 2026