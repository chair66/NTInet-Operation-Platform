$ErrorActionPreference = "Stop"

$projectRoot = (Get-Location).Path
$targetPath = Join-Path $projectRoot "app\services\conversation_service.py"

if (-not (Test-Path $targetPath)) {
    throw "Run this script from the ntinet-operations-platform folder. Could not find: $targetPath"
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$source = [System.IO.File]::ReadAllText($targetPath)

$oldImport = "from sqlalchemy.orm import Session"
$newImport = "from sqlalchemy.orm import Session, noload"
$oldStatement = "statement = select(CommunicationConversation)"
$newStatement = "statement = select(CommunicationConversation).options(noload(CommunicationConversation.messages))"

if ($source.Contains($newStatement)) {
    Write-Host "The conversation query hotfix is already installed." -ForegroundColor Green
    exit 0
}

if (-not $source.Contains($oldImport)) {
    throw "Expected SQLAlchemy import was not found. No files were changed."
}

if (-not $source.Contains($oldStatement)) {
    throw "Expected conversation list query was not found. No files were changed."
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backupPath = "$targetPath.pre-v1.24.2-$stamp.bak"
Copy-Item $targetPath $backupPath

$updated = $source.Replace($oldImport, $newImport).Replace($oldStatement, $newStatement)
[System.IO.File]::WriteAllText($targetPath, $updated, $utf8NoBom)

python -m py_compile $targetPath
if ($LASTEXITCODE -ne 0) {
    Copy-Item $backupPath $targetPath -Force
    throw "Python validation failed. The original file was restored from $backupPath"
}

Write-Host "NOP v1.24.2 conversation query hotfix installed successfully." -ForegroundColor Green
Write-Host "Backup: $backupPath"
Write-Host "Restart NOP, then open http://127.0.0.1:8000/customers/7"
