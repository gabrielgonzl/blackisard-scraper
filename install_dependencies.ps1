Write-Host "🚀 Instalando dependencias del Blackisard Scraper..." -ForegroundColor Green
Write-Host ""

Write-Host "📦 Instalando requests..." -ForegroundColor Yellow
pip install requests

Write-Host "📦 Instalando beautifulsoup4..." -ForegroundColor Yellow
pip install beautifulsoup4

Write-Host ""
Write-Host "✅ ¡Instalación completada!" -ForegroundColor Green
Write-Host ""
Write-Host "🎯 Ahora puedes ejecutar:" -ForegroundColor Cyan
Write-Host "   python scraper.py --debug" -ForegroundColor White
Write-Host ""
Write-Host "Presiona cualquier tecla para continuar..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")