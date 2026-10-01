# Despliegue en Servidor - Blackisard Scraper

Esta guía te explica cómo ejecutar el scraper de Blackisard desde un servidor en la nube.

## 🚀 Opciones de Despliegue

### 1. **GitHub Actions** (Recomendada - Gratuita)

La forma más fácil de empezar:

#### Pasos:
1. **Sube tu código a GitHub**
   ```bash
   git init
   git add .
   git commit -m "Inicial: Blackisard scraper"
   git branch -M main
   git remote add origin https://github.com/tu-usuario/blackisard-scraper.git
   git push -u origin main
   ```

2. **El workflow ya está configurado** en `.github/workflows/scrape.yml`

3. **Configura el schedule** (opcional):
   - Ve a `Settings` > `Secrets and variables` > `Actions`
   - Añade secret `DISCOUNT_THRESHOLD: 40`
   - Las ejecuciones manuales funcionan inmediatamente

4. **Resultado**:
   - ✅ Ejecuta automáticamente cada 6 horas
   - ✅ Puedes ejecutarlo manualmente desde GitHub
   - ✅ Guarda `ofertas.md` y `state.json` como artifacts
   - ✅ Hace commit automático de los cambios

---

### 2. **Railway** (Muy Fácil - $5/mes)

#### Pasos:
1. **Ve a [railway.app](https://railway.app)**
2. **Conecta tu repositorio GitHub**
3. **Railway detecta automáticamente** el `railway.toml`
4. **Configura variables de entorno**:
   ```
   DISCOUNT_THRESHOLD=40
   REQUEST_TIMEOUT=30
   PLATFORM=railway
   ```
5. **Resultado**:
   - ✅ Se ejecuta automáticamente
   - ✅ Logs en tiempo real
   - ✅ Reinicio automático si falla
   - ✅ Dominio público para ver resultados

---

### 3. **Heroku** (Clásica - Gratuito limitado)

#### Pasos:
1. **Instalar Heroku CLI**
2. **Crear app**:
   ```bash
   heroku create blackisard-scraper
   ```
3. **Configurar variables**:
   ```bash
   heroku config:set DISCOUNT_THRESHOLD=40
   heroku config:set PLATFORM=heroku
   ```
4. **Deploy**:
   ```bash
   git push heroku main
   ```
5. **Configurar scheduler**:
   ```bash
   heroku addons:create scheduler:standard
   heroku run:dispatcher add --cron "0 */6 * * *" --command "python run_server.py"
   ```

---

### 4. **Docker** (Cualquier servidor)

#### Pasos:
1. **Build imagen**:
   ```bash
   docker build -t blackisard-scraper .
   ```

2. **Run container**:
   ```bash
   docker run -d \
     --name scraper \
     -e DISCOUNT_THRESHOLD=40 \
     -e PLATFORM=docker \
     -v $(pwd)/data:/app/data \
     blackisard-scraper
   ```

3. **Con cron para automatización**:
   ```bash
   # Añadir a crontab
   0 */6 * * * docker exec scraper python run_server.py
   ```

---

### 5. **VPS/Servidor propio**

#### Pasos:
1. **Subir código**:
   ```bash
   scp -r blackisard-scraper/ usuario@servidor:/home/usuario/
   ```

2. **Instalar dependencias**:
   ```bash
   ssh usuario@servidor
   cd blackisard-scraper
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Crear script de ejecución**:
   ```bash
   #!/bin/bash
   cd /home/usuario/blackisard-scraper
   source venv/bin/activate
   python run_server.py
   ```

4. **Configurar cron**:
   ```bash
   crontab -e
   # Ejecutar cada 6 horas
   0 */6 * * * /home/usuario/blackisard-scraper/run.sh >> /home/usuario/scraper.log 2>&1
   ```

---

## 📊 **Monitoreo y Logs**

### En cualquier plataforma, puedes monitorear:

```bash
# Ver logs
tail -f scraper.log

# Ver últimos resultados
cat ofertas.md

# Ver estado
cat state.json

# Ver marcador de última ejecución
cat scraper_result.json
```

---

## ⚙️ **Configuración por Entorno**

### Variables de entorno disponibles:

| Variable | Default | Descripción |
|----------|---------|-------------|
| `DISCOUNT_THRESHOLD` | 40 | Descuento mínimo (%) |
| `REQUEST_TIMEOUT` | 30 | Timeout peticiones (s) |
| `OUTPUT_FILE` | ofertas.md | Archivo de salida |
| `STATE_FILE` | state.json | Archivo de estado |
| `DEBUG_MODE` | false | Modo debug |
| `LOG_LEVEL` | INFO | Nivel de logs |
| `PLATFORM` | generic | Plataforma de deploy |

### Ejemplo para diferentes casos:

```bash
# Para scraping agresivo (más frecuente)
DISCOUNT_THRESHOLD=30
REQUEST_TIMEOUT=60

# Para testing
DEBUG_MODE=true
LOG_LEVEL=DEBUG

# Para producción estable
DISCOUNT_THRESHOLD=50
REQUEST_TIMEOUT=45
```

---

## 🔧 **Solución de Problemas**

### Error: "No module named 'requests'"
```bash
# Solución: Reinstalar dependencias
pip install -r requirements.txt
```

### Error: "Permission denied"
```bash
# Solución: Dar permisos de ejecución
chmod +x run_server.py
```

### El scraper no encuentra productos
```bash
# Ejecutar en modo debug
DEBUG_MODE=true python run_server.py
```

### No se actualizan los resultados
```bash
# Verificar que el archivo se esté modificando
ls -la ofertas.md state.json
tail -f scraper.log
```

---

## 📈 **Recomendaciones por Uso**

| Uso | Plataforma | Frecuencia | Costo |
|-----|------------|------------|-------|
| **Personal/Ocasional** | GitHub Actions | Manual + automático | 🆓 Gratis |
| **Regular/Familiar** | Railway | Automático | $5/mes |
| **Comercial/Intensivo** | VPS propio | Automático | $10-20/mes |
| **Experimentación** | Docker local | Manual | 🆓 Gratis |

---

## 🚨 **Consideraciones Importantes**

### Legal y Ético:
- ✅ Respeta `robots.txt` de Blackisard
- ✅ Usa User-Agent identificable
- ✅ No hagas scraping excesivo
- ✅ Úsalo solo para fines personales/educativos

### Técnico:
- ✅ El scraper incluye delays entre peticiones
- ✅ Maneja errores y timeouts gracefully
- ✅ Guarda estado para evitar duplicados
- ✅ Logs detallados para debugging

### Robustez:
- ✅ Reintentos automáticos en fallos
- ✅ Detección automática de páginas
- ✅ Filtros robustos para precios
- ✅ Compatibilidad con cambios en la web

---

## 🎯 **Próximos Pasos**

1. **Elige una plataforma** de la lista arriba
2. **Sigue los pasos** de configuración
3. **Ejecuta el scraper** una vez manualmente
4. **Verifica los resultados** en `ofertas.md`
5. **Configura la frecuencia** deseada
6. **¡Disfruta de las ofertas automáticas!**

---

**¿Necesitas ayuda?** El proyecto incluye logs detallados y manejo robusto de errores para facilitar el debugging.