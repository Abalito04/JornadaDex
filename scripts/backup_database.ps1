param(
    [string]$DatabaseUrl = $env:DATABASE_URL,
    [string]$BackupDir = (Join-Path $PSScriptRoot "..\backups"),
    [string]$PgDumpPath = "pg_dump",
    [int]$KeepDays = 30,
    [int]$RetryCount = 5,
    [int]$RetryDelaySeconds = 30
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
$pgDumpErrorFile = Join-Path $BackupDir ("jornadadex-{0}.pg_dump.err" -f $timestamp)

Write-BackupLog "Iniciando backup en $backupFile"

$lastPgDumpError = ""
for ($attempt = 1; $attempt -le $RetryCount; $attempt++) {
    if (Test-Path -LiteralPath $pgDumpErrorFile) {
        Remove-Item -LiteralPath $pgDumpErrorFile -Force
    }

    & $pgDumpCommand.Source --format=custom --no-owner --no-privileges --file $backupFile $DatabaseUrl 2> $pgDumpErrorFile
    if ($LASTEXITCODE -eq 0) {
        break
    }

    $lastPgDumpError = ""
    if (Test-Path -LiteralPath $pgDumpErrorFile) {
        $lastPgDumpError = (Get-Content -LiteralPath $pgDumpErrorFile -Raw).Trim()
    }

    if (Test-Path -LiteralPath $backupFile) {
        Remove-Item -LiteralPath $backupFile -Force
    }

    Write-BackupLog "pg_dump fallo en intento $attempt/$RetryCount con codigo $LASTEXITCODE. Error: $lastPgDumpError"

    if ($attempt -lt $RetryCount) {
        Start-Sleep -Seconds $RetryDelaySeconds
    }
}

if ($LASTEXITCODE -ne 0) {
    throw "pg_dump fallo despues de $RetryCount intentos. Ultimo error: $lastPgDumpError"
}

if (Test-Path -LiteralPath $pgDumpErrorFile) {
    Remove-Item -LiteralPath $pgDumpErrorFile -Force
}

$hash = Get-FileHash -LiteralPath $backupFile -Algorithm SHA256
Set-Content -LiteralPath ($backupFile + ".sha256") -Value ("{0}  {1}" -f $hash.Hash, (Split-Path $backupFile -Leaf))

$cutoff = (Get-Date).AddDays(-$KeepDays)
Get-ChildItem -LiteralPath $BackupDir -File |
    Where-Object { ($_.Name -like "*.dump" -or $_.Name -like "*.dump.sha256") -and $_.LastWriteTime -lt $cutoff } |
    Remove-Item -Force

Write-BackupLog "Backup completado OK. Archivo: $backupFile"
