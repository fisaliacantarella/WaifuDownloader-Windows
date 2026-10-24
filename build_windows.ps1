$ErrorActionPreference = "Stop"

$bash = "C:\msys64\usr\bin\bash.exe"
$cygpath = "C:\msys64\usr\bin\cygpath.exe"
if (-not (Test-Path -LiteralPath $bash) -or -not (Test-Path -LiteralPath $cygpath)) {
    throw "MSYS2 is not installed. Install it from https://www.msys2.org/, then run this script again."
}

& (Join-Path $PSScriptRoot "setup_windows.ps1")
if ($LASTEXITCODE -ne 0) { throw "GTK/PyInstaller dependency setup failed." }

$env:MSYSTEM = "UCRT64"
$env:CHERE_INVOKING = "1"
$unixProjectPath = & $cygpath -u $PSScriptRoot
$buildCommand = "cd '$unixProjectPath' && mkdir -p build && glib-compile-resources src/waifudownloader.gresource.xml --sourcedir=src --target=build/waifudownloader-windows.gresource && pyinstaller --noconfirm --clean --windowed --onedir --name 'Waifu Downloader for Windows' --icon data/icons/waifu-downloader.ico --add-data 'build/waifudownloader-windows.gresource;.' --add-data 'data;data' --add-data 'C:/msys64/ucrt64/lib/girepository-1.0;gi_typelibs' --hidden-import gi.overrides.Gtk --hidden-import gi.overrides.Gdk --hidden-import gi._gtktemplate windows_app.py"
& $bash -lc $buildCommand
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed to build the Windows application." }

$distFolder = Join-Path $PSScriptRoot "dist\Waifu Downloader for Windows"
$executable = Join-Path $distFolder "Waifu Downloader for Windows.exe"
$releaseZip = Join-Path $PSScriptRoot "dist\WaifuDownloader-Windows-x64.zip"
if (-not (Test-Path -LiteralPath $executable)) { throw "Build output is missing: $executable" }
if (Test-Path -LiteralPath $releaseZip) { Remove-Item -LiteralPath $releaseZip -Force }
Compress-Archive -Path (Join-Path $distFolder "*") -DestinationPath $releaseZip -ErrorAction Stop
if (-not (Test-Path -LiteralPath $releaseZip)) { throw "Could not create release archive: $releaseZip" }

Write-Host "Build complete."
Write-Host "Executable: $distFolder\Waifu Downloader for Windows.exe"
Write-Host "GitHub Release asset: $releaseZip"
