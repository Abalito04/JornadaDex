param(
    [string]$TaskName = "JornadaDex Daily PostgreSQL Backup",
    [string]$Time = "03:00",
    [string]$BackupDir = (Join-Path $PSScriptRoot "..\backups"),
    [string]$PgDumpPath = "pg_dump",
    [int]$KeepDays = 30
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($env:DATABASE_URL)) {
    throw "DATABASE_URL no esta disponible en esta sesion. Configurala primero como variable de usuario de Windows."
}

$backupScript = Join-Path $PSScriptRoot "backup_database.ps1"
if (-not (Test-Path -LiteralPath $backupScript)) {
    throw "No se encontro $backupScript"
}

$pgDumpCommand = Get-Command $PgDumpPath -ErrorAction SilentlyContinue
if (-not $pgDumpCommand) {
    throw "No se encontro pg_dump en '$PgDumpPath'. Pasa -PgDumpPath con la ruta completa a pg_dump.exe."
}

$resolvedPgDumpPath = $pgDumpCommand.Source
$trigger = New-ScheduledTaskTrigger -Daily -At $Time
$argument = "-NoProfile -ExecutionPolicy Bypass -File `"$backupScript`" -BackupDir `"$BackupDir`" -PgDumpPath `"$resolvedPgDumpPath`" -KeepDays $KeepDays"
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $argument
$userId = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
$principal = New-ScheduledTaskPrincipal -UserId $userId -LogonType Interactive -RunLevel LeastPrivilege
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2)

Register-ScheduledTask -TaskName $TaskName -Trigger $trigger -Action $action -Principal $principal -Settings $settings -Force | Out-Null

Write-Host "Tarea instalada: $TaskName"
Write-Host "Horario diario: $Time"
Write-Host "Carpeta de backups: $BackupDir"
Write-Host "pg_dump: $resolvedPgDumpPath"
Write-Host "Para probar ahora: powershell -ExecutionPolicy Bypass -File `"$backupScript`" -PgDumpPath `"$resolvedPgDumpPath`""
