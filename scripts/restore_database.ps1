param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile,
    [string]$DatabaseUrl = $env:TEST_DATABASE_URL,
    [string]$PgRestorePath = "pg_restore"
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($DatabaseUrl)) {
    throw "TEST_DATABASE_URL no esta configurada. No restaures sobre produccion; usa una base de prueba."
}

if (-not (Test-Path -LiteralPath $BackupFile)) {
    throw "No existe el archivo de backup: $BackupFile"
}

$pgRestoreCommand = Get-Command $PgRestorePath -ErrorAction SilentlyContinue
if (-not $pgRestoreCommand) {
    throw "No se encontro pg_restore. Instala PostgreSQL client tools o pasa -PgRestorePath con la ruta completa a pg_restore.exe."
}

Write-Host "Restaurando $BackupFile en base de prueba..."
& $pgRestoreCommand.Source --clean --if-exists --no-owner --no-privileges --dbname $DatabaseUrl $BackupFile
if ($LASTEXITCODE -ne 0) {
    throw "pg_restore fallo con codigo $LASTEXITCODE"
}

Write-Host "Restore completado OK."
