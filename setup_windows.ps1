$ErrorActionPreference = "Stop"
$bash = "C:\msys64\usr\bin\bash.exe"

if (-not (Test-Path -LiteralPath $bash)) {
    throw "MSYS2 is not installed. Install it from https://www.msys2.org/, then run this script again."
}

$env:MSYSTEM = "UCRT64"
$env:CHERE_INVOKING = "1"
& $bash -lc "pacman -S --needed --noconfirm mingw-w64-ucrt-x86_64-python mingw-w64-ucrt-x86_64-python-gobject mingw-w64-ucrt-x86_64-gtk4 mingw-w64-ucrt-x86_64-libadwaita mingw-w64-ucrt-x86_64-adwaita-icon-theme mingw-w64-ucrt-x86_64-python-requests mingw-w64-ucrt-x86_64-pyinstaller"
if ($LASTEXITCODE -ne 0) { throw "Installing GTK4/PyGObject through MSYS2 failed." }

Write-Host "GTK dependencies are ready. Launch the app with .\run_windows.ps1"
