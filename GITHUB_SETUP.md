# 🚀 INSTRUCCIONES PARA SUBIR A GITHUB

## ✅ PASO 1: Crear el repositorio en GitHub

1. **Ve a**: https://github.com/new
2. **Owner**: gabrielgonzl
3. **Repository name**: `blackisard-scraper`
4. **Description**: `Scraper automático de ofertas de Blackisard - Detecta descuentos ≥40%`
5. **Public** ✅ (recomendado para Actions gratis)
6. **NO marques** "Add a README file"
7. **Click**: "Create repository"

## ✅ PASO 2: Conectar y subir código

Después de crear el repositorio, GitHub te mostrará una página. Copia y pega estos comandos:

```bash
# En tu terminal local, en el directorio del scraper:
cd /ruta/a/tu/directorio/blackisard-scraper

# Conectar con tu repositorio de GitHub
git remote add origin https://github.com/gabrielgonzl/blackisard-scraper.git

# Subir código
git push -u origin main
```

## ✅ PASO 3: ¡YA ESTÁ LISTO!

Una vez subido el código:

1. **Ve a tu repositorio**: https://github.com/gabrielgonzl/blackisard-scraper
2. **Click en "Actions"** (en la barra superior)
3. **El workflow se ejecutará automáticamente** la primera vez
4. **Para ejecutarlo manualmente**:
   - Ve a Actions > "Blackisard Scraper" > "Run workflow"

## 📊 CONFIGURACIÓN AUTOMÁTICA

El scraper viene preconfigurado con:

- ⏰ **Ejecución automática**: Cada 6 horas
- 🎯 **Threshold**: 40% descuento mínimo
- 📁 **Archivos generados**: 
  - `ofertas.md` - Lista de ofertas
  - `state.json` - Estado persistente
  - `scraper.log` - Logs de ejecución

## 🔧 VARIABLES DE ENTORNO (Opcional)

Si quieres cambiar la configuración:

1. **Ve a**: Settings > Secrets and variables > Actions
2. **Añade variables**:
   - `DISCOUNT_THRESHOLD`: `40`
   - `REQUEST_TIMEOUT`: `30`

## 🚨 PRIMERA EJECUCIÓN

**Recomendación**: Ejecuta manualmente la primera vez para verificar que todo funciona:

1. Ve a Actions
2. Selecciona "Blackisard Scraper" 
3. Click "Run workflow"
4. Espera a que termine (puede tomar 2-3 minutos)
5. Verifica los resultados en la pestaña "Artifacts"

## 📁 DESPUÉS DEL PRIMER RUN

Una vez ejecutado, podrás:

- **Descargar resultados**: Actions > Run > Artifacts
- **Ver ofertas**: `ofertas.md` 
- **Ver estado**: `state.json`
- **Ver logs**: `scraper.log`

## ⏰ AUTOMATIZACIÓN

**Ya está configurado** para ejecutarse automáticamente cada 6 horas:
- `0 */6 * * *` (cada 6 horas)
- Puedes cambiar esto editando `.github/workflows/scrape.yml`

## 🆘 SI ALGO FALLA

1. **Revisa los logs**: Actions > Run > Details
2. **El log de errores está al final** de la ejecución
3. **Puedes ejecutar manualmente** para debuggear

---

## 🎉 ¡DISFRUTA DE TUS OFERTAS AUTOMÁTICAS!

Una vez configurado, el scraper detectará automáticamente:
- ✅ Productos en stock
- ✅ Descuentos reales ≥40%
- ✅ Solo ofertas nuevas (no duplicados)
- ✅ Te registrará cambios de precio

**¡Tu scraper de Blackisard está listo para funcionar en la nube!** 🚀