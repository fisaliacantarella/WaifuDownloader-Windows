$ErrorActionPreference = "Stop"
$bash = "C:\msys64\usr\bin\bash.exe"
$cygpath = "C:\msys64\usr\bin\cygpath.exe"

if (-not (Test-Path -LiteralPath $bash)) {
    throw "MSYS2 is not installed. Run .\setup_windows.ps1 first."
}

$env:MSYSTEM = "UCRT64"
$env:CHERE_INVOKING = "1"
$projectPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$unixProjectPath = & $cygpath -u $projectPath
& $bash -lc "cd '$unixProjectPath' && python windows_app.py"
exit $LASTEXITCODE
