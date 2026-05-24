param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$BackupTime = "03:00",
    [string]$UpdateTime = "03:30"
)

$ErrorActionPreference = "Stop"

$project = (Resolve-Path $ProjectRoot).Path
$backupScript = Join-Path $project "scripts\backup-project.ps1"
$updateScript = Join-Path $project "scripts\update-from-github.ps1"

$backupAction = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$backupScript`" -ProjectRoot `"$project`""

$updateAction = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$updateScript`" -ProjectRoot `"$project`""

$backupTrigger = New-ScheduledTaskTrigger -Daily -At $BackupTime
$updateTrigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At $UpdateTime

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2)

Register-ScheduledTask `
    -TaskName "Klein Haitabu Backup" `
    -Action $backupAction `
    -Trigger $backupTrigger `
    -Settings $settings `
    -Description "Erstellt taeglich ein Backup der Klein Haitabu Plattform." `
    -Force | Out-Null

Register-ScheduledTask `
    -TaskName "Klein Haitabu GitHub Update" `
    -Action $updateAction `
    -Trigger $updateTrigger `
    -Settings $settings `
    -Description "Erstellt ein Backup und zieht danach sonntags Updates von GitHub." `
    -Force | Out-Null

Write-Host "Windows-Aufgaben wurden eingerichtet:"
Write-Host "- Klein Haitabu Backup: taeglich um $BackupTime"
Write-Host "- Klein Haitabu GitHub Update: sonntags um $UpdateTime"
