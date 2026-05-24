param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$BackupRoot = (Join-Path (Split-Path (Resolve-Path "$PSScriptRoot\..").Path -Parent) "Klein Haitabu Backups"),
    [int]$RetentionDays = 30
)

$ErrorActionPreference = "Stop"

$project = (Resolve-Path $ProjectRoot).Path
$timestamp = Get-Date -Format "yyyy-MM-dd_HH-mm-ss"
$backupDir = Join-Path $BackupRoot $timestamp
$zipPath = Join-Path $BackupRoot "klein-haitabu_$timestamp.zip"
$manifestPath = Join-Path $BackupRoot "klein-haitabu_$timestamp.txt"

$excludedTopLevel = @(".git", ".venv", "_backups")
$excludedNames = @("__pycache__", "staticfiles")
$excludedExtensions = @(".pyc", ".pyo", ".log")

New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null
New-Item -ItemType Directory -Force -Path $backupDir | Out-Null

function Test-ExcludedPath {
    param([string]$Path)

    $relative = $Path.Substring($project.Length).TrimStart("\", "/")
    if ([string]::IsNullOrWhiteSpace($relative)) {
        return $false
    }

    $parts = $relative -split "[\\/]"
    if ($parts.Count -gt 0 -and $excludedTopLevel -contains $parts[0]) {
        return $true
    }

    foreach ($part in $parts) {
        if ($excludedNames -contains $part) {
            return $true
        }
    }

    if ($excludedExtensions -contains ([System.IO.Path]::GetExtension($Path))) {
        return $true
    }

    return $false
}

Get-ChildItem -Path $project -Recurse -Force -File |
    Where-Object { -not (Test-ExcludedPath $_.FullName) } |
    ForEach-Object {
        $relative = $_.FullName.Substring($project.Length).TrimStart("\", "/")
        $target = Join-Path $backupDir $relative
        $targetParent = Split-Path $target -Parent

        New-Item -ItemType Directory -Force -Path $targetParent | Out-Null
        Copy-Item -LiteralPath $_.FullName -Destination $target -Force
    }

Compress-Archive -Path (Join-Path $backupDir "*") -DestinationPath $zipPath -Force
Remove-Item -LiteralPath $backupDir -Recurse -Force

$manifest = @(
    "Klein Haitabu Backup",
    "Erstellt: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")",
    "Projekt: $project",
    "Archiv: $zipPath",
    "",
    "Enthalten: Projektdateien, lokale SQLite-Datenbank, .env, Dokumentation",
    "Ausgeschlossen: .git, .venv, _backups, __pycache__, staticfiles, *.pyc, *.pyo, *.log",
    "",
    "Wichtig: Dieses Backup kann Zugangsdaten aus .env enthalten. Bitte sicher ablegen."
)

Set-Content -Path $manifestPath -Value $manifest -Encoding UTF8

$cutoff = (Get-Date).AddDays(-$RetentionDays)
Get-ChildItem -Path $BackupRoot -File -Filter "klein-haitabu_*" |
    Where-Object { $_.LastWriteTime -lt $cutoff } |
    Remove-Item -Force

Write-Host "Backup erstellt:"
Write-Host $zipPath
