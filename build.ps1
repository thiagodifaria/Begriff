Write-Host "Iniciando o ciclo completo de build do ambiente Begriff..." -ForegroundColor Green

Write-Host "[PASSO 1/4] Parando e removendo contêineres existentes..." -ForegroundColor Yellow
docker-compose down --remove-orphans

Write-Host "[PASSO 2/4] Limpando cache de build, redes, imagens e volumes não utilizados..." -ForegroundColor Yellow
docker system prune -af --volumes

Write-Host "[PASSO 3/4] Reconstruindo todas as imagens do zero (pode levar vários minutos)..." -ForegroundColor Cyan
docker-compose build --no-cache --parallel

if ($LASTEXITCODE -ne 0) {
    Write-Host "O processo de build falhou. Verifique os logs de erro acima." -ForegroundColor Red
    exit 1
}

Write-Host "[PASSO 4/4] Iniciando todos os servicos em modo 'detached'..." -ForegroundColor Cyan
docker-compose up -d

Write-Host "Ambiente Begriff iniciado com sucesso! Todos os servicos estão rodando em segundo plano." -ForegroundColor Green