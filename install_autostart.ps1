$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$batPath = Join-Path $scriptDir "run_bot_forever.bat"
$startupFolder = [Environment]::GetFolderPath("Startup")
$shortcutPath = Join-Path $startupFolder "Bot Ticket TDT.lnk"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $batPath
$shortcut.WorkingDirectory = $scriptDir
$shortcut.WindowStyle = 7
$shortcut.Description = "Tu dong chay Bot Ticket TDT khi bat may"
$shortcut.Save()

Write-Host "[OK] Da them bot vao Windows Startup!"
Write-Host "     Bot se tu chay khi ban bat may va login Windows."
Write-Host ""
Write-Host "LUU Y: Tat may = bot offline."
Write-Host "       Muon online 24/7 ke ca khi tat may -> xem file HOSTING_24_7.md"
