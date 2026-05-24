param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$Branch = "main",
    [string]$BackupRoot = (Join-Path (Split-Path (Resolve-Path "$PSScriptRoot\..").Path -Parent) "Klein Haitabu Backups")
)

$ErrorActionPreference = "Stop"

$project = (Resolve-Path $ProjectRoot).Path
$backupScript = Join-Path $PSScriptRoot "backup-project.ps1"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git wurde nicht gefunden. Bitte Git for Windows installieren oder den Git-Ordner zum PATH hinzufuegen."
}

Write-Host "Erstelle Sicherheitsbackup vor dem Update..."
& $backupScript -ProjectRoot $project -BackupRoot $BackupRoot

Push-Location $project
try {
    $dirty = git status --porcelain
    if ($dirty) {
        Write-Host ""
        Write-Host "Update gestoppt: Es gibt lokale Aenderungen im Projekt."
        Write-Host "Das Backup wurde bereits erstellt. Bitte Aenderungen pruefen, committen oder sichern."
        exit 2
    }

    git fetch origin $Branch

    $local = git rev-parse HEAD
    $remote = git rev-parse "origin/$Branch"

    if ($local -eq $remote) {
        Write-Host "Projekt ist bereits aktuell."
        exit 0
    }

    git pull --ff-only origin $Branch
    Write-Host "Update von GitHub abgeschlossen."
}
finally {
    Pop-Location
}
