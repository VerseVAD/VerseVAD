$ErrorActionPreference = "Stop"

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$UvDirectory = Join-Path $ProjectRoot ".tools\uv"
$UvExecutable = Join-Path $UvDirectory "uv.exe"
$RuntimeDirectory = Join-Path $ProjectRoot ".runtime"
$VirtualEnvironment = Join-Path $ProjectRoot ".venv"
$VirtualEnvironmentConfig = Join-Path $VirtualEnvironment "pyvenv.cfg"
$DownloadDirectory = Join-Path $RuntimeDirectory "downloads"
$UvArchive = Join-Path $DownloadDirectory "uv-0.11.30.zip"
$ExpectedUvHash = "be8d78c992312212e5cc05e9f9de3fa996db73b7c86a186dfb9231eb9f91d33e"
$UvUrl = "https://github.com/astral-sh/uv/releases/download/0.11.30/uv-x86_64-pc-windows-msvc.zip"

Write-Host "VerseVAD local setup"
Write-Host "This creates a private Python environment inside the project folder."
Write-Host "It does not require administrator access or change system-wide Python settings."
Write-Host "Setup may download the pinned Python runtime and dependencies."
Write-Host "Poems and lexicons are not uploaded."
Write-Host ""

if (-not (Test-Path -LiteralPath $UvExecutable)) {
    Write-Host "Downloading the pinned project setup tool (uv 0.11.30)..."
    New-Item -ItemType Directory -Force -Path $UvDirectory | Out-Null
    New-Item -ItemType Directory -Force -Path $DownloadDirectory | Out-Null
    Invoke-WebRequest -Uri $UvUrl -OutFile $UvArchive -UseBasicParsing
    $ObservedHash = (Get-FileHash -LiteralPath $UvArchive -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($ObservedHash -ne $ExpectedUvHash) {
        throw "The downloaded setup-tool checksum did not match. No archive was extracted."
    }
    Expand-Archive -LiteralPath $UvArchive -DestinationPath $UvDirectory -Force
}

if (-not (Test-Path -LiteralPath $UvExecutable)) {
    throw "The local setup tool is still missing after setup. Please report this message."
}

$env:UV_CACHE_DIR = Join-Path $RuntimeDirectory "uv-cache"
$env:UV_PYTHON_INSTALL_DIR = Join-Path $RuntimeDirectory "python"
$env:UV_PYTHON_INSTALL_REGISTRY = "0"
$env:UV_PYTHON_PREFERENCE = "only-managed"

# A Python virtual environment records absolute interpreter and launcher paths.
# If the VerseVAD folder was moved or renamed, rebuild only that disposable
# environment before syncing. The downloaded runtime and private research
# resources remain untouched.
if (Test-Path -LiteralPath $VirtualEnvironmentConfig) {
    $ConfiguredHomeLine = Get-Content -LiteralPath $VirtualEnvironmentConfig |
        Where-Object { $_ -match "^home\s*=" } |
        Select-Object -First 1
    $ConfiguredHome = if ($ConfiguredHomeLine) {
        ($ConfiguredHomeLine -split "=", 2)[1].Trim()
    } else {
        ""
    }
    if (-not $ConfiguredHome -or -not (Test-Path -LiteralPath $ConfiguredHome)) {
        $ResolvedVirtualEnvironment = [System.IO.Path]::GetFullPath($VirtualEnvironment)
        $ResolvedParent = Split-Path -Parent $ResolvedVirtualEnvironment
        if ($ResolvedParent -ne $ProjectRoot -or
            (Split-Path -Leaf $ResolvedVirtualEnvironment) -ne ".venv") {
            throw "Refusing to rebuild an environment outside the VerseVAD folder."
        }
        Write-Host "The VerseVAD folder moved; rebuilding its disposable local environment..."
        Remove-Item -LiteralPath $ResolvedVirtualEnvironment -Recurse -Force
    }
}

Write-Host "Creating or checking the locked project environment..."
& $UvExecutable sync --locked
if ($LASTEXITCODE -ne 0) {
    throw "The locked project environment could not be created."
}

Write-Host "Running VerseVAD's local diagnostic checks..."
& $UvExecutable run --frozen --offline versevad-diagnose --quick --runtime-only
if ($LASTEXITCODE -ne 0) {
    throw "Setup finished, but one or more diagnostic checks failed."
}

Write-Host ""
Write-Host "VerseVAD setup completed successfully."
Write-Host "Double-click start_versevad.bat to open the application."
