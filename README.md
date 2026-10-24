# Waifu Downloader for Windows

This Windows port is based on [NyarchLinux/WaifuDownloader](https://github.com/NyarchLinux/WaifuDownloader)
and remains licensed under GPL-3.0-or-later. Upstream license files and notices are included.

## Credits

- Original application: [NyarchLinux/WaifuDownloader](https://github.com/NyarchLinux/WaifuDownloader).
- Original copyright and license notices are retained in the source files.
- Windows-specific changes are part of this port and remain under GPL-3.0-or-later.

The application reuses the original GTK4/libadwaita UI, icons, and mascot. Available providers are
Waifu.im, Danbooru, and yande.re. Select a provider on the **Provider** page in Preferences.
**Auto** is selected by default and tries another provider if one fails or returns no results.

## Added in this Windows port

- Search images by name or tags.
- Choose Waifu.im, Danbooru, or yande.re manually, or use **Auto** to fall back between providers.
- Optionally resolve provider host names through Cloudflare DNS over HTTPS.

Click the search icon in the header to open the provider search field. Waifu.im searches one tag;
Danbooru and yande.re accept booru tag syntax, for example `genshin_impact raiden_shogun`.
The NSFW switch filters to rating `s` when off and non-safe ratings when on.

The **Use DNS over HTTPS** option in Preferences uses Cloudflare DNS. It is off by default and can
help only when a provider is blocked at the DNS-resolution level. It does not affect blocks at other
network layers.

## Windows setup

1. Install MSYS2 from [msys2.org](https://www.msys2.org/).
2. Open PowerShell in the project folder and run:

   ```powershell
   .\setup_windows.ps1
   .\run_windows.ps1
   ```

To create a distributable Windows build, run this in PowerShell from the project folder:

```powershell
.\build_windows.ps1
```

The script installs the MSYS2 UCRT64 build dependencies, compiles the GTK resources, and packages
the app with PyInstaller. It creates a folder build and a ZIP asset:

- `dist\Waifu Downloader for Windows\Waifu Downloader for Windows.exe`
- `dist\WaifuDownloader-Windows-x64.zip`

Use the ZIP for distribution. It contains the executable and its bundled runtime files; do not
upload only the `.exe`. Folder builds are used because GTK applications need supporting DLLs and
data files alongside the executable. Build on 64-bit Windows with MSYS2 installed.

## Publish a GitHub Release

1. Push this project folder to your GitHub repository.
2. Open the repository on GitHub and select **Releases** → **Create a new release**.
3. Create and select a version tag, for example `v1.0.0`, and enter a release title.
4. Drag `dist\WaifuDownloader-Windows-x64.zip` into the release asset area.
5. Add release notes, then select **Publish release**.

Users download the ZIP, extract it, and launch `Waifu Downloader for Windows.exe` from the
extracted folder.

The original app icon is available as [waifu-downloader.ico](data/icons/waifu-downloader.ico) and is
also registered with GTK. Preferences are stored in `%APPDATA%\Waifu Downloader for Windows\config.json`.
