# 🎛️ CONFIGURACIÓN AVANZADA - GitHub Actions

## Cambiar frecuencia de ejecución

Edita `.github/workflows/scrape.yml`:

```yaml
schedule:
  # Cada 6 horas (actual)
  - cron: '0 */6 * * *'
  
  # Opciones populares:
  - cron: '0 */12 * * *'  # Cada 12 horas
  - cron: '0 8,20 * * *'  # Dos veces al día (8am y 8pm)
  - cron: '0 8 * * *'     # Diario a las 8am
  - cron: '0 */4 * * *'   # Cada 4 horas
```

## Variables de entorno

Ve a: Settings > Secrets and variables > Actions

Añade estos secrets:
```
DISCOUNT_THRESHOLD=40          # Descuento mínimo
REQUEST_TIMEOUT=30             # Timeout peticiones
OUTPUT_FILE=ofertas.md         # Archivo salida
STATE_FILE=state.json          # Archivo estado
LOG_LEVEL=INFO                 # Nivel logs
```

## Habilitar notifications

En GitHub:
1. Ve a Settings > Notifications  
2. Actions: ✅ Enabled
3. Selecciona cómo quieres recibir notificaciones

## Webhook para Discord/Telegram

Crea un webhook (URL) y añade en el workflow:

```yaml
- name: Notify Discord
  run: |
    curl -X POST ${{ secrets.DISCORD_WEBHOOK }} \
      -H "Content-Type: application/json" \
      -d '{"content":"🎯 Blackisard scraper ejecutado. Nuevas ofertas detectadas!"}'
```

## Configurar push automático

El workflow ya incluye:
```yaml
git add ofertas.md state.json || echo "No hay cambios"
git commit -m "Actualizar ofertas - $(date)" || echo "Sin cambios"
git push || echo "Push falló"
```

## Monitoreo

Puedes añadir alertas:
- **Email notifications**: En Settings > Notifications
- **Discord webhook**: Para notificaciones en tiempo real  
- **Slack integration**: Para equipos

## Scheduling avanzado

Para ejecución bajo demanda:
```yaml
workflow_dispatch:  # Habilita ejecución manual
  inputs:
    discount_threshold:
      description: 'Descuento mínimo (%)'
      required: false
      default: '40'
      type: choice
      options:
      - '30'
      - '40' 
      - '50'
```

## Debug y troubleshooting

Si algo falla:

1. **Ve a Actions > Run > Details**
2. **Revisa los logs** línea por línea
3. **Verifica artifacts** (ofertas.md, state.json)
4. **Ejecuta manualmente** para testing

## Límites de GitHub Actions

**Gratis incluye**:
- 2000 minutos/mes
- 500MB storage
- Ejecuta en Ubuntu, Windows, macOS

**Para uso intensivo**, considera Railway o VPS propio.