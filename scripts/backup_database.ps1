param(
    [string]$DatabaseUrl = $env:DATABASE_URL,
    [string]$BackupDir = (Join-Path $PSScriptRoot "..\backups"),
    [string]$PgDumpPath = "pg_dump",
    [int]$KeepDays = 30
)

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logFile = Join-Path $BackupDir "backup.log"

function Write-BackupLog {
    param([string]$Message)
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Write-Host $line
    Add-Content -LiteralPath $logFile -Value $line
}

if ([string]::IsNullOrWhiteSpace($DatabaseUrl)) {
    throw "DATABASE_URL no esta configurada. Cargala como variable de entorno antes de ejecutar el backup."
}

New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

$pgDumpCommand = Get-Command $PgDumpPath -ErrorAction SilentlyContinue
if (-not $pgDumpCommand) {
    throw "No se encontro pg_dump. Instala PostgreSQL client tools o pasa -PgDumpPath con la ruta completa a pg_dump.exe."
}

$backupFile = Join-Path $BackupDir ("jornadadex-{0}.dump" -f $timestamp)

Write-BackupLog "Iniciando backup en $backupFile"

& $pgDumpCommand.Source --format=custom --no-owner --no-privileges --file $backupFile $DatabaseUrl
if ($LASTEXITCODE -ne 0) {
    if (Test-Path -LiteralPath $backupFile) {
        Remove-Item -LiteralPath $backupFile -Force
    }
    throw "pg_dump fallo con codigo $LASTEXITCODE"
}

$hash = Get-FileHash -LiteralPath $backupFile -Algorithm SHA256
Set-Content -LiteralPath ($backupFile + ".sha256") -Value ("{0}  {1}" -f $hash.Hash, (Split-Path $backupFile -Leaf))

$cutoff = (Get-Date).AddDays(-$KeepDays)
Get-ChildItem -LiteralPath $BackupDir -File |
    Where-Object { ($_.Name -like "*.dump" -or $_.Name -like "*.dump.sha256") -and $_.LastWriteTime -lt $cutoff } |
    Remove-Item -Force

Write-BackupLog "Backup completado OK. Archivo: $backupFile"
